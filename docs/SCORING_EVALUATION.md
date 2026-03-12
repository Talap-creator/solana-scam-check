# Scoring Evaluation

Use this to measure how well current rule-based scoring matches labeled reality.

## Dataset format

CSV columns:

- `token_address` (string)
- `label` (`1` = rug, `0` = safe)
- `cohort` (recommended: `known_rug`, `honeypot`, `known_legit`, `mature_project`, `low_liquidity_legit`)
- `score` (`0..100`, current RugSignal score)
- `rug_probability` (optional, `0..1`; if omitted then `score/100` is used)
- optional behaviour labels:
  - `developer_cluster_label`
  - `early_buyer_cluster_label`
  - `insider_selling_label`
  - `liquidity_management_label`
- optional cohort flags:
  - `known_rug`
  - `known_honeypot`
  - `known_legit`
  - `mature_project`
- `notes` for manual review context

Template:

- [scoring_dataset_template.csv](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/docs/scoring_dataset_template.csv)

## Run

```powershell
cd backend
python tools/evaluate_scoring.py --csv ../docs/scoring_dataset_template.csv
```

## Output metrics

- dataset size and class prevalence
- cohort distribution
- ROC AUC
- Brier score
- threshold metrics (`0.50`, `0.70`, `0.80`, `0.90`):
  - accuracy
  - precision
  - recall
  - specificity
  - F1
- calibration bins (predicted vs actual rug rate)
- optional behaviour-label coverage

## Next step for better accuracy

Collect a larger labeled set and recalibrate thresholds/weights from the metrics report.

Recommended minimum dataset splits:

- `known_rugs`
- `honeypots`
- `low_liquidity_legit`
- `mature_projects`
- `known_legit`
