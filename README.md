<p align="center">
  <img src="https://img.shields.io/badge/Solana-Devnet-blueviolet?logo=solana" alt="Solana Devnet"/>
  <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build"/>
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"/>
  <img src="https://img.shields.io/badge/hackathon-Decentrathon%205.0-orange" alt="Decentrathon"/>
  <img src="https://img.shields.io/badge/Colosseum-Frontier-purple" alt="Colosseum Frontier"/>
</p>

# RugSignal — AI Oracle with On-Chain Enforcement for Solana

**AI agent that scores Solana tokens for rug pull risk and physically blocks risky swaps via smart contract. Not just a warning — an autonomous on-chain enforcer.**

> Decentrathon 5.0 — National Solana Hackathon 2026 | Colosseum Frontier

---

## Problem

Rug pulls on Solana steal billions. **$6B+ lost** in 2024-2025 (LIBRA, MELANIA, HAWK Tuah, TRUMP, ENRON). **98.6%** of Pump.fun tokens are rugs (Solidus Labs).

Every existing tool does the same thing: **warn**. User ignores warning, buys anyway, loses money.

## Solution

RugSignal is the first system that moves from **off-chain advisory** to **on-chain enforcement**:

```
Token Added → AI Scores → Score Published to Solana PDA → Swap Attempt → Smart Contract Reads Score → BLOCK or ALLOW
```

1. **Rule Engine** — 56 on-chain features, 6 risk categories
2. **ML Model** — XGBoost (ONNX, 407KB, 8MB RAM), trained on 2350 tokens
3. **AI Agent** — GPT-4o-mini reasoning + natural language explanation
4. **Oracle** — Score published to Solana PDA on-chain
5. **GuardedVault** — Smart contract reads AI score and **blocks risky swaps automatically**

```rust
// The core innovation: on-chain enforcement
if token_risk_score.score > vault.risk_threshold {
    return Err(ErrorCode::RiskTooHigh.into());
    // Swap blocked. Funds safe.
}
```

## Why Solana?

- **Speed**: 400ms finality — oracle scores update in real-time, before the rug happens
- **Cost**: $0.0001 per TX — publishing scores on-chain is economically viable (impossible on Ethereum at $5-50/TX)
- **PDA architecture**: Program Derived Addresses provide trustless, permissionless score storage that any protocol can read
- **Composability**: GuardedVault is a Solana program — any DEX, wallet, or DeFi protocol can integrate it as a CPI call
- **Ecosystem need**: Solana has the highest memecoin/rug activity — this is where the problem lives

---

## Demo

| Step | What happens |
|------|-------------|
| 1 | Connect Phantom wallet (devnet) |
| 2 | Add token address to Oracle |
| 3 | AI agent auto-scores every 90s |
| 4 | Score appears on-chain with [Solana Explorer](https://explorer.solana.com/address/HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS?cluster=devnet) link |
| 5 | Create GuardedVault, set risk threshold |
| 6 | Deposit devnet SOL |
| 7 | **Simulate Swap** → contract checks score → BLOCKED or ALLOWED |

**Live links:**

| | URL |
|---|---|
| Website | https://solanatrust.tech |
| Oracle | https://solanatrust.tech/oracle |
| Telegram Bot | https://t.me/solanatrust_bot |
| Smart Contract | [Explorer](https://explorer.solana.com/address/HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS?cluster=devnet) |
| GitHub | https://github.com/Talap-creator/solana-scam-check |

---

## Backtest: 10/10 Rug Pulls Caught

| Token | Loss | Score | Result |
|-------|------|-------|--------|
| $LIBRA (Milei/Argentina) | $251M from 50K investors | 85/100 CRITICAL | CAUGHT |
| $MELANIA (First Lady) | $30M+ extracted | 95/100 CRITICAL | CAUGHT |
| HAWK Tuah (Hailey Welch) | $490M wiped in 20min | 87/100 CRITICAL | CAUGHT |
| $TRUMP (Presidential) | 87% crash from $7B mcap | 87/100 CRITICAL | CAUGHT |
| $ENRON (Satire Rug) | $700M mcap, 92% insider | 82/100 CRITICAL | CAUGHT |
| M3M3 (Meteora Scandal) | $69M via 150+ wallets | 82/100 CRITICAL | CAUGHT |
| VINE (Vine App) | $500M → $16M | 70/100 HIGH | CAUGHT |
| SHARPEI ($SHAR) | Crashed 96% in 2 SECONDS | 62/100 HIGH | CAUGHT |
| Gen Z Quant | Rugged live on stream | 100/100 CRITICAL | CAUGHT |
| HNUT (Peanut) | 99%+ collapse | 82/100 CRITICAL | CAUGHT |

**100% detection rate** · 0.2% false positive rate (3/1916 legit tokens)

---

## Architecture

```
┌──────────────────┐     ┌───────────────────┐     ┌──────────────────────┐
│   Frontend       │     │   Backend         │     │   Solana Devnet      │
│   Next.js 16     │────▶│   FastAPI          │────▶│   Anchor Program     │
│   Phantom Wallet │     │   Rule Engine     │     │   PDA: Oracle        │
│   Vault Panel    │     │   ML Model (ONNX) │     │   PDA: Scores        │
│   SSE Streaming  │◀────│   AI Agent (GPT)  │     │   PDA: Vaults        │
└──────────────────┘     └───────────────────┘     └──────────────────────┘
                              │
                         ┌────┴────┐
                         │ Telegram │
                         │   Bot    │
                         └─────────┘
```

### Scoring Pipeline

```
Token Address
     │
[1. Rule Engine] 56 on-chain features, 6 categories
     │  Technical (30%) · Distribution (25%) · Market (25%) · Behaviour (20%)
     │  → rule_score (0-100)
     │
[2. ML Model] XGBoost/ONNX on 37 DexScreener features
     │  → ml_probability (0.0-1.0)
     │
[3. Blend] final_score = 0.6 × rule_score + 0.4 × (ml_probability × 100)
     │
[4. AI Agent] GPT-4o-mini adds reasoning (advisory only, no score override)
     │
[5. Publish] score + risk_level + reasoning → Solana PDA on-chain
```

### Smart Contract (Anchor/Rust)

**Program ID:** `HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS`

| Instruction | Description |
|---|---|
| `initialize_oracle` | Set publisher authority |
| `publish_score` | AI agent writes risk score to PDA |
| `create_vault` | User creates vault with risk threshold |
| `deposit` | User deposits SOL into vault |
| **`guarded_swap`** | **Checks AI score vs threshold — rejects if risky** |
| `emergency_exit` | Auto-withdraw if score ≥ 75 |
| `update_threshold` | Adjust vault risk tolerance |

---

## Quick Start

### 3 commands (Docker)

```bash
git clone https://github.com/Talap-creator/solana-scam-check.git
cp backend/.env.example backend/.env  # fill in API keys
docker-compose up                     # postgres:16 → backend:8000 → frontend:3000
```

### Manual setup

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

### Environment Variables

**Backend** (`.env`):
```
DATABASE_URL=sqlite:///./rugsignal.db
JWT_SECRET_KEY=your-secret-key-minimum-60-characters-long
OPENAI_API_KEY=sk-...
ORACLE_PUBLISHER_KEYPAIR=[1,2,3...]
ORACLE_PROGRAM_ID=HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS
ORACLE_RPC_URL=https://api.devnet.solana.com
HELIUS_API_KEY=...
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
```

**Frontend** (`.env`):
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## Telegram Bot

[@solanatrust_bot](https://t.me/solanatrust_bot) — instant token risk scoring in Telegram.

Send any Solana token address:

```
You:  7BgBvyjrZX1YKz4oh9mjb8ZScatkkwb8DzFx7LoiVkM3
Bot:  ⛔ Score: 85/100 (CRITICAL)
      ML Model: 87.3% rug probability
      Top risks: concentrated holders, no freeze authority...
```

Uses the same backend scoring pipeline as the website — no separate logic.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, Python 3.12, SQLAlchemy |
| ML | XGBoost → ONNX Runtime (407KB model, 8MB RAM) |
| AI | GPT-4o-mini |
| Blockchain | Solana Devnet, Anchor 0.30.1 |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Wallet | Phantom, Solflare via Solana Wallet Adapter |
| Data | DexScreener API, Solana RPC |
| Deploy | Docker, Render, Vercel |
| Bot | Telegram Bot API (python-telegram-bot) |

---

## Roadmap

| Phase | Milestone |
|-------|-----------|
| **v1 (current)** | Devnet oracle, 3-layer scoring, GuardedVault, 10/10 backtest |
| **v2** | Mainnet deployment, real SOL vaults |
| **v3** | Public REST API for wallets, DEXes, bots |
| **v4** | Jupiter/Raydium plugin — auto-check before swap |
| **v5** | Decentralized oracle — multi-publisher consensus with staking |
| **v6** | Cross-chain (Base, Ethereum) |

---

## Team

**SolanaTrust** — Kazakhstan

| Name | Role |
|------|------|
| [**Kenzhebayev Talap**](https://www.linkedin.com/in/talap-kenzhebaev-product-manager) | Founder & Lead Developer |

---

## License

MIT
