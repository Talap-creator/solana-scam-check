from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any

import numpy as np
from joblib import load

from ..schemas import TokenFeatureSchema


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


class MLInferenceEngine:
    version = "ml_v1_heuristic"

    def __init__(self) -> None:
        self.uses_calibrated_output = False
        self._model: Any | None = None
        self._feature_columns: list[str] = []
        self._feature_medians: dict[str, float] = {}
        self._artifact_version: str | None = None
        self._load_artifact()

    def _load_artifact(self) -> None:
        artifact_env = os.getenv("SCORING_MODEL_ARTIFACT", "").strip()
        if artifact_env:
            artifact_path = Path(artifact_env)
        else:
            artifact_path = Path(__file__).resolve().parents[3] / "models" / "ml_v1.joblib"

        if not artifact_path.exists():
            return

        try:
            payload = load(artifact_path)
            model = payload.get("model")
            feature_columns = payload.get("feature_columns") or []
            feature_medians = payload.get("feature_medians") or {}
            model_version = payload.get("model_version") or "ml_v1_artifact"
            if model is None or not feature_columns:
                return
            self._model = model
            self._feature_columns = list(feature_columns)
            self._feature_medians = {str(k): float(v) for k, v in feature_medians.items()}
            self._artifact_version = str(model_version)
            self.version = self._artifact_version
            self.uses_calibrated_output = bool(payload.get("is_calibrated", False))
        except Exception:
            # Fallback to heuristic mode.
            self._model = None
            self._feature_columns = []
            self._feature_medians = {}
            self._artifact_version = None
            self.uses_calibrated_output = False

    def _to_feature_dict(self, features: TokenFeatureSchema, rule_score: float) -> dict[str, float]:
        raw = features.model_dump()
        out: dict[str, float] = {}
        for key, value in raw.items():
            if isinstance(value, bool):
                out[key] = 1.0 if value else 0.0
            elif isinstance(value, (int, float)) and value is not None:
                out[key] = float(value)
            else:
                out[key] = self._feature_medians.get(key, 0.0)
        out["rule_score"] = float(rule_score)
        return out

    def predict_probability(self, features: TokenFeatureSchema, rule_score: float) -> float:
        if self._model is not None and self._feature_columns:
            values = self._to_feature_dict(features, rule_score)
            vector = np.array(
                [[values.get(col, self._feature_medians.get(col, 0.0)) for col in self._feature_columns]],
                dtype=float,
            )
            probability = float(self._model.predict_proba(vector)[0][1])
            return max(0.0, min(1.0, round(probability, 4)))

        # Placeholder for baseline inference before model artifact integration.
        x = (rule_score - 45.0) / 14.0
        x += 0.8 * features.dev_cluster_share
        x += 0.6 if features.insider_wallet_detected else 0.0
        x += 0.5 if features.honeypot_simulation_failed else 0.0
        x += 0.3 if features.mint_after_launch_detected else 0.0
        probability = _sigmoid(x)
        return max(0.0, min(1.0, round(probability, 4)))
