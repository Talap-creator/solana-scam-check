from __future__ import annotations


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def clamp_score(value: float) -> int:
    return int(round(max(0.0, min(100.0, float(value)))))


def confidence_label(value: float) -> str:
    if value >= 0.70:
        return "high"
    if value >= 0.35:
        return "medium"
    return "limited"


def behaviour_risk_level(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def module_status(score: float) -> str:
    if score >= 55:
        return "flagged"
    if score >= 25:
        return "watch"
    return "clear"


def module_severity(score: float) -> str:
    if score >= 55:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def label_from_fraction(value: float) -> str:
    if value >= 0.80:
        return "full"
    if value >= 0.35:
        return "partial"
    return "limited"
