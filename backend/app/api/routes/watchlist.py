from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...dependencies import get_repository
from ...db import get_db
from ...models import User, UserWatchlistEntry
from ...schemas import (
    AccountWatchlistItem,
    AccountWatchlistResponse,
    WatchlistResponse,
    WatchlistStatusResponse,
    WatchlistToggleRequest,
    WatchlistToggleResponse,
)
from ...services.analyzer import normalize_entity_id
from ...services.auth import get_current_user


router = APIRouter(prefix="/api/v1", tags=["watchlist"])


def build_account_watchlist_item(entry: UserWatchlistEntry) -> AccountWatchlistItem:
    report = get_repository().latest_report_for_entity(entry.entity_type, entry.entity_id)

    if report is not None:
        return AccountWatchlistItem(
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            report_id=report.id,
            name=report.display_name,
            symbol=report.symbol,
            delta=f"score {report.score} / confidence {report.confidence:.2f}",
            state=report.review_state,
            status=report.status,
            score=report.score,
            refreshed_at=report.refreshed_at,
            tracked_at=entry.created_at,
        )

    return AccountWatchlistItem(
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        report_id=None,
        name=entry.display_name or entry.entity_id,
        symbol=None,
        delta="Awaiting next tracked update",
        state="tracked",
        status=None,
        score=None,
        refreshed_at="just now",
        tracked_at=entry.created_at,
    )


@router.get("/watchlist", response_model=WatchlistResponse)
async def watchlist() -> WatchlistResponse:
    return WatchlistResponse(items=get_repository().build_watchlist_items())


@router.get("/auth/watchlist", response_model=AccountWatchlistResponse)
async def account_watchlist(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountWatchlistResponse:
    rows = (
        db.query(UserWatchlistEntry)
        .filter(UserWatchlistEntry.user_id == user.id)
        .order_by(UserWatchlistEntry.created_at.desc())
        .all()
    )
    return AccountWatchlistResponse(items=[build_account_watchlist_item(row) for row in rows])


@router.get("/auth/watchlist/status/{entity_type}/{entity_id:path}", response_model=WatchlistStatusResponse)
async def account_watchlist_status(
    entity_type: str,
    entity_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistStatusResponse:
    normalized_entity_id = normalize_entity_id(entity_type, entity_id)
    entry = (
        db.query(UserWatchlistEntry)
        .filter(
            UserWatchlistEntry.user_id == user.id,
            UserWatchlistEntry.entity_type == entity_type,
            UserWatchlistEntry.entity_id == normalized_entity_id,
        )
        .first()
    )
    return WatchlistStatusResponse(tracked=entry is not None)


@router.post("/auth/watchlist", response_model=WatchlistToggleResponse)
async def add_account_watchlist(
    payload: WatchlistToggleRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistToggleResponse:
    normalized_entity_id = normalize_entity_id(payload.entity_type, payload.entity_id)
    entry = (
        db.query(UserWatchlistEntry)
        .filter(
            UserWatchlistEntry.user_id == user.id,
            UserWatchlistEntry.entity_type == payload.entity_type,
            UserWatchlistEntry.entity_id == normalized_entity_id,
        )
        .first()
    )

    if entry is None:
        entry = UserWatchlistEntry(
            user_id=user.id,
            entity_type=payload.entity_type,
            entity_id=normalized_entity_id,
            display_name=payload.display_name,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
    elif payload.display_name and not entry.display_name:
        entry.display_name = payload.display_name
        db.commit()
        db.refresh(entry)

    return WatchlistToggleResponse(tracked=True, item=build_account_watchlist_item(entry))


@router.delete("/auth/watchlist/{entity_type}/{entity_id:path}", response_model=WatchlistStatusResponse)
async def remove_account_watchlist(
    entity_type: str,
    entity_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WatchlistStatusResponse:
    normalized_entity_id = normalize_entity_id(entity_type, entity_id)
    entry = (
        db.query(UserWatchlistEntry)
        .filter(
            UserWatchlistEntry.user_id == user.id,
            UserWatchlistEntry.entity_type == entity_type,
            UserWatchlistEntry.entity_id == normalized_entity_id,
        )
        .first()
    )

    if entry is not None:
        db.delete(entry)
        db.commit()

    return WatchlistStatusResponse(tracked=False)
