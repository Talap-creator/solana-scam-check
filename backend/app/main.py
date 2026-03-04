from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class RiskFactor(BaseModel):
    code: str
    severity: str
    label: str
    explanation: str
    weight: int


class CheckOverview(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    display_name: str
    status: str
    score: int
    confidence: float
    summary: str
    refreshed_at: str
    liquidity: str
    top_holder_share: str
    review_state: str
    factors: list[RiskFactor]
    metrics: list[dict[str, str]]
    timeline: list[dict[str, str]]


class WatchlistItem(BaseModel):
    name: str
    delta: str
    state: str


class ReviewQueueItem(BaseModel):
    id: str
    display_name: str
    entity_type: str
    severity: str
    score: int
    owner: str
    updated_at: str


MOCK_REPORTS: dict[str, CheckOverview] = {
    "pearl-token": CheckOverview(
        id="pearl-token",
        entity_type="token",
        entity_id="9xQeWvG816bUx9EPfEZLQ7ZL8A6V7zVYhWf9e7s6PzF1",
        display_name="PEARL / Solana meme token",
        status="critical",
        score=82,
        confidence=0.81,
        summary="Высокий риск из-за активной mint authority, сильной концентрации предложения и подозрительной истории deployer.",
        refreshed_at="4 минуты назад",
        liquidity="$12.4K",
        top_holder_share="87.4%",
        review_state="Escalated",
        factors=[
            RiskFactor(
                code="TOKEN_ACTIVE_MINT_AUTHORITY",
                severity="high",
                label="Mint authority активна",
                explanation="Supply токена можно изменить после запуска.",
                weight=20,
            ),
            RiskFactor(
                code="TOKEN_HOLDER_CONCENTRATION",
                severity="high",
                label="87% у top 10 holders",
                explanation="Критичная концентрация предложения у ограниченного круга адресов.",
                weight=18,
            ),
        ],
        metrics=[
            {"label": "Score", "value": "82"},
            {"label": "Confidence", "value": "0.81"},
            {"label": "Top 10 share", "value": "87.4%"},
            {"label": "Liquidity", "value": "$12.4K"},
        ],
        timeline=[
            {"label": "Active mint authority", "value": "Detected", "tone": "danger"},
            {"label": "Linked deployer history", "value": "3 suspicious launches", "tone": "danger"},
            {"label": "Project domain age", "value": "12 days", "tone": "warn"},
            {"label": "Background refresh", "value": "In progress", "tone": "neutral"},
        ],
    ),
    "wallet-alpha": CheckOverview(
        id="wallet-alpha",
        entity_type="wallet",
        entity_id="8PX1DbLyJQzY63K5kTz2S88xJ5UQh1dBnmfV91rYx4cR",
        display_name="Wallet / 8PX1...x4cR",
        status="high",
        score=67,
        confidence=0.77,
        summary="Повторяющийся launch-dump паттерн и связи с ранее flagged токенами.",
        refreshed_at="18 минут назад",
        liquidity="n/a",
        top_holder_share="n/a",
        review_state="Queued",
        factors=[
            RiskFactor(
                code="WALLET_LINKED_FLAGGED",
                severity="high",
                label="Связь с flagged entities",
                explanation="Кошелек взаимодействовал с несколькими адресами из risk lists.",
                weight=16,
            ),
            RiskFactor(
                code="WALLET_LAUNCH_DUMP",
                severity="high",
                label="Launch-dump behavior",
                explanation="Повторяющийся шаблон запуска и быстрого слива ликвидности.",
                weight=18,
            ),
        ],
        metrics=[
            {"label": "Score", "value": "67"},
            {"label": "Confidence", "value": "0.77"},
            {"label": "Linked flags", "value": "5"},
            {"label": "Age", "value": "41 days"},
        ],
        timeline=[
            {"label": "Flagged links", "value": "5 matches", "tone": "danger"},
            {"label": "Recent launch pattern", "value": "Detected", "tone": "danger"},
            {"label": "Last active", "value": "2 hours ago", "tone": "neutral"},
            {"label": "Background refresh", "value": "Complete", "tone": "neutral"},
        ],
    ),
    "project-orbit": CheckOverview(
        id="project-orbit",
        entity_type="project",
        entity_id="orbit-project",
        display_name="Orbit Project",
        status="medium",
        score=42,
        confidence=0.63,
        summary="Данных недостаточно для высокого риска, но trust signals проекта слабые.",
        refreshed_at="1 час назад",
        liquidity="$58K",
        top_holder_share="54.1%",
        review_state="Watching",
        factors=[
            RiskFactor(
                code="PROJECT_THIN_SOCIALS",
                severity="medium",
                label="Слабый social presence",
                explanation="Низкая активность и неполная project metadata.",
                weight=8,
            ),
            RiskFactor(
                code="PROJECT_LOW_CONFIDENCE",
                severity="medium",
                label="Недостаточно confidence",
                explanation="Часть источников данных недоступна или пуста.",
                weight=6,
            ),
        ],
        metrics=[
            {"label": "Score", "value": "42"},
            {"label": "Confidence", "value": "0.63"},
            {"label": "Liquidity", "value": "$58K"},
            {"label": "Domain age", "value": "72 days"},
        ],
        timeline=[
            {"label": "Social validation", "value": "Weak", "tone": "warn"},
            {"label": "Domain age", "value": "72 days", "tone": "neutral"},
            {"label": "Liquidity", "value": "Stable", "tone": "neutral"},
            {"label": "Background refresh", "value": "Pending", "tone": "neutral"},
        ],
    ),
}

WATCHLIST: list[WatchlistItem] = [
    WatchlistItem(name="PEARL", delta="+12 score", state="Critical"),
    WatchlistItem(name="Orbit Project", delta="confidence down", state="Watch"),
    WatchlistItem(name="Wallet / 8PX1", delta="new flagged link", state="Queued"),
]

REVIEW_QUEUE: list[ReviewQueueItem] = [
    ReviewQueueItem(
        id="pearl-token",
        display_name="PEARL / Solana meme token",
        entity_type="token",
        severity="critical",
        score=82,
        owner="talap",
        updated_at="4 минуты назад",
    ),
    ReviewQueueItem(
        id="wallet-alpha",
        display_name="Wallet / 8PX1...x4cR",
        entity_type="wallet",
        severity="high",
        score=67,
        owner="unassigned",
        updated_at="18 минут назад",
    ),
]


app = FastAPI(
    title="Solace Scan API",
    description="Backend API for Solana scam-checking and explainable risk scoring.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/overview")
async def overview() -> dict[str, object]:
    return {
        "product": "Solace Scan",
        "network": "Solana",
        "supported_entities": ["token", "wallet", "project"],
        "status_model": ["low", "medium", "high", "critical"],
    }


@app.get("/api/v1/checks")
async def list_checks() -> dict[str, list[CheckOverview]]:
    return {"items": list(MOCK_REPORTS.values())}


@app.get("/api/v1/checks/{check_id}")
async def get_check(check_id: str) -> CheckOverview:
    report = MOCK_REPORTS.get(check_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Check not found")
    return report


@app.post("/api/v1/check/token")
async def check_token(address: str) -> dict[str, object]:
    return {
        "queued": False,
        "entity_type": "token",
        "requested_address": address,
        "check_id": "pearl-token",
    }


@app.get("/api/v1/watchlist")
async def watchlist() -> dict[str, list[WatchlistItem]]:
    return {"items": WATCHLIST}


@app.get("/api/v1/admin/review-queue")
async def review_queue() -> dict[str, list[ReviewQueueItem]]:
    return {"items": REVIEW_QUEUE}
