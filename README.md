# RugSignal — AI Oracle for Solana Token Risk

**AI agent that scores Solana tokens for rug pull risk and enforces decisions on-chain via smart contract.**

> National Solana Hackathon by Decentrathon 2026 | Case 2: AI + Blockchain

## The Problem

Rug pulls on Solana steal millions. Existing tools only warn — they don't prevent. Smart contracts remain static and can't adapt to changing risk.

## The Solution

RugSignal combines AI analysis with on-chain enforcement:

1. **AI Agent** analyzes token on-chain data (holders, liquidity, authorities, deployer history)
2. **GPT-4o-mini** scores the token (0-100 risk) with reasoning
3. **Score is published on-chain** to Solana PDA via Oracle program
4. **GuardedVault smart contract** reads the AI score and **blocks risky swaps automatically**

```
Token Added → AI Analyzes → Score Published On-Chain → Swap Attempt → Contract Reads Score → BLOCK or ALLOW
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Frontend       │     │   Backend         │     │   Solana Devnet     │
│   Next.js        │────▶│   FastAPI          │────▶│   Anchor Program    │
│   Phantom Wallet │     │   AI Agent (GPT)  │     │   PDA: Oracle       │
│   Vault Panel    │     │   Oracle Publisher │     │   PDA: Scores       │
│                  │◀────│                    │     │   PDA: Vaults       │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

### Smart Contract Instructions (Anchor/Rust)

| Instruction | Description |
|---|---|
| `initialize_oracle` | Set publisher authority |
| `publish_score` | AI agent writes risk score to PDA |
| `create_vault` | User creates vault with risk threshold |
| `deposit` | User deposits SOL into vault |
| `guarded_swap` | **Checks AI score vs threshold — rejects if risky** |
| `emergency_exit` | Withdraw all funds if token goes critical (score ≥ 75) |
| `update_threshold` | Adjust vault risk tolerance |

**Program ID:** `HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS`

### AI Scoring Pipeline

1. **Feature extraction** — 56 on-chain features (authorities, holder distribution, liquidity, deployer history, behavioral signals)
2. **Rule engine** — weighted heuristic scoring across 6 risk categories
3. **AI Agent (GPT-4o-mini)** — analyzes features, returns score + natural language reasoning
4. **On-chain publish** — score written to Solana PDA, verifiable by anyone

### Key PDA Derivations

```
Oracle Config:  seeds = ["oracle"]
Token Score:    seeds = ["score", token_mint]
User Vault:     seeds = ["vault", owner]
Vault SOL:      seeds = ["vault_sol", owner]
```

## Demo Flow

1. Connect Phantom wallet (Solana Devnet)
2. Add token address to Oracle Monitor
3. AI agent scores it automatically (every 90s)
4. Score appears in ON-CHAIN SCORES table with Explorer link
5. Create GuardedVault with risk threshold (e.g., 50)
6. Deposit devnet SOL
7. **Simulate Swap** — contract checks score:
   - Score ≤ threshold → **SWAP ALLOWED** (green)
   - Score > threshold → **BLOCKED by GuardedVault** (red)
8. Change threshold to see different outcomes

## Tech Stack

| Layer | Technology |
|---|---|
| Blockchain | Solana Devnet, Anchor Framework |
| Smart Contract | Rust (Anchor) |
| Backend | Python, FastAPI, SQLAlchemy, PostgreSQL |
| AI | OpenAI GPT-4o-mini |
| Frontend | Next.js 16, React 19, TypeScript |
| Wallet | Phantom, Solflare (Solana Wallet Adapter) |
| Deploy | Render (backend), Vercel (frontend) |

## Project Structure

```
rugsignal/
├── programs/rugsignal_oracle/src/lib.rs  # Anchor smart contract
├── backend/
│   ├── app/services/ai_scorer.py         # GPT-4o-mini integration
│   ├── app/services/oracle_agent.py      # Autonomous scoring loop
│   ├── app/services/solana_publisher.py  # On-chain tx publisher
│   └── app/scoring/                      # Rule engine + features
├── frontend/
│   ├── src/app/oracle/page.tsx           # Oracle dashboard
│   ├── src/components/oracle/
│   │   ├── vault-panel.tsx               # GuardedVault UI
│   │   └── wallet-provider.tsx           # Solana wallet adapter
│   └── src/app/page.tsx                  # Landing page
└── README.md
```

## Environment Variables

### Backend
```
HELIUS_API_KEY=           # Solana RPC (mainnet data)
OPENAI_API_KEY=           # GPT-4o-mini for AI scoring
ORACLE_PUBLISHER_KEYPAIR= # JSON array of keypair bytes
ORACLE_PROGRAM_ID=        # HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS
ORACLE_RPC_URL=           # https://api.devnet.solana.com
DATABASE_URL=             # PostgreSQL connection
JWT_SECRET_KEY=           # Auth secret
```

## Live Demo

- **Website:** https://solanatrust.tech
- **Oracle Dashboard:** https://solanatrust.tech/oracle
- **Program on Explorer:** https://explorer.solana.com/address/HXrM4MfnenFcSWiakw4A6mQAstwhpKQECGBPa7Sn4MuS?cluster=devnet

## Team

Built by SolanaTrust team for National Solana Hackathon by Decentrathon 2026.
