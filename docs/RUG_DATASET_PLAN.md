# Rug Dataset Plan

## Target cohorts
- `known_rug`
- `honeypot`
- `known_legit`
- `mature_project`
- `low_liquidity_legit`

## Minimum labels per row
- `token_address`
- `label`
- `cohort`
- `score`
- `rug_probability`

## Behaviour labels
- `developer_cluster_label`
- `early_buyer_cluster_label`
- `insider_selling_label`
- `liquidity_management_label`

## Collection priorities
1. Confirmed rugs with public postmortem evidence
2. Honeypots with reproducible sell-failure evidence
3. Legit low-liquidity tokens to reduce false positives
4. Mature projects with known admin permissions still enabled
5. Blue-chip or known-project wrapped assets on Solana
6. Suspicious live-like behaviour patterns for regression, including:
   - developer-cluster dominant cases
   - early-buyer plus liquidity-manipulation cases
   - coordinated developer/insider exit cases

## Uses
- offline scoring evaluation
- false-positive review
- threshold calibration
- future supervised behaviour model training

## Starter files
- Template with example values: [scoring_dataset_template.csv](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/docs/scoring_dataset_template.csv)
- Empty seed for manual collection: [rug_dataset_seed.csv](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/docs/rug_dataset_seed.csv)
- First real seed cases: [rug_dataset_seed_real.csv](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/docs/rug_dataset_seed_real.csv)
- Stub builder script: [build_dataset_stub.py](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/backend/tools/build_dataset_stub.py)
- Behaviour API/examples: [BEHAVIOUR_API_SPEC.md](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/docs/BEHAVIOUR_API_SPEC.md)
- Behaviour regression fixtures: [behaviour_cases.json](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/backend/tests/fixtures/behaviour_cases.json)

Suggested workflow:
1. Fill `rug_dataset_seed.csv` with real token addresses and manual notes
2. Copy validated rows into the main labeled dataset CSV
3. Run `python tools/evaluate_scoring.py --csv ../docs/scoring_dataset_template.csv` or your working dataset path
4. Use `python tools/build_dataset_stub.py --out ../docs/dataset_stub.csv --source both --limit 50` to generate a fresh unlabeled stub from stored scan data
5. Reuse `backend/tests/fixtures/behaviour_cases.json` as canonical behaviour-regression cases when changing module thresholds or evidence logic
