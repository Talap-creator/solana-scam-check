import unittest

from app.config import Settings
from app.scoring.behaviour import build_behaviour_analysis_v2


class BehaviourServiceV2Tests(unittest.TestCase):
    def test_clear_case_returns_four_modules(self) -> None:
        computation, schema = build_behaviour_analysis_v2(
            settings=Settings(),
            owner_shares={"wallet-a": 12.0, "wallet-b": 10.0},
            market_age_days=240,
            developer_cluster_signal={
                "detected": False,
                "cluster_wallet_count": 0,
                "cluster_supply_control_pct": 0.0,
                "shared_funder": None,
                "confidence": 0.0,
            },
            early_buyer_cluster_signal={
                "detected": False,
                "cluster_wallet_count": 0,
                "cluster_supply_control_pct": 0.0,
                "shared_funder": None,
                "confidence": 0.0,
            },
            insider_selling_signal={
                "detected": False,
                "seller_wallet_count": 0,
                "seller_supply_control_pct": 0.0,
                "confidence": 0.0,
            },
            insider_liquidity_correlation=False,
            liquidity_management_signal={
                "detected": False,
                "severity": "green",
                "summary": "No unusual liquidity management detected.",
                "details": "",
            },
        )

        self.assertEqual(len(schema.modules), 4)
        self.assertEqual(schema.overall_behaviour_risk, "low")
        self.assertEqual(schema.modules["developer_cluster"].status, "clear")
        self.assertEqual(computation.summary, "No strong scam-specific behaviour signals were found.")
        self.assertIn("modules_ran", schema.debug or {})
        self.assertIn("multi_hop_shared_funder_count", schema.modules["developer_cluster"].evidence.metrics)

    def test_flagged_pair_receives_uplift(self) -> None:
        computation, schema = build_behaviour_analysis_v2(
            settings=Settings(),
            owner_shares={"wallet-a": 18.0, "wallet-b": 14.0, "wallet-c": 11.0},
            market_age_days=7,
            developer_cluster_signal={
                "detected": True,
                "cluster_wallet_count": 3,
                "cluster_supply_control_pct": 43.0,
                "shared_funder": "Fund3r111111111111111111111111111111111",
                "confidence": 0.8,
            },
            early_buyer_cluster_signal={
                "detected": True,
                "cluster_wallet_count": 3,
                "cluster_supply_control_pct": 28.0,
                "shared_funder": "Fund3r111111111111111111111111111111111",
                "confidence": 0.75,
            },
            insider_selling_signal={
                "detected": True,
                "seller_wallet_count": 3,
                "seller_supply_control_pct": 24.0,
                "confidence": 0.7,
            },
            insider_liquidity_correlation=True,
            liquidity_management_signal={
                "detected": True,
                "severity": "red",
                "summary": "Recent sell pressure overlaps with thin liquidity structure and weak market depth.",
                "details": "Liquidity/FDV ratio: 0.40% | 24h buys/sells: 4/19 | 24h volume: $28000.00",
            },
        )

        self.assertGreaterEqual(schema.score, 55)
        self.assertIn(schema.overall_behaviour_risk, {"high", "critical"})
        self.assertEqual(schema.modules["developer_cluster"].status, "flagged")
        self.assertEqual(schema.modules["insider_selling"].status, "flagged")
        self.assertEqual(computation.confidence, "high")
        self.assertTrue((schema.debug or {}).get("triggered_rules", {}).get("flagged_pair_multiplier_applied"))
        self.assertIn("multi_hop_shared_funder_count", schema.modules["early_buyers"].evidence.metrics)

    def test_liquidity_only_flagged_is_softened_for_mature_context(self) -> None:
        computation, schema = build_behaviour_analysis_v2(
            settings=Settings(),
            owner_shares={"wallet-a": 11.0, "wallet-b": 8.0, "wallet-c": 6.0},
            market_age_days=540,
            market_maturity_score=62,
            known_project_flag=True,
            developer_cluster_signal={
                "detected": False,
                "cluster_wallet_count": 0,
                "cluster_supply_control_pct": 0.0,
                "shared_funder": None,
                "confidence": 0.0,
            },
            early_buyer_cluster_signal={
                "detected": False,
                "cluster_wallet_count": 0,
                "cluster_supply_control_pct": 0.0,
                "shared_funder": None,
                "confidence": 0.0,
            },
            insider_selling_signal={
                "detected": False,
                "seller_wallet_count": 0,
                "seller_supply_control_pct": 0.0,
                "confidence": 0.0,
            },
            insider_liquidity_correlation=False,
            liquidity_management_signal={
                "detected": True,
                "severity": "red",
                "summary": "Short-window liquidity stress was observed, but without corroborating wallet-behaviour anomalies.",
                "details": "Liquidity/FDV ratio: 0.60% | 24h buys/sells: 18/24 | 24h volume: $410000.00",
                "rapid_liquidity_drop_score": 0.78,
                "liquidity_volatility_score": 0.74,
                "lp_owner_deployer_link_score": 0.0,
                "liquidity_change_vs_holder_exits_score": 0.0,
                "short_window_sell_pressure_score": 0.76,
                "short_window_price_drop_score": 0.51,
                "short_window_volume_acceleration_score": 0.44,
            },
        )

        self.assertEqual(schema.overall_behaviour_risk, "low")
        self.assertEqual(schema.modules["liquidity_management"].status, "watch")
        self.assertLess(schema.score, 20)
        self.assertEqual(
            computation.summary,
            "Some liquidity-management irregularities were observed, but no broader suspicious wallet behaviour was detected.",
        )
        self.assertTrue((schema.debug or {}).get("triggered_rules", {}).get("liquidity_only_flagged_softened"))


if __name__ == "__main__":
    unittest.main()
