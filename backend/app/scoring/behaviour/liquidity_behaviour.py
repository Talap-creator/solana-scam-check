from __future__ import annotations

from ...config import Settings
from .feature_utils import clamp_score, clamp_unit, confidence_label, module_severity, module_status
from .models import BehaviourModuleComputation


def evaluate_liquidity_management(
    *,
    signal: dict[str, float | int | bool | str],
    insider_liquidity_correlation: bool,
    settings: Settings,
) -> BehaviourModuleComputation:
    detected = bool(signal.get("detected"))
    severity = str(signal.get("severity") or "green")
    summary = str(signal.get("summary") or "No unusual liquidity management detected.")
    raw_details = str(signal.get("details") or "")
    detail_parts = [part.strip() for part in raw_details.split("|") if part.strip()]
    rapid_liquidity_drop_score = float(signal.get("rapid_liquidity_drop_score") or (1.0 if severity == "red" else 0.55 if detected else 0.0))
    liquidity_volatility_score = float(signal.get("liquidity_volatility_score") or (0.75 if "volume" in raw_details.lower() else 0.20 if detected else 0.0))
    lp_owner_link_score = float(signal.get("lp_owner_deployer_link_score") or (0.75 if "controllable lp" in summary.lower() or "ownership" in summary.lower() else 0.0))
    change_vs_exits = float(signal.get("liquidity_change_vs_holder_exits_score") or (1.0 if insider_liquidity_correlation else 0.0))
    short_window_sell_pressure_score = float(signal.get("short_window_sell_pressure_score") or 0.0)
    short_window_price_drop_score = float(signal.get("short_window_price_drop_score") or 0.0)
    short_window_volume_acceleration_score = float(signal.get("short_window_volume_acceleration_score") or 0.0)
    score = clamp_score(
        100
        * (
            0.30 * float(detected)
            + 0.25 * rapid_liquidity_drop_score
            + 0.15 * liquidity_volatility_score
            + 0.10 * lp_owner_link_score
            + 0.10 * change_vs_exits
            + 0.05 * short_window_sell_pressure_score
            + 0.03 * short_window_price_drop_score
            + 0.02 * short_window_volume_acceleration_score
        )
    )
    confidence_value = (
        0.40 * (1.0 if detail_parts else 0.25)
        + 0.25 * rapid_liquidity_drop_score
        + 0.20 * liquidity_volatility_score
        + 0.10 * change_vs_exits
        + 0.05 * short_window_price_drop_score
    )

    if not detail_parts:
        detail_parts = ["Liquidity behaviour does not currently match a classic rug liquidity pattern."]

    return BehaviourModuleComputation(
        key="liquidity_management",
        title="Liquidity management behaviour",
        status=module_status(score),
        severity=module_severity(score),
        score=float(score),
        summary=summary,
        details=detail_parts[:4],
        evidence={
            "liquidity_add_remove_pattern_score": round(rapid_liquidity_drop_score, 4),
            "rapid_liquidity_drop_score": round(rapid_liquidity_drop_score, 4),
            "lp_owner_deployer_link_score": round(lp_owner_link_score, 4),
            "liquidity_volatility_score": round(liquidity_volatility_score, 4),
            "liquidity_change_vs_holder_exits_score": round(change_vs_exits, 4),
            "short_window_sell_pressure_score": round(short_window_sell_pressure_score, 4),
            "short_window_price_drop_score": round(short_window_price_drop_score, 4),
            "short_window_volume_acceleration_score": round(short_window_volume_acceleration_score, 4),
            "warn_threshold_pct": settings.behaviour_rapid_liquidity_drop_warn_pct,
            "high_threshold_pct": settings.behaviour_rapid_liquidity_drop_high_pct,
        },
        confidence=confidence_label(confidence_value),
    )
