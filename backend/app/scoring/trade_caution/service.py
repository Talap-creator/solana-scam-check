from __future__ import annotations

from ...schemas import TradeCautionDimensions, TradeCautionOverview
from ..behaviour.models import BehaviourComputation
from .calculators import clamp_score, clamp_unit, norm, norm_inverse_log, trade_caution_label, trade_caution_level
from .summary import compose_trade_caution_summary


def build_trade_caution_overview(
    *,
    rug_probability: int,
    technical_risk: int,
    distribution_risk: int,
    market_execution_risk: int,
    market_maturity: int,
    market_age_days: int | None,
    market_cap_usd: float | None,
    volume_24h_usd: float | None,
    usd_liquidity: float | None,
    largest_pool_liquidity_usd: float | None,
    pool_count: int,
    dex_count: int,
    top_1_share: float | None,
    top_10_share: float | None,
    dev_cluster_share: float,
    known_project_flag: bool,
    listed_on_major_cex: bool,
    listed_on_known_aggregator: bool,
    mint_authority_enabled: bool,
    freeze_authority_enabled: bool,
    update_authority_enabled: bool,
    dangerous_contract_capability_score: float,
    metadata_mismatch: bool,
    lp_lock_missing: bool,
    lp_owner_is_deployer: bool,
    suspicious_liquidity_control: bool,
    honeypot_simulation_failed: bool,
    sell_restrictions_detected: bool,
    behaviour: BehaviourComputation,
) -> TradeCautionOverview:
    admin_caution = clamp_score(
        100
        * clamp_unit(
            (0.40 * float(mint_authority_enabled))
            + (0.25 * float(freeze_authority_enabled))
            + (0.15 * float(update_authority_enabled))
            + (0.15 * clamp_unit(dangerous_contract_capability_score))
            + (0.05 * float(metadata_mismatch))
        )
    )

    low_pool_count_score = 1.0 if pool_count <= 1 else 0.55 if pool_count == 2 else 0.15
    low_dex_coverage_score = 1.0 if dex_count <= 1 else 0.45 if dex_count == 2 else 0.10
    lp_structure_score = clamp_unit(
        (0.45 * float(lp_lock_missing))
        + (0.35 * float(lp_owner_is_deployer))
        + (0.20 * float(suspicious_liquidity_control))
    )
    execution_caution = clamp_score(
        100
        * clamp_unit(
            (0.45 * norm_inverse_log(usd_liquidity, 5_000, 50_000_000))
            + (0.20 * norm_inverse_log(largest_pool_liquidity_usd, 5_000, 20_000_000))
            + (0.15 * low_pool_count_score)
            + (0.10 * low_dex_coverage_score)
            + (0.10 * lp_structure_score)
        )
    )

    gini_proxy = clamp_unit(
        (0.55 * norm(top_1_share, 5, 55)) + (0.45 * norm(top_10_share, 30, 95))
    )
    concentration_caution = clamp_score(
        100
        * clamp_unit(
            (0.30 * norm(top_1_share, 5, 45))
            + (0.35 * norm(top_10_share, 25, 90))
            + (0.15 * gini_proxy)
            + (0.20 * clamp_unit(dev_cluster_share))
        )
    )

    token_age_score = norm(float(market_age_days or 0), 7, 720)
    volume_score = norm(volume_24h_usd, 250_000, 500_000_000)
    market_cap_score = norm(market_cap_usd, 20_000_000, 5_000_000_000)
    dex_coverage_score = 1.0 if listed_on_known_aggregator else 0.0
    known_project_score = 1.0 if known_project_flag else 0.0
    market_structure_strength = clamp_score(
        100
        * clamp_unit(
            (0.30 * token_age_score)
            + (0.25 * volume_score)
            + (0.20 * market_cap_score)
            + (0.15 * dex_coverage_score)
            + (0.10 * known_project_score)
        )
        + (8 if listed_on_major_cex else 0)
    )

    behavioural_caution = clamp_score(
        0.30 * behaviour.modules["developer_cluster"].score
        + 0.20 * behaviour.modules["early_buyers"].score
        + 0.25 * behaviour.modules["insider_selling"].score
        + 0.25 * behaviour.modules["liquidity_management"].score
    )

    trade_caution_score = clamp_score(
        (0.25 * admin_caution)
        + (0.30 * execution_caution)
        + (0.20 * concentration_caution)
        + (0.20 * behavioural_caution)
        - (0.15 * market_structure_strength)
    )

    if honeypot_simulation_failed or sell_restrictions_detected:
        trade_caution_score = max(trade_caution_score, 90)
    if admin_caution >= 55 and execution_caution >= 70:
        trade_caution_score = max(trade_caution_score, 60)
    if freeze_authority_enabled and suspicious_liquidity_control:
        trade_caution_score = max(trade_caution_score, 75)
    if (top_10_share or 0) >= 85 and (usd_liquidity or 0) < 75_000:
        trade_caution_score = max(trade_caution_score, 75)
    if (
        behaviour.modules["developer_cluster"].status == "flagged"
        and behaviour.modules["insider_selling"].status == "flagged"
    ):
        trade_caution_score = max(trade_caution_score, 80)

    if known_project_flag and (market_age_days or 0) >= 180 and market_structure_strength >= 60:
        if not honeypot_simulation_failed and not sell_restrictions_detected:
            trade_caution_score = min(trade_caution_score, 84)

    level = trade_caution_level(trade_caution_score)
    drivers: list[tuple[str, int]] = []
    if mint_authority_enabled:
        drivers.append(("Mint authority enabled", 90))
    if freeze_authority_enabled:
        drivers.append(("Freeze authority enabled", 80))
    if update_authority_enabled:
        drivers.append(("Update authority enabled", 55))
    if execution_caution >= 60:
        drivers.append(("Thin pool liquidity", 85))
    if pool_count <= 1:
        drivers.append(("Limited pool count", 60))
    if dex_count <= 1:
        drivers.append(("Low DEX coverage", 55))
    if concentration_caution >= 55:
        drivers.append(("Holder concentration", 70))
    if behaviour.modules["developer_cluster"].status != "clear":
        drivers.append(("Developer wallet coordination", 88))
    if behaviour.modules["insider_selling"].status != "clear":
        drivers.append(("Insider selling patterns", 84))
    if behaviour.modules["liquidity_management"].status != "clear":
        drivers.append(("Limited market depth", 66))
    if lp_owner_is_deployer or lp_lock_missing:
        drivers.append(("Weak LP structure", 72))
    ordered_drivers = [label for label, _ in sorted(drivers, key=lambda item: item[1], reverse=True)]

    summary = compose_trade_caution_summary(
        level=level,
        admin_caution=admin_caution,
        execution_caution=execution_caution,
        concentration_caution=concentration_caution,
        behavioural_caution=behavioural_caution,
        rug_probability=rug_probability,
    )

    return TradeCautionOverview(
        score=trade_caution_score,
        level=level,
        label=trade_caution_label(level),
        summary=summary,
        drivers=ordered_drivers[:5],
        dimensions=TradeCautionDimensions(
            admin_caution=admin_caution,
            execution_caution=execution_caution,
            concentration_caution=concentration_caution,
            behavioural_caution=behavioural_caution,
            market_structure_strength=market_structure_strength,
        ),
    )
