from __future__ import annotations

from ...config import Settings
from ...schemas import BehaviourAnalysisOverview, BehaviourConfidenceBreakdown, BehaviourModuleEvidence, BehaviourModuleOverview
from .confidence import compute_behaviour_confidence
from .developer_cluster import evaluate_developer_cluster
from .early_buyers import evaluate_early_buyers
from .feature_utils import behaviour_risk_level, clamp_score
from .insider_selling import evaluate_insider_selling
from .liquidity_behaviour import evaluate_liquidity_management
from .models import BehaviourComputation
from .summary import compose_behaviour_summary


def _to_schema(computation: BehaviourComputation) -> BehaviourAnalysisOverview:
    return BehaviourAnalysisOverview(
        summary=computation.summary,
        overall_behaviour_risk=computation.overall_behaviour_risk,  # type: ignore[arg-type]
        confidence=computation.confidence,  # type: ignore[arg-type]
        score=computation.score,
        modules={
            key: BehaviourModuleOverview(
                key=module.key,
                title=module.title,
                status=module.status,  # type: ignore[arg-type]
                severity=module.severity,  # type: ignore[arg-type]
                score=module.score,
                summary=module.summary,
                details=module.details,
                evidence=BehaviourModuleEvidence(metrics=module.evidence),
                confidence=module.confidence,  # type: ignore[arg-type]
            )
            for key, module in computation.modules.items()
        },
        confidence_breakdown=BehaviourConfidenceBreakdown(**computation.confidence_breakdown),
        version=computation.version,
        debug=computation.debug,
    )


def build_behaviour_analysis_v2(
    *,
    settings: Settings,
    owner_shares: dict[str, float],
    market_age_days: int | None,
    market_maturity_score: int | None = None,
    known_project_flag: bool = False,
    developer_cluster_signal: dict[str, float | int | bool | str | None],
    early_buyer_cluster_signal: dict[str, float | int | bool | str | None],
    insider_selling_signal: dict[str, float | int | bool],
    insider_liquidity_correlation: bool,
    liquidity_management_signal: dict[str, float | int | bool | str],
    debug_context: dict[str, object] | None = None,
) -> tuple[BehaviourComputation, BehaviourAnalysisOverview]:
    developer_cluster = evaluate_developer_cluster(
        owner_shares=owner_shares,
        signal=developer_cluster_signal,
        settings=settings,
    )
    early_buyers = evaluate_early_buyers(
        signal=early_buyer_cluster_signal,
        market_age_days=market_age_days,
        owner_shares=owner_shares,
        developer_cluster_signal=developer_cluster_signal,
        settings=settings,
    )
    insider_selling = evaluate_insider_selling(
        signal=insider_selling_signal,
        insider_liquidity_correlation=insider_liquidity_correlation,
        developer_cluster_signal=developer_cluster_signal,
        settings=settings,
    )
    liquidity_management = evaluate_liquidity_management(
        signal=liquidity_management_signal,
        insider_liquidity_correlation=insider_liquidity_correlation,
        settings=settings,
    )
    modules = {
        "developer_cluster": developer_cluster,
        "early_buyers": early_buyers,
        "insider_selling": insider_selling,
        "liquidity_management": liquidity_management,
    }
    strong_modules = {"developer_cluster", "insider_selling"}
    medium_modules = {"early_buyers"}
    contextual_modules = {"liquidity_management"}
    flagged = {key for key, module in modules.items() if module.status == "flagged"}
    watch = {key for key, module in modules.items() if module.status == "watch"}
    strong_flagged = flagged & strong_modules
    medium_flagged = flagged & medium_modules
    liquidity_only_flagged = flagged == contextual_modules and not watch
    mature_context = bool(
        (market_maturity_score is not None and market_maturity_score >= 45)
        or known_project_flag
        or (market_age_days is not None and market_age_days >= 180)
    )

    if liquidity_only_flagged:
        liquidity_management.score = min(liquidity_management.score, 48.0 if mature_context else 54.0)
        liquidity_management.status = "watch"
        liquidity_management.severity = "medium"
        modules["liquidity_management"] = liquidity_management

    behaviour_risk_score = clamp_score(
        0.30 * developer_cluster.score
        + 0.20 * early_buyers.score
        + 0.25 * insider_selling.score
        + 0.25 * liquidity_management.score
    )
    if liquidity_only_flagged:
        behaviour_risk_score = min(behaviour_risk_score, 18 if mature_context else 24)
    elif not strong_flagged and not medium_flagged and flagged == {"liquidity_management"}:
        behaviour_risk_score = min(behaviour_risk_score, 24)

    flagged_pairs = (
        (developer_cluster.status == "flagged" and insider_selling.status == "flagged")
        or (early_buyers.status == "flagged" and liquidity_management.status == "flagged")
    )
    if flagged_pairs:
        behaviour_risk_score = clamp_score(behaviour_risk_score * settings.behaviour_boost_multiplier)

    confidence_label_value, breakdown, _ = compute_behaviour_confidence(
        owner_wallet_count=len(owner_shares),
        developer_confidence=developer_cluster.confidence,
        early_buyer_confidence=early_buyers.confidence,
        insider_confidence=insider_selling.confidence,
        liquidity_confidence=liquidity_management.confidence,
        has_liquidity_data=bool(liquidity_management_signal),
    )
    computation = BehaviourComputation(
        summary=compose_behaviour_summary(
            modules,
            market_maturity_score=market_maturity_score,
            known_project_flag=known_project_flag,
            token_age_days=market_age_days,
        ),
        overall_behaviour_risk=behaviour_risk_level(behaviour_risk_score),
        confidence=confidence_label_value,
        score=behaviour_risk_score,
        modules=modules,
        confidence_breakdown=breakdown,
        debug={
            "modules_ran": list(modules.keys()),
            "triggered_rules": {
                "developer_cluster_flagged": developer_cluster.status == "flagged",
                "early_buyers_flagged": early_buyers.status == "flagged",
                "insider_selling_flagged": insider_selling.status == "flagged",
                "liquidity_management_flagged": liquidity_management.status == "flagged",
                "liquidity_only_flagged_softened": liquidity_only_flagged,
                "flagged_pair_multiplier_applied": flagged_pairs,
                "insider_liquidity_correlation": insider_liquidity_correlation,
                "mature_context": mature_context,
            },
            "coverage": {
                "tracked_owner_wallets": len(owner_shares),
                "liquidity_data_available": bool(liquidity_management_signal),
                "market_age_days": market_age_days,
                "market_maturity_score": market_maturity_score,
                "known_project_flag": known_project_flag,
            },
            **(debug_context or {}),
        },
    )
    return computation, _to_schema(computation)
