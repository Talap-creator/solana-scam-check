from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...dependencies import get_repository, settings
from ...db import get_db
from ...models import TokenOverride, User
from ...schemas import AddressRequest, ChecksResponse, EntityType, ProjectRequest, SubmissionResponse
from ...services.auth import get_optional_current_user
from ...services.analyzer import is_valid_solana_address, normalize_entity_id
from ...services.plan_limits import daily_scan_limit_for_user, token_scans_today
from ...services.scan_tracking import track_token_scan
from ...services.solana_rpc import SolanaRpcError
from ...services.overrides import apply_override


router = APIRouter(prefix="/api/v1", tags=["checks"])


def build_submission(
    entity_type: EntityType,
    requested_value: str,
    db: Session,
    user: User | None,
) -> SubmissionResponse:
    if entity_type == "token" and user is not None:
        used_today = token_scans_today(db, user)
        daily_limit, _ = daily_scan_limit_for_user(user, settings)
        if used_today >= daily_limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Daily scan limit reached for plan '{user.plan}'. "
                    f"Used {used_today}/{daily_limit} token scans today (UTC)."
                ),
            )

    try:
        report = get_repository().create_report(entity_type, requested_value)
    except SolanaRpcError as exc:
        message = str(exc)
        if "not an SPL token mint" in message or "not found" in message or "Invalid param" in message:
            raise HTTPException(status_code=400, detail=message) from exc
        raise HTTPException(status_code=502, detail=message) from exc

    if entity_type == "token":
        override = (
            db.query(TokenOverride)
            .filter(
                TokenOverride.token_address == report.entity_id,
                TokenOverride.chain == "solana",
            )
            .first()
        )
        if override is not None:
            report = apply_override(report, override)

    if entity_type == "token" and user is not None:
        track_token_scan(db, user, report)

    return SubmissionResponse(
        queued=report.status in {"high", "critical"},
        entity_type=report.entity_type,
        requested_value=requested_value,
        check_id=report.id,
    )


@router.get("/checks", response_model=ChecksResponse)
async def list_checks() -> ChecksResponse:
    return ChecksResponse(items=get_repository().latest_reports())


@router.get("/checks/{check_id}")
async def get_check(check_id: str):
    report = get_repository().get_report(check_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Check not found")
    return report


@router.post("/check/token", response_model=SubmissionResponse)
async def check_token(
    payload: AddressRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> SubmissionResponse:
    if not is_valid_solana_address(payload.address):
        raise HTTPException(
            status_code=400,
            detail="Token check currently supports only Solana SPL mint addresses. The submitted value is not a valid Solana address.",
        )
    return build_submission("token", payload.address, db, user)


@router.post("/check/wallet", response_model=SubmissionResponse)
async def check_wallet(
    payload: AddressRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> SubmissionResponse:
    return build_submission("wallet", payload.address, db, user)


@router.post("/check/project", response_model=SubmissionResponse)
async def check_project(
    payload: ProjectRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> SubmissionResponse:
    return build_submission("project", payload.query, db, user)


@router.post("/recheck/{entity_type}/{entity_id:path}", response_model=SubmissionResponse)
async def recheck(
    entity_type: EntityType,
    entity_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> SubmissionResponse:
    normalized_entity_id = normalize_entity_id(entity_type, entity_id)
    repository = get_repository()
    if not repository.has_entity(entity_type, normalized_entity_id):
        raise HTTPException(status_code=404, detail="Entity not found")
    return build_submission(entity_type, normalized_entity_id, db, user)
