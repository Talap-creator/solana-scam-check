import unittest
from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import SessionLocal, init_db
from app.main import app
from app.models import DeveloperOperatorProfile, DeveloperOperatorSnapshot
from app.services.repository import _build_developer_operator_payloads


class DeveloperFeedTests(unittest.TestCase):
    def test_developer_feed_returns_operator_items(self) -> None:
        client = TestClient(app)

        response = client.get("/api/v1/feed/developers?limit=50")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("items", payload)
        self.assertGreater(len(payload["items"]), 0)
        item = payload["items"][0]
        self.assertIn("id", item)
        self.assertIn("kind", item)
        self.assertIn("operator_score", item)
        self.assertIn("high_risk_launches", item)
        self.assertIn("latest_launches", item)
        self.assertIsInstance(item["latest_launches"], list)
        self.assertIn("profile_signals", item)
        self.assertIsInstance(item["profile_signals"], list)

    def test_developer_feed_persists_profiles_and_dedupes_snapshots(self) -> None:
        client = TestClient(app)
        try:
            init_db()
        except OperationalError:
            self.skipTest("Database is unavailable for developer feed persistence assertions.")

        first_response = client.get("/api/v1/feed/developers?limit=20")
        self.assertEqual(first_response.status_code, 200)
        first_payload = first_response.json()
        self.assertGreater(len(first_payload["items"]), 0)
        first_item = first_payload["items"][0]

        second_response = client.get("/api/v1/feed/developers?limit=20")
        self.assertEqual(second_response.status_code, 200)

        with SessionLocal() as db:
            persisted = db.get(DeveloperOperatorProfile, first_item["id"])
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.operator_score, first_item["operator_score"])
            snapshots = (
                db.query(DeveloperOperatorSnapshot)
                .filter(DeveloperOperatorSnapshot.operator_key == first_item["id"])
                .all()
            )
            self.assertEqual(len(snapshots), 1)

    def test_developer_feed_uses_lead_wallet_when_shared_funder_is_missing(self) -> None:
        report = SimpleNamespace(
            id="token-report-1",
            entity_type="token",
            entity_id="Mint111111111111111111111111111111111111111",
            display_name="TEST / Test Token",
            symbol="TEST",
            name="Test Token",
            created_at=datetime.now(timezone.utc),
            status="high",
            confidence=0.62,
            page_mode="early_launch",
            rug_probability=78,
            trade_caution=SimpleNamespace(level="high"),
            launch_radar=SimpleNamespace(
                launch_age_minutes=11,
                early_cluster_activity="none",
                early_trade_pressure="balanced",
            ),
            risk_increasers=[],
            behaviour_analysis_v2=SimpleNamespace(
                confidence_breakdown=[],
                modules={
                    "developer_cluster": SimpleNamespace(
                        status="watch",
                        summary="Lead wallet can be resolved from the launch cluster.",
                        evidence=SimpleNamespace(
                            metrics={
                                "shared_funder": None,
                                "lead_wallet": "LeadWallet1111111111111111111111111111111111",
                                "shared_funding_ratio": 0.42,
                                "estimated_cluster_wallet_count": 3,
                                "estimated_cluster_supply_share": 17.8,
                            }
                        )
                    ),
                    "insider_selling": SimpleNamespace(
                        status="watch",
                        evidence=SimpleNamespace(metrics={}),
                        summary="Seller overlap is still forming.",
                    ),
                }
            ),
        )

        payloads = _build_developer_operator_payloads([report])
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["kind"], "wallet")
        self.assertEqual(payloads[0]["wallet_preview"], "LeadWallet1111111111111111111111111111111111")
        self.assertEqual(payloads[0]["id"], "LeadWallet1111111111111111111111111111111111")


if __name__ == "__main__":
    unittest.main()
