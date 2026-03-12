from __future__ import annotations

from .feature_utils import clamp_unit, confidence_label, label_from_fraction


def compute_behaviour_confidence(
    *,
    owner_wallet_count: int,
    developer_confidence: str,
    early_buyer_confidence: str,
    insider_confidence: str,
    liquidity_confidence: str,
    has_liquidity_data: bool,
) -> tuple[str, dict[str, str], float]:
    holder_coverage_score = clamp_unit(owner_wallet_count / 5.0)
    tx_coverage_score = clamp_unit(
        0.8 if insider_confidence == "high" else 0.55 if insider_confidence == "medium" else 0.2
    )
    funding_trace_score = clamp_unit(
        0.8 if developer_confidence == "high" else 0.55 if developer_confidence == "medium" else 0.2
    )
    liquidity_score = 1.0 if has_liquidity_data and liquidity_confidence == "high" else 0.6 if has_liquidity_data else 0.2
    source_consistency_score = clamp_unit(
        (
            (1.0 if developer_confidence != "limited" else 0.4)
            + (1.0 if early_buyer_confidence != "limited" else 0.4)
            + (1.0 if insider_confidence != "limited" else 0.4)
            + (1.0 if liquidity_confidence != "limited" else 0.4)
        )
        / 4.0
    )
    total = (
        0.25 * holder_coverage_score
        + 0.20 * tx_coverage_score
        + 0.20 * funding_trace_score
        + 0.20 * liquidity_score
        + 0.15 * source_consistency_score
    )
    return (
        confidence_label(total),
        {
            "holder_coverage": label_from_fraction(holder_coverage_score),
            "transaction_coverage": label_from_fraction(tx_coverage_score),
            "funding_trace_depth": "deep" if funding_trace_score >= 0.70 else "moderate" if funding_trace_score >= 0.35 else "shallow",
            "liquidity_data": label_from_fraction(liquidity_score),
        },
        total,
    )
