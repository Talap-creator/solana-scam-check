"""Oracle API routes — manage monitored tokens and view on-chain scores."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import OracleMonitoredToken, OraclePublishEvent
from ...services.oracle_agent import get_oracle_agent

router = APIRouter(prefix="/api/v1/oracle", tags=["oracle"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class MonitorTokenRequest(BaseModel):
    token_address: str
    display_name: str | None = None


class MonitorTokenResponse(BaseModel):
    id: str
    token_address: str
    display_name: str | None
    is_active: bool


class OracleScoreResponse(BaseModel):
    token_address: str
    score: int | None
    risk_level: str | None
    confidence: float | None
    last_published_at: str | None
    tx_signature: str | None
    display_name: str | None
    reasoning: str | None


class OracleStatusResponse(BaseModel):
    agent_running: bool
    last_run: str | None
    total_published: int
    errors: int
    monitored_tokens: int


class PublishEventResponse(BaseModel):
    id: str
    token_address: str
    score: int
    risk_level: str
    confidence: float
    reasoning: str | None
    tx_signature: str | None
    status: str
    error_message: str | None
    published_at: str


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.get("/status", response_model=OracleStatusResponse)
def oracle_status(db: Session = Depends(get_db)):
    agent = get_oracle_agent()
    token_count = db.query(OracleMonitoredToken).filter(
        OracleMonitoredToken.is_active.is_(True)
    ).count()

    if agent:
        s = agent.status
        return OracleStatusResponse(
            agent_running=s["running"],
            last_run=s["last_run"],
            total_published=s["total_published"],
            errors=s["errors"],
            monitored_tokens=token_count,
        )

    return OracleStatusResponse(
        agent_running=False,
        last_run=None,
        total_published=0,
        errors=0,
        monitored_tokens=token_count,
    )


@router.get("/scores", response_model=list[OracleScoreResponse])
def list_scores(db: Session = Depends(get_db)):
    tokens = (
        db.query(OracleMonitoredToken)
        .filter(OracleMonitoredToken.is_active.is_(True))
        .order_by(OracleMonitoredToken.last_published_at.desc().nullslast())
        .all()
    )
    return [
        OracleScoreResponse(
            token_address=t.token_address,
            score=t.last_score,
            risk_level=t.last_risk_level,
            confidence=float(t.last_confidence) if t.last_confidence else None,
            last_published_at=t.last_published_at.isoformat() if t.last_published_at else None,
            tx_signature=t.last_tx_signature,
            display_name=t.display_name,
            reasoning=t.last_reasoning,
        )
        for t in tokens
    ]


@router.get("/scores/{token_address}", response_model=OracleScoreResponse)
def get_score(token_address: str, db: Session = Depends(get_db)):
    t = db.query(OracleMonitoredToken).filter_by(token_address=token_address).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not monitored")
    return OracleScoreResponse(
        token_address=t.token_address,
        score=t.last_score,
        risk_level=t.last_risk_level,
        confidence=float(t.last_confidence) if t.last_confidence else None,
        last_published_at=t.last_published_at.isoformat() if t.last_published_at else None,
        tx_signature=t.last_tx_signature,
        display_name=t.display_name,
        reasoning=t.last_reasoning,
    )


@router.post("/monitor", response_model=MonitorTokenResponse)
def add_monitored_token(payload: MonitorTokenRequest, db: Session = Depends(get_db)):
    existing = db.query(OracleMonitoredToken).filter_by(
        token_address=payload.token_address
    ).first()

    if existing:
        existing.is_active = True
        if payload.display_name:
            existing.display_name = payload.display_name
        db.commit()
        db.refresh(existing)
        return MonitorTokenResponse(
            id=existing.id,
            token_address=existing.token_address,
            display_name=existing.display_name,
            is_active=existing.is_active,
        )

    token = OracleMonitoredToken(
        token_address=payload.token_address,
        display_name=payload.display_name,
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return MonitorTokenResponse(
        id=token.id,
        token_address=token.token_address,
        display_name=token.display_name,
        is_active=token.is_active,
    )


@router.delete("/monitor/{token_address}")
def remove_monitored_token(token_address: str, db: Session = Depends(get_db)):
    token = db.query(OracleMonitoredToken).filter_by(token_address=token_address).first()
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    token.is_active = False
    db.commit()
    return {"status": "removed", "token_address": token_address}


@router.get("/history", response_model=list[PublishEventResponse])
def list_publish_history(
    limit: int = 50,
    token_address: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(OraclePublishEvent).order_by(
        OraclePublishEvent.published_at.desc()
    )
    if token_address:
        query = query.filter_by(token_address=token_address)

    events = query.limit(limit).all()
    return [
        PublishEventResponse(
            id=e.id,
            token_address=e.token_address,
            score=e.score,
            risk_level=e.risk_level,
            confidence=float(e.confidence),
            reasoning=e.reasoning,
            tx_signature=e.tx_signature,
            status=e.status,
            error_message=e.error_message,
            published_at=e.published_at.isoformat(),
        )
        for e in events
    ]


@router.post("/agent/start")
async def start_agent():
    agent = get_oracle_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Oracle agent not initialized")
    agent.start(interval_seconds=60)
    return {"status": "started"}


@router.post("/agent/stop")
async def stop_agent():
    agent = get_oracle_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Oracle agent not initialized")
    agent.stop()
    return {"status": "stopped"}
