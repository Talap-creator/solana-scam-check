from __future__ import annotations

from datetime import datetime, timezone

from ..models import TokenOverride
from ..schemas import CheckOverview, RiskBreakdownItem, RiskFactor, TimelineEvent


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_token_override(token_address: str, overrides: list[TokenOverride]) -> TokenOverride | None:
    normalized = token_address.strip()
    for item in overrides:
        if item.token_address == normalized and item.chain == "solana":
            return item
    return None


def apply_override(report: CheckOverview, override: TokenOverride) -> CheckOverview:
    reason_suffix = f" Reason: {override.reason}" if override.reason else ""

    if override.verdict == "blacklist":
        report.score = max(report.score, 95)
        report.rug_probability = max(report.rug_probability, 95)
        report.technical_risk = max(report.technical_risk, 90)
        report.distribution_risk = max(report.distribution_risk, 90)
        report.market_execution_risk = max(report.market_execution_risk, 90)
        report.behaviour_risk = max(report.behaviour_risk, 90)
        report.market_maturity = min(report.market_maturity, 15)
        report.status = "critical"
        report.review_state = "Escalated"
        report.summary = f"Token forced to critical risk by admin blacklist override.{reason_suffix}"
        report.factors.insert(
            0,
            RiskFactor(
                code="ADMIN_BLACKLIST_OVERRIDE",
                severity="high",
                label="Admin blacklist override",
                explanation=f"Token is explicitly blacklisted by moderators.{reason_suffix}",
                weight=100,
            ),
        )
        report.risk_increasers.insert(0, report.factors[0])
        report.risk_breakdown = [
            RiskBreakdownItem(block="Technical risk", score=100, weight=0.30, weighted_score=30.0, kind="risk"),
            RiskBreakdownItem(block="Distribution risk", score=100, weight=0.25, weighted_score=25.0, kind="risk"),
            RiskBreakdownItem(block="Market / execution risk", score=100, weight=0.25, weighted_score=25.0, kind="risk"),
            RiskBreakdownItem(block="Behaviour risk", score=100, weight=0.20, weighted_score=20.0, kind="risk"),
            RiskBreakdownItem(block="Market maturity", score=0, weight=1.00, weighted_score=0.0, kind="positive"),
        ]
        report.timeline.insert(
            0,
            TimelineEvent(label="Admin override", value="Blacklisted", tone="danger"),
        )
        return report

    report.score = min(report.score, 10)
    report.rug_probability = min(report.rug_probability, 10)
    report.technical_risk = min(report.technical_risk, 20)
    report.distribution_risk = min(report.distribution_risk, 20)
    report.market_execution_risk = min(report.market_execution_risk, 20)
    report.behaviour_risk = min(report.behaviour_risk, 20)
    report.market_maturity = max(report.market_maturity, 80)
    report.status = "low"
    report.review_state = "Clear"
    report.summary = f"Token forced to low risk by admin whitelist override.{reason_suffix}"
    report.factors.insert(
        0,
        RiskFactor(
            code="ADMIN_WHITELIST_OVERRIDE",
            severity="low",
            label="Admin whitelist override",
            explanation=f"Token is explicitly whitelisted by moderators.{reason_suffix}",
            weight=1,
        ),
    )
    report.risk_reducers.insert(0, report.factors[0])
    report.risk_breakdown = [
        RiskBreakdownItem(block="Technical risk", score=5, weight=0.30, weighted_score=1.5, kind="risk"),
        RiskBreakdownItem(block="Distribution risk", score=5, weight=0.25, weighted_score=1.25, kind="risk"),
        RiskBreakdownItem(block="Market / execution risk", score=5, weight=0.25, weighted_score=1.25, kind="risk"),
        RiskBreakdownItem(block="Behaviour risk", score=5, weight=0.20, weighted_score=1.0, kind="risk"),
        RiskBreakdownItem(block="Market maturity", score=95, weight=1.00, weighted_score=95.0, kind="positive"),
    ]
    report.timeline.insert(
        0,
        TimelineEvent(label="Admin override", value="Whitelisted", tone="neutral"),
    )
    return report
