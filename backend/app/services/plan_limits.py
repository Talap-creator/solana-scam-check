from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import TokenScan, User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def start_of_utc_day(timestamp: datetime | None = None) -> datetime:
    value = timestamp or utc_now()
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def next_utc_day_reset(timestamp: datetime | None = None) -> datetime:
    return start_of_utc_day(timestamp) + timedelta(days=1)


def daily_scan_limit_for_plan(plan: str, settings: Settings) -> int:
    normalized = plan.strip().lower()
    if normalized == "pro":
        return settings.pro_daily_scan_limit
    if normalized == "enterprise":
        return settings.enterprise_daily_scan_limit
    return settings.free_daily_scan_limit


def daily_scan_limit_for_user(user: User, settings: Settings) -> tuple[int, str]:
    if user.custom_daily_scan_limit is not None:
        return max(1, int(user.custom_daily_scan_limit)), "custom"
    return daily_scan_limit_for_plan(user.plan, settings), "plan"


def token_scans_today(db: Session, user: User) -> int:
    return int(
        db.query(func.count(TokenScan.id))
        .filter(TokenScan.user_id == user.id, TokenScan.scan_time >= start_of_utc_day())
        .scalar()
        or 0
    )


def remaining_token_scans_today(db: Session, user: User, settings: Settings) -> int:
    limit, _ = daily_scan_limit_for_user(user, settings)
    used = token_scans_today(db, user)
    return max(0, limit - used)
