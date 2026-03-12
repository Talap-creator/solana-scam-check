# RugSignal API

FastAPI backend for RugSignal, focused on Solana token analysis, live launch assessment, account auth, watchlists, and admin operations.

## Structure

```text
backend/
|-- app/
|   |-- api/routes/
|   |-- services/
|   |-- scoring/
|   |-- config.py
|   |-- db.py
|   |-- dependencies.py
|   |-- main.py
|   `-- schemas.py
|-- models/
|-- tests/
|-- tools/
|-- Dockerfile
|-- requirements.txt
`-- .env.example
```

## Local Run

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Do not use `--reload` unless you explicitly need a debug loop.

## Environment

Required in production:

- `JWT_SECRET_KEY`
- `HELIUS_API_KEY` or another Solana RPC source

Common variables:

- `DATABASE_URL`
- `CORS_ALLOW_ORIGINS`
- `TOKEN_HOLDERS_MAX_PAGES`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `ADMIN_BOOTSTRAP_EMAIL`
- `FREE_DAILY_SCAN_LIMIT`
- `PRO_DAILY_SCAN_LIMIT`
- `ENTERPRISE_DAILY_SCAN_LIMIT`
- `FEED_LIVE_SOURCE_ENABLED`
- `FEED_LIVE_PROFILES_LIMIT`
- `FEED_LIVE_SYNC_TTL_SECONDS`

Local example:

- `DATABASE_URL=sqlite:///./rugsignal.db`

Docker example:

- `DATABASE_URL=postgresql+psycopg://rugsignal:rugsignal@postgres:5432/rugsignal`

## Docker

The backend container is production-oriented and starts with:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

From project root:

```powershell
docker compose up --build backend postgres
```

## Main Endpoints

- `GET /health`
- `GET /api/v1/overview`
- `GET /api/v1/insights`
- `GET /api/v1/checks`
- `GET /api/v1/checks/{check_id}`
- `POST /api/v1/check/token`
- `POST /api/v1/check/wallet`
- `POST /api/v1/check/project`
- `POST /api/v1/recheck/{entity_type}/{entity_id}`
- `GET /api/v1/feed/launches`
- `GET /api/v1/watchlist`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/admin/dashboard`

## Token Report Notes

The token-report response now includes early-stage UX fields:

- `page_mode`
- `launch_risk`
- `launch_radar`
- `early_warnings`
- `market_source`

`launch_risk` is currently implemented as a backend rule layer on top of the existing signal set. It is production-usable, but not yet a dedicated standalone scoring model.

## Tests

```powershell
cd backend
python -m unittest tests.test_token_report_modes tests.test_v2_pipeline_adapter
```
