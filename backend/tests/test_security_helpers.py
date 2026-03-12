import unittest

from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app
from app.services.password_policy import validate_password_strength
from app.services.rate_limits import InMemoryRateLimiter, client_address_for_rate_limit


def build_request(*, headers: dict[str, str] | None = None, host: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "headers": [
            (key.lower().encode("utf-8"), value.encode("utf-8"))
            for key, value in (headers or {}).items()
        ],
        "client": (host, 443),
        "method": "GET",
        "path": "/",
        "scheme": "https",
    }
    return Request(scope)


class PasswordPolicyTests(unittest.TestCase):
    def test_rejects_short_predictable_passwords(self) -> None:
        self.assertEqual(
            validate_password_strength("Password123!", "user@example.com"),
            "Password is too predictable. Choose a less common phrase.",
        )
        self.assertEqual(
            validate_password_strength("Sh0rt!", "user@example.com"),
            "Password must be at least 12 characters long.",
        )

    def test_accepts_strong_password(self) -> None:
        self.assertIsNone(validate_password_strength("A!phaBeta2026", "user@example.com"))


class RateLimitTests(unittest.TestCase):
    def test_client_address_prefers_forwarded_for(self) -> None:
        request = build_request(headers={"x-forwarded-for": "203.0.113.4, 10.0.0.2"})
        self.assertEqual(client_address_for_rate_limit(request), "203.0.113.4")

    def test_limiter_blocks_after_threshold(self) -> None:
        limiter = InMemoryRateLimiter()
        self.assertEqual(limiter.check("login", "127.0.0.1", 2, 60), (True, 0))
        self.assertEqual(limiter.check("login", "127.0.0.1", 2, 60), (True, 0))
        allowed, retry_after = limiter.check("login", "127.0.0.1", 2, 60)
        self.assertFalse(allowed)
        self.assertGreaterEqual(retry_after, 1)


class SecurityHeaderTests(unittest.TestCase):
    def test_health_response_includes_security_headers(self) -> None:
        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "strict-origin-when-cross-origin")


if __name__ == "__main__":
    unittest.main()
