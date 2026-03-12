import unittest
from datetime import timedelta

from app.services.analyzer import generate_report, utc_now


class TokenReportModeTests(unittest.TestCase):
    def test_early_launch_mode_caps_confidence_and_emits_launch_context(self) -> None:
        report = generate_report(
            "token",
            "So11111111111111111111111111111111111111112",
            live_token_analysis=False,
            created_at=utc_now() - timedelta(minutes=12),
        )

        self.assertEqual(report.page_mode, "early_launch")
        self.assertLess(report.confidence, 0.75)
        self.assertIsNotNone(report.launch_radar.launch_age_minutes)
        self.assertLess(report.launch_radar.launch_age_minutes or 9999, 60)
        self.assertGreaterEqual(len(report.early_warnings), 1)
        self.assertIn("early", report.summary.lower())

    def test_early_market_mode_uses_first_day_language(self) -> None:
        report = generate_report(
            "token",
            "So11111111111111111111111111111111111111112",
            live_token_analysis=False,
            created_at=utc_now() - timedelta(hours=6),
        )

        self.assertEqual(report.page_mode, "early_market")
        self.assertGreaterEqual(report.launch_radar.launch_age_minutes or 0, 60)
        self.assertLess(report.launch_radar.launch_age_minutes or 99999, 1440)
        self.assertIn("first day", report.summary.lower())

    def test_mature_mode_restores_mature_context(self) -> None:
        report = generate_report(
            "token",
            "So11111111111111111111111111111111111111112",
            live_token_analysis=False,
            created_at=utc_now() - timedelta(days=3),
        )

        self.assertEqual(report.page_mode, "mature")
        self.assertGreaterEqual(report.launch_radar.launch_age_minutes or 0, 1440)
        self.assertEqual(report.market_source, "Synthetic launch pool")


if __name__ == "__main__":
    unittest.main()
