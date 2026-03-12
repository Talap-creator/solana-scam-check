from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Row:
    token_address: str
    label: int
    cohort: str
    score: int
    probability: float
    behaviour_labels: dict[str, int | None]


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def load_rows(path: Path) -> list[Row]:
    rows: list[Row] = []
    behaviour_columns = (
        "developer_cluster_label",
        "early_buyer_cluster_label",
        "insider_selling_label",
        "liquidity_management_label",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"token_address", "label", "score"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")

        for line in reader:
            token = str(line["token_address"]).strip()
            label = int(str(line["label"]).strip())
            cohort = str(line.get("cohort", "")).strip() or "unclassified"
            score = int(float(str(line["score"]).strip()))
            probability_raw = str(line.get("rug_probability", "")).strip()
            probability = float(probability_raw) if probability_raw else score / 100.0
            behaviour_labels: dict[str, int | None] = {}
            for column in behaviour_columns:
                raw = str(line.get(column, "")).strip()
                behaviour_labels[column] = int(raw) if raw in {"0", "1"} else None

            if label not in (0, 1):
                raise ValueError(f"label must be 0 or 1, got {label} for token {token}")

            rows.append(
                Row(
                    token_address=token,
                    label=label,
                    cohort=cohort,
                    score=max(0, min(100, score)),
                    probability=clamp01(probability),
                    behaviour_labels=behaviour_labels,
                )
            )

    if not rows:
        raise ValueError("CSV has no rows")

    return rows


def confusion(rows: list[Row], threshold: float) -> tuple[int, int, int, int]:
    tp = fp = tn = fn = 0
    for row in rows:
        pred = 1 if row.probability >= threshold else 0
        if pred == 1 and row.label == 1:
            tp += 1
        elif pred == 1 and row.label == 0:
            fp += 1
        elif pred == 0 and row.label == 0:
            tn += 1
        else:
            fn += 1
    return tp, fp, tn, fn


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def roc_auc(rows: list[Row]) -> float:
    positives = [row for row in rows if row.label == 1]
    negatives = [row for row in rows if row.label == 0]
    if not positives or not negatives:
        return 0.0

    wins = 0.0
    total = len(positives) * len(negatives)
    for pos in positives:
        for neg in negatives:
            if pos.probability > neg.probability:
                wins += 1.0
            elif pos.probability == neg.probability:
                wins += 0.5

    return wins / total


def brier_score(rows: list[Row]) -> float:
    return sum((row.probability - row.label) ** 2 for row in rows) / len(rows)


def calibration_bins(rows: list[Row], bins: int = 10) -> list[tuple[int, float, float, int]]:
    grouped: list[list[Row]] = [[] for _ in range(bins)]
    for row in rows:
        index = min(bins - 1, int(row.probability * bins))
        grouped[index].append(row)

    result: list[tuple[int, float, float, int]] = []
    for index, bucket in enumerate(grouped):
        if not bucket:
            result.append((index, 0.0, 0.0, 0))
            continue
        avg_pred = sum(item.probability for item in bucket) / len(bucket)
        avg_actual = sum(item.label for item in bucket) / len(bucket)
        result.append((index, avg_pred, avg_actual, len(bucket)))
    return result


def cohort_counts(rows: list[Row]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.cohort] = counts.get(row.cohort, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def behaviour_label_coverage(rows: list[Row]) -> list[tuple[str, int, int]]:
    columns = (
        "developer_cluster_label",
        "early_buyer_cluster_label",
        "insider_selling_label",
        "liquidity_management_label",
    )
    coverage: list[tuple[str, int, int]] = []
    for column in columns:
        present = sum(1 for row in rows if row.behaviour_labels.get(column) is not None)
        positive = sum(1 for row in rows if row.behaviour_labels.get(column) == 1)
        coverage.append((column, present, positive))
    return coverage


def print_report(rows: list[Row]) -> None:
    total = len(rows)
    positive = sum(item.label for item in rows)
    negative = total - positive
    prevalence = safe_div(positive, total)

    print("=== Scoring Evaluation Report ===")
    print(f"samples: {total}")
    print(f"positives (rug): {positive}")
    print(f"negatives (safe): {negative}")
    print(f"prevalence: {prevalence:.4f}")
    print("")
    print("cohort distribution")
    for cohort, count in cohort_counts(rows):
        print(f"- {cohort}: {count}")
    print(f"roc_auc: {roc_auc(rows):.4f}")
    print(f"brier_score: {brier_score(rows):.4f}")
    print("")
    print("threshold metrics")
    for threshold in (0.50, 0.70, 0.80, 0.90):
        tp, fp, tn, fn = confusion(rows, threshold)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        specificity = safe_div(tn, tn + fp)
        f1 = safe_div(2 * precision * recall, precision + recall)
        accuracy = safe_div(tp + tn, total)
        print(
            f"t={threshold:.2f} | acc={accuracy:.4f} precision={precision:.4f} "
            f"recall={recall:.4f} specificity={specificity:.4f} f1={f1:.4f} "
            f"(tp={tp} fp={fp} tn={tn} fn={fn})"
        )

    print("")
    print("calibration bins (10)")
    print("bin | avg_pred | avg_actual | count")
    for index, avg_pred, avg_actual, count in calibration_bins(rows, bins=10):
        print(f"{index:>3} | {avg_pred:>8.4f} | {avg_actual:>10.4f} | {count}")
    print("")
    print("behaviour-label coverage")
    for column, present, positive in behaviour_label_coverage(rows):
        print(f"- {column}: present={present} positive={positive}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RugSignal scoring using labeled CSV data.")
    parser.add_argument(
        "--csv",
        required=True,
        help="Path to labeled dataset CSV with columns: token_address,label,score[,cohort,rug_probability,behaviour labels]",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = load_rows(Path(args.csv))
    print_report(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
