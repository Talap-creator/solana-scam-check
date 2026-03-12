from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...dependencies import settings
from ...db import get_db
from ...models import TokenScan, User
from ...schemas import (
    AuthTokenResponse,
    LoginRequest,
    RegisterRequest,
    UserProfileResponse,
    UserScanItem,
    UserScansResponse,
    UserUsageResponse,
)
from ...services.auth import create_access_token, get_current_user, get_user_by_email, hash_password, verify_password
from ...services.plan_limits import (
    daily_scan_limit_for_user,
    next_utc_day_reset,
    remaining_token_scans_today,
    token_scans_today,
)


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    normalized_email = payload.email.lower()
    existing = get_user_by_email(db, normalized_email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=normalized_email,
        password_hash=hash_password(payload.password),
        plan=payload.plan,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return AuthTokenResponse(access_token=token)


@router.post("/login", response_model=AuthTokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    user = get_user_by_email(db, payload.email.lower())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(user.id)
    return AuthTokenResponse(access_token=token)


@router.get("/me", response_model=UserProfileResponse)
async def me(user: User = Depends(get_current_user)) -> UserProfileResponse:
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        plan=user.plan,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.get("/usage", response_model=UserUsageResponse)
async def usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserUsageResponse:
    used_today = token_scans_today(db, user)
    daily_limit, limit_source = daily_scan_limit_for_user(user, settings)
    remaining_today = remaining_token_scans_today(db, user, settings)
    return UserUsageResponse(
        plan=user.plan,
        used_today=used_today,
        daily_limit=daily_limit,
        remaining_today=remaining_today,
        limit_source=limit_source,
        reset_at=next_utc_day_reset(),
    )


@router.get("/scans", response_model=UserScansResponse)
async def my_scans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserScansResponse:
    rows = (
        db.query(TokenScan)
        .filter(TokenScan.user_id == user.id)
        .order_by(TokenScan.scan_time.desc())
        .limit(100)
        .all()
    )
    return UserScansResponse(
        items=[
            UserScanItem(
                id=row.id,
                token_address=row.token_address,
                risk_score=int(row.risk_score),
                confidence=float(row.confidence),
                scan_time=row.scan_time,
            )
            for row in rows
        ]
    )
