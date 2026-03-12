from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ...dependencies import get_repository, settings
from ...db import get_db
from ...models import TokenScan, TokenStat
from ...schemas import (
    InsightsResponse,
    MostScannedTokenItem,
    OverviewResponse,
    TrendingRugItem,
)


router = APIRouter(prefix="/api/v1", tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
async def overview() -> OverviewResponse:
    repository = get_repository()
    reports = repository.latest_reports()
    counts = {
        "checks": len(reports),
        "watchlist": len(repository.build_watchlist_items()),
        "review_queue": len(repository.build_review_queue_items()),
    }
    return OverviewResponse(
        product="RugSignal",
        network="Solana",
        supported_entities=["token", "wallet", "project"],
        status_model=["low", "medium", "high", "critical"],
        totals=counts,
        freshness=reports[0].refreshed_at if reports else "n/a",
        active_rules=settings.active_rules,
    )


@router.get("/insights", response_model=InsightsResponse)
async def insights(db: Session = Depends(get_db)) -> InsightsResponse:
    most_scanned_rows = (
        db.query(
            TokenStat.token_address,
            TokenStat.scan_count,
            func.avg(TokenScan.risk_score).label("avg_risk"),
        )
        .outerjoin(TokenScan, TokenScan.token_address == TokenStat.token_address)
        .group_by(TokenStat.token_address, TokenStat.scan_count)
        .order_by(desc(TokenStat.scan_count))
        .limit(10)
        .all()
    )

    since = datetime.now(timezone.utc) - timedelta(days=1)
    trending_rows = (
        db.query(
            TokenScan.token_address,
            TokenScan.risk_score,
            TokenScan.confidence,
            TokenScan.scan_time,
        )
        .filter(TokenScan.scan_time >= since, TokenScan.risk_score >= 75)
        .order_by(desc(TokenScan.scan_time), desc(TokenScan.risk_score))
        .limit(200)
        .all()
    )

    seen: set[str] = set()
    trending: list[TrendingRugItem] = []
    for row in trending_rows:
        if row.token_address in seen:
            continue
        seen.add(row.token_address)
        trending.append(
            TrendingRugItem(
                token_address=row.token_address,
                risk_score=int(row.risk_score),
                confidence=float(row.confidence),
                scan_time=row.scan_time,
            )
        )
        if len(trending) >= 10:
            break

    return InsightsResponse(
        most_scanned_tokens=[
            MostScannedTokenItem(
                token_address=row.token_address,
                scan_count=int(row.scan_count),
                average_risk_score=round(float(row.avg_risk or 0.0), 2),
            )
            for row in most_scanned_rows
        ],
        trending_rugs=trending,
    )
