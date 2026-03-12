import unittest

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import SessionLocal, init_db
from app.dependencies import get_repository
from app.main import app
from app.models import LaunchFeedSnapshot, LaunchFeedToken


class LaunchFeedTests(unittest.TestCase):
    def test_launch_feed_returns_items_with_trade_caution(self) -> None:
        client = TestClient(app)

        response = client.get("/api/v1/feed/launches?limit=20")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertIn("items", payload)
        self.assertGreater(len(payload["items"]), 0)
        item = payload["items"][0]
        self.assertIn("mint", item)
        self.assertIn("report_id", item)
        self.assertIn("rug_risk_level", item)
        self.assertIn("trade_caution_level", item)
        self.assertIn("launch_quality", item)
        self.assertIn("copycat_status", item)
        self.assertIn("initial_live_estimate", item)
        self.assertIn("rug_risk_drivers", item)
        self.assertIn("trade_caution_drivers", item)
        self.assertIsInstance(item["rug_risk_drivers"], list)
        self.assertIsInstance(item["trade_caution_drivers"], list)
        self.assertIn("top_reducer", item)
        self.assertIn("deployer_short_address", item)

    def test_launch_feed_filters_copycats(self) -> None:
        client = TestClient(app)

        response = client.get("/api/v1/feed/launches?limit=20&tab=copycats")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(len(payload["items"]), 0)
        for item in payload["items"]:
            self.assertNotEqual(item["copycat_status"], "none")

    def test_launch_feed_supports_cursor_and_query(self) -> None:
        client = TestClient(app)

        first_page = client.get("/api/v1/feed/launches?limit=1")
        self.assertEqual(first_page.status_code, 200)
        first_payload = first_page.json()
        self.assertEqual(len(first_payload["items"]), 1)
        self.assertIsNotNone(first_payload["next_cursor"])

        second_page = client.get(f"/api/v1/feed/launches?limit=1&cursor={first_payload['next_cursor']}")
        self.assertEqual(second_page.status_code, 200)
        second_payload = second_page.json()
        self.assertGreater(len(second_payload["items"]), 0)
        self.assertNotEqual(first_payload["items"][0]["report_id"], second_payload["items"][0]["report_id"])

        query_response = client.get("/api/v1/feed/launches?limit=20&q=link")
        self.assertEqual(query_response.status_code, 200)
        query_payload = query_response.json()
        self.assertGreater(len(query_payload["items"]), 0)
        for item in query_payload["items"]:
            haystack = f"{item['name']} {item['symbol']} {item['mint']}".lower()
            self.assertIn("link", haystack)

    def test_launch_feed_recently_rugged_tab_returns_recent_high_risk_items(self) -> None:
        client = TestClient(app)

        response = client.get("/api/v1/feed/launches?limit=20&tab=recently-rugged")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(len(payload["items"]), 0)
        for item in payload["items"]:
            self.assertIn(item["rug_risk_level"], {"high", "critical"})
            self.assertLessEqual(item["age_minutes"], 1440)

    def test_launch_feed_persists_tokens_and_rehydrates_reports(self) -> None:
        client = TestClient(app)
        try:
            init_db()
        except OperationalError:
            self.skipTest("Database is unavailable for launch feed persistence assertions.")

        response = client.get("/api/v1/feed/launches?limit=5")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(len(payload["items"]), 0)
        first_item = payload["items"][0]
        second_response = client.get("/api/v1/feed/launches?limit=5")
        self.assertEqual(second_response.status_code, 200)

        with SessionLocal() as db:
            persisted = db.get(LaunchFeedToken, first_item["mint"])
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.report_id, first_item["report_id"])
            snapshots = (
                db.query(LaunchFeedSnapshot)
                .filter(LaunchFeedSnapshot.mint == first_item["mint"])
                .all()
            )
            self.assertEqual(len(snapshots), 1)

        repository = get_repository()
        original_reports = dict(repository.reports)
        original_index = {key: list(value) for key, value in repository.entity_index.items()}

        try:
            repository.reports.clear()
            repository.entity_index.clear()
            rehydrated = repository.get_report(first_item["report_id"])
            self.assertIsNotNone(rehydrated)
            self.assertEqual(rehydrated.id, first_item["report_id"])
            self.assertEqual(rehydrated.entity_id, first_item["mint"])
        finally:
            repository.reports = original_reports
            repository.entity_index = original_index


if __name__ == "__main__":
    unittest.main()
