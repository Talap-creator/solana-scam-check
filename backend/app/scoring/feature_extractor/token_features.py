from __future__ import annotations

import re
from datetime import UTC, datetime

from ...schemas import CheckOverview
from ..schemas import TokenFeatureSchema


def _parse_percent(value: str | None) -> float | None:
    if not value:
        return None
    text = value.strip().lower()
    if text in {"n/a", "na", "unknown", "unavailable from rpc"}:
        return None
    if text.startswith("<"):
        number = text[1:].replace("%", "").strip()
        try:
            return max(0.0, float(number) / 100.0)
        except ValueError:
            return 0.001
    cleaned = text.replace("%", "").strip()
    try:
        return max(0.0, min(1.0, float(cleaned) / 100.0))
    except ValueError:
        return None


def _parse_money(value: str | None) -> float | None:
    if not value:
        return None
    text = value.strip().upper()
    if text in {"N/A", "NA", "UNKNOWN"}:
        return None
    if text.startswith("$"):
        text = text[1:]
    multiplier = 1.0
    if text.endswith("K"):
        multiplier = 1_000.0
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000.0
        text = text[:-1]
    elif text.endswith("B"):
        multiplier = 1_000_000_000.0
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def _parse_amount(value: str | None) -> float:
    if not value:
        return 0.0
    text = value.strip().upper()
    multiplier = 1.0
    if text.endswith("K"):
        multiplier = 1_000.0
        text = text[:-1]
    elif text.endswith("M"):
        multiplier = 1_000_000.0
        text = text[:-1]
    elif text.endswith("B"):
        multiplier = 1_000_000_000.0
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return 0.0


def _market_age_to_seconds(value: str | None) -> int | None:
    if not value:
        return None
    text = value.strip().lower()
    if text in {"unknown", "n/a"}:
        return None
    if text.startswith("<1 day"):
        return 12 * 3600
    match = re.match(r"^(\d+)\s+(day|days|month|months|year|years)$", text)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("day"):
        return amount * 86400
    if unit.startswith("month"):
        return amount * 30 * 86400
    return amount * 365 * 86400


def _metric_value(report: CheckOverview, label: str) -> str | None:
    for metric in report.metrics:
        if metric.label.lower() == label.lower():
            return metric.value
    return None


def _timeline_value(report: CheckOverview, label: str) -> str | None:
    for event in report.timeline:
        if event.label.lower() == label.lower():
            return event.value
    return None


class TokenFeatureExtractor:
    feature_version = "features_v1"

    def from_report(self, report: CheckOverview) -> TokenFeatureSchema:
        market_age_text = _metric_value(report, "Market age")
        liquidity_source = _timeline_value(report, "Liquidity source") or ""
        top10 = _parse_percent(report.top_holder_share)
        top1 = _parse_percent(_metric_value(report, "Largest holder"))
        supply_total = _parse_amount(_metric_value(report, "Supply"))
        liquidity_total = _parse_money(report.liquidity)
        market_age_seconds = _market_age_to_seconds(market_age_text)
        market_age_days = int(market_age_seconds / 86400) if market_age_seconds is not None else None
        now = datetime.now(UTC)
        age_seconds = int((now - report.created_at).total_seconds()) if report.created_at else None

        metadata_conflict = any(item.code == "TOKEN_METADATA_MISMATCH" for item in report.factors)
        missing_profile = any(item.code == "TOKEN_NO_MARKET_PROFILE" for item in report.factors)
        partial_holder = any(item.code == "TOKEN_PARTIAL_HOLDER_COVERAGE" for item in report.factors)

        listed_on_known_aggregator = "dex screener" in liquidity_source.lower()
        source_count = 1
        if listed_on_known_aggregator:
            source_count += 1
        if report.name or report.symbol:
            source_count += 1
        if top10 is not None:
            source_count += 1

        suspicious_pattern_score = 0.0
        if market_age_days is not None and market_age_days <= 7:
            if (top1 or 0.0) >= 0.20:
                suspicious_pattern_score += 0.45
            if (top10 or 0.0) >= 0.70:
                suspicious_pattern_score += 0.30
            if (liquidity_total or 0.0) <= 100_000:
                suspicious_pattern_score += 0.25
        suspicious_pattern_score = min(1.0, suspicious_pattern_score)
        dev_cluster_share = min(1.0, (top1 or 0.0) * 0.65) if suspicious_pattern_score > 0 else 0.0
        insider_wallet_detected = suspicious_pattern_score >= 0.75

        return TokenFeatureSchema(
            token_address=report.entity_id,
            token_name=report.name,
            symbol=report.symbol,
            decimals=int(_metric_value(report, "Decimals") or 0),
            supply_total=supply_total,
            token_age_seconds=age_seconds,
            market_age_seconds=market_age_seconds,
            first_seen_at=report.created_at,
            mint_authority_enabled=(_timeline_value(report, "Mint authority") or "").lower() == "enabled",
            freeze_authority_enabled=(_timeline_value(report, "Freeze authority") or "").lower() == "enabled",
            update_authority_enabled=None,
            authority_count=0,
            top_1_holder_share=top1,
            top_5_holder_share=None,
            top_10_holder_share=top10,
            top_20_holder_share=None,
            gini_supply=min(1.0, (top10 or 0.0) * 0.95) if top10 is not None else None,
            herfindahl_index=min(1.0, (top1 or 0.0) * 0.9) if top1 is not None else None,
            largest_holder_is_lp=False,
            holder_count_total=None,
            holder_count_verified=None,
            holder_coverage_ratio=0.5 if partial_holder else 0.9 if top10 is not None else 0.3,
            liquidity_usd_total=liquidity_total,
            largest_pool_liquidity_usd=liquidity_total,
            pool_count=1 if liquidity_total else 0,
            dex_count=1 if listed_on_known_aggregator else 0,
            lp_lock_detected=None,
            lp_lock_duration_seconds=None,
            lp_owner_is_deployer=None,
            liquidity_to_market_cap_ratio=None,
            liquidity_change_1h_pct=None,
            liquidity_change_24h_pct=None,
            volume_1h_usd=None,
            volume_24h_usd=None,
            trade_count_1h=None,
            trade_count_24h=None,
            price_change_1h_pct=None,
            price_change_24h_pct=None,
            market_cap_usd=None,
            fdv_usd=None,
            listed_on_known_aggregator=listed_on_known_aggregator,
            listed_on_major_cex=False,
            known_project_flag=False,
            first_50_buyers_cluster_ratio=0.0,
            first_100_buyers_cluster_ratio=0.0,
            dev_cluster_share=dev_cluster_share,
            dev_cluster_wallet_count=0,
            early_sell_ratio=0.0,
            insider_wallet_detected=insider_wallet_detected,
            suspicious_funding_graph_score=suspicious_pattern_score,
            repeated_wallet_pattern_score=suspicious_pattern_score,
            wash_trade_score=0.0,
            deployer_wallet_age_days=None,
            deployer_tx_count=None,
            deployer_previous_token_count=None,
            deployer_previous_rug_count=None,
            linked_cluster_previous_token_count=None,
            linked_cluster_previous_rug_count=None,
            deployer_reputation_score=None,
            cluster_reputation_score=None,
            transfer_tax_modifiable=None,
            blacklist_function_detected=None,
            pause_function_detected=None,
            mint_after_launch_detected=False,
            honeypot_simulation_failed=False,
            metadata_conflict_score=0.75 if metadata_conflict else 0.0,
            missing_market_profile=missing_profile,
            partial_holder_coverage=partial_holder,
            stale_data_seconds=max(0, age_seconds or 0),
            source_count=source_count,
        )
