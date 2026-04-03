# RugSignal - AI Oracle for Solana Token Risk

**Autonomous AI agent that scores Solana tokens for rug pull risk and enforces protection on-chain via smart contracts.**

> National Solana Hackathon by Decentrathon 2026 | Case 2: AI + Blockchain

---

## The Problem

Rug pulls on Solana steal billions. In 2024-2025 alone, $6B+ was lost across major scams (LIBRA, MELANIA, HAWK Tuah, ENRON, M3M3). 98.6% of all Pump.fun tokens are rugs (Solidus Labs). Existing tools only warn - they don't prevent.

## The Solution

RugSignal combines 3-layer AI analysis with on-chain enforcement:

1. **Rule Engine** - 56 on-chain features across 6 risk categories
2. **ML Model** - XGBoost trained on 2350 tokens (ONNX, 8MB RAM)
3. **AI Agent** - GPT-4o-mini reasoning + natural language explanation
4. **Score published on-chain** to Solana PDA via Oracle program
5. **GuardedVault smart contract** reads AI score and **blocks risky swaps automatically**

```
Token Added -> AI Analyzes -> Score On-Chain -> Swap Attempt -> Contract Reads Score -> BLOCK or ALLOW
```

---

## Backtest Results

Tested against the top 10 rug pulls of 2024-2025:

| Token | Loss | Score | Result |
|-------|------|-------|--------|
| $LIBRA (Milei/Argentina) | $251M from 50K investors | 85/100 CRITICAL | CAUGHT |
| $MELANIA (First Lady) | $30M+ extracted | 95/100 CRITICAL | CAUGHT |
| HAWK Tuah (Hailey Welch) | $490M wiped in 20min | 87/100 CRITICAL | CAUGHT |
| $TRUMP (Presidential) | 87% crash from $7B mcap | 87/100 CRITICAL | CAUGHT |
| $ENRON (Satire Rug) | $700M mcap, 92% insider | 82/100 CRITICAL | CAUGHT |
| M3M3 (Meteora Scandal) | $69M via 150+ wallets | 82/100 CRITICAL | CAUGHT |
| VINE (Vine App) | $500M -> $16M | 70/100 HIGH | CAUGHT |
| SHARPEI ($SHAR) | Crashed 96% in 2 SECONDS | 62/100 HIGH | CAUGHT |
| Gen Z Quant | Rugged live on stream | 100/100 CRITICAL | CAUGHT |
| HNUT (Peanut) | 99%+ collapse | 82/100 CRITICAL | CAUGHT |

**Pre-rug detection: 10/10 (100%)** - combined Rule Engine + ML Model scoring

**Metrics breakdown:**

| Layer | Accuracy | What it measures |
|-------|----------|------------------|
| Rule Engine + ML (backtest) | 99.9% recall on 2350 tokens | Post-rug detection on labeled dataset |
| Rule Engine (pre-rug signals) | 10/10 high-profile cases | Pre-rug pattern detection (vol/liq ratio, age, imbalance) |
| ML Model alone (XGBoost) | 85.7% accuracy, 0.899 AUC | Binary classification on 37 DexScreener features |
| False alarm rate | 0.2% (3/1916 legit tokens) | How often legit tokens get flagged |

Run backtest: `python backend/tools/backtest.py`

---

## Architecture

```
+------------------+     +-------------------+     +----------------------+
|   Frontend       |     |   Backend         |     |   Solana Devnet      |
|   Next.js 16     |---->|   FastAPI          |---->|   Anchor Program     |
|   Phantom Wallet |     |   Rule Engine     |     |   PDA: Oracle        |
|   Vault Panel    |     |   ML Model (ONNX) |     |   PDA: Scores        |
|   SSE Streaming  |<----|   AI Agent (GPT)  |     |   PDA: Vaults        |
+------------------+     +-------------------+     +----------------------+
```

### Smart Contract (Anchor/Rust)

**Program ID:** `HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS`

| Instruction | Description |
|---|---|
| `initialize_oracle` | Set publisher authority |
| `publish_score` | AI agent writes risk score to PDA |
| `create_vault` | User creates vault with risk threshold |
| `deposit` | User deposits SOL into vault |
| **`guarded_swap`** | **Checks AI score vs threshold - rejects if risky** |
| `emergency_exit` | Auto-withdraw if score >= 75 (critical) |
| `update_threshold` | Adjust vault risk tolerance |

Key enforcement logic:
```rust
// guarded_swap: the core innovation
if token_risk_score.score > vault.risk_threshold {
    return Err(ErrorCode::RiskTooHigh.into());
    // Swap blocked. Funds safe.
}
```

PDA derivations:
```
Oracle Config:  seeds = ["oracle"]
Token Score:    seeds = ["score", token_mint]
User Vault:     seeds = ["vault", owner]
Vault SOL:      seeds = ["vault_sol", owner]
```

### Scoring Pipeline

```
Token Address
     |
[1. Rule Engine] 56 on-chain features, 6 categories:
     - Technical Risk (30%): mint/freeze authority, honeypot, transfer tax
     - Distribution Risk (25%): holder concentration, Gini coefficient
     - Market Risk (25%): liquidity depth, volume, DEX coverage
     - Behaviour Risk (20%): dev clusters, insider selling, early buyers
     -> rule_score (0-100)
     |
[2. ML Model] XGBoost (ONNX) on 37 DexScreener features
     -> ml_probability (0.0-1.0)
     |
[3. Blend] final_score = 0.6 * rule_score + 0.4 * (ml_probability * 100)
     -> numeric score (0-100)
     |
[4. AI Agent] GPT-4o-mini receives features + ml_probability
     -> adds natural language reasoning (text explanation)
     -> does NOT change the numeric score, only adds context
     |
[5. Publish] score + risk_level + reasoning -> Solana PDA on-chain
```

**How the blend works:**
- Rule Engine provides the base score from on-chain analysis
- ML Model adjusts it with DexScreener market data patterns
- GPT-4o-mini explains WHY the score is what it is (advisory only, no score override)
- Final numeric score is deterministic: `0.6 * rules + 0.4 * ML`

### Oracle Agent Loop

```
Every 90 seconds:
  1. Query monitored tokens from DB
  2. Fetch DexScreener data (free API)
  3. Run ML model -> rug probability
  4. Call GPT-4o-mini for reasoning
  5. Blend: 60% Rule Engine + 40% ML (GPT adds reasoning only)
  6. Publish to Solana devnet (Anchor TX)
  7. Store TX signature in DB
  8. Frontend updates scores table
```

### ML Model

- **Type:** XGBoost classifier -> ONNX export
- **Size:** 407KB model, 8MB RAM (vs 300MB for sklearn)
- **Features:** 37 numeric (price, volume, liquidity, txns, socials, authorities)
- **Training data:** 2350 tokens (434 confirmed rugs + 1916 legit)
- **Top feature:** liquidity_usd (64.6% importance)
- **Metrics:** 85.7% accuracy, 0.899 ROC AUC

---

## Project Structure

```
rugsignal/
|-- programs/rugsignal_oracle/src/lib.rs   # Anchor smart contract (7 instructions)
|-- backend/
|   |-- app/
|   |   |-- main.py                        # FastAPI entry, startup, CORS
|   |   |-- config.py                      # 50+ config options
|   |   |-- models.py                      # 16 DB tables (SQLAlchemy)
|   |   |-- api/routes/
|   |   |   |-- oracle.py                  # Oracle endpoints + SSE streaming
|   |   |   |-- v2_scan.py                 # Token scan endpoint
|   |   |   |-- auth.py                    # JWT auth (register, login)
|   |   |   |-- admin.py                   # Admin panel
|   |   |   |-- feed.py                    # Live token feed
|   |   |   |-- billing.py                 # Helio payments
|   |   |   |-- watchlist.py               # User watchlist
|   |   |-- services/
|   |   |   |-- analyzer.py                # Main scoring engine (2000+ lines)
|   |   |   |-- oracle_agent.py            # Autonomous scoring loop
|   |   |   |-- ai_scorer.py               # GPT-4o-mini integration
|   |   |   |-- solana_publisher.py        # On-chain TX publisher
|   |   |   |-- dexscreener.py             # DexScreener API client
|   |   |   |-- solana_rpc.py              # Solana RPC (holders, metadata)
|   |   |   |-- repository.py              # Report generation
|   |   |-- scoring/
|   |   |   |-- pipeline.py                # Scoring pipeline (rule + ML blend)
|   |   |   |-- ml/inference.py            # ONNX inference engine
|   |   |   |-- behaviour/                 # 4 behaviour modules
|   |   |   |-- rules/engine_v2.py         # Rule engine
|   |   |   |-- feature_extractor/         # 56+ feature extraction
|   |-- models/
|   |   |-- rugsignal_model.onnx           # Production ML model (407KB)
|   |   |-- feature_cols.json              # 37 feature names
|   |   |-- results.json                   # Training metrics
|   |   |-- backtest_results.json          # Backtest output
|   |-- data/
|   |   |-- dexscreener_2k.csv             # 1916 legit tokens (45 features)
|   |   |-- rugged_tokens.csv              # 434 confirmed rugs (47 features)
|   |-- tools/
|   |   |-- backtest.py                    # Backtest vs top 10 rug pulls
|   |   |-- parse_dexscreener.py           # Token parser (DexScreener + RPC)
|   |   |-- parse_rugged_tokens.py         # Rug token parser
|-- frontend/
|   |-- src/app/
|   |   |-- page.tsx                       # Landing page
|   |   |-- oracle/page.tsx                # Oracle dashboard
|   |   |-- dashboard/page.tsx             # User dashboard
|   |   |-- analysis/page.tsx              # Deep analysis
|   |-- src/components/oracle/
|   |   |-- vault-panel.tsx                # GuardedVault UI
|   |   |-- agent-chat.tsx                 # AI agent SSE chat
|   |   |-- oracle-scores-table.tsx        # On-chain scores
|   |   |-- oracle-history-table.tsx       # Publish history
|   |   |-- wallet-provider.tsx            # Solana wallet adapter
|-- docker-compose.yml                     # postgres + backend + frontend
```

---

## API Endpoints

### Oracle

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/oracle/status` | Agent running status |
| GET | `/api/v1/oracle/scores` | All monitored token scores |
| GET | `/api/v1/oracle/scores/{address}` | Single token score |
| POST | `/api/v1/oracle/monitor` | Add token to monitoring |
| DELETE | `/api/v1/oracle/monitor/{address}` | Remove token |
| POST | `/api/v1/oracle/agent/start` | Start autonomous agent |
| POST | `/api/v1/oracle/agent/stop` | Stop agent |
| POST | `/api/v1/oracle/agent/analyze` | Stream AI analysis (SSE) |
| GET | `/api/v1/oracle/history` | Publish event history |

### Token Scanning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/v2/scan/token` | Full token risk scan |
| GET | `/api/v1/feed/launches` | New token launch feed |
| GET | `/api/v1/feed/developers` | Developer operator profiles |

### Auth & User

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login (JWT) |
| GET | `/api/v1/auth/me` | User profile |
| GET | `/api/v1/auth/usage` | Daily scan usage |
| GET/POST/DELETE | `/api/v1/auth/watchlist` | Watchlist |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/dashboard` | System metrics |
| GET | `/api/v1/admin/users` | User management |
| GET/POST/DELETE | `/api/v1/admin/overrides` | Token verdict overrides |

---

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up
# postgres:16 -> backend:8000 -> frontend:3000
```

### Environment Variables

**Backend:**
```
DATABASE_URL=sqlite:///./rugsignal.db
JWT_SECRET_KEY=your-secret-key-minimum-60-characters-long
OPENAI_API_KEY=sk-...
ORACLE_PUBLISHER_KEYPAIR=[1,2,3...]
ORACLE_PROGRAM_ID=HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS
ORACLE_RPC_URL=https://api.devnet.solana.com
HELIUS_API_KEY=...
```

**Frontend:**
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Data & Training

```bash
# Parse live tokens from DexScreener
python backend/tools/parse_dexscreener.py --count 2000

# Parse confirmed rugged tokens
python backend/tools/parse_rugged_tokens.py --count 500

# Run backtest
python backend/tools/backtest.py
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.12, SQLAlchemy, Uvicorn |
| ML Model | XGBoost -> ONNX Runtime (8MB RAM) |
| AI | OpenAI GPT-4o-mini |
| Blockchain | Solana Devnet, Anchor 0.30.1, solders |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Wallet | Phantom, Solflare (Solana Wallet Adapter) |
| Data | DexScreener API (free), Solana RPC |
| Deploy | Docker, Render (backend), Vercel (frontend) |
| Payments | Helio (Solana-native) |

---

## Demo Flow

1. Connect Phantom wallet (Solana Devnet)
2. Add token address to Oracle Monitor
3. AI agent scores it automatically (every 90s)
4. Score appears in ON-CHAIN SCORES table with Solana Explorer link
5. Create GuardedVault with risk threshold (e.g., 50)
6. Deposit devnet SOL
7. **Simulate Swap** - contract checks score:
   - Score <= threshold -> **SWAP ALLOWED** (green)
   - Score > threshold -> **BLOCKED by GuardedVault** (red)
8. Change threshold to see different outcomes

---

## Key Innovation

**RugSignal is the first system that moves AI risk scores from off-chain advisory to on-chain enforcement.**

Traditional: "This token looks risky" (user ignores, buys anyway, loses money)

RugSignal: AI score lives in Solana PDA -> GuardedVault reads it -> **physically prevents the swap**

---

## Roadmap

| Phase | Timeline | Milestone |
|-------|----------|-----------|
| **v1 (current)** | Q2 2026 | Devnet oracle, 3-layer scoring, GuardedVault, backtest proof |
| **v2 - Mainnet** | Q3 2026 | Deploy oracle program to Solana mainnet, real SOL vaults |
| **v3 - Public API** | Q3 2026 | REST API for third-party integrations (wallets, DEXes, bots) |
| **v4 - DEX Integration** | Q4 2026 | Jupiter/Raydium plugin: auto-check before swap in real DEX UI |
| **v5 - Decentralization** | Q1 2027 | Multi-publisher oracle (staked validators score tokens independently) |
| **v6 - Cross-chain** | Q2 2027 | Expand to EVM chains (Base, Ethereum memecoins) |

**API for third parties (v3):**
- Wallet providers: check token risk before user buys
- DEX aggregators: flag risky tokens in swap UI
- Telegram/Discord bots: instant risk check via API
- DeFi protocols: on-chain score lookup for lending/collateral decisions

**Decentralized oracle (v5):**
- Multiple independent publishers stake SOL to participate
- Consensus mechanism: median score from N publishers
- Slashing for malicious/inaccurate scores
- Fully trustless: no single point of failure

---

## Hackathon Criteria

| Criteria | Weight | How We Address It |
|----------|--------|-------------------|
| Product & Idea | 20 | Real problem: $6B+ lost to rug pulls in 2024-2025 |
| Technical Implementation | 25 | 3-layer scoring (rules + ML + AI), ONNX, Anchor |
| Use of Solana | 15 | On-chain oracle PDA, GuardedVault enforcement |
| Innovation | 15 | First AI oracle with on-chain swap enforcement |
| UX | 10 | Mobile-optimized, real-time SSE, Explorer links |
| Demo | 10 | Backtest: 10/10 rug pulls caught, live devnet TX |
| Completeness | 5 | Full stack: frontend + backend + contract + ML + data |

---

## Live

- **Website:** https://solanatrust.tech
- **Oracle:** https://solanatrust.tech/oracle
- **Program:** [Explorer](https://explorer.solana.com/address/HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS?cluster=devnet)

## Team

**SolanaTrust** - Kazakhstan

| Name | Role |
|------|------|
| [**Kenzhebayev Talap**](https://www.linkedin.com/in/talap-kenzhebaev-product-manager) | Founder & Lead Developer - architecture, Solana smart contracts, ML pipeline, backend, frontend |

Built for National Solana Hackathon by Decentrathon 2026.

## License

MIT
