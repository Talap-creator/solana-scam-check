from __future__ import annotations

from ...config import Settings
from .feature_utils import clamp_score, clamp_unit, confidence_label, module_severity, module_status
from .models import BehaviourModuleComputation


def evaluate_insider_selling(
    *,
    signal: dict[str, float | int | bool],
    insider_liquidity_correlation: bool,
    developer_cluster_signal: dict[str, float | int | bool | str | None],
    settings: Settings,
) -> BehaviourModuleComputation:
    seller_wallet_count = int(signal.get("seller_wallet_count") or 0)
    seller_supply_control_pct = float(signal.get("seller_supply_control_pct") or 0.0)
    large_holder_sell_ratio = float(signal.get("large_holder_sell_ratio_recent") or clamp_unit(
        seller_supply_control_pct / max(settings.behaviour_dev_cluster_sell_high, 1.0)
    ))
    dev_cluster_sell_ratio = clamp_unit(
        seller_supply_control_pct / max(settings.behaviour_dev_cluster_sell_high, 1.0)
    ) if bool(developer_cluster_signal.get("detected")) else 0.0
    coordinated_exit_window_score = float(signal.get("coordinated_exit_window_score") or clamp_unit(seller_wallet_count / 3.0))
    sell_window_span_seconds = int(signal.get("sell_window_span_seconds") or 0)
    sell_before_liquidity_drop_score = 1.0 if insider_liquidity_correlation else 0.0
    score = clamp_score(
        100
        * (
            0.30 * float(bool(signal.get("detected")))
            + 0.25 * large_holder_sell_ratio
            + 0.20 * dev_cluster_sell_ratio
            + 0.15 * coordinated_exit_window_score
            + 0.10 * sell_before_liquidity_drop_score
        )
    )
    confidence_value = (
        0.35 * clamp_unit(float(signal.get("confidence") or 0.0))
        + 0.25 * coordinated_exit_window_score
        + 0.20 * large_holder_sell_ratio
        + 0.20 * sell_before_liquidity_drop_score
    )

    if score >= 55:
        summary = "Possible insider selling pattern detected."
        details = [
            f"Recent seller wallets tracked: {seller_wallet_count}.",
            f"Those wallets represent about {seller_supply_control_pct:.1f}% of tracked supply.",
            (
                "Selling activity overlaps with weak liquidity conditions."
                if insider_liquidity_correlation
                else "Recent selling activity is concentrated enough to warrant review."
            ),
        ]
    elif score >= 25:
        summary = "Some large-holder exit activity was detected."
        details = [
            "Large-holder selling signals are present, but not yet strong enough for a high-confidence insider flag.",
            "Observed exits should be reviewed together with liquidity and developer-cluster context.",
        ]
    else:
        summary = "No insider selling pattern detected."
        details = [
            "No meaningful pre-collapse exit signal was inferred from current wallet behaviour.",
            "Recent large-holder transfer activity does not currently indicate coordinated exits.",
        ]

    return BehaviourModuleComputation(
        key="insider_selling",
        title="Insider selling patterns",
        status=module_status(score),
        severity=module_severity(score),
        score=float(score),
        summary=summary,
        details=details,
        evidence={
            "large_holder_sell_ratio_recent": round(large_holder_sell_ratio, 4),
            "dev_cluster_sell_ratio_recent": round(dev_cluster_sell_ratio, 4),
            "early_wallet_sell_ratio_recent": round(large_holder_sell_ratio * 0.7, 4),
            "sell_before_liquidity_drop_score": round(sell_before_liquidity_drop_score, 4),
            "coordinated_exit_window_score": round(coordinated_exit_window_score, 4),
            "top_holder_exit_density": seller_wallet_count,
            "wallet_exit_similarity_score": round(coordinated_exit_window_score, 4),
            "sell_window_span_seconds": sell_window_span_seconds,
        },
        confidence=confidence_label(confidence_value),
    )
