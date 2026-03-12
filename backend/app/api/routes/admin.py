from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import TokenOverride, TokenScan, TokenStat, User
from ...schemas import (
    AdminBulkUserLimitUpdateRequest,
    AdminBulkUserLimitUpdateResponse,
    AdminUserLimitUpdateRequest,
    AdminDashboardResponse,
    AdminPopularToken,
    AdminScanItem,
    AdminScansResponse,
    AdminTokenItem,
    AdminTokensResponse,
    AdminUserItem,
    AdminUsersResponse,
    ReviewQueueResponse,
    TokenOverrideItem,
    TokenOverrideRequest,
    TokenOverridesResponse,
)
from ...services.auth import ensure_admin, get_current_user
from ...dependencies import get_repository
from ...services.plan_limits import daily_scan_limit_for_plan, daily_scan_limit_for_user
from ...dependencies import settings


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    return ensure_admin(user)


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminDashboardResponse:
    users_count = db.query(func.count(User.id)).scalar() or 0
    since = datetime.now(timezone.utc) - timedelta(days=1)
    daily_scans = db.query(func.count(TokenScan.id)).filter(TokenScan.scan_time >= since).scalar() or 0
    average_risk_score = db.query(func.avg(TokenScan.risk_score)).scalar()

    popular = (
        db.query(TokenStat.token_address, TokenStat.scan_count)
        .order_by(desc(TokenStat.scan_count))
        .limit(10)
        .all()
    )

    return AdminDashboardResponse(
        users_count=int(users_count),
        daily_scans=int(daily_scans),
        popular_tokens=[
            AdminPopularToken(token_address=row.token_address, scan_count=int(row.scan_count))
            for row in popular
        ],
        average_risk_score=round(float(average_risk_score or 0.0), 2),
    )


@router.get("/users", response_model=AdminUsersResponse)
async def admin_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminUsersResponse:
    rows = (
        db.query(
            User.id,
            User.email,
            User.plan,
            User.custom_daily_scan_limit,
            User.created_at,
            func.count(TokenScan.id).label("scans"),
        )
        .outerjoin(TokenScan, TokenScan.user_id == User.id)
        .group_by(User.id, User.email, User.plan, User.custom_daily_scan_limit, User.created_at)
        .order_by(desc(User.created_at))
        .limit(200)
        .all()
    )

    return AdminUsersResponse(
        items=[
            AdminUserItem(
                id=row.id,
                email=row.email,
                plan=row.plan,
                custom_daily_scan_limit=row.custom_daily_scan_limit,
                effective_daily_limit=(
                    int(row.custom_daily_scan_limit)
                    if row.custom_daily_scan_limit is not None
                    else daily_scan_limit_for_plan(row.plan, settings)
                ),
                scans=int(row.scans or 0),
                created_at=row.created_at,
            )
            for row in rows
        ]
    )


@router.patch("/users/limits/bulk", response_model=AdminBulkUserLimitUpdateResponse)
async def bulk_update_user_limits(
    payload: AdminBulkUserLimitUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminBulkUserLimitUpdateResponse:
    users = db.query(User).filter(User.id.in_(payload.user_ids)).all()
    for user in users:
        user.plan = payload.plan
        user.custom_daily_scan_limit = payload.custom_daily_scan_limit
    db.commit()
    return AdminBulkUserLimitUpdateResponse(updated_count=len(users))


@router.patch("/users/{user_id}/limits", response_model=AdminUserItem)
async def update_user_limits(
    user_id: str,
    payload: AdminUserLimitUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminUserItem:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.plan = payload.plan
    user.custom_daily_scan_limit = payload.custom_daily_scan_limit
    db.commit()
    db.refresh(user)

    scans_count = int(db.query(func.count(TokenScan.id)).filter(TokenScan.user_id == user.id).scalar() or 0)
    effective_limit, _ = daily_scan_limit_for_user(user, settings)
    return AdminUserItem(
        id=user.id,
        email=user.email,
        plan=user.plan,
        custom_daily_scan_limit=user.custom_daily_scan_limit,
        effective_daily_limit=effective_limit,
        scans=scans_count,
        created_at=user.created_at,
    )


@router.get("/scans", response_model=AdminScansResponse)
async def admin_scans(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminScansResponse:
    rows = (
        db.query(
            TokenScan.id,
            User.email.label("user_email"),
            TokenScan.token_address,
            TokenScan.risk_score,
            TokenScan.confidence,
            TokenScan.scan_time,
        )
        .join(User, User.id == TokenScan.user_id)
        .order_by(desc(TokenScan.scan_time))
        .limit(300)
        .all()
    )

    return AdminScansResponse(
        items=[
            AdminScanItem(
                id=row.id,
                user_email=row.user_email,
                token_address=row.token_address,
                risk_score=int(row.risk_score),
                confidence=float(row.confidence),
                scan_time=row.scan_time,
            )
            for row in rows
        ]
    )


@router.get("/tokens", response_model=AdminTokensResponse)
async def admin_tokens(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> AdminTokensResponse:
    avg_risk_by_token = (
        db.query(
            TokenScan.token_address.label("token_address"),
            func.avg(TokenScan.risk_score).label("avg_risk"),
        )
        .group_by(TokenScan.token_address)
        .subquery()
    )

    rows = (
        db.query(
            TokenStat.token_address,
            TokenStat.scan_count,
            TokenStat.last_scanned,
            avg_risk_by_token.c.avg_risk,
        )
        .outerjoin(avg_risk_by_token, avg_risk_by_token.c.token_address == TokenStat.token_address)
        .order_by(desc(TokenStat.scan_count))
        .limit(300)
        .all()
    )

    return AdminTokensResponse(
        items=[
            AdminTokenItem(
                token_address=row.token_address,
                scan_count=int(row.scan_count),
                average_risk_score=round(float(row.avg_risk or 0.0), 2),
                last_scanned=row.last_scanned,
            )
            for row in rows
        ]
    )


@router.get("/review-queue", response_model=ReviewQueueResponse)
async def review_queue(
    _: User = Depends(get_admin_user),
) -> ReviewQueueResponse:
    return ReviewQueueResponse(items=get_repository().build_review_queue_items())


@router.get("/overrides", response_model=TokenOverridesResponse)
async def list_overrides(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> TokenOverridesResponse:
    rows = (
        db.query(TokenOverride)
        .filter(TokenOverride.chain == "solana")
        .order_by(desc(TokenOverride.updated_at))
        .limit(300)
        .all()
    )
    return TokenOverridesResponse(
        items=[
            TokenOverrideItem(
                token_address=row.token_address,
                chain=row.chain,
                verdict=row.verdict,
                reason=row.reason,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
    )


@router.post("/overrides", response_model=TokenOverrideItem)
async def upsert_override(
    payload: TokenOverrideRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> TokenOverrideItem:
    token_address = payload.token_address.strip()
    if not token_address:
        raise HTTPException(status_code=400, detail="token_address is required")

    existing = db.query(TokenOverride).filter(TokenOverride.token_address == token_address).first()
    if existing is None:
        existing = TokenOverride(
            token_address=token_address,
            chain="solana",
            verdict=payload.verdict,
            reason=payload.reason,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(existing)
    else:
        existing.verdict = payload.verdict
        existing.reason = payload.reason
        existing.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(existing)

    return TokenOverrideItem(
        token_address=existing.token_address,
        chain=existing.chain,
        verdict=existing.verdict,
        reason=existing.reason,
        updated_at=existing.updated_at,
    )


@router.delete("/overrides/{token_address}")
async def delete_override(
    token_address: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
) -> dict[str, bool]:
    existing = db.query(TokenOverride).filter(TokenOverride.token_address == token_address).first()
    if existing is None:
        raise HTTPException(status_code=404, detail="Override not found")
    db.delete(existing)
    db.commit()
    return {"deleted": True}
