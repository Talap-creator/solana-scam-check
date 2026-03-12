# RugSignal v2 Implementation Spec

## Product architecture
- Backend: FastAPI
- Database: PostgreSQL
- Cache: Redis
- Data sources: Helius RPC, Solana RPC, Dexscreener API
- Services: Auth Service, Scan Service, Feature Extractor, Risk Engine, Admin API
- Pipeline: User -> Frontend -> API -> Scan Service -> Feature Engine -> Risk Engine -> Report -> UI

## Auth and users
### Auth methods
- Email/password
- JWT access tokens

### Core tables
- `users`: `id`, `email`, `password_hash`, `plan`, `created_at`, `last_login`, `role`
- `token_scans`: `id`, `user_id`, `token_address`, `chain`, `scan_time`, `risk_score`, `confidence`
- `token_stats`: `token_address`, `scan_count`, `last_scanned`

### Plans
- `free`
- `pro`
- `enterprise`

## Admin panel
- Admin-only access
- Sections: Dashboard, Users, Scans, Tokens, Overrides

### Dashboard metrics
- Users count
- Daily scans
- Popular tokens
- Average risk score

### Overrides
- Whitelist token
- Blacklist token

## Risk engine v2
### Layered blocks
- Technical risk
- Distribution risk
- Market / execution risk
- Behaviour risk
- Market maturity

### Product interpretation
- `rug_probability` is the main product verdict
- `technical_risk` measures administrative and contract control
- `market_execution_risk` measures liquidity depth and exit execution risk
- `market_maturity` is a positive reducer, not a rescue patch after an inflated score

### Final probability design
- rule aggregate uses technical, distribution, liquidity rug component, behaviour and data quality
- low liquidity alone should not be treated as direct rug probability
- market maturity lowers final rug probability inside the model, not after the fact

### Token factors
- Technical risk: mint authority, freeze authority, upgrade authority
- Distribution risk: top10 holders, top1 holder, gini supply
- Market / execution risk: liquidity USD, pool depth, DEX coverage, LP structure
- Behaviour risk: dev clustering, insider selling, suspicious wallet patterns
- Market maturity: token age, volume, market cap, known project and listing footprint

## UX v2
### Landing navigation
- Logo
- Scan
- Features
- Pricing
- Roadmap
- Team
- Login

### Report flow
- User enters token and starts scan
- System shows staged loading
- Report appears with partial data for anonymous users
- Full report unlocked after registration/login

### Blurred report paywall
- Keep headline metrics visible
- Blur advanced blocks:
  - Holder graph
  - Dev wallet detection
  - Full timeline details
- CTA modal: "Unlock full report"

### Report sections
- Main summary
- Key findings
- Risk dimensions
- Timeline
- Top findings

## Pricing
- Free: $0, 5 scans/day, basic token report
- Pro: $29/month, 200 scans/day, wallet checker + advanced report
- Professional: $79/month, 1000 scans/day, project checker + API
- Enterprise: custom, unlimited scans + datasets + alerts

## Roadmap
- Phase 1: Token Rug Checker
- Phase 2: Wallet Risk Checker
- Phase 3: Project Risk Scanner
- Phase 4: Rug Dataset
- Phase 5: AI Trading Agents

## Team block
- Founder
- Blockchain engineer
- ML engineer
- Frontend engineer

## Footer block
- Links: Features, Pricing, Docs, API
- Resources: Blog, Research, Datasets
- Company: Team, Roadmap, Contact

## Growth mechanics
- Most scanned tokens today
- Trending risky tokens
- Share report
- Alerts subscription

## ML layer (future)
- Dataset: rug tokens + safe tokens
- Features: liquidity, holders, wallet graph
- Model: LightGBM
- Output: `rug_probability`

## Execution roadmap
### Milestone A: UX + conversion
- Landing sections complete
- Pricing + roadmap + team + footer complete
- Blurred report paywall

### Milestone B: Auth + persistence
- User registration/login
- JWT auth middleware
- Scan tracking in PostgreSQL

### Milestone C: Admin
- Admin dashboard metrics
- User/scans/tokens management
- Overrides (whitelist/blacklist)

### Milestone D: Scoring v2 rollout
- Layered scoring implementation
- Calibration dataset
- Confidence model update

### Milestone E: Realtime and alerts
- Risk alerts feed
- Liquidity removal alerts
- Watchlist notifications
