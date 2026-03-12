from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models import TokenScan, TokenStat, User
from ..schemas import CheckOverview


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def track_token_scan(db: Session, user: User, report: CheckOverview) -> None:
    scan = TokenScan(
        user_id=user.id,
        token_address=report.entity_id,
        chain="solana",
        risk_score=report.score,
        confidence=report.confidence,
        scan_time=utc_now(),
    )
    db.add(scan)

    stat = db.query(TokenStat).filter(TokenStat.token_address == report.entity_id).first()
    if stat is None:
        stat = TokenStat(
            token_address=report.entity_id,
            scan_count=1,
            last_scanned=utc_now(),
        )
        db.add(stat)
    else:
        stat.scan_count += 1
        stat.last_scanned = utc_now()

    db.commit()
