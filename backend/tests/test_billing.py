import unittest
import uuid
from dataclasses import replace

from fastapi.testclient import TestClient

from app.api.routes import billing as billing_routes
from app.db import init_db
from app.main import app


class BillingTests(unittest.TestCase):
    def test_premium_session_returns_paylink_config(self) -> None:
        original_settings = billing_routes.settings
        billing_routes.settings = replace(
            original_settings,
            helio_premium_paylink_id="paylink_premium_123",
            helio_premium_payment_type="paystream",
        )
        try:
            init_db()
            client = TestClient(app)
            email = f"billing-{uuid.uuid4().hex[:8]}@example.com"
            register = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "Nebula!2048X",
                    "plan": "free",
                },
            )
            self.assertEqual(register.status_code, 201)
            token = register.json()["access_token"]

            session_response = client.get(
                "/api/v1/billing/premium-session",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(session_response.status_code, 200)
            payload = session_response.json()
            self.assertTrue(payload["available"])
            self.assertEqual(payload["paylink_id"], "paylink_premium_123")
            self.assertEqual(payload["payment_type"], "paystream")
            self.assertEqual(payload["additional_json"]["email"], email)
            self.assertEqual(payload["additional_json"]["plan"], "pro")
        finally:
            billing_routes.settings = original_settings

    def test_helio_webhook_upgrades_user_to_pro(self) -> None:
        original_settings = billing_routes.settings
        billing_routes.settings = replace(
            original_settings,
            helio_premium_paylink_id="paylink_premium_123",
            helio_premium_payment_type="paystream",
            helio_webhook_secret="super-secret",
        )
        try:
            init_db()
            client = TestClient(app)
            email = f"premium-{uuid.uuid4().hex[:8]}@example.com"
            register = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "Nebula!2048X",
                    "plan": "free",
                },
            )
            self.assertEqual(register.status_code, 201)
            token = register.json()["access_token"]
            me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(me.status_code, 200)
            user_id = me.json()["id"]

            webhook = client.post(
                "/api/v1/billing/helio/webhook?secret=super-secret",
                json={
                    "event": "subscription_started",
                    "status": "completed",
                    "paylinkId": "paylink_premium_123",
                    "transactionId": f"txn-{uuid.uuid4().hex[:8]}",
                    "additionalJSON": {
                        "userId": user_id,
                        "email": email,
                        "plan": "pro",
                    },
                },
            )
            self.assertEqual(webhook.status_code, 200)
            self.assertTrue(webhook.json()["accepted"])
            self.assertTrue(webhook.json()["upgraded"])

            upgraded_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(upgraded_me.status_code, 200)
            self.assertEqual(upgraded_me.json()["plan"], "pro")
        finally:
            billing_routes.settings = original_settings

    def test_helio_webhook_rejects_invalid_secret(self) -> None:
        original_settings = billing_routes.settings
        billing_routes.settings = replace(
            original_settings,
            helio_premium_paylink_id="paylink_premium_123",
            helio_webhook_secret="expected-secret",
        )
        try:
            init_db()
            client = TestClient(app)
            response = client.post(
                "/api/v1/billing/helio/webhook?secret=wrong-secret",
                json={"event": "subscription_started", "status": "completed"},
            )
            self.assertEqual(response.status_code, 401)
        finally:
            billing_routes.settings = original_settings


if __name__ == "__main__":
    unittest.main()
