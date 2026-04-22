"""Smoke test for RugSignal backend.

Hits /api/v1/check/token and /api/v1/checks/{id} for a spread of real tokens
so regressions in the analyzer/oracle pipelines surface before deploy.

Usage:
    BACKEND_URL=https://solana-scam-check.onrender.com python backend/scripts/smoke_test.py
    BACKEND_URL=http://127.0.0.1:8000 python backend/scripts/smoke_test.py
"""
from __future__ import annotations

import os
import sys
import time

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# Mix of profiles that have historically broken the pipeline.
TOKENS: list[tuple[str, str]] = [
    ("JITO (mature major)",     "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL"),
    ("BONK (high-volume meme)", "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"),
    ("USDC (stable, not a mint rug)", "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"),
    ("Grass (mid-cap)",         "Grass7B4RdKfBCjTKgSqnXkqjwiGvQyFbuSCUJr3XXjs"),
    ("EKpQGS (small/unknown)",  "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdMG5zojm"),
]


def check(label: str, address: str, client: httpx.Client) -> tuple[bool, str]:
    t0 = time.time()
    try:
        r = client.post(f"{BACKEND_URL}/api/v1/check/token", json={"address": address}, timeout=60)
    except Exception as exc:
        return False, f"POST error: {exc}"
    if r.status_code != 200:
        return False, f"POST /check/token -> {r.status_code}: {r.text[:200]}"

    check_id = r.json().get("check_id")
    if not check_id:
        return False, "no check_id in response"

    try:
        r2 = client.get(f"{BACKEND_URL}/api/v1/checks/{check_id}", timeout=30)
    except Exception as exc:
        return False, f"GET error: {exc}"
    if r2.status_code != 200:
        return False, f"GET /checks/{{id}} -> {r2.status_code}"

    data = r2.json()
    score = data.get("score")
    status = data.get("status")
    if score is None or status is None:
        return False, f"missing score/status in report: {list(data)[:10]}"

    elapsed = time.time() - t0
    return True, f"score={score} risk={status} ({elapsed:.1f}s)"


def main() -> int:
    print(f"Smoke test against {BACKEND_URL}")
    print("-" * 60)
    passed = failed = 0
    with httpx.Client() as client:
        # Liveness first.
        try:
            client.get(f"{BACKEND_URL}/api/v1/health", timeout=10)
        except Exception as exc:
            print(f"FAIL: backend unreachable: {exc}")
            return 1

        for label, address in TOKENS:
            ok, msg = check(label, address, client)
            marker = "PASS" if ok else "FAIL"
            print(f"  [{marker}] {label:40s} {msg}")
            passed += int(ok)
            failed += int(not ok)

    print("-" * 60)
    print(f"{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
