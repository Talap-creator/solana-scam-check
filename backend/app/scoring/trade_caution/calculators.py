from __future__ import annotations


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def clamp_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, float(value)))))


def norm(value: float | None, lower: float, upper: float) -> float:
    if value is None:
        return 0.5
    if upper <= lower:
        return 0.0
    return clamp_unit((value - lower) / (upper - lower))


def norm_inverse_log(value: float | None, lower: float, upper: float) -> float:
    if value is None or value <= 0:
        return 1.0
    if lower <= 0:
        lower = 1.0
    if upper <= lower:
        return 0.0

    from math import log10

    value_c = max(lower, min(upper, value))
    normalized = (log10(value_c) - log10(lower)) / (log10(upper) - log10(lower))
    return clamp_unit(1 - normalized)


def trade_caution_level(score: int) -> str:
    if score >= 75:
        return "avoid"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


def trade_caution_label(level: str) -> str:
    labels = {
        "low": "Low caution",
        "moderate": "Moderate caution",
        "high": "High caution",
        "avoid": "Avoid",
    }
    return labels.get(level, "Moderate caution")
