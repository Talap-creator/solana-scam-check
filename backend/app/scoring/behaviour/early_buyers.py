from __future__ import annotations

from ...config import Settings
from .feature_utils import clamp_score, clamp_unit, confidence_label, module_severity, module_status
from .models import BehaviourModuleComputation


def evaluate_early_buyers(
    *,
    signal: dict[str, float | int | bool | str | None],
    market_age_days: int | None,
    owner_shares: dict[str, float],
    developer_cluster_signal: dict[str, float | int | bool | str | None],
    settings: Settings,
) -> BehaviourModuleComputation:
    tracked_wallets = max(1, len(owner_shares))
    cluster_wallets = int(signal.get("cluster_wallet_count") or 0)
    cluster_supply_share = float(signal.get("cluster_supply_control_pct") or 0.0)
    shared_funding_ratio = float(signal.get("shared_funding_ratio") or (cluster_wallets / tracked_wallets))
    same_window_buy_density = float(signal.get("same_window_buy_density") or 0.0)
    buy_size_similarity_score = float(signal.get("buy_size_similarity_score") or 0.0)
    overlap_with_top_holders = float(signal.get("overlap_with_top_holders") or 0.0)
    multi_hop_shared_funder_count = int(signal.get("multi_hop_shared_funder_count") or 0)
    funding_trace_depth_avg = float(signal.get("funding_trace_depth_avg") or 0.0)
    lead_wallet = signal.get("lead_wallet")
    overlap_with_dev_cluster = clamp_unit(
        float(developer_cluster_signal.get("cluster_supply_control_pct") or 0.0) / 100.0
    ) if bool(signal.get("detected")) and bool(developer_cluster_signal.get("detected")) else 0.0
    recency_factor = 1.0 if market_age_days is not None and market_age_days <= 45 else 0.45
    score = clamp_score(
        100
        * (
            0.35 * float(bool(signal.get("detected")))
            + 0.25 * clamp_unit(shared_funding_ratio / max(settings.behaviour_shared_funding_ratio_warn, 0.01))
            + 0.15 * clamp_unit(cluster_supply_share / max(settings.behaviour_cluster_supply_warn, 1.0))
            + 0.10 * same_window_buy_density
            + 0.05 * buy_size_similarity_score
            + 0.05 * overlap_with_dev_cluster
            + 0.05 * overlap_with_top_holders
            + 0.05 * min(1.0, multi_hop_shared_funder_count / 2.0)
        )
    )
    confidence_value = (
        0.35 * clamp_unit(float(signal.get("confidence") or 0.0))
        + 0.25 * clamp_unit(shared_funding_ratio)
        + 0.15 * clamp_unit(tracked_wallets / 5.0)
        + 0.15 * same_window_buy_density
        + 0.10 * recency_factor
        + 0.05 * min(1.0, funding_trace_depth_avg / 2.0)
    )

    if score >= 55:
        summary = "Possible early-buyer concentration detected."
        details = [
            f"Clustered early wallets account for about {cluster_supply_share:.1f}% of tracked supply.",
            f"{cluster_wallets} early wallets show shared funding or compact activity timing.",
            "Early-wallet overlap is consistent with coordinated accumulation rather than organic entry.",
        ]
    elif score >= 25:
        summary = "Some early-wallet clustering signals were detected."
        details = [
            "Early entry patterns show mild overlap in funding or timing.",
            "The pattern is notable, but current evidence does not support a strong coordinated-entry flag.",
        ]
    else:
        summary = "No major early-buyer concentration detected."
        details = [
            "Available data does not indicate abnormal early concentration or block-level clustering.",
            "No material overlap between early wallets and tracked holder concentration was confirmed.",
        ]

    return BehaviourModuleComputation(
        key="early_buyers",
        title="Early buyer concentration",
        status=module_status(score),
        severity=module_severity(score),
        score=float(score),
        summary=summary,
        details=details,
        evidence={
            "shared_funding_ratio": round(shared_funding_ratio, 4),
            "same_window_buy_density": round(same_window_buy_density, 4),
            "buy_size_similarity_score": round(buy_size_similarity_score, 4),
            "overlap_with_top_holders": round(overlap_with_top_holders, 4),
            "overlap_with_dev_cluster": round(overlap_with_dev_cluster, 4),
            "multi_hop_shared_funder_count": multi_hop_shared_funder_count,
            "funding_trace_depth_avg": round(funding_trace_depth_avg, 2),
            "lead_wallet": lead_wallet,
        },
        confidence=confidence_label(confidence_value),
    )
