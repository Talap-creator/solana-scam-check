from __future__ import annotations

from dataclasses import dataclass

from ..normalization import (
    bucketize_percentile,
    clamp01,
    normalize_bool,
    normalize_inverse_log_scale,
    normalize_threshold,
)
from ..schemas import ScoreCategoryScores, ScoreContributor, TokenFeatureSchema


@dataclass
class RuleEngineOutput:
    rule_score: float
    category_scores: ScoreCategoryScores
    findings: list[ScoreContributor]
    uncertainty_flags: list[str]


def _to_score(value: float) -> int:
    return max(0, min(100, int(round(value * 100))))


class RuleEngineV2:
    version = "rules_v2"

    def evaluate(self, features: TokenFeatureSchema) -> RuleEngineOutput:
        findings: list[ScoreContributor] = []
        uncertainty_flags: list[str] = []

        mint_flag = normalize_bool(features.mint_authority_enabled, missing_value=0.0)
        freeze_flag = normalize_bool(features.freeze_authority_enabled, missing_value=0.0)
        update_flag = normalize_bool(features.update_authority_enabled, missing_value=0.4)

        authority = clamp01((0.55 * mint_flag) + (0.25 * freeze_flag) + (0.20 * update_flag))
        if features.token_age_seconds and features.token_age_seconds > 180 * 86400:
            authority *= 0.8
        if features.known_project_flag:
            authority *= 0.65
        if features.listed_on_major_cex:
            authority *= 0.6

        top1 = bucketize_percentile(
            features.top_1_holder_share,
            [(0.08, 0.0), (0.15, 0.25), (0.30, 0.55), (0.50, 0.8), (1.0, 1.0)],
        )
        if features.largest_holder_is_lp:
            top1 *= 0.5

        top10 = bucketize_percentile(
            features.top_10_holder_share,
            [(0.20, 0.0), (0.40, 0.2), (0.60, 0.45), (0.80, 0.75), (1.0, 1.0)],
        )
        gini = normalize_threshold(features.gini_supply, 0.35, 0.9, missing_value=0.35)
        dev_cluster = normalize_threshold(features.dev_cluster_share, 0.05, 0.65, missing_value=0.25)
        distribution = clamp01((0.35 * top1) + (0.35 * top10) + (0.15 * gini) + (0.15 * dev_cluster))
        if (features.holder_count_total or 0) < 50:
            uncertainty_flags.append("holder_count_low")

        liq_total = normalize_inverse_log_scale(
            features.liquidity_usd_total,
            min_value=250,
            max_value=1_000_000,
            missing_value=0.65,
        )
        liq_largest = normalize_inverse_log_scale(
            features.largest_pool_liquidity_usd,
            min_value=250,
            max_value=1_000_000,
            missing_value=0.65,
        )
        lp_missing = 1.0 if features.lp_lock_detected is None else 0.0
        lp_owner_deployer = normalize_bool(features.lp_owner_is_deployer, missing_value=0.0)
        low_pool_count = normalize_threshold(features.pool_count, 1, 4, invert=True, missing_value=1.0)
        liquidity = clamp01(
            (0.55 * liq_total)
            + (0.15 * liq_largest)
            + (0.10 * lp_missing)
            + (0.10 * lp_owner_deployer)
            + (0.10 * low_pool_count)
        )

        young_market = normalize_threshold(features.market_age_seconds, 3 * 86400, 180 * 86400, invert=True, missing_value=0.65)
        low_volume = normalize_inverse_log_scale(features.volume_24h_usd, 5_000, 2_000_000, missing_value=0.65)
        missing_market_cap = 1.0 if features.market_cap_usd is None else 0.0
        low_dex_coverage = normalize_threshold(features.dex_count, 1, 3, invert=True, missing_value=1.0)
        unknown_project = 1.0 if not features.known_project_flag else 0.0
        market = clamp01(
            (0.35 * young_market)
            + (0.20 * low_volume)
            + (0.20 * missing_market_cap)
            + (0.10 * low_dex_coverage)
            + (0.15 * unknown_project)
        )

        buyer50 = normalize_threshold(features.first_50_buyers_cluster_ratio, 0.15, 0.85, missing_value=0.35)
        buyer100 = normalize_threshold(features.first_100_buyers_cluster_ratio, 0.20, 0.90, missing_value=0.35)
        early_sell = normalize_threshold(features.early_sell_ratio, 0.10, 0.90, missing_value=0.35)
        suspicious_graph = normalize_threshold(features.suspicious_funding_graph_score, 0.10, 0.90, missing_value=0.35)
        behaviour = clamp01(
            (0.30 * buyer50)
            + (0.20 * buyer100)
            + (0.20 * dev_cluster)
            + (0.15 * early_sell)
            + (0.15 * suspicious_graph)
        )

        stale_data = normalize_threshold(features.stale_data_seconds, 60, 3 * 3600, missing_value=0.25)
        low_source_count = normalize_threshold(features.source_count, 1, 4, invert=True, missing_value=0.6)
        data_quality = clamp01(
            (0.35 * clamp01(features.metadata_conflict_score))
            + (0.20 * normalize_bool(features.partial_holder_coverage, missing_value=0.0))
            + (0.20 * normalize_bool(features.missing_market_profile, missing_value=0.0))
            + (0.15 * stale_data)
            + (0.10 * low_source_count)
        )

        authority_score = _to_score(authority)
        distribution_score = _to_score(distribution)
        liquidity_score = _to_score(liquidity)
        market_score = _to_score(market)
        behaviour_score = _to_score(behaviour)
        data_quality_score = _to_score(data_quality)

        rule_score = (
            (0.22 * authority_score)
            + (0.20 * distribution_score)
            + (0.20 * liquidity_score)
            + (0.13 * market_score)
            + (0.20 * behaviour_score)
            + (0.05 * data_quality_score)
        )

        if features.mint_authority_enabled:
            findings.append(
                ScoreContributor(
                    code="mint_authority_enabled",
                    severity="high",
                    title="Mint authority still enabled",
                    description="Onchain mint authority can still change token supply.",
                    impact=0.14,
                )
            )
        if features.top_10_holder_share is not None and features.top_10_holder_share >= 0.8:
            findings.append(
                ScoreContributor(
                    code="top10_concentration",
                    severity="high",
                    title="Top-10 holders are highly concentrated",
                    description="Large concentration of supply increases manipulation risk.",
                    impact=0.12,
                )
            )
        if (features.liquidity_usd_total or 0.0) < 20_000:
            findings.append(
                ScoreContributor(
                    code="low_liquidity",
                    severity="medium",
                    title="Low liquidity depth",
                    description="Thin liquidity can amplify slippage and exit risk.",
                    impact=0.10,
                )
            )
        if features.insider_wallet_detected:
            findings.append(
                ScoreContributor(
                    code="insider_wallet_detected",
                    severity="high",
                    title="Insider wallet activity detected",
                    description="Wallet activity matches suspicious insider patterns.",
                    impact=0.11,
                )
            )
        elif features.suspicious_funding_graph_score >= 0.60:
            findings.append(
                ScoreContributor(
                    code="suspicious_early_wallet_pattern",
                    severity="high",
                    title="Suspicious early wallet pattern",
                    description="Early holder clustering and liquidity profile indicate coordinated behavior.",
                    impact=0.10,
                )
            )

        if not findings:
            findings.append(
                ScoreContributor(
                    code="no_critical_signal",
                    severity="low",
                    title="No critical live signal detected",
                    description="Current scan did not detect a strong exploit pattern.",
                    impact=0.02,
                )
            )

        return RuleEngineOutput(
            rule_score=round(rule_score, 2),
            category_scores=ScoreCategoryScores(
                technical_risk=authority_score,
                distribution_risk=distribution_score,
                market_execution_risk=liquidity_score,
                market_maturity=_to_score(1.0 - market),
                behaviour_risk=behaviour_score,
                liquidity_rug_component=_to_score(
                    clamp01((0.60 * lp_owner_deployer) + (0.40 * normalize_bool(features.lp_lock_detected is False, missing_value=0.0)))
                ),
            ),
            findings=sorted(findings, key=lambda item: item.impact, reverse=True),
            uncertainty_flags=uncertainty_flags,
        )
