import unittest

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import SessionLocal, init_db
from app.dependencies import get_repository
from app.main import app
from app.models import PersistedCheckReport


class PersistedWalletReportsTests(unittest.TestCase):
    def test_wallet_reports_are_persisted_and_rehydrated(self) -> None:
        client = TestClient(app)
        try:
            init_db()
        except OperationalError:
            self.skipTest("Database is unavailable for persisted wallet report assertions.")

        wallet_address = "8PX1DbLyJQzY63K5kTz2S88xJ5UQh1dBnmfV91rYx4cR"
        submission = client.post("/api/v1/check/wallet", json={"address": wallet_address})
        self.assertEqual(submission.status_code, 200)
        report_id = submission.json()["check_id"]

        with SessionLocal() as db:
            stored = db.get(PersistedCheckReport, report_id)
            self.assertIsNotNone(stored)
            self.assertEqual(stored.entity_type, "wallet")
            self.assertEqual(stored.entity_id, wallet_address)

        repository = get_repository()
        original_reports = dict(repository.reports)
        original_index = {key: list(value) for key, value in repository.entity_index.items()}

        try:
            repository.reports.clear()
            repository.entity_index.clear()
            rehydrated = repository.get_report(report_id)
            self.assertIsNotNone(rehydrated)
            self.assertEqual(rehydrated.id, report_id)
            self.assertEqual(rehydrated.entity_type, "wallet")
            self.assertEqual(rehydrated.entity_id, wallet_address)

            latest = repository.latest_report_for_entity("wallet", wallet_address)
            self.assertIsNotNone(latest)
            self.assertEqual(latest.id, report_id)

            self.assertTrue(repository.has_entity("wallet", wallet_address))
        finally:
            repository.reports = original_reports
            repository.entity_index = original_index


if __name__ == "__main__":
    unittest.main()
