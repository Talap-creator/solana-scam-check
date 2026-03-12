from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import sys


CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db import SessionLocal
from app.models import TokenFeatureSnapshot, TokenScan


CSV_COLUMNS = [
    'token_address',
    'label',
    'cohort',
    'score',
    'rug_probability',
    'known_rug',
    'known_honeypot',
    'known_legit',
    'mature_project',
    'developer_cluster_label',
    'early_buyer_cluster_label',
    'insider_selling_label',
    'liquidity_management_label',
    'notes',
]


@dataclass
class StubRow:
    token_address: str
    score: int | None
    rug_probability: float | None
    notes: str


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def from_snapshots(limit: int) -> list[StubRow]:
    rows: list[StubRow] = []
    seen: set[str] = set()
    with SessionLocal() as db:
        snapshots = db.query(TokenFeatureSnapshot).order_by(TokenFeatureSnapshot.scanned_at.desc()).all()
        for item in snapshots:
            if item.token_address in seen:
                continue
            seen.add(item.token_address)
            score = int(item.final_score)
            rows.append(
                StubRow(
                    token_address=item.token_address,
                    score=score,
                    rug_probability=clamp01(score / 100.0),
                    notes='Auto-generated from token_feature_snapshots',
                )
            )
            if len(rows) >= limit:
                break
    return rows


def from_scans(limit: int, seen: set[str] | None = None) -> list[StubRow]:
    rows: list[StubRow] = []
    seen = seen or set()
    with SessionLocal() as db:
        scans = db.query(TokenScan).order_by(TokenScan.scan_time.desc()).all()
        for item in scans:
            if item.token_address in seen:
                continue
            seen.add(item.token_address)
            score = int(item.risk_score)
            rows.append(
                StubRow(
                    token_address=item.token_address,
                    score=score,
                    rug_probability=clamp01(score / 100.0),
                    notes='Auto-generated from token_scans',
                )
            )
            if len(rows) >= limit:
                break
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Build a dataset stub CSV from current RugSignal scan storage.')
    parser.add_argument('--out', required=True, help='Path to output CSV file')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of unique token rows to emit')
    parser.add_argument('--source', choices=['scans', 'snapshots', 'both'], default='both', help='Where to load token rows from')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    limit = max(1, args.limit)
    rows: list[StubRow] = []
    seen: set[str] = set()

    if args.source in {'snapshots', 'both'}:
        snapshot_rows = from_snapshots(limit)
        rows.extend(snapshot_rows)
        seen.update(item.token_address for item in snapshot_rows)

    if len(rows) < limit and args.source in {'scans', 'both'}:
        scan_rows = from_scans(limit - len(rows), seen)
        rows.extend(scan_rows)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    'token_address': row.token_address,
                    'label': '',
                    'cohort': '',
                    'score': '' if row.score is None else row.score,
                    'rug_probability': '' if row.rug_probability is None else f'{row.rug_probability:.2f}',
                    'known_rug': '',
                    'known_honeypot': '',
                    'known_legit': '',
                    'mature_project': '',
                    'developer_cluster_label': '',
                    'early_buyer_cluster_label': '',
                    'insider_selling_label': '',
                    'liquidity_management_label': '',
                    'notes': row.notes,
                }
            )

    print(f'Wrote {len(rows)} rows to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
