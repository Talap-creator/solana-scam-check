"""RugSignal Oracle Agent — autonomous AI scoring loop.

Monitors tokens, runs the existing RugSignal scoring pipeline,
and publishes risk scores on-chain via the Solana Oracle program.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..config import Settings
from ..models import OracleMonitoredToken, OraclePublishEvent
from ..scoring.ml.inference import MLInferenceEngine
from .solana_publisher import SolanaPublisher
from .ai_scorer import ai_score_token
from .dexscreener import DexScreenerClient, pick_most_liquid_pair

logger = logging.getLogger(__name__)


def _risk_level_from_score(score: int) -> str:
    if score < 25:
        return "low"
    if score < 50:
        return "medium"
    if score < 75:
        return "high"
    return "critical"


class OracleAgent:
    """Autonomous agent that scores tokens and publishes results on-chain."""

    def __init__(
        self,
        *,
        settings: Settings,
        publisher: SolanaPublisher,
        get_db: callable,
        get_repository: callable,
        get_pipeline: callable | None = None,
    ):
        self._settings = settings
        self._publisher = publisher
        self._get_db = get_db
        self._get_repository = get_repository
        self._get_pipeline = get_pipeline
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_run: datetime | None = None
        self._total_published: int = 0
        self._errors: int = 0
        self._ml_engine = MLInferenceEngine()
        self._dex_client = DexScreenerClient()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "total_published": self._total_published,
            "errors": self._errors,
        }

    def start(self, interval_seconds: int = 60):
        """Start the autonomous scoring loop."""
        if self._running:
            logger.warning("Oracle agent is already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(interval_seconds))
        logger.info("Oracle agent started (interval=%ds)", interval_seconds)

    def stop(self):
        """Stop the scoring loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Oracle agent stopped")

    async def _loop(self, interval: int):
        """Main autonomous loop."""
        while self._running:
            try:
                await self._run_cycle()
                self._last_run = datetime.now(timezone.utc)
            except Exception:
                self._errors += 1
                logger.exception("Oracle agent cycle failed")
            await asyncio.sleep(interval)

    async def _run_cycle(self):
        """Score all monitored tokens and publish results."""
        db: Session = next(self._get_db())
        try:
            tokens = (
                db.query(OracleMonitoredToken)
                .filter(OracleMonitoredToken.is_active.is_(True))
                .all()
            )

            if not tokens:
                logger.debug("No monitored tokens, skipping cycle")
                return

            logger.info("Oracle cycle: scoring %d tokens", len(tokens))

            for token in tokens:
                await self._score_and_publish(db, token)

            db.commit()
        finally:
            db.close()

    async def _score_and_publish(
        self, db: Session, token: OracleMonitoredToken
    ):
        """Score a single token and publish the result on-chain."""
        try:
            # Step 1: Run existing RugSignal scoring pipeline
            score_result = await self._get_score(token.token_address)

            score = score_result["score"]
            risk_level = score_result["risk_level"]
            confidence = score_result["confidence"]
            reasoning = score_result.get("reasoning", "")

            logger.info(
                "Scoring done: %s score=%d risk=%s conf=%.2f, publishing...",
                token.token_address[:12], score, risk_level, confidence,
            )

            # Step 2: Publish on-chain
            result = await self._publisher.publish_score(
                token_mint=token.token_address,
                score=score,
                risk_level=risk_level,
                confidence=int(confidence * 100),
            )

            # Step 3: Record event in DB
            event = OraclePublishEvent(
                token_address=token.token_address,
                score=score,
                risk_level=risk_level,
                confidence=confidence,
                reasoning=reasoning or None,
                tx_signature=result.tx_signature,
                status="published" if result.success else "failed",
                error_message=result.error,
            )
            db.add(event)

            # Step 4: Update monitored token state
            token.last_score = score
            token.last_risk_level = risk_level
            token.last_confidence = confidence
            token.last_published_at = datetime.now(timezone.utc)
            token.last_tx_signature = result.tx_signature
            token.last_reasoning = reasoning or None

            if result.success:
                self._total_published += 1
                logger.info(
                    "Published: %s score=%d risk=%s tx=%s",
                    token.token_address[:12],
                    score,
                    risk_level,
                    result.tx_signature,
                )
            else:
                self._errors += 1
                logger.error(
                    "Failed to publish %s: %s",
                    token.token_address[:12],
                    result.error,
                )

        except Exception as exc:
            self._errors += 1
            import traceback
            logger.error("Error scoring %s: %s\n%s", token.token_address, exc, traceback.format_exc())

    async def _get_score(self, token_address: str) -> dict:
        """Get risk score using AI agent (Claude) + rule engine fallback.

        1. Gather on-chain features via RugSignal pipeline
        2. Send features to Claude AI for analysis
        3. Fall back to rule engine if AI unavailable
        """
        features = {}
        rule_score = None

        # Step 1: Gather features from existing pipeline
        try:
            repository = self._get_repository()
            report = repository.create_report("token", token_address)

            if report is not None:
                if self._get_pipeline:
                    pipeline = self._get_pipeline()
                    result = pipeline.run(report=report)
                    rule_score = {
                        "score": result.response.score,
                        "risk_level": result.response.risk_level,
                        "confidence": result.response.confidence,
                    }
                    features = getattr(result, "features", {}) or {}
                else:
                    if isinstance(report, dict):
                        overview = report.get("overview", report)
                        features = report.get("features", {})
                        score = overview.get("score", overview.get("rug_probability", 50))
                        confidence = overview.get("confidence", 0.5)
                    else:
                        overview = getattr(report, "overview", report)
                        features = getattr(report, "features", {}) or {}
                        score = getattr(overview, "score", None) or getattr(overview, "rug_probability", 50)
                        confidence = getattr(overview, "confidence", 0.5)

                    score = int(score) if score is not None else 50
                    rule_score = {
                        "score": score,
                        "risk_level": _risk_level_from_score(score),
                        "confidence": float(confidence),
                    }
        except Exception as exc:
            logger.warning("Feature extraction failed for %s: %s", token_address[:12], exc)

        # Step 2: ML model scoring via DexScreener features
        ml_probability = -1.0
        if self._ml_engine.has_model:
            try:
                pairs = self._dex_client.get_token_pairs("solana", token_address)
                pair = pick_most_liquid_pair(pairs)
                if pair:
                    ml_probability = self._ml_engine.predict_from_dexscreener(pair)
                    logger.info(
                        "ML model scored %s: rug_probability=%.2f%%",
                        token_address[:12], ml_probability * 100,
                    )
            except Exception as exc:
                logger.warning("ML scoring failed for %s: %s", token_address[:12], exc)

        # Step 3: AI scoring via Claude
        features_dict = features if isinstance(features, dict) else {}
        if ml_probability >= 0:
            features_dict["ml_rug_probability"] = round(ml_probability * 100, 1)
        ai_result = await ai_score_token(token_address, features_dict)
        if ai_result:
            # Blend AI score with ML probability if available
            if ml_probability >= 0:
                ai_score = ai_result["score"]
                ml_score = int(ml_probability * 100)
                blended = int(0.6 * ai_score + 0.4 * ml_score)
                ai_result["score"] = blended
                ai_result["risk_level"] = _risk_level_from_score(blended)
                ai_result["ml_probability"] = round(ml_probability, 4)
            logger.info(
                "AI+ML scored %s: %d (%s) — %s",
                token_address[:12], ai_result["score"], ai_result["risk_level"],
                ai_result.get("reasoning", ""),
            )
            return ai_result

        # Step 4: ML-only fallback (no AI available)
        if ml_probability >= 0:
            ml_score = int(ml_probability * 100)
            result = {
                "score": ml_score,
                "risk_level": _risk_level_from_score(ml_score),
                "confidence": 0.7,
                "ml_probability": round(ml_probability, 4),
                "reasoning": f"ML model rug probability: {ml_probability * 100:.1f}%",
            }
            logger.info("ML-only score for %s: %s", token_address[:12], result)
            return result

        # Step 5: Fall back to rule engine
        if rule_score:
            logger.info("Using rule engine score for %s: %s", token_address[:12], rule_score)
            return rule_score

        logger.warning("All scoring failed for %s, using fallback", token_address[:12])
        return {"score": 50, "risk_level": "medium", "confidence": 0.3}

    async def score_single(self, token_address: str) -> dict:
        """Score a single token on-demand (not part of the loop)."""
        return await self._get_score(token_address)


# ─── Singleton management ─────────────────────────────────────────────────────

_agent_instance: OracleAgent | None = None


def get_oracle_agent() -> OracleAgent | None:
    return _agent_instance


def init_oracle_agent(
    *,
    settings: Settings,
    publisher: SolanaPublisher,
    get_db: callable,
    get_repository: callable,
    get_pipeline: callable | None = None,
) -> OracleAgent:
    global _agent_instance
    _agent_instance = OracleAgent(
        settings=settings,
        publisher=publisher,
        get_db=get_db,
        get_repository=get_repository,
        get_pipeline=get_pipeline,
    )
    return _agent_instance
