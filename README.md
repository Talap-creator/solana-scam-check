# Solace Scan

Solana scam-checking platform with:

- `frontend`: React + TypeScript + Tailwind via Next.js
- `backend`: FastAPI + Python
- `solana layer`: planned Rust-based onchain analysis module

## Structure

```text
solana-scam-check/
├── frontend/        # Next.js app
├── backend/         # FastAPI API
├── README.md
└── TECH_SPEC.md
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

## Run backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Main routes

- `/`
- `/dashboard`
- `/history`
- `/watchlist`
- `/admin`
- `/report/token/pearl-token`

## Main API endpoints

- `GET /health`
- `GET /api/v1/overview`
- `GET /api/v1/checks`
- `GET /api/v1/checks/{check_id}`
- `GET /api/v1/watchlist`
- `GET /api/v1/admin/review-queue`
- `POST /api/v1/check/token`

