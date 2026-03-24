from __future__ import annotations

from ...config import Settings
from .feature_utils import clamp_score, clamp_unit, confidence_label, module_severity, module_status
from .models import BehaviourModuleComputation


def evaluate_developer_cluster(
    *,
    owner_shares: dict[str, float],
    signal: dict[str, float | int | bool | str | None],
    settings: Settings,
) -> BehaviourModuleComputation:
    tracked_wallets = len(owner_shares)
    cluster_wallets = int(signal.get("cluster_wallet_count") or 0)
    cluster_supply_share = float(signal.get("cluster_supply_control_pct") or 0.0)
    shared_funder = signal.get("shared_funder")
    lead_wallet = signal.get("lead_wallet")
    shared_funding_ratio = float(signal.get("shared_funding_ratio") or ((cluster_wallets / tracked_wallets) if tracked_wallets else 0.0))
    timing_similarity_score = float(signal.get("timing_similarity_score") or 0.0)
    direct_wallet_overlap_count = int(signal.get("direct_wallet_overlap_count") or 0)
    shared_outgoing_wallets_count = int(signal.get("shared_outgoing_wallets_count") or 0)
    multi_hop_shared_funder_count = int(signal.get("multi_hop_shared_funder_count") or 0)
    funding_trace_depth_avg = float(signal.get("funding_trace_depth_avg") or 0.0)
    funding_score = clamp_unit(shared_funding_ratio / max(settings.behaviour_shared_funding_ratio_high, 0.01))
    supply_score = clamp_unit(cluster_supply_share / max(settings.behaviour_cluster_supply_high, 1.0))
    detected = bool(signal.get("detected"))
    score = clamp_score(
        100
        * (
            0.40 * float(detected)
            + 0.35 * funding_score
            + 0.15 * supply_score
            + 0.05 * timing_similarity_score
            + 0.05 * min(1.0, direct_wallet_overlap_count / 2.0)
            + 0.05 * min(1.0, multi_hop_shared_funder_count / 2.0)
        )
    )
    confidence_value = (
        0.30 * clamp_unit(tracked_wallets / 5.0)
        + 0.40 * clamp_unit(float(signal.get("confidence") or 0.0))
        + 0.20 * clamp_unit(shared_funding_ratio)
        + 0.10 * timing_similarity_score
        + 0.05 * min(1.0, funding_trace_depth_avg / 2.0)
    )

    if score >= 55:
        summary = "Possible developer-linked wallet cluster detected."
        details = [
            f"{cluster_wallets} tracked holder wallets appear linked through overlapping funding routes.",
            f"Estimated cluster control over tracked supply is {cluster_supply_share:.1f}%.",
            (
                f"Shared funding source observed: {str(shared_funder)[:4]}...{str(shared_funder)[-4:]}"
                if shared_funder
                else "Shared funding overlap was detected among tracked holder wallets."
            ),
        ]
    elif score >= 25:
        summary = "Some holder-linkage signals warrant review."
        details = [
            "Wallet overlap signals are present but not strong enough for a high-confidence cluster flag.",
            f"Tracked cluster coverage is {shared_funding_ratio * 100:.1f}% of analyzed holder wallets.",
        ]
    else:
        summary = "No clear developer cluster detected."
        details = [
            "No strong multi-wallet control pattern was inferred from current holder and funding overlap data.",
            "Available holder evidence does not show meaningful coordinated control.",
        ]

    return BehaviourModuleComputation(
        key="developer_cluster",
        title="Developer wallet cluster",
        status=module_status(score),
        severity=module_severity(score),
        score=float(score),
        summary=summary,
        details=details,
        evidence={
            "shared_funding_wallet_count": cluster_wallets,
            "shared_funding_ratio": round(shared_funding_ratio, 4),
            "top_wallets_with_common_funder_count": cluster_wallets,
            "holder_activity_time_similarity_score": round(timing_similarity_score, 4),
            "direct_token_transfer_between_top_wallets": direct_wallet_overlap_count,
            "shared_outgoing_wallets_count": shared_outgoing_wallets_count,
            "multi_hop_shared_funder_count": multi_hop_shared_funder_count,
            "cluster_funding_depth_avg": round(funding_trace_depth_avg, 2),
            "estimated_cluster_wallet_count": cluster_wallets,
            "estimated_cluster_supply_share": round(cluster_supply_share, 2),
            "shared_funder": shared_funder,
            "lead_wallet": lead_wallet,
        },
        confidence=confidence_label(confidence_value),
    )
