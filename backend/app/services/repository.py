from __future__ import annotations

from datetime import datetime
import sys

from ..config import get_settings
from ..schemas import (
    CheckOverview,
    CopycatStatus,
    EntityType,
    LaunchFeedItem,
    MetricItem,
    ReviewQueueItem,
    RiskFactor,
    TradeCautionDimensions,
    TradeCautionOverview,
    WatchlistItem,
)
from .dexscreener import DexScreenerClient, extract_token_profile, pick_most_liquid_pair
from .analyzer import generate_report, normalize_entity_id, relative_time, risk_status, utc_now
from .solana_rpc import SolanaRpcClient

settings = get_settings()


class ReportRepository:
    def __init__(
        self,
        rpc_client: SolanaRpcClient | None = None,
        token_holders_max_pages: int = 25,
        dexscreener_client: DexScreenerClient | None = None,
    ) -> None:
        self.reports: dict[str, CheckOverview] = {}
        self.entity_index: dict[tuple[EntityType, str], list[str]] = {}
        self.rpc_client = rpc_client
        self.token_holders_max_pages = token_holders_max_pages
        self.dexscreener_client = dexscreener_client
        self.live_feed_last_sync_at: datetime | None = None
        self.seed_data()

    def register_report(self, report: CheckOverview) -> CheckOverview:
        self.reports[report.id] = report
        index_key = (report.entity_type, report.entity_id)
        self.entity_index.setdefault(index_key, []).append(report.id)
        return report

    def create_report(self, entity_type: EntityType, raw_value: str) -> CheckOverview:
        entity_id = normalize_entity_id(entity_type, raw_value)
        index_key = (entity_type, entity_id)
        version = len(self.entity_index.get(index_key, []))
        report = generate_report(
            entity_type,
            raw_value,
            version=version,
            rpc_client=self.rpc_client,
            token_holders_max_pages=self.token_holders_max_pages,
            dexscreener_client=self.dexscreener_client,
        )
        return self.register_report(report)

    def latest_reports(self) -> list[CheckOverview]:
        return sorted(self.reports.values(), key=lambda item: item.created_at, reverse=True)

    def get_report(self, check_id: str) -> CheckOverview | None:
        report = self.reports.get(check_id)
        if report is None:
            return None
        report.refreshed_at = relative_time(report.created_at)
        return report

    def latest_report_for_entity(self, entity_type: EntityType, entity_id: str) -> CheckOverview | None:
        normalized_entity_id = normalize_entity_id(entity_type, entity_id)
        report_ids = self.entity_index.get((entity_type, normalized_entity_id), [])
        if not report_ids:
            return None
        return self.get_report(report_ids[-1])

    def has_entity(self, entity_type: EntityType, entity_id: str) -> bool:
        normalized = normalize_entity_id(entity_type, entity_id)
        return bool(self.entity_index.get((entity_type, normalized)))

    def build_watchlist_items(self) -> list[WatchlistItem]:
        items: list[WatchlistItem] = []
        for report in self.latest_reports()[:6]:
            delta = f"score {report.score} / confidence {report.confidence:.2f}"
            items.append(
                WatchlistItem(
                    name=report.display_name,
                    delta=delta,
                    state=report.review_state,
                )
            )
        return items

    def build_review_queue_items(self) -> list[ReviewQueueItem]:
        queue: list[ReviewQueueItem] = []
        for report in self.latest_reports():
            if report.status not in {"high", "critical"}:
                continue
            queue.append(
                ReviewQueueItem(
                    id=report.id,
                    display_name=report.display_name,
                    entity_type=report.entity_type,
                    severity=report.status,
                    score=report.score,
                    owner="unassigned" if report.status == "high" else "risk-team",
                    updated_at=report.refreshed_at,
                )
            )
        return queue[:12]

    def build_launch_feed_items(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
        tab: str = "new",
        sort: str = "newest",
        age: str = "all",
        liquidity: str = "all",
        copycat_only: bool = False,
        query: str = "",
    ) -> tuple[list[LaunchFeedItem], str | None]:
        self._maybe_sync_live_launch_source()
        token_reports = [report for report in self.latest_reports() if report.entity_type == "token"]
        symbol_counts: dict[str, int] = {}
        name_counts: dict[str, int] = {}

        for report in token_reports:
            symbol = (report.symbol or report.display_name.split("/")[0].strip()).upper()
            name = (report.name or report.display_name).strip().lower()
            if symbol:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            if name:
                name_counts[name] = name_counts.get(name, 0) + 1

        items: list[LaunchFeedItem] = []
        now = utc_now()
        for report in token_reports:
            age_minutes = max(0, int((now - report.created_at).total_seconds() // 60))
            liquidity_value = 0.0
            market_cap_value = 0.0
            for metric in report.metrics:
                if metric.label == "Liquidity":
                    liquidity_value = _parse_money_value(metric.value)
                elif metric.label in {"Supply", "Market Cap"}:
                    market_cap_value = _parse_compact_number(metric.value)

            symbol = (report.symbol or report.display_name.split("/")[0].strip()).upper()
            name = (report.name or report.display_name).strip()
            launch_quality = _derive_launch_quality(report)
            copycat_status: CopycatStatus = "none"
            if symbol and symbol_counts.get(symbol, 0) > 1:
                copycat_status = "collision"
            elif name and name_counts.get(name.lower(), 0) > 1:
                copycat_status = "collision"
            elif any(factor.code == "TOKEN_METADATA_MISMATCH" for factor in report.risk_increasers):
                copycat_status = "possible"

            items.append(
                LaunchFeedItem(
                    mint=report.entity_id,
                    report_id=report.id,
                    name=name,
                    symbol=symbol,
                    logo_url=report.logo_url,
                    age_minutes=age_minutes,
                    liquidity_usd=liquidity_value,
                    market_cap_usd=market_cap_value,
                    rug_probability=report.rug_probability,
                    rug_risk_level=report.status,
                    trade_caution_level=(report.trade_caution.level if report.trade_caution else "moderate"),
                    launch_quality=launch_quality,
                    copycat_status=copycat_status,
                    updated_at=report.created_at,
                    initial_live_estimate=_is_initial_live_estimate(report),
                    summary=report.summary,
                    rug_risk_drivers=[factor.label for factor in report.risk_increasers[:2]],
                    trade_caution_drivers=(report.trade_caution.drivers[:3] if report.trade_caution else []),
                    top_reducer=(report.risk_reducers[0].label if report.risk_reducers else None),
                    deployer_short_address=_shorten_address(report.entity_id),
                )
            )
        filtered = _filter_launch_feed_items(
            items,
            tab=tab,
            sort=sort,
            age=age,
            liquidity=liquidity,
            copycat_only=copycat_only,
            query=query,
        )
        offset = _parse_cursor(cursor)
        page = filtered[offset : offset + limit]
        next_cursor = str(offset + limit) if offset + limit < len(filtered) else None
        return page, next_cursor

    def _maybe_sync_live_launch_source(self) -> None:
        if not settings.feed_live_source_enabled or self.dexscreener_client is None:
            return
        if "unittest" in sys.modules:
            return

        now = utc_now()
        if (
            self.live_feed_last_sync_at is not None
            and int((now - self.live_feed_last_sync_at).total_seconds()) < settings.feed_live_sync_ttl_seconds
        ):
            return

        self.live_feed_last_sync_at = now

        try:
            profiles = self.dexscreener_client.get_latest_token_profiles()
        except Exception:
            return

        created = 0
        for profile in profiles:
            if created >= settings.feed_live_profiles_limit:
                break
            if str(profile.get("chainId") or "").lower() != "solana":
                continue
            token_address = str(profile.get("tokenAddress") or "").strip()
            if not token_address or self.has_entity("token", token_address):
                continue
            try:
                live_name: str | None = None
                live_symbol: str | None = None
                live_logo = str(profile.get("icon") or "") or None
                live_liquidity = 0.0
                live_market_cap = 0.0
                live_created_at: datetime | None = None
                try:
                    pairs = self.dexscreener_client.get_token_pairs("solana", token_address)
                    pair = pick_most_liquid_pair(pairs)
                    if pair is not None:
                        pair_name, pair_symbol, pair_logo = extract_token_profile(pair, token_address)
                        live_name = pair_name
                        live_symbol = pair_symbol
                        if pair_logo:
                            live_logo = pair_logo
                        live_liquidity = float((pair.get("liquidity") or {}).get("usd") or 0.0)
                        live_market_cap = float(pair.get("marketCap") or pair.get("fdv") or 0.0)
                        pair_created_at = pair.get("pairCreatedAt")
                        if pair_created_at:
                            live_created_at = datetime.fromtimestamp(float(pair_created_at) / 1000, tz=now.tzinfo)
                except Exception:
                    pass

                version = len(self.entity_index.get(("token", normalize_entity_id("token", token_address)), []))
                report = generate_report(
                    "token",
                    token_address,
                    version=version,
                    forced_name=live_name or f"Live launch / {token_address[:4]}...{token_address[-4:]}",
                    rpc_client=self.rpc_client,
                    live_token_analysis=False,
                    token_holders_max_pages=min(self.token_holders_max_pages, 1),
                    dexscreener_client=self.dexscreener_client,
                )
                report.name = live_name
                report.symbol = live_symbol
                report.logo_url = live_logo
                if live_created_at is not None:
                    report.created_at = live_created_at
                if live_liquidity > 0:
                    report.liquidity = _format_money_value(live_liquidity)
                _upsert_metric(report, "Liquidity", report.liquidity)
                if live_market_cap > 0:
                    _upsert_metric(report, "Market Cap", _format_compact_value(live_market_cap))
                _apply_live_feed_risk_overrides(report, profile, live_liquidity, live_market_cap, live_created_at, now)
                self.register_report(report)
            except Exception:
                continue
            created += 1

    def seed_data(self) -> None:
        now = utc_now()
        seeds = [
            (
                "token",
                "9xQeWvG816bUx9EPfEZLQ7ZL8A6V7zVYhWf9e7s6PzF1",
                "pearl-token",
                "PEARL / Solana meme token",
                now,
            ),
            (
                "token",
                "LinkhB3afbBKb2EQQu7s7umdZceV3wcvAUJhQAfQ23L",
                "chainlink-feed",
                "LINK / Chainlink",
                now.replace(minute=max(0, now.minute - 8)),
            ),
            (
                "token",
                "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                "bonk-feed",
                "BONK / Bonk",
                now.replace(minute=max(0, now.minute - 18)),
            ),
            (
                "token",
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "usdc-feed",
                "USDC / USD Coin",
                now.replace(minute=max(0, now.minute - 33)),
            ),
            (
                "token",
                "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E",
                "btc-feed",
                "BTC / Wrapped BTC",
                now.replace(hour=max(0, now.hour - 2)),
            ),
            (
                "token",
                "SC4MX7Q1nA111111111111111111111111111111111",
                "scamx-feed",
                "SCAMX / Scam X",
                now.replace(minute=max(0, now.minute - 5)),
            ),
            (
                "token",
                "RUGD11111111111111111111111111111111111111",
                "rugged-feed",
                "RUGD / Recently Rugged",
                now.replace(minute=max(0, now.minute - 3)),
            ),
            (
                "wallet",
                "8PX1DbLyJQzY63K5kTz2S88xJ5UQh1dBnmfV91rYx4cR",
                "wallet-alpha",
                "Wallet / 8PX1...x4cR",
                now.replace(minute=max(0, now.minute - 12)),
            ),
            (
                "project",
                "orbit-project.io",
                "project-orbit",
                "Orbit Project",
                now.replace(hour=max(0, now.hour - 1)),
            ),
        ]

        for entity_type, raw_value, report_id, name, created_at in seeds:
            report = generate_report(
                entity_type,
                raw_value,
                forced_id=report_id,
                forced_name=name,
                created_at=created_at,
                rpc_client=self.rpc_client,
                live_token_analysis=False,
                token_holders_max_pages=self.token_holders_max_pages,
                dexscreener_client=self.dexscreener_client,
            )
            if report_id == "rugged-feed":
                report.status = "critical"
                report.score = 92
                report.rug_probability = 92
                report.summary = "Multiple scam-linked and post-launch failure signals were detected."
                report.review_state = "Escalated"
                report.risk_increasers = [
                    RiskFactor(
                        code="RUGGED_RECENT_COLLAPSE",
                        severity="high",
                        label="Recent rug-like collapse detected",
                        explanation="Recent activity and onchain signals are consistent with a failed launch.",
                        weight=30,
                    ),
                    RiskFactor(
                        code="RUGGED_EXIT_PATTERN",
                        severity="high",
                        label="Coordinated exits observed",
                        explanation="Linked wallets exited around the same window as market deterioration.",
                        weight=24,
                    ),
                ]
                report.factors = list(report.risk_increasers)
                report.trade_caution = TradeCautionOverview(
                    score=96,
                    level="avoid",
                    label="Avoid",
                    summary="Trading conditions are severely impaired after a recent collapse event.",
                    drivers=["Recent rug-like collapse detected", "Coordinated exits observed", "Thin liquidity"],
                    dimensions=TradeCautionDimensions(
                        admin_caution=82,
                        execution_caution=94,
                        concentration_caution=88,
                        behavioural_caution=96,
                        market_structure_strength=8,
                    ),
                )
            self.register_report(report)


def _parse_money_value(value: str) -> float:
    normalized = value.strip().replace("$", "").replace(",", "")
    if not normalized or normalized == "n/a":
        return 0.0
    multiplier = 1.0
    if normalized.endswith("K"):
        multiplier = 1_000.0
        normalized = normalized[:-1]
    elif normalized.endswith("M"):
        multiplier = 1_000_000.0
        normalized = normalized[:-1]
    elif normalized.endswith("B"):
        multiplier = 1_000_000_000.0
        normalized = normalized[:-1]
    try:
        return float(normalized) * multiplier
    except ValueError:
        return 0.0


def _format_money_value(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.0f}"


def _parse_compact_number(value: str) -> float:
    normalized = value.strip().replace(",", "")
    if not normalized or normalized == "n/a":
        return 0.0
    multiplier = 1.0
    if normalized.endswith("K"):
        multiplier = 1_000.0
        normalized = normalized[:-1]
    elif normalized.endswith("M"):
        multiplier = 1_000_000.0
        normalized = normalized[:-1]
    elif normalized.endswith("B"):
        multiplier = 1_000_000_000.0
        normalized = normalized[:-1]
    try:
        return float(normalized) * multiplier
    except ValueError:
        return 0.0


def _format_compact_value(value: float) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:.0f}"


def _upsert_metric(report: CheckOverview, label: str, value: str) -> None:
    for metric in report.metrics:
        if metric.label == label:
            metric.value = value
            return
    report.metrics.append(MetricItem(label=label, value=value))


def _is_initial_live_estimate(report: CheckOverview) -> bool:
    return report.summary.startswith("Live DexScreener launch profile detected.")


def _apply_live_feed_risk_overrides(
    report: CheckOverview,
    profile: dict,
    liquidity_usd: float,
    market_cap_usd: float,
    created_at: datetime | None,
    now: datetime,
) -> None:
    age_minutes = max(0, int((now - created_at).total_seconds() // 60)) if created_at is not None else 0
    links = profile.get("links") or []
    has_socials = len(links) > 0

    rug_probability = 12
    if age_minutes <= 15:
        rug_probability += 8
    if liquidity_usd < 5_000:
        rug_probability += 14
    elif liquidity_usd < 20_000:
        rug_probability += 8
    if market_cap_usd > 0 and liquidity_usd > 0 and market_cap_usd / max(liquidity_usd, 1.0) >= 8:
        rug_probability += 10
    if not has_socials:
        rug_probability += 6
    rug_probability = min(rug_probability, 58)

    admin_caution = 18
    execution_caution = 22
    concentration_caution = 16
    behavioural_caution = 14
    market_structure_strength = 8

    if age_minutes <= 15:
        execution_caution += 18
        market_structure_strength = max(4, market_structure_strength - 3)
    elif age_minutes <= 60:
        execution_caution += 10
        market_structure_strength += 4
    else:
        market_structure_strength += 10

    if liquidity_usd < 5_000:
        execution_caution += 38
    elif liquidity_usd < 20_000:
        execution_caution += 24
    elif liquidity_usd < 50_000:
        execution_caution += 10

    if market_cap_usd < 25_000:
        concentration_caution += 16
    elif market_cap_usd < 100_000:
        concentration_caution += 8
    else:
        market_structure_strength += 6

    if not has_socials:
        behavioural_caution += 8
    else:
        market_structure_strength += 6

    trade_caution_score = max(
        0,
        min(
            100,
            int(
                (0.25 * admin_caution)
                + (0.35 * execution_caution)
                + (0.20 * concentration_caution)
                + (0.20 * behavioural_caution)
                - (0.15 * market_structure_strength)
            ),
        ),
    )
    if trade_caution_score >= 75:
        caution_level = "avoid"
        caution_label = "Avoid"
    elif trade_caution_score >= 50:
        caution_level = "high"
        caution_label = "High caution"
    elif trade_caution_score >= 25:
        caution_level = "moderate"
        caution_label = "Moderate caution"
    else:
        caution_level = "low"
        caution_label = "Low caution"

    rug_drivers: list[RiskFactor] = []
    caution_drivers: list[str] = []

    if age_minutes <= 60:
        rug_drivers.append(
            RiskFactor(
                code="LIVE_PROFILE_FRESH_MARKET",
                severity="medium",
                label="Very young live market",
                explanation="The token has a newly detected market with limited history.",
                weight=10,
            )
        )
        caution_drivers.append("Very young market")
    if liquidity_usd < 20_000:
        rug_drivers.append(
            RiskFactor(
                code="LIVE_PROFILE_THIN_LIQUIDITY",
                severity="medium" if liquidity_usd >= 5_000 else "high",
                label="Thin launch liquidity",
                explanation="Current liquidity is shallow for a newly discovered launch.",
                weight=16 if liquidity_usd < 5_000 else 10,
            )
        )
        caution_drivers.append("Thin launch liquidity")
    if market_cap_usd > 0 and liquidity_usd > 0 and market_cap_usd / max(liquidity_usd, 1.0) >= 8:
        rug_drivers.append(
            RiskFactor(
                code="LIVE_PROFILE_HIGH_FDV_RATIO",
                severity="medium",
                label="High market-cap to liquidity ratio",
                explanation="Market capitalization appears elevated relative to current pool depth.",
                weight=12,
            )
        )
        caution_drivers.append("High market-cap to liquidity ratio")
    if not has_socials:
        caution_drivers.append("Limited social footprint")

    if not rug_drivers:
        rug_drivers.append(
            RiskFactor(
                code="LIVE_PROFILE_LIMITED_DATA",
                severity="low",
                label="Limited launch data",
                explanation="The token is newly detected and still has a shallow discovery profile.",
                weight=6,
            )
        )

    report.rug_probability = rug_probability
    report.score = rug_probability
    report.status = risk_status(rug_probability)
    report.factors = list(rug_drivers)
    report.risk_increasers = list(rug_drivers)
    report.risk_reducers = []
    report.trade_caution = TradeCautionOverview(
        score=trade_caution_score,
        level=caution_level,
        label=caution_label,
        summary=(
            "Live launch profile has limited history. "
            "Current trading conditions should be treated cautiously until a deeper report is generated."
        ),
        drivers=caution_drivers or ["Limited launch history"],
        dimensions=TradeCautionDimensions(
            admin_caution=admin_caution,
            execution_caution=execution_caution,
            concentration_caution=concentration_caution,
            behavioural_caution=behavioural_caution,
            market_structure_strength=market_structure_strength,
        ),
    )
    report.summary = (
        "Live DexScreener launch profile detected. "
        "This is an initial lightweight verdict based on launch age, liquidity, and market structure."
    )


def _derive_launch_quality(report: CheckOverview) -> str:
    behaviour = report.behaviour_analysis_v2
    if behaviour is None:
        return "unknown"
    modules = behaviour.modules
    early = modules.get("early_buyers")
    liquidity = modules.get("liquidity_management")
    insider = modules.get("insider_selling")
    developer = modules.get("developer_cluster")
    if early and early.status == "flagged" and liquidity and liquidity.status == "flagged":
        return "likely_wash"
    if (early and early.status == "flagged") or (developer and developer.status == "flagged"):
        return "coordinated"
    if (liquidity and liquidity.status in {"watch", "flagged"}) or (insider and insider.status == "watch"):
        return "noisy"
    return "organic"


def _shorten_address(value: str) -> str | None:
    trimmed = value.strip()
    if len(trimmed) < 10:
        return None
    return f"{trimmed[:4]}...{trimmed[-4:]}"


def _filter_launch_feed_items(
    items: list[LaunchFeedItem],
    *,
    tab: str,
    sort: str,
    age: str,
    liquidity: str,
    copycat_only: bool,
    query: str,
) -> list[LaunchFeedItem]:
    filtered = list(items)

    if tab == "high-rug":
        filtered = [item for item in filtered if item.rug_risk_level in {"high", "critical"}]
    elif tab == "high-caution":
        filtered = [item for item in filtered if item.trade_caution_level in {"high", "avoid"}]
    elif tab == "coordinated":
        filtered = [item for item in filtered if item.launch_quality in {"coordinated", "likely_wash"}]
    elif tab == "copycats":
        filtered = [item for item in filtered if item.copycat_status != "none"]
    elif tab == "recently-rugged":
        filtered = [
            item
            for item in filtered
            if item.rug_risk_level in {"high", "critical"} and item.age_minutes <= 1440
        ]

    if age == "10m":
        filtered = [item for item in filtered if item.age_minutes < 10]
    elif age == "1h":
        filtered = [item for item in filtered if item.age_minutes < 60]
    elif age == "24h":
        filtered = [item for item in filtered if item.age_minutes < 1440]

    if liquidity == "lt1k":
        filtered = [item for item in filtered if item.liquidity_usd < 1_000]
    elif liquidity == "1k-5k":
        filtered = [item for item in filtered if 1_000 <= item.liquidity_usd < 5_000]
    elif liquidity == "5k-20k":
        filtered = [item for item in filtered if 5_000 <= item.liquidity_usd < 20_000]
    elif liquidity == "gte20k":
        filtered = [item for item in filtered if item.liquidity_usd >= 20_000]

    if copycat_only:
        filtered = [item for item in filtered if item.copycat_status != "none"]

    normalized_query = query.strip().lower()
    if normalized_query:
        filtered = [
            item
            for item in filtered
            if normalized_query in item.name.lower()
            or normalized_query in item.symbol.lower()
            or normalized_query in item.mint.lower()
        ]

    if sort == "highest-rug":
        filtered.sort(key=lambda item: item.rug_probability, reverse=True)
    elif sort == "highest-caution":
        caution_rank = {"low": 0, "moderate": 1, "high": 2, "avoid": 3}
        filtered.sort(key=lambda item: caution_rank[item.trade_caution_level], reverse=True)
    elif sort == "highest-liquidity":
        filtered.sort(key=lambda item: item.liquidity_usd, reverse=True)
    elif sort == "highest-market-cap":
        filtered.sort(key=lambda item: item.market_cap_usd, reverse=True)
    else:
        filtered.sort(key=lambda item: item.age_minutes)

    return filtered


def _parse_cursor(value: str | None) -> int:
    if not value:
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
