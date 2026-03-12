# Behaviour API Spec

## Overview

Behaviour Intelligence Layer v2 is exposed in:

- `POST /v2/scan/token`
- `GET /v2/scan/token/{address}/behaviour`

The main scan response includes a structured `behaviour_analysis` object.
The dedicated behaviour endpoint returns the same object directly.

## Main structure

```json
{
  "summary": "No strong scam-specific behaviour signals were found.",
  "overall_behaviour_risk": "low",
  "confidence": "medium",
  "score": 18,
  "modules": {
    "developer_cluster": {
      "status": "clear",
      "severity": "low",
      "score": 8.0,
      "summary": "No clear developer cluster detected.",
      "details": [
        "No strong multi-wallet control pattern was inferred from current holder and funding overlap data."
      ],
      "evidence": {
        "shared_funding_ratio": 0.0,
        "holder_activity_time_similarity_score": 0.0
      },
      "confidence": "limited"
    }
  },
  "confidence_breakdown": {
    "holder_coverage": "partial",
    "transaction_coverage": "partial",
    "funding_trace_depth": "moderate",
    "liquidity_data": "full"
  },
  "version": "behaviour_v2"
}
```

## Module fields

Each module returns:

- `status`: `clear | watch | flagged`
- `severity`: `low | medium | high`
- `score`: `0..100`
- `summary`
- `details[]`
- `evidence{}`
- `confidence`: `limited | medium | high`

## Supported modules

- `developer_cluster`
- `early_buyers`
- `insider_selling`
- `liquidity_management`

## Debug mode

Use:

```text
GET /v2/scan/token/{address}/behaviour?debug=true
```

When `debug=true`, the response includes:

```json
{
  "debug": {
    "modules_ran": [
      "developer_cluster",
      "early_buyers",
      "insider_selling",
      "liquidity_management"
    ],
    "triggered_rules": {
      "developer_cluster_flagged": false,
      "early_buyers_flagged": false,
      "insider_selling_flagged": false,
      "liquidity_management_flagged": false,
      "flagged_pair_multiplier_applied": false,
      "insider_liquidity_correlation": false
    },
    "coverage": {
      "tracked_owner_wallets": 4,
      "liquidity_data_available": true,
      "market_age_days": 210
    },
    "cache": {
      "hits": 12,
      "misses": 5
    },
    "source_coverage": {
      "largest_accounts_available": true,
      "holder_scan_complete": true,
      "dex_pair_available": true,
      "market_profile_available": true
    }
  }
}
```

When `debug=false` or omitted, the `debug` field is `null`.

## Regression fixtures

Behaviour regression fixture cases are stored in:

- [behaviour_cases.json](/c:/Users/Starlinecomp/Documents/Github%20Projects/rugsignal/backend/tests/fixtures/behaviour_cases.json)

Current canonical cases:

1. `mature_legit_clear`
2. `low_liquidity_legit_watch`
3. `sol_live_like_benign_liquidity`
4. `usdc_live_like_benign_liquidity`
5. `bonk_live_like_benign_liquidity`
6. `link_live_like_benign_liquidity`
7. `developer_cluster_dominant_high`
8. `early_buyers_plus_liquidity_high`
9. `developer_and_insider_exit_critical`
10. `suspicious_fresh_flagged`

## Benign live-like examples

The following mature or known-legit tokens are treated as canonical benign calibration references for
behaviour narrative weighting. In these cases `liquidity_management` may remain `watch`, but the
overall behaviour verdict stays `low` and the summary remains non-alarmist.

### Expected benign summary

```text
Some liquidity-management irregularities were observed, but no broader suspicious wallet behaviour was detected.
```

### Reference outputs

```json
[
  {
    "token": "SOL",
    "rug_probability": 2,
    "behaviour_risk": 8,
    "market_maturity": 61,
    "overall_behaviour_risk": "low",
    "module_statuses": {
      "developer_cluster": "clear",
      "early_buyers": "clear",
      "insider_selling": "clear",
      "liquidity_management": "watch"
    }
  },
  {
    "token": "USDC",
    "rug_probability": 2,
    "behaviour_risk": 8,
    "market_maturity": 81,
    "overall_behaviour_risk": "low",
    "module_statuses": {
      "developer_cluster": "clear",
      "early_buyers": "clear",
      "insider_selling": "clear",
      "liquidity_management": "watch"
    }
  },
  {
    "token": "BONK",
    "rug_probability": 2,
    "behaviour_risk": 8,
    "market_maturity": 63,
    "overall_behaviour_risk": "low",
    "module_statuses": {
      "developer_cluster": "clear",
      "early_buyers": "clear",
      "insider_selling": "clear",
      "liquidity_management": "watch"
    }
  },
  {
    "token": "LINK",
    "rug_probability": 8,
    "behaviour_risk": 12,
    "market_maturity": 49,
    "overall_behaviour_risk": "low",
    "module_statuses": {
      "developer_cluster": "clear",
      "early_buyers": "clear",
      "insider_selling": "clear",
      "liquidity_management": "watch"
    }
  }
]
```

## Suspicious live-like examples

The following regression cases represent stronger behaviour-linked risk patterns that should materially
lift `behaviour_risk` and produce a firmer narrative.

### Reference suspicious patterns

```json
[
  {
    "case_id": "developer_cluster_dominant_high",
    "expected_overall_behaviour_risk": "critical",
    "expected_summary": "Coordinated wallet behaviour was detected and should be reviewed closely.",
    "expected_modules": {
      "developer_cluster": "flagged",
      "early_buyers": "clear",
      "insider_selling": "flagged",
      "liquidity_management": "watch"
    }
  },
  {
    "case_id": "early_buyers_plus_liquidity_high",
    "expected_summary": "Coordinated early-wallet activity was observed alongside liquidity-related anomalies.",
    "expected_modules": {
      "developer_cluster": "clear",
      "early_buyers": "flagged",
      "insider_selling": "clear",
      "liquidity_management": "flagged"
    }
  },
  {
    "case_id": "developer_and_insider_exit_critical",
    "expected_summary": "Multiple scam-linked behaviour signals were detected.",
    "expected_modules": {
      "developer_cluster": "flagged",
      "early_buyers": "clear",
      "insider_selling": "flagged",
      "liquidity_management": "flagged"
    }
  }
]
```
