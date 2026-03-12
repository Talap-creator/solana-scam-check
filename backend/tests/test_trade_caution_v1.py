import unittest

from app.scoring.behaviour.models import BehaviourComputation, BehaviourModuleComputation
from app.scoring.trade_caution import build_trade_caution_overview


def _behaviour(score_map: dict[str, float], status_map: dict[str, str]) -> BehaviourComputation:
    modules = {
        "developer_cluster": BehaviourModuleComputation(
            key="developer_cluster",
            title="Developer wallet cluster",
            status=status_map.get("developer_cluster", "clear"),
            severity="high" if status_map.get("developer_cluster") == "flagged" else "medium" if status_map.get("developer_cluster") == "watch" else "low",
            score=score_map.get("developer_cluster", 0.0),
            summary="",
        ),
        "early_buyers": BehaviourModuleComputation(
            key="early_buyers",
            title="Early buyer concentration",
            status=status_map.get("early_buyers", "clear"),
            severity="high" if status_map.get("early_buyers") == "flagged" else "medium" if status_map.get("early_buyers") == "watch" else "low",
            score=score_map.get("early_buyers", 0.0),
            summary="",
        ),
        "insider_selling": BehaviourModuleComputation(
            key="insider_selling",
            title="Insider selling",
            status=status_map.get("insider_selling", "clear"),
            severity="high" if status_map.get("insider_selling") == "flagged" else "medium" if status_map.get("insider_selling") == "watch" else "low",
            score=score_map.get("insider_selling", 0.0),
            summary="",
        ),
        "liquidity_management": BehaviourModuleComputation(
            key="liquidity_management",
            title="Liquidity management",
            status=status_map.get("liquidity_management", "clear"),
            severity="high" if status_map.get("liquidity_management") == "flagged" else "medium" if status_map.get("liquidity_management") == "watch" else "low",
            score=score_map.get("liquidity_management", 0.0),
            summary="",
        ),
    }
    return BehaviourComputation(
        summary="",
        overall_behaviour_risk="low",
        confidence="medium",
        score=int(sum(score_map.values()) / max(len(score_map), 1)),
        modules=modules,
        confidence_breakdown={},
    )


class TradeCautionV1Tests(unittest.TestCase):
    def test_link_like_case_can_be_low_rug_but_high_caution(self) -> None:
        caution = build_trade_caution_overview(
            rug_probability=8,
            technical_risk=62,
            distribution_risk=25,
            market_execution_risk=79,
            market_maturity=49,
            market_age_days=270,
            market_cap_usd=12_000_000,
            volume_24h_usd=250_000,
            usd_liquidity=380.0,
            largest_pool_liquidity_usd=380.0,
            pool_count=1,
            dex_count=1,
            top_1_share=9.2,
            top_10_share=50.9,
            dev_cluster_share=0.0,
            known_project_flag=False,
            listed_on_major_cex=False,
            listed_on_known_aggregator=True,
            mint_authority_enabled=True,
            freeze_authority_enabled=True,
            update_authority_enabled=False,
            dangerous_contract_capability_score=0.35,
            metadata_mismatch=False,
            lp_lock_missing=False,
            lp_owner_is_deployer=False,
            suspicious_liquidity_control=False,
            honeypot_simulation_failed=False,
            sell_restrictions_detected=False,
            behaviour=_behaviour(
                {
                    "developer_cluster": 0.0,
                    "early_buyers": 0.0,
                    "insider_selling": 0.0,
                    "liquidity_management": 48.0,
                },
                {
                    "developer_cluster": "clear",
                    "early_buyers": "clear",
                    "insider_selling": "clear",
                    "liquidity_management": "watch",
                },
            ),
        )

        self.assertEqual(caution.level, "high")
        self.assertGreaterEqual(caution.score, 60)

    def test_sol_like_case_stays_low_or_moderate_caution(self) -> None:
        caution = build_trade_caution_overview(
            rug_probability=2,
            technical_risk=1,
            distribution_risk=18,
            market_execution_risk=28,
            market_maturity=61,
            market_age_days=900,
            market_cap_usd=90_000_000_000,
            volume_24h_usd=3_000_000_000,
            usd_liquidity=2_500_000,
            largest_pool_liquidity_usd=2_500_000,
            pool_count=4,
            dex_count=3,
            top_1_share=4.0,
            top_10_share=22.0,
            dev_cluster_share=0.0,
            known_project_flag=True,
            listed_on_major_cex=True,
            listed_on_known_aggregator=True,
            mint_authority_enabled=False,
            freeze_authority_enabled=False,
            update_authority_enabled=False,
            dangerous_contract_capability_score=0.1,
            metadata_mismatch=False,
            lp_lock_missing=False,
            lp_owner_is_deployer=False,
            suspicious_liquidity_control=False,
            honeypot_simulation_failed=False,
            sell_restrictions_detected=False,
            behaviour=_behaviour(
                {
                    "developer_cluster": 0.0,
                    "early_buyers": 0.0,
                    "insider_selling": 0.0,
                    "liquidity_management": 18.0,
                },
                {
                    "developer_cluster": "clear",
                    "early_buyers": "clear",
                    "insider_selling": "clear",
                    "liquidity_management": "clear",
                },
            ),
        )

        self.assertIn(caution.level, {"low", "moderate"})
        self.assertLess(caution.score, 50)

    def test_suspicious_case_reaches_avoid(self) -> None:
        caution = build_trade_caution_overview(
            rug_probability=82,
            technical_risk=88,
            distribution_risk=93,
            market_execution_risk=91,
            market_maturity=10,
            market_age_days=12,
            market_cap_usd=1_500_000,
            volume_24h_usd=45_000,
            usd_liquidity=8_000,
            largest_pool_liquidity_usd=8_000,
            pool_count=1,
            dex_count=1,
            top_1_share=28.0,
            top_10_share=96.0,
            dev_cluster_share=0.82,
            known_project_flag=False,
            listed_on_major_cex=False,
            listed_on_known_aggregator=False,
            mint_authority_enabled=True,
            freeze_authority_enabled=True,
            update_authority_enabled=True,
            dangerous_contract_capability_score=0.95,
            metadata_mismatch=True,
            lp_lock_missing=True,
            lp_owner_is_deployer=True,
            suspicious_liquidity_control=True,
            honeypot_simulation_failed=False,
            sell_restrictions_detected=False,
            behaviour=_behaviour(
                {
                    "developer_cluster": 94.0,
                    "early_buyers": 82.0,
                    "insider_selling": 91.0,
                    "liquidity_management": 88.0,
                },
                {
                    "developer_cluster": "flagged",
                    "early_buyers": "flagged",
                    "insider_selling": "flagged",
                    "liquidity_management": "flagged",
                },
            ),
        )

        self.assertEqual(caution.level, "avoid")
        self.assertGreaterEqual(caution.score, 75)


if __name__ == "__main__":
    unittest.main()
