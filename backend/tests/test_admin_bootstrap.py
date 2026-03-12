from dataclasses import replace
from unittest import TestCase

from app.api.routes import auth as auth_routes


class AdminBootstrapTests(TestCase):
    def test_resolve_user_role_promotes_bootstrap_email(self) -> None:
        original_settings = auth_routes.settings
        auth_routes.settings = replace(auth_routes.settings, admin_bootstrap_email="admin@solanatrust.io")
        try:
          self.assertEqual(auth_routes.resolve_user_role("admin@solanatrust.io"), "admin")
          self.assertEqual(auth_routes.resolve_user_role("user@example.com"), "user")
        finally:
          auth_routes.settings = original_settings
