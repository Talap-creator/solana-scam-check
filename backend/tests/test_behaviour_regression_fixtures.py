import json
from pathlib import Path
import unittest

from app.config import Settings
from app.scoring.behaviour import build_behaviour_analysis_v2


FIXTURES_PATH = Path(__file__).resolve().parent / "fixtures" / "behaviour_cases.json"


class BehaviourRegressionFixturesTests(unittest.TestCase):
    def test_fixture_cases_match_expected_behaviour_verdicts(self) -> None:
        cases = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))

        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                _, schema = build_behaviour_analysis_v2(
                    settings=Settings(),
                    owner_shares=case["input"]["owner_shares"],
                    market_age_days=case["input"]["market_age_days"],
                    market_maturity_score=case["input"].get("market_maturity_score"),
                    known_project_flag=case["input"].get("known_project_flag", False),
                    developer_cluster_signal=case["input"]["developer_cluster_signal"],
                    early_buyer_cluster_signal=case["input"]["early_buyer_cluster_signal"],
                    insider_selling_signal=case["input"]["insider_selling_signal"],
                    insider_liquidity_correlation=case["input"]["insider_liquidity_correlation"],
                    liquidity_management_signal=case["input"]["liquidity_management_signal"],
                )

                expected = case["expected"]
                self.assertEqual(schema.overall_behaviour_risk, expected["overall_behaviour_risk"])
                if "confidence" in expected:
                    self.assertEqual(schema.confidence, expected["confidence"])
                if "summary" in expected:
                    self.assertEqual(schema.summary, expected["summary"])
                for module_key, module_status in expected["module_statuses"].items():
                    self.assertEqual(schema.modules[module_key].status, module_status)


if __name__ == "__main__":
    unittest.main()
