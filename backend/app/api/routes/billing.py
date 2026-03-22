from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import BillingEvent, User, build_billing_event_key
from ...schemas import BillingWebhookResponse, PremiumCheckoutSessionResponse
from ...services.auth import get_current_user, get_user_by_email, get_user_by_id
from ...dependencies import settings


router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

PREMIUM_PRIMARY_COLOR = "#3b82f6"
PREMIUM_NEUTRAL_COLOR = "#94a3b8"
PREMIUM_BACKGROUND_COLOR = "#020617"


def _normalize_key(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def _normalize_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        text = str(value).strip()
        return text or None
    return None


def _iter_payload_mappings(value: Any):
    if isinstance(value, dict):
        yield value
        for nested_value in value.values():
            yield from _iter_payload_mappings(nested_value)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_payload_mappings(item)


def _find_first_value(payload: dict[str, Any], keys: set[str]) -> Any:
    normalized_keys = {_normalize_key(key) for key in keys}
    for mapping in _iter_payload_mappings(payload):
        for key, value in mapping.items():
            if _normalize_key(str(key)) in normalized_keys and value not in (None, "", []):
                return value
    return None


def _extract_additional_json(payload: dict[str, Any]) -> dict[str, str]:
    raw = _find_first_value(payload, {"additionalJSON", "additional_json"})
    if raw is None:
        return {}
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        text = _normalize_string(value)
        if text is not None:
            normalized[str(key)] = text
    return normalized


def _extract_paylink_id(payload: dict[str, Any]) -> str | None:
    direct = _normalize_string(_find_first_value(payload, {"paylinkId", "paylink_id"}))
    if direct:
        return direct
    for mapping in _iter_payload_mappings(payload):
        for key, value in mapping.items():
            if _normalize_key(str(key)) == "paylink" and isinstance(value, dict):
                candidate = _normalize_string(value.get("id") or value.get("paylinkId"))
                if candidate:
                    return candidate
    return None


def _extract_float(payload: dict[str, Any], keys: set[str]) -> float | None:
    candidate = _find_first_value(payload, keys)
    if candidate is None:
        return None
    try:
        return float(candidate)
    except (TypeError, ValueError):
        return None


def _contains_any(haystack: str, needles: set[str]) -> bool:
    return any(needle in haystack for needle in needles)


def _classify_webhook_action(event_type: str | None, status_value: str | None) -> str:
    joined = " ".join(part for part in [event_type, status_value] if part).lower()
    success_tokens = {"success", "succeed", "complete", "confirm", "paid", "active", "started", "renew"}
    failure_tokens = {"fail", "cancel", "refund", "reverse", "expire", "ended"}
    pending_tokens = {"pending", "processing", "queued", "created", "initiated"}

    if _contains_any(joined, success_tokens) and not _contains_any(joined, failure_tokens):
        return "upgrade"
    if _contains_any(joined, failure_tokens):
        return "ignore"
    if _contains_any(joined, pending_tokens):
        return "ignore"
    return "ignore"


def _validate_webhook_secret(request: Request) -> None:
    expected_secret = (settings.helio_webhook_secret or "").strip()
    if not expected_secret:
        return

    candidates = [
        request.headers.get("x-helio-webhook-secret"),
        request.headers.get("x-webhook-secret"),
        request.query_params.get("secret"),
    ]
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        candidates.append(authorization[7:].strip())

    if expected_secret not in {candidate.strip() for candidate in candidates if candidate and candidate.strip()}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret")


def _resolve_user(
    db: Session,
    *,
    additional_json: dict[str, str],
    payload: dict[str, Any],
) -> User | None:
    user_id = additional_json.get("userId") or additional_json.get("user_id")
    if user_id:
        user = get_user_by_id(db, user_id)
        if user is not None:
            return user

    email = (
        additional_json.get("email")
        or additional_json.get("userEmail")
        or _normalize_string(_find_first_value(payload, {"customerEmail", "customer_email", "email"}))
    )
    if not email:
        return None

    return get_user_by_email(db, email.lower())


@router.get("/premium-session", response_model=PremiumCheckoutSessionResponse)
async def premium_checkout_session(user: User = Depends(get_current_user)) -> PremiumCheckoutSessionResponse:
    if user.plan in {"pro", "enterprise"}:
        return PremiumCheckoutSessionResponse(
            available=False,
            already_active=True,
            email=user.email,
        )

    if not settings.helio_premium_paylink_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Premium checkout is not configured yet.",
        )

    return PremiumCheckoutSessionResponse(
        available=True,
        already_active=False,
        paylink_id=settings.helio_premium_paylink_id,
        payment_type=settings.helio_premium_payment_type,
        primary_color=PREMIUM_PRIMARY_COLOR,
        neutral_color=PREMIUM_NEUTRAL_COLOR,
        background_color=PREMIUM_BACKGROUND_COLOR,
        email=user.email,
        additional_json={
            "userId": user.id,
            "email": user.email,
            "plan": "pro",
            "source": "solanatrust-premium",
        },
    )


@router.post("/helio/webhook", response_model=BillingWebhookResponse)
async def helio_webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> BillingWebhookResponse:
    _validate_webhook_secret(request)

    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payload must be a JSON object")

    additional_json = _extract_additional_json(payload)
    event_type = _normalize_string(_find_first_value(payload, {"eventType", "event_type", "event", "type"}))
    status_value = _normalize_string(_find_first_value(payload, {"paymentStatus", "subscriptionStatus", "status", "state"}))
    paylink_id = _extract_paylink_id(payload)
    action = _classify_webhook_action(event_type, status_value)
    plan = additional_json.get("plan", "pro")
    event_id = _normalize_string(_find_first_value(payload, {"eventId", "event_id", "webhookId", "webhook_id"}))
    transaction_id = _normalize_string(
        _find_first_value(payload, {"transactionId", "transaction_id", "paymentId", "payment_id", "depositId"})
    )
    subscription_id = _normalize_string(_find_first_value(payload, {"subscriptionId", "subscription_id", "paystreamId"}))
    amount_usd = _extract_float(payload, {"amountUsd", "amount_usd", "usdAmount", "totalAmount"})
    currency = _normalize_string(_find_first_value(payload, {"currency", "currencyCode"}))
    event_key = build_billing_event_key(
        event_id=event_id,
        transaction_id=transaction_id,
        subscription_id=subscription_id,
        event_type=event_type,
        status=status_value,
        payload_json=payload,
    )

    existing = db.query(BillingEvent).filter(BillingEvent.event_key == event_key).first()
    if existing is not None:
        return BillingWebhookResponse(
            accepted=True,
            upgraded=existing.upgraded,
            message="Webhook already processed.",
        )

    configured_paylink_id = settings.helio_premium_paylink_id
    if configured_paylink_id and paylink_id and paylink_id != configured_paylink_id:
        event = BillingEvent(
            event_key=event_key,
            event_type=event_type,
            status=status_value,
            plan=plan,
            paylink_id=paylink_id,
            transaction_id=transaction_id,
            subscription_id=subscription_id,
            amount_usd=amount_usd,
            currency=currency,
            user_email=additional_json.get("email"),
            payload_json=payload,
            upgraded=False,
        )
        db.add(event)
        db.commit()
        return BillingWebhookResponse(
            accepted=True,
            upgraded=False,
            message="Webhook ignored because paylink does not match premium configuration.",
        )

    user = _resolve_user(db, additional_json=additional_json, payload=payload)
    upgraded = False

    if action == "upgrade" and user is not None:
        if user.plan != "enterprise":
            user.plan = "pro"
        upgraded = True

    event = BillingEvent(
        event_key=event_key,
        event_type=event_type,
        status=status_value,
        plan=plan,
        paylink_id=paylink_id,
        transaction_id=transaction_id,
        subscription_id=subscription_id,
        amount_usd=amount_usd,
        currency=currency,
        user_id=user.id if user is not None else None,
        user_email=(user.email if user is not None else additional_json.get("email")),
        payload_json=payload,
        upgraded=upgraded,
    )
    db.add(event)
    db.commit()

    if upgraded:
        return BillingWebhookResponse(
            accepted=True,
            upgraded=True,
            message="Premium plan activated.",
        )

    if user is None:
        return BillingWebhookResponse(
            accepted=True,
            upgraded=False,
            message="Webhook received, but no matching user was found.",
        )

    return BillingWebhookResponse(
        accepted=True,
        upgraded=False,
        message="Webhook stored. No plan change applied.",
    )
