# RugSignal

RugSignal is a Solana risk-intelligence app for early launch screening, token report analysis, live launch-feed monitoring, and account-linked watchlists.

## Stack

- `frontend`: Next.js 16, React 19, TypeScript
- `backend`: FastAPI, SQLAlchemy, PostgreSQL or SQLite
- `data sources`: Solana RPC, Helius asset metadata, DexScreener market data

## Project Layout

```text
rugsignal/
|-- frontend/
|-- backend/
|-- docs/
|-- docker-compose.yml
|-- README.md
`-- TECH_SPEC.md
```

## Local Run

Frontend:

```powershell
cd frontend
npm install
npm run build
npm run start
```

Backend:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run policy:

- do not use `next dev`
- do not use `uvicorn --reload`
- keep local runs in lightweight production mode unless you are explicitly debugging

## Docker Deploy

1. Copy `.env.example` to `.env`
2. Fill `JWT_SECRET_KEY`
3. Add `HELIUS_API_KEY` or a dedicated `SOLANA_RPC_URL`
4. Run:

```powershell
docker compose up --build -d
```

Published services:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- postgres: `localhost:5432`

Notes:

- frontend uses a standalone Next.js build
- browser auth/API calls go through Next same-origin `/api/v1/*` proxy routes, so the backend URL is only needed on the server side
- backend runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- postgres uses the named volume `rugsignal_postgres_data`

## Key Routes

- `/`
- `/coins`
- `/dashboard`
- `/watchlist`
- `/report/[entityType]/[reportId]`
- `/admin`

## Key API Endpoints

- `GET /health`
- `GET /api/v1/overview`
- `GET /api/v1/checks`
- `GET /api/v1/checks/{check_id}`
- `GET /api/v1/feed/launches`
- `GET /api/v1/watchlist`
- `POST /api/v1/check/token`
- `POST /api/v1/recheck/{entity_type}/{entity_id}`
- `POST /v2/scan/token`

## Token Report Contract

The token report now exposes explicit early-stage fields:

- `page_mode`: `early_launch | early_market | mature`
- `launch_risk`
- `trade_caution`
- `launch_radar`
- `early_warnings`
- `market_source`

This keeps very new tokens from showing misleading `LOW + High confidence` messaging and makes early-launch uncertainty explicit in the UI.
