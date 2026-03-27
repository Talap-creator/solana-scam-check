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
from .solana_publisher import SolanaPublisher

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

        except Exception:
            self._errors += 1
            logger.exception("Error scoring %s", token.token_address)

    async def _get_score(self, token_address: str) -> dict:
        """Get risk score from the existing RugSignal pipeline.

        Falls back to the V1 report analyzer if the V2 pipeline
        is not available.
        """
        try:
            repository = self._get_repository()
            report = repository.create_report("token", token_address)

            if report is None:
                logger.warning("create_report returned None for %s", token_address)
                return {"score": 50, "risk_level": "medium", "confidence": 0.3}

            if self._get_pipeline:
                pipeline = self._get_pipeline()
                result = pipeline.run(report=report)
                return {
                    "score": result.response.score,
                    "risk_level": result.response.risk_level,
                    "confidence": result.response.confidence,
                }

            # Fallback: extract from V1 report (could be dict or object)
            if isinstance(report, dict):
                overview = report.get("overview", report)
                score = overview.get("score", overview.get("rug_probability", 50))
                confidence = overview.get("confidence", 0.5)
            else:
                overview = getattr(report, "overview", report)
                score = getattr(overview, "score", None) or getattr(overview, "rug_probability", 50)
                confidence = getattr(overview, "confidence", 0.5)

            score = int(score) if score is not None else 50
            return {
                "score": score,
                "risk_level": _risk_level_from_score(score),
                "confidence": float(confidence),
            }

        except Exception as exc:
            logger.warning("Pipeline failed for %s, using fallback: %s", token_address, exc)
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
