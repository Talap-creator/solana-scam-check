from __future__ import annotations

from fastapi import APIRouter, Query

from ...dependencies import get_repository
from ...schemas import DeveloperOperatorFeedResponse, LaunchFeedResponse


router = APIRouter(prefix="/api/v1/feed", tags=["feed"])


@router.get("/launches", response_model=LaunchFeedResponse)
async def get_launch_feed(
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = Query(default=None),
    tab: str = Query(default="new"),
    sort: str = Query(default="newest"),
    age: str = Query(default="all"),
    liquidity: str = Query(default="all"),
    copycat_only: bool = Query(default=False),
    q: str = Query(default=""),
) -> LaunchFeedResponse:
    items, next_cursor = get_repository().build_launch_feed_items(
        limit=limit,
        cursor=cursor,
        tab=tab,
        sort=sort,
        age=age,
        liquidity=liquidity,
        copycat_only=copycat_only,
        query=q,
    )
    return LaunchFeedResponse(
        items=items,
        next_cursor=next_cursor,
    )


@router.get("/developers", response_model=DeveloperOperatorFeedResponse)
async def get_developer_feed(
    limit: int = Query(default=200, ge=1, le=500),
) -> DeveloperOperatorFeedResponse:
    items = get_repository().build_developer_operator_items(limit=limit)
    return DeveloperOperatorFeedResponse(items=items)
