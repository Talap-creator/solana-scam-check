from __future__ import annotations


class ScoreCalibrator:
    version = "cal_v1"

    def calibrate_probability(self, probability: float) -> float:
        # Mild platt-like smoothing for stability in absence of fitted calibrator.
        p = max(0.0, min(1.0, probability))
        calibrated = (0.92 * p) + 0.04
        return max(0.0, min(1.0, round(calibrated, 4)))
