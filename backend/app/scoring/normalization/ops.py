from __future__ import annotations

import math


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize_bool(value: bool | None, missing_value: float = 0.5) -> float:
    if value is None:
        return clamp01(missing_value)
    return 1.0 if value else 0.0


def normalize_threshold(
    value: float | None,
    low: float,
    high: float,
    *,
    invert: bool = False,
    missing_value: float = 0.5,
) -> float:
    if value is None:
        return clamp01(missing_value)
    if high <= low:
        return 0.0
    normalized = clamp01((float(value) - low) / (high - low))
    return 1.0 - normalized if invert else normalized


def normalize_log_scale(
    value: float | None,
    min_value: float,
    max_value: float,
    *,
    missing_value: float = 0.5,
) -> float:
    if value is None:
        return clamp01(missing_value)
    if min_value <= 0 or max_value <= min_value:
        return 0.0
    safe_value = min(max(float(value), min_value), max_value)
    min_log = math.log10(min_value)
    max_log = math.log10(max_value)
    val_log = math.log10(safe_value)
    return clamp01((val_log - min_log) / (max_log - min_log))


def normalize_inverse_log_scale(
    value: float | None,
    min_value: float,
    max_value: float,
    *,
    missing_value: float = 0.5,
) -> float:
    return 1.0 - normalize_log_scale(
        value,
        min_value,
        max_value,
        missing_value=missing_value,
    )


def bucketize_percentile(value: float | None, buckets: list[tuple[float, float]]) -> float:
    if value is None:
        return 0.5
    v = float(value)
    sorted_buckets = sorted(buckets, key=lambda item: item[0])
    for threshold, mapped in sorted_buckets:
        if v <= threshold:
            return clamp01(mapped)
    return clamp01(sorted_buckets[-1][1] if sorted_buckets else 0.5)
