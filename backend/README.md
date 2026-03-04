# Solace Scan API

FastAPI backend for the Solana scam-checking platform.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `GET /api/v1/overview`
