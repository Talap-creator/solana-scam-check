from __future__ import annotations

import json
import logging
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from ..schemas import TokenFeatureSchema

logger = logging.getLogger(__name__)


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


# Feature mapping: model feature name -> extraction lambda from DexScreener pair data
def _extract_dexscreener_features(pair: dict) -> dict[str, float]:
    """Extract ML model features from a DexScreener pair response."""
    base = pair.get("baseToken") or {}
    liq = pair.get("liquidity") or {}
    vol = pair.get("volume") or {}
    txns = pair.get("txns") or {}
    pc = pair.get("priceChange") or {}
    info = pair.get("info") or {}
    socials = info.get("socials") or []
    websites = info.get("websites") or []

    social_types = {s.get("type", "").lower() for s in socials}
    pair_created = pair.get("pairCreatedAt") or 0
    import time
    age_hours = (time.time() * 1000 - pair_created) / 3_600_000 if pair_created else 0

    t5 = txns.get("m5") or {}
    t1h = txns.get("h1") or {}
    t6h = txns.get("h6") or {}
    t24h = txns.get("h24") or {}

    buys_1h = float(t1h.get("buys") or 0)
    sells_1h = float(t1h.get("sells") or 0)
    buys_24h = float(t24h.get("buys") or 0)
    sells_24h = float(t24h.get("sells") or 0)

    mcap = float(pair.get("marketCap") or 0)
    liquidity_usd = float(liq.get("usd") or 0)

    return {
        "price_usd": float(pair.get("priceUsd") or 0),
        "price_native": float(pair.get("priceNative") or 0),
        "fdv": float(pair.get("fdv") or 0),
        "market_cap": mcap,
        "liquidity_usd": liquidity_usd,
        "liquidity_base": float(liq.get("base") or 0),
        "liquidity_quote": float(liq.get("quote") or 0),
        "volume_5m": float(vol.get("m5") or 0),
        "volume_1h": float(vol.get("h1") or 0),
        "volume_6h": float(vol.get("h6") or 0),
        "volume_24h": float(vol.get("h24") or 0),
        "txns_5m_buys": float(t5.get("buys") or 0),
        "txns_5m_sells": float(t5.get("sells") or 0),
        "txns_1h_buys": buys_1h,
        "txns_1h_sells": sells_1h,
        "txns_6h_buys": float(t6h.get("buys") or 0),
        "txns_6h_sells": float(t6h.get("sells") or 0),
        "txns_24h_buys": buys_24h,
        "txns_24h_sells": sells_24h,
        "price_change_5m": float(pc.get("m5") or 0),
        "price_change_1h": float(pc.get("h1") or 0),
        "price_change_6h": float(pc.get("h6") or 0),
        "price_change_24h": float(pc.get("h24") or 0),
        "pair_age_hours": age_hours,
        "has_website": 1.0 if websites else 0.0,
        "has_twitter": 1.0 if "twitter" in social_types else 0.0,
        "has_telegram": 1.0 if "telegram" in social_types else 0.0,
        "has_discord": 1.0 if "discord" in social_types else 0.0,
        "social_count": float(len(socials) + len(websites)),
        "mint_authority_exists": 0.0,  # filled from RPC if available
        "freeze_authority_exists": 0.0,
        "decimals": 0.0,
        "buy_sell_ratio_1h": buys_1h / sells_1h if sells_1h > 0 else (2.0 if buys_1h > 0 else 1.0),
        "buy_sell_ratio_24h": buys_24h / sells_24h if sells_24h > 0 else (2.0 if buys_24h > 0 else 1.0),
        "liquidity_to_mcap_ratio": liquidity_usd / mcap if mcap > 0 else 0.0,
        "volume_to_liquidity_ratio": float(vol.get("h24") or 0) / liquidity_usd if liquidity_usd > 0 else 0.0,
        "txns_total_24h": buys_24h + sells_24h,
    }


def _extract_features_from_schema(features: TokenFeatureSchema) -> dict[str, float]:
    """Map TokenFeatureSchema fields to the model's expected feature names."""
    buys_1h = float(features.trade_count_1h or 0) * 0.55
    sells_1h = float(features.trade_count_1h or 0) * 0.45
    buys_24h = float(features.trade_count_24h or 0) * 0.55
    sells_24h = float(features.trade_count_24h or 0) * 0.45
    liq = float(features.liquidity_usd_total or 0)
    mcap = float(features.market_cap_usd or 0)
    vol_24h = float(features.volume_24h_usd or 0)
    age_hours = (features.market_age_seconds or 0) / 3600.0

    return {
        "price_usd": 0.0,
        "price_native": 0.0,
        "fdv": float(features.fdv_usd or 0),
        "market_cap": mcap,
        "liquidity_usd": liq,
        "liquidity_base": 0.0,
        "liquidity_quote": 0.0,
        "volume_5m": 0.0,
        "volume_1h": float(features.volume_1h_usd or 0),
        "volume_6h": 0.0,
        "volume_24h": vol_24h,
        "txns_5m_buys": 0.0,
        "txns_5m_sells": 0.0,
        "txns_1h_buys": buys_1h,
        "txns_1h_sells": sells_1h,
        "txns_6h_buys": 0.0,
        "txns_6h_sells": 0.0,
        "txns_24h_buys": buys_24h,
        "txns_24h_sells": sells_24h,
        "price_change_5m": 0.0,
        "price_change_1h": float(features.price_change_1h_pct or 0),
        "price_change_6h": 0.0,
        "price_change_24h": float(features.price_change_24h_pct or 0),
        "pair_age_hours": age_hours,
        "has_website": 0.0,
        "has_twitter": 0.0,
        "has_telegram": 0.0,
        "has_discord": 0.0,
        "social_count": 0.0,
        "mint_authority_exists": 1.0 if features.mint_authority_enabled else 0.0,
        "freeze_authority_exists": 1.0 if features.freeze_authority_enabled else 0.0,
        "decimals": float(features.decimals),
        "buy_sell_ratio_1h": buys_1h / sells_1h if sells_1h > 0 else 1.0,
        "buy_sell_ratio_24h": buys_24h / sells_24h if sells_24h > 0 else 1.0,
        "liquidity_to_mcap_ratio": liq / mcap if mcap > 0 else 0.0,
        "volume_to_liquidity_ratio": vol_24h / liq if liq > 0 else 0.0,
        "txns_total_24h": buys_24h + sells_24h,
    }


class MLInferenceEngine:
    version = "ml_v1_heuristic"

    def __init__(self) -> None:
        self.uses_calibrated_output = False
        self._model: Any | None = None
        self._onnx_session: Any | None = None
        self._feature_columns: list[str] = []
        self._feature_medians: dict[str, float] = {}
        self._artifact_version: str | None = None
        self._load_artifact()

    def _load_artifact(self) -> None:
        models_dir = Path(__file__).resolve().parents[3] / "models"

        # Try ONNX model first (lightweight, no sklearn/xgboost needed)
        onnx_path = models_dir / "rugsignal_model.onnx"
        feature_cols_path = models_dir / "feature_cols.json"

        if onnx_path.exists() and feature_cols_path.exists():
            try:
                import onnxruntime as ort
                self._onnx_session = ort.InferenceSession(
                    str(onnx_path),
                    providers=["CPUExecutionProvider"],
                )
                with open(feature_cols_path) as f:
                    self._feature_columns = json.load(f)
                self._artifact_version = "rugsignal_xgb_onnx_v1"
                self.version = self._artifact_version
                self.uses_calibrated_output = True
                logger.info("Loaded ONNX ML model: %s (%d features)", onnx_path.name, len(self._feature_columns))
                return
            except Exception as exc:
                logger.warning("Failed to load ONNX model: %s", exc)

        # Fallback: try legacy joblib model
        artifact_env = os.getenv("SCORING_MODEL_ARTIFACT", "").strip()
        if artifact_env:
            artifact_path = Path(artifact_env)
        else:
            artifact_path = models_dir / "ml_v1.joblib"

        if not artifact_path.exists():
            return

        try:
            from joblib import load
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
            self._model = None
            self._feature_columns = []
            self._feature_medians = {}
            self._artifact_version = None
            self.uses_calibrated_output = False

    def _build_vector(self, feature_dict: dict[str, float]) -> np.ndarray:
        """Build feature vector in the order the model expects."""
        return np.array(
            [[feature_dict.get(col, 0.0) for col in self._feature_columns]],
            dtype=np.float32,
        )

    def predict_from_dexscreener(self, pair: dict) -> float:
        """Run ML prediction using DexScreener pair data directly."""
        if not self._onnx_session and not self._model:
            return -1.0  # no model available

        feature_dict = _extract_dexscreener_features(pair)
        vector = self._build_vector(feature_dict)

        if self._onnx_session:
            input_name = self._onnx_session.get_inputs()[0].name
            result = self._onnx_session.run(None, {input_name: vector})
            probas = result[1][0]  # [{class0: prob, class1: prob}]
            if isinstance(probas, dict):
                probability = float(probas.get(1, 0.0))
            else:
                probability = float(probas[1]) if len(probas) > 1 else float(probas[0])
            return max(0.0, min(1.0, round(probability, 4)))

        if self._model:
            probability = float(self._model.predict_proba(vector)[0][1])
            return max(0.0, min(1.0, round(probability, 4)))

        return -1.0

    def predict_probability(self, features: TokenFeatureSchema, rule_score: float) -> float:
        """Run ML prediction using TokenFeatureSchema (pipeline integration)."""
        if self._onnx_session:
            feature_dict = _extract_features_from_schema(features)
            vector = self._build_vector(feature_dict)
            input_name = self._onnx_session.get_inputs()[0].name
            result = self._onnx_session.run(None, {input_name: vector})
            probas = result[1][0]
            if isinstance(probas, dict):
                probability = float(probas.get(1, 0.0))
            else:
                probability = float(probas[1]) if len(probas) > 1 else float(probas[0])
            return max(0.0, min(1.0, round(probability, 4)))

        if self._model is not None and self._feature_columns:
            values = self._to_feature_dict(features, rule_score)
            vector = np.array(
                [[values.get(col, self._feature_medians.get(col, 0.0)) for col in self._feature_columns]],
                dtype=float,
            )
            probability = float(self._model.predict_proba(vector)[0][1])
            return max(0.0, min(1.0, round(probability, 4)))

        # Heuristic fallback
        x = (rule_score - 45.0) / 14.0
        x += 0.8 * features.dev_cluster_share
        x += 0.6 if features.insider_wallet_detected else 0.0
        x += 0.5 if features.honeypot_simulation_failed else 0.0
        x += 0.3 if features.mint_after_launch_detected else 0.0
        probability = _sigmoid(x)
        return max(0.0, min(1.0, round(probability, 4)))

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

    @property
    def has_model(self) -> bool:
        return self._onnx_session is not None or self._model is not None


# ─── Singleton ──────────────────────────────────────────────────────────────

_ml_engine_instance: MLInferenceEngine | None = None


def get_ml_engine() -> MLInferenceEngine:
    """Return a shared MLInferenceEngine singleton to avoid duplicate ONNX sessions."""
    global _ml_engine_instance
    if _ml_engine_instance is None:
        _ml_engine_instance = MLInferenceEngine()
    return _ml_engine_instance
