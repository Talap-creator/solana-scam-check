# Behaviour Layer Roadmap

## Goal
Strengthen rug detection by moving behaviour intelligence from a supporting heuristic into a first-class layer.

## Core modules
- Developer wallet cluster detection
- Early buyer clustering
- Insider selling detection
- Liquidity behaviour analysis
- Rug dataset and calibration loop

## Detection ideas
### Developer wallet cluster detection
- Funding source overlap
- Shared transaction timing
- Repeated interaction patterns
- Clustered liquidity interactions

Outputs:
- `developer_wallet_cluster_detected`
- `developer_cluster_wallet_count`
- `developer_cluster_supply_control_pct`

### Early buyer clustering
- Share of supply bought in first blocks
- Buyer graph clustering
- Shared funding source
- Same-time wallet activation

Outputs:
- `early_buyer_cluster_detected`
- `early_buyer_cluster_supply_pct`
- `early_buyer_cluster_confidence`

### Insider selling detection
- Large wallets selling before liquidity collapse
- Wallets linked to dev funding source
- Coordinated exits after distribution events

Outputs:
- `insider_exit_pattern_detected`
- `insider_exit_confidence`

### Liquidity behaviour analysis
- LP holder concentration
- LP burn / lock status
- Rapid liquidity withdrawals
- Liquidity volatility around selling events

Outputs:
- `lp_holder_concentration`
- `lp_burn_status`
- `liquidity_volatility_score`
- `liquidity_removal_pattern_detected`

## Dataset tracks
Collect labeled examples for:
- known rugs
- honeypots
- legit tokens
- mature projects

Use cases:
- ML training
- threshold calibration
- regression tests
- false-positive review

## Current benign calibration references

The current regression/calibration baseline for non-alarmist behaviour summaries includes:

- `SOL`
- `USDC`
- `BONK`
- `LINK`

Expected pattern for these cases:

- `developer_cluster = clear`
- `early_buyers = clear`
- `insider_selling = clear`
- `liquidity_management = watch`
- `overall_behaviour_risk = low`
- summary remains contextual rather than scam-leaning
