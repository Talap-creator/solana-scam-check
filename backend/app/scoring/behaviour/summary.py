from __future__ import annotations

from .models import BehaviourModuleComputation


def compose_behaviour_summary(
    modules: dict[str, BehaviourModuleComputation],
    *,
    market_maturity_score: int | None = None,
    known_project_flag: bool = False,
    token_age_days: int | None = None,
) -> str:
    flagged = {key for key, module in modules.items() if module.status == "flagged"}
    watch = {key for key, module in modules.items() if module.status == "watch"}
    strong_flagged = flagged & {"developer_cluster", "insider_selling"}
    moderate_flagged = flagged & {"early_buyers"}
    liquidity_only_flagged = flagged == {"liquidity_management"} and not watch
    mature_context = bool(
        (market_maturity_score is not None and market_maturity_score >= 45)
        or known_project_flag
        or (token_age_days is not None and token_age_days >= 180)
    )

    if strong_flagged and ("liquidity_management" in flagged or moderate_flagged):
        return "Multiple scam-linked behaviour signals were detected."
    if strong_flagged:
        return "Coordinated wallet behaviour was detected and should be reviewed closely."
    if moderate_flagged and ("liquidity_management" in flagged or "liquidity_management" in watch):
        return "Coordinated early-wallet activity was observed alongside liquidity-related anomalies."
    if liquidity_only_flagged:
        if mature_context:
            return (
                "Some liquidity-management irregularities were observed, but no broader suspicious wallet "
                "behaviour was detected."
            )
        return (
            "A liquidity-related behaviour signal was observed, though it is not accompanied by stronger "
            "coordination or insider activity patterns."
        )
    if moderate_flagged:
        return "Some coordinated early-wallet behaviour was detected and may warrant closer review."
    if watch & {"developer_cluster", "insider_selling", "early_buyers"}:
        return "Some coordinated wallet behaviour was detected and should be reviewed."
    if "liquidity_management" in watch:
        if mature_context:
            return (
                "Some liquidity-management irregularities were observed, but no broader suspicious wallet "
                "behaviour was detected."
            )
        return "A mild liquidity-related anomaly was observed, but broader scam-linked behaviour was not detected."
    return "No strong scam-specific behaviour signals were found."
