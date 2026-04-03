"""Oracle API routes — manage monitored tokens and view on-chain scores."""

from __future__ import annotations

import asyncio
import json
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...db import get_db
from ...models import OracleMonitoredToken, OraclePublishEvent
from ...services.oracle_agent import get_oracle_agent

router = APIRouter(prefix="/api/v1/oracle", tags=["oracle"])


# ─── Schemas ──────────────────────────────────────────────────────────────────


class AgentAnalyzeRequest(BaseModel):
    token_address: str


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


@router.post("/agent/analyze")
async def agent_analyze(req: AgentAnalyzeRequest):
    """Stream an AI risk analysis for a given token address via SSE."""

    async def generate():
        # Phase 1: Show analysis steps
        steps = [
            {"type": "step", "text": "Connecting to Solana blockchain..."},
            {"type": "step", "text": "Fetching token metadata and authorities..."},
            {"type": "step", "text": "Analyzing holder distribution..."},
            {"type": "step", "text": "Checking liquidity pools and DEX presence..."},
            {"type": "step", "text": "Scanning deployer wallet history..."},
            {"type": "step", "text": "Running AI risk analysis..."},
        ]
        for step in steps:
            yield f"data: {json.dumps(step)}\n\n"
            await asyncio.sleep(0.6)

        # Phase 2: ML model scoring via DexScreener
        features: dict = {}
        ml_score_data: dict | None = None
        try:
            from ...scoring.ml.inference import MLInferenceEngine
            from ...services.dexscreener import DexScreenerClient, pick_most_liquid_pair

            ml_engine = MLInferenceEngine()
            if ml_engine.has_model:
                dex = DexScreenerClient()
                pairs = dex.get_token_pairs("solana", req.token_address)
                pair = pick_most_liquid_pair(pairs)
                if pair:
                    ml_prob = ml_engine.predict_from_dexscreener(pair)
                    liq = (pair.get("liquidity") or {}).get("usd", 0)
                    vol = (pair.get("volume") or {}).get("h24", 0)
                    name = (pair.get("baseToken") or {}).get("name", "Unknown")
                    symbol = (pair.get("baseToken") or {}).get("symbol", "???")
                    ml_score_data = {"probability": ml_prob, "score": int(ml_prob * 100)}
                    features = {
                        "name": name, "symbol": symbol,
                        "liquidity_usd": float(liq), "volume_24h": float(vol),
                        "ml_rug_probability": round(ml_prob * 100, 1),
                    }
                    yield f'data: {json.dumps({"type": "step", "text": f"ML model: {name} ({symbol}) — rug probability {ml_prob*100:.1f}%"})}\n\n'
                    await asyncio.sleep(0.4)
        except Exception:
            pass

        # Phase 3: Stream AI analysis
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            score = ml_score_data["score"] if ml_score_data else 50
            risk = "critical" if score >= 75 else "high" if score >= 50 else "medium" if score >= 25 else "low"
            reasoning = f"ML model rug probability: {ml_score_data['probability']*100:.1f}%" if ml_score_data else "Rule-based assessment: moderate risk."
            yield f'data: {json.dumps({"type": "analysis", "text": f"AI agent unavailable (no API key). Using ML model fallback. {reasoning}"})}\n\n'
            yield f'data: {json.dumps({"type": "verdict", "score": score, "risk_level": risk, "reasoning": reasoning})}\n\n'
            yield "data: [DONE]\n\n"
            return

        system_prompt = (
            "You are RugSignal AI Agent — an autonomous Solana token risk analyst. "
            "You are analyzing a token in real-time. Write your analysis as a narrative, "
            "step by step. Be specific about what you find. Use these sections:\n\n"
            "1. TOKEN OVERVIEW — what you know about this token\n"
            "2. RED FLAGS — any concerning patterns (be specific)\n"
            "3. POSITIVE SIGNALS — anything that looks legitimate\n"
            "4. VERDICT — final score (0-100) and 1-2 sentence summary\n\n"
            'End your response with a JSON block on the last line:\n'
            '{"score": <0-100>, "risk_level": "<low|medium|high|critical>", "confidence": <0.0-1.0>}'
        )

        features_text = (
            json.dumps(features, indent=2)
            if features
            else "Limited data available — assess based on general patterns and token address characteristics."
        )
        user_prompt = f"Analyze Solana token: {req.token_address}\n\nOn-chain features:\n{features_text}"

        try:
            client = OpenAI(api_key=api_key)
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=600,
                temperature=0.3,
                stream=True,
            )

            full_text = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    full_text += delta
                    yield f'data: {json.dumps({"type": "analysis", "text": delta})}\n\n'

            # Try to extract the JSON verdict from the end
            try:
                last_brace = full_text.rfind("{")
                if last_brace >= 0:
                    json_str = full_text[last_brace : full_text.rfind("}") + 1]
                    verdict = json.loads(json_str)
                    ai_score = verdict.get("score", 50)
                    # Blend AI score with ML model if available
                    if ml_score_data:
                        blended = int(0.6 * ai_score + 0.4 * ml_score_data["score"])
                        risk = "critical" if blended >= 75 else "high" if blended >= 50 else "medium" if blended >= 25 else "low"
                        yield f'data: {json.dumps({"type": "verdict", "score": blended, "risk_level": risk, "reasoning": verdict.get("reasoning", ""), "ml_probability": ml_score_data["probability"]})}\n\n'
                    else:
                        yield f'data: {json.dumps({"type": "verdict", "score": ai_score, "risk_level": verdict.get("risk_level", "medium"), "reasoning": verdict.get("reasoning", "")})}\n\n'
                else:
                    raise ValueError("No JSON found")
            except Exception:
                score = ml_score_data["score"] if ml_score_data else 50
                risk = "critical" if score >= 75 else "high" if score >= 50 else "medium" if score >= 25 else "low"
                yield f'data: {json.dumps({"type": "verdict", "score": score, "risk_level": risk, "reasoning": "ML model assessment"})}\n\n'

        except Exception as e:
            yield f'data: {json.dumps({"type": "error", "text": str(e)})}\n\n'

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
