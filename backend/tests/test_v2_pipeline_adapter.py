import unittest

from app.scoring.pipeline import TokenScoringPipeline
from app.services.analyzer import generate_report


class V2PipelineAdapterTests(unittest.TestCase):
    def test_pipeline_uses_live_report_scoring_contract(self) -> None:
        report = generate_report("token", "So11111111111111111111111111111111111111112", live_token_analysis=False)
        result = TokenScoringPipeline().run(report=report)
        response = result.response

        self.assertEqual(response.score, report.score)
        self.assertEqual(int(response.rug_probability), report.rug_probability)
        self.assertEqual(response.technical_risk, report.technical_risk)
        self.assertEqual(response.market_execution_risk, report.market_execution_risk)
        self.assertEqual(response.market_maturity, report.market_maturity)
        self.assertEqual(response.explanation.summary, report.summary)
        self.assertEqual(response.category_scores.technical_risk, report.technical_risk)
        self.assertEqual(response.model.version, "live_report_adapter_v21")
        self.assertIn("scoring_source", response.feature_metadata)
        self.assertIsNotNone(response.behaviour_analysis)
        self.assertEqual(len(response.behaviour_analysis.modules), 4)
        self.assertIn("modules_ran", response.behaviour_analysis.debug or {})


if __name__ == "__main__":
    unittest.main()
