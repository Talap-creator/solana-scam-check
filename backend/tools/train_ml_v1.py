from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train RugSignal ML baseline model artifact.")
    parser.add_argument("--csv", required=True, help="Path to labeled dataset CSV")
    parser.add_argument("--out-dir", default="models", help="Directory for model artifacts")
    parser.add_argument("--target", default="label", help="Target column name")
    parser.add_argument("--time-col", default="scanned_at", help="Time column for split")
    parser.add_argument("--model-version", default="ml_v1", help="Model version label")
    return parser.parse_args()


def build_model():
    try:
        from lightgbm import LGBMClassifier

        return LGBMClassifier(
            n_estimators=320,
            learning_rate=0.045,
            max_depth=-1,
            num_leaves=31,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            class_weight="balanced",
        ), "lightgbm"
    except Exception:
        return GradientBoostingClassifier(random_state=42), "sklearn_gbm_fallback"


def time_split(df: pd.DataFrame, time_col: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if time_col in df.columns:
        ordered = df.copy()
        ordered[time_col] = pd.to_datetime(ordered[time_col], utc=True, errors="coerce")
        ordered = ordered.sort_values(time_col, na_position="last")
        cut = int(len(ordered) * 0.8)
        return ordered.iloc[:cut].copy(), ordered.iloc[cut:].copy()
    cut = int(len(df) * 0.8)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def to_features(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    excluded = {"token_address", "token", "chain", target_col, "label", "scanned_at", "timestamp", "datetime"}
    working = df.copy()
    for column in working.columns:
        if working[column].dtype == bool:
            working[column] = working[column].astype(int)

    feature_cols = [col for col in working.columns if col not in excluded]
    X = working[feature_cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(working[target_col], errors="coerce").fillna(0).astype(int)
    return X, y, feature_cols


def precision_at_top_k(y_true: np.ndarray, y_prob: np.ndarray, k_ratio: float = 0.1) -> float:
    if len(y_true) == 0:
        return 0.0
    k = max(1, int(len(y_true) * k_ratio))
    idx = np.argsort(y_prob)[::-1][:k]
    return float(np.mean(y_true[idx]))


def evaluate(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
    y_true = y_true.astype(int)
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0,
        "pr_auc": float(average_precision_score(y_true, y_prob)),
        "brier": float(brier_score_loss(y_true, y_prob)),
        "precision_at_top10pct": precision_at_top_k(y_true, y_prob, 0.10),
        "recall_at_critical_0.70": float(np.sum((y_prob >= 0.70) & (y_true == 1)) / max(1, np.sum(y_true == 1))),
    }


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)
    if args.target not in df.columns:
        raise ValueError(f"target column '{args.target}' not found in dataset")

    train_df, valid_df = time_split(df, args.time_col)
    X_train, y_train, feature_cols = to_features(train_df, args.target)
    X_valid, y_valid, _ = to_features(valid_df, args.target)

    imputer = SimpleImputer(strategy="median")
    X_train_i = imputer.fit_transform(X_train)
    X_valid_i = imputer.transform(X_valid)

    base_model, backend_name = build_model()
    class_counts = y_train.value_counts().to_dict()
    min_class_count = min(class_counts.values()) if class_counts else 0
    small_dataset = len(y_train) < 30 or min_class_count < 3

    best_name = "none"
    best_metrics: dict[str, float] | None = None
    best_model = None
    is_calibrated = False

    if small_dataset:
        base_model.fit(X_train_i, y_train.values)
        prob = base_model.predict_proba(X_valid_i)[:, 1]
        best_metrics = evaluate(y_valid.values, prob)
        best_model = base_model
    else:
        calibrators = {
            "isotonic": CalibratedClassifierCV(base_model, method="isotonic", cv=3),
            "sigmoid": CalibratedClassifierCV(base_model, method="sigmoid", cv=3),
        }
        for name, calibrator in calibrators.items():
            calibrator.fit(X_train_i, y_train.values)
            prob = calibrator.predict_proba(X_valid_i)[:, 1]
            metrics = evaluate(y_valid.values, prob)
            if best_metrics is None or metrics["brier"] < best_metrics["brier"]:
                best_name = name
                best_metrics = metrics
                best_model = calibrator
                is_calibrated = True

    if best_model is None or best_metrics is None:
        raise RuntimeError("unable to train model")

    medians = dict(zip(feature_cols, imputer.statistics_, strict=False))
    artifact = {
        "model": best_model,
        "feature_columns": feature_cols,
        "feature_medians": medians,
        "backend": backend_name,
        "calibration_method": best_name,
        "is_calibrated": is_calibrated,
        "model_version": args.model_version,
    }

    model_path = out_dir / f"{args.model_version}.joblib"
    metrics_path = out_dir / f"{args.model_version}.metrics.json"
    dump(artifact, model_path)
    metrics_path.write_text(json.dumps(best_metrics, indent=2), encoding="utf-8")

    print("Training complete")
    print(f"model: {model_path}")
    print(f"metrics: {metrics_path}")
    print(json.dumps(best_metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
