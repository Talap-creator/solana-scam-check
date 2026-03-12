import unittest

from app.services.analyzer import compute_token_scoring_v21


class ScoringV21Tests(unittest.TestCase):
    def test_mature_known_project_gets_softened_rug_probability(self) -> None:
        scoring = compute_token_scoring_v21(
            mint_authority_enabled=True,
            freeze_authority_enabled=True,
            update_authority_enabled=False,
            dangerous_contract_capability_score=0.35,
            top_10_share=52.0,
            top_1_share=11.0,
            usd_liquidity=120_000.0,
            market_age_days=900,
            market_cap_usd=12_000_000_000.0,
            volume_24h_usd=450_000_000.0,
            listed_on_known_aggregator=True,
            listed_on_major_cex=True,
            known_project_flag=True,
            metadata_mismatch=False,
            holder_scan_complete=True,
            has_market_profile=True,
        )

        self.assertGreaterEqual(int(scoring["technical_risk"]), 30)
        self.assertLessEqual(int(scoring["technical_risk"]), 70)
        self.assertLessEqual(int(scoring["rug_probability"]), 25)
        self.assertGreaterEqual(int(scoring["market_maturity"]), 70)
        self.assertFalse(bool(scoring["hard_critical"]))

    def test_low_liquidity_legit_token_keeps_market_risk_separate_from_rug(self) -> None:
        scoring = compute_token_scoring_v21(
            mint_authority_enabled=False,
            freeze_authority_enabled=False,
            update_authority_enabled=False,
            dangerous_contract_capability_score=0.10,
            top_10_share=38.0,
            top_1_share=7.5,
            usd_liquidity=18_000.0,
            market_age_days=420,
            market_cap_usd=180_000_000.0,
            volume_24h_usd=6_500_000.0,
            listed_on_known_aggregator=True,
            listed_on_major_cex=False,
            known_project_flag=True,
            metadata_mismatch=False,
            holder_scan_complete=True,
            has_market_profile=True,
        )

        self.assertGreaterEqual(int(scoring["market_execution_risk"]), 55)
        self.assertLessEqual(int(scoring["rug_probability"]), 30)
        self.assertLessEqual(int(scoring["liquidity_rug_component"]), 20)
        self.assertGreaterEqual(int(scoring["market_maturity"]), 35)

    def test_suspicious_new_token_escalates_to_high_risk(self) -> None:
        scoring = compute_token_scoring_v21(
            mint_authority_enabled=True,
            freeze_authority_enabled=True,
            update_authority_enabled=True,
            dangerous_contract_capability_score=0.95,
            top_10_share=96.0,
            top_1_share=28.0,
            usd_liquidity=12_000.0,
            market_age_days=20,
            market_cap_usd=1_500_000.0,
            volume_24h_usd=45_000.0,
            listed_on_known_aggregator=False,
            listed_on_major_cex=False,
            known_project_flag=False,
            metadata_mismatch=True,
            holder_scan_complete=True,
            has_market_profile=True,
        )

        self.assertGreaterEqual(int(scoring["behaviour_risk"]), 60)
        self.assertGreaterEqual(int(scoring["liquidity_rug_component"]), 60)
        self.assertGreaterEqual(int(scoring["rug_probability"]), 75)
        self.assertTrue(bool(scoring["hard_critical"]))


if __name__ == "__main__":
    unittest.main()
