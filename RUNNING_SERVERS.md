# Minimal Server Runbook

Use the lightest local run mode for this repo.

Frontend:
- `cd frontend`
- `npm run build`
- `npm run start`
  This resolves to `node .next/standalone/server.js` because the frontend uses `output: standalone`.

Backend:
- `cd backend`
- `.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`

Rules:
- Do not use `next dev`
- Do not use `uvicorn --reload`
- Do not enable extra watchers or hot-reload tools unless explicitly requested
