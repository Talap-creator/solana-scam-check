import unittest

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import SessionLocal, init_db
from app.main import app
from app.models import DeveloperOperatorProfile, DeveloperOperatorSnapshot


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


if __name__ == "__main__":
    unittest.main()
