import unittest
import uuid

from fastapi.testclient import TestClient

from app.main import app


class AuthWatchlistTests(unittest.TestCase):
    def test_account_watchlist_toggle_roundtrip(self) -> None:
        client = TestClient(app)
        email = f"watchlist-{uuid.uuid4().hex[:8]}@example.com"

        register = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Password123!",
                "plan": "free",
            },
        )
        self.assertEqual(register.status_code, 201)
        token = register.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        add_response = client.post(
            "/api/v1/auth/watchlist",
            json={
                "entity_type": "token",
                "entity_id": "WatchlistMint11111111111111111111111111111111",
                "display_name": "Watchlist Test Token",
            },
            headers=headers,
        )
        self.assertEqual(add_response.status_code, 200)
        add_payload = add_response.json()
        self.assertTrue(add_payload["tracked"])
        self.assertEqual(add_payload["item"]["name"], "Watchlist Test Token")

        status_response = client.get(
            "/api/v1/auth/watchlist/status/token/WatchlistMint11111111111111111111111111111111",
            headers=headers,
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertTrue(status_response.json()["tracked"])

        list_response = client.get("/api/v1/auth/watchlist", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        items = list_response.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["entity_id"], "WatchlistMint11111111111111111111111111111111")

        remove_response = client.delete(
            "/api/v1/auth/watchlist/token/WatchlistMint11111111111111111111111111111111",
            headers=headers,
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertFalse(remove_response.json()["tracked"])

        final_list = client.get("/api/v1/auth/watchlist", headers=headers)
        self.assertEqual(final_list.status_code, 200)
        self.assertEqual(final_list.json()["items"], [])


if __name__ == "__main__":
    unittest.main()
