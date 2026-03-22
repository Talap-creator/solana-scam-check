from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import sys

from sqlalchemy.exc import SQLAlchemyError

from .. import models
from ..config import get_settings
from ..db import SessionLocal
from ..schemas import (
    CheckOverview,
    CopycatStatus,
    DeveloperOperatorItem,
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

    def register_report(self, report: CheckOverview, *, persist: bool = True) -> CheckOverview:
        self.reports[report.id] = report
        index_key = (report.entity_type, report.entity_id)
        self.entity_index.setdefault(index_key, []).append(report.id)
        if persist:
            self._persist_check_report(report)
            if report.entity_type == "token":
                self._persist_launch_feed_reports([report])
                self._persist_developer_operator_reports([report])
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
            report = self._rehydrate_persisted_check_report(check_id=check_id)
            if report is None:
                report = self._rehydrate_persisted_launch_report(check_id=check_id)
            if report is None:
                return None
        report.refreshed_at = relative_time(report.created_at)
        return report

    def latest_report_for_entity(self, entity_type: EntityType, entity_id: str) -> CheckOverview | None:
        normalized_entity_id = normalize_entity_id(entity_type, entity_id)
        report_ids = self.entity_index.get((entity_type, normalized_entity_id), [])
        if not report_ids:
            persisted = self._latest_persisted_check_report(entity_type=entity_type, entity_id=normalized_entity_id)
            if persisted is not None:
                return persisted
            if entity_type != "token":
                return None
            return self._rehydrate_persisted_launch_report(mint=normalized_entity_id)
        return self.get_report(report_ids[-1])

    def has_entity(self, entity_type: EntityType, entity_id: str) -> bool:
        normalized = normalize_entity_id(entity_type, entity_id)
        if self.entity_index.get((entity_type, normalized)):
            return True
        try:
            with SessionLocal() as db:
                persisted = (
                    db.query(models.PersistedCheckReport.report_id)
                    .filter(
                        models.PersistedCheckReport.entity_type == entity_type,
                        models.PersistedCheckReport.entity_id == normalized,
                    )
                    .first()
                )
                if persisted is not None:
                    return True
                if entity_type != "token":
                    return False
                return db.get(models.LaunchFeedToken, normalized) is not None
        except SQLAlchemyError:
            return False

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
        self._persist_launch_feed_reports(token_reports)
        items = self._load_persisted_launch_feed_items()
        if not items and token_reports:
            symbol_counts, name_counts = _build_launch_feed_identity_counts(token_reports)
            now = utc_now()
            items = [
                _build_launch_feed_item(report, symbol_counts, name_counts, now)
                for report in token_reports
            ]
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

    def build_developer_operator_items(self, *, limit: int = 200) -> list[DeveloperOperatorItem]:
        token_reports = [report for report in self.latest_reports() if report.entity_type == "token"]
        if token_reports:
            self._persist_developer_operator_reports(token_reports)
        items = self._load_persisted_developer_operator_items()
        return items[:limit]

    def _persist_check_report(self, report: CheckOverview) -> None:
        try:
            payload = report.model_dump(mode="json")
            with SessionLocal() as db:
                existing = db.get(models.PersistedCheckReport, report.id)
                if existing is None:
                    db.add(
                        models.PersistedCheckReport(
                            report_id=report.id,
                            entity_type=report.entity_type,
                            entity_id=report.entity_id,
                            display_name=report.display_name,
                            created_at=_coerce_utc_datetime(report.created_at),
                            persisted_at=utc_now(),
                            report_json=payload,
                        )
                    )
                else:
                    existing.entity_type = report.entity_type
                    existing.entity_id = report.entity_id
                    existing.display_name = report.display_name
                    existing.created_at = _coerce_utc_datetime(report.created_at)
                    existing.persisted_at = utc_now()
                    existing.report_json = payload
                db.commit()
        except SQLAlchemyError:
            return

    def _rehydrate_persisted_check_report(self, *, check_id: str) -> CheckOverview | None:
        try:
            with SessionLocal() as db:
                record = db.get(models.PersistedCheckReport, check_id)
        except SQLAlchemyError:
            return None

        if record is None:
            return None

        try:
            report = CheckOverview.model_validate(record.report_json)
        except Exception:
            return None

        self.register_report(report, persist=False)
        return report

    def _latest_persisted_check_report(
        self,
        *,
        entity_type: EntityType,
        entity_id: str,
    ) -> CheckOverview | None:
        try:
            with SessionLocal() as db:
                record = (
                    db.query(models.PersistedCheckReport)
                    .filter(
                        models.PersistedCheckReport.entity_type == entity_type,
                        models.PersistedCheckReport.entity_id == entity_id,
                    )
                    .order_by(models.PersistedCheckReport.created_at.desc())
                    .first()
                )
        except SQLAlchemyError:
            return None

        if record is None:
            return None

        try:
            report = CheckOverview.model_validate(record.report_json)
        except Exception:
            return None

        self.register_report(report, persist=False)
        return report

    def _persist_launch_feed_reports(self, reports: list[CheckOverview]) -> None:
        token_reports = [report for report in reports if report.entity_type == "token"]
        if not token_reports:
            return

        all_token_reports = [report for report in self.latest_reports() if report.entity_type == "token"]
        symbol_counts, name_counts = _build_launch_feed_identity_counts(all_token_reports)
        now = utc_now()

        try:
            with SessionLocal() as db:
                for report in token_reports:
                    item = _build_launch_feed_item(report, symbol_counts, name_counts, now)
                    snapshot_signature = _build_launch_feed_snapshot_signature(item)
                    existing = db.get(models.LaunchFeedToken, item.mint)
                    if existing is None:
                        db.add(
                            models.LaunchFeedToken(
                                mint=item.mint,
                                report_id=item.report_id,
                                name=item.name,
                                symbol=item.symbol,
                                logo_url=item.logo_url,
                                liquidity_usd=item.liquidity_usd,
                                market_cap_usd=item.market_cap_usd,
                                rug_probability=item.rug_probability,
                                rug_risk_level=item.rug_risk_level,
                                trade_caution_level=item.trade_caution_level,
                                launch_quality=item.launch_quality,
                                copycat_status=item.copycat_status,
                                initial_live_estimate=item.initial_live_estimate,
                                summary=item.summary,
                                rug_risk_drivers=item.rug_risk_drivers,
                                trade_caution_drivers=item.trade_caution_drivers,
                                top_reducer=item.top_reducer,
                                deployer_short_address=item.deployer_short_address,
                                report_created_at=item.updated_at,
                                first_seen_at=now,
                                last_seen_at=now,
                            )
                        )
                        _append_launch_feed_snapshot(
                            db,
                            item=item,
                            snapshot_signature=snapshot_signature,
                            observed_at=now,
                        )
                        continue

                    existing.last_seen_at = now
                    if _coerce_utc_datetime(existing.report_created_at) > _coerce_utc_datetime(item.updated_at):
                        continue

                    existing.report_id = item.report_id
                    existing.name = item.name
                    existing.symbol = item.symbol
                    existing.logo_url = item.logo_url
                    existing.liquidity_usd = item.liquidity_usd
                    existing.market_cap_usd = item.market_cap_usd
                    existing.rug_probability = item.rug_probability
                    existing.rug_risk_level = item.rug_risk_level
                    existing.trade_caution_level = item.trade_caution_level
                    existing.launch_quality = item.launch_quality
                    existing.copycat_status = item.copycat_status
                    existing.initial_live_estimate = item.initial_live_estimate
                    existing.summary = item.summary
                    existing.rug_risk_drivers = item.rug_risk_drivers
                    existing.trade_caution_drivers = item.trade_caution_drivers
                    existing.top_reducer = item.top_reducer
                    existing.deployer_short_address = item.deployer_short_address
                    existing.report_created_at = item.updated_at
                    _append_launch_feed_snapshot(
                        db,
                        item=item,
                        snapshot_signature=snapshot_signature,
                        observed_at=now,
                    )
                db.commit()
        except SQLAlchemyError:
            return

    def _load_persisted_launch_feed_items(self) -> list[LaunchFeedItem]:
        try:
            with SessionLocal() as db:
                records = (
                    db.query(models.LaunchFeedToken)
                    .order_by(models.LaunchFeedToken.report_created_at.desc())
                    .all()
                )
        except SQLAlchemyError:
            return []

        now = utc_now()
        return [_build_launch_feed_item_from_record(record, now) for record in records]

    def _persist_developer_operator_reports(self, reports: list[CheckOverview]) -> None:
        token_reports = [report for report in reports if report.entity_type == "token"]
        if not token_reports:
            return

        all_token_reports = [report for report in self.latest_reports() if report.entity_type == "token"]
        payloads = _build_developer_operator_payloads(all_token_reports)
        if not payloads:
            return

        now = utc_now()
        try:
            with SessionLocal() as db:
                for payload in payloads:
                    operator_key = str(payload["id"])
                    snapshot_signature = _build_developer_operator_snapshot_signature(payload)
                    existing = db.get(models.DeveloperOperatorProfile, operator_key)
                    if existing is None:
                        db.add(
                            models.DeveloperOperatorProfile(
                                operator_key=operator_key,
                                kind=str(payload["kind"]),
                                label=str(payload["label"]),
                                wallet_preview=str(payload["wallet_preview"]),
                                funding_source=payload.get("funding_source"),
                                unresolved=bool(payload["unresolved"]),
                                launches_count=int(payload["launches"]),
                                high_risk_launches=int(payload["high_risk_launches"]),
                                avg_rug_probability=float(payload["avg_rug_probability"]),
                                avg_trade_caution=str(payload["avg_trade_caution"]),
                                confidence_label=str(payload["confidence"]),
                                coverage_label=str(payload["coverage"]),
                                operator_score=int(payload["operator_score"]),
                                profile_status=str(payload["profile_status"]),
                                risky_launch_ratio=int(payload["risky_launch_ratio"]),
                                summary=str(payload["summary"]),
                                premium_prompt=str(payload["premium_prompt"]),
                                flags_json=list(payload["flags"]),
                                top_metrics_json=_json_ready(list(payload["top_metrics"])),
                                profile_signals_json=_json_ready(list(payload["profile_signals"])),
                                latest_launches_json=_json_ready(list(payload["latest_launches"])),
                                latest_refreshed_at=_coerce_utc_datetime(payload["latest_refreshed_at"]),
                                first_seen_at=now,
                                last_seen_at=now,
                            )
                        )
                    else:
                        existing.kind = str(payload["kind"])
                        existing.label = str(payload["label"])
                        existing.wallet_preview = str(payload["wallet_preview"])
                        existing.funding_source = payload.get("funding_source")
                        existing.unresolved = bool(payload["unresolved"])
                        existing.launches_count = int(payload["launches"])
                        existing.high_risk_launches = int(payload["high_risk_launches"])
                        existing.avg_rug_probability = float(payload["avg_rug_probability"])
                        existing.avg_trade_caution = str(payload["avg_trade_caution"])
                        existing.confidence_label = str(payload["confidence"])
                        existing.coverage_label = str(payload["coverage"])
                        existing.operator_score = int(payload["operator_score"])
                        existing.profile_status = str(payload["profile_status"])
                        existing.risky_launch_ratio = int(payload["risky_launch_ratio"])
                        existing.summary = str(payload["summary"])
                        existing.premium_prompt = str(payload["premium_prompt"])
                        existing.flags_json = list(payload["flags"])
                        existing.top_metrics_json = _json_ready(list(payload["top_metrics"]))
                        existing.profile_signals_json = _json_ready(list(payload["profile_signals"]))
                        existing.latest_launches_json = _json_ready(list(payload["latest_launches"]))
                        existing.latest_refreshed_at = _coerce_utc_datetime(payload["latest_refreshed_at"])
                        existing.last_seen_at = now

                    _append_developer_operator_snapshot(
                        db,
                        operator_key=operator_key,
                        snapshot_signature=snapshot_signature,
                        payload=payload,
                        observed_at=now,
                    )
                db.commit()
        except SQLAlchemyError:
            return

    def _load_persisted_developer_operator_items(self) -> list[DeveloperOperatorItem]:
        try:
            with SessionLocal() as db:
                records = (
                    db.query(models.DeveloperOperatorProfile)
                    .order_by(
                        models.DeveloperOperatorProfile.operator_score.desc(),
                        models.DeveloperOperatorProfile.latest_refreshed_at.desc(),
                    )
                    .all()
                )
        except SQLAlchemyError:
            return []

        return [_build_developer_operator_item_from_record(record) for record in records]

    def _rehydrate_persisted_launch_report(
        self,
        *,
        check_id: str | None = None,
        mint: str | None = None,
    ) -> CheckOverview | None:
        try:
            with SessionLocal() as db:
                query = db.query(models.LaunchFeedToken)
                if check_id is not None:
                    record = query.filter(models.LaunchFeedToken.report_id == check_id).first()
                elif mint is not None:
                    record = query.filter(models.LaunchFeedToken.mint == mint).first()
                else:
                    record = None
        except SQLAlchemyError:
            return None

        if record is None:
            return None

        report = generate_report(
            "token",
            record.mint,
            forced_id=record.report_id,
            forced_name=f"{record.symbol} / {record.name}",
            created_at=_coerce_utc_datetime(record.report_created_at),
            rpc_client=self.rpc_client,
            live_token_analysis=False,
            token_holders_max_pages=self.token_holders_max_pages,
            dexscreener_client=self.dexscreener_client,
        )
        report.name = record.name
        report.symbol = record.symbol
        report.logo_url = record.logo_url
        self.register_report(report, persist=False)
        return report

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
            self.register_report(report, persist=False)


def _build_launch_feed_identity_counts(reports: list[CheckOverview]) -> tuple[dict[str, int], dict[str, int]]:
    symbol_counts: dict[str, int] = {}
    name_counts: dict[str, int] = {}
    for report in reports:
        symbol = (report.symbol or report.display_name.split("/")[0].strip()).upper()
        name = (report.name or report.display_name).strip().lower()
        if symbol:
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        if name:
            name_counts[name] = name_counts.get(name, 0) + 1
    return symbol_counts, name_counts


def _build_launch_feed_item(
    report: CheckOverview,
    symbol_counts: dict[str, int],
    name_counts: dict[str, int],
    now: datetime,
) -> LaunchFeedItem:
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
    copycat_status: CopycatStatus = "none"
    if symbol and symbol_counts.get(symbol, 0) > 1:
        copycat_status = "collision"
    elif name and name_counts.get(name.lower(), 0) > 1:
        copycat_status = "collision"
    elif any(factor.code == "TOKEN_METADATA_MISMATCH" for factor in report.risk_increasers):
        copycat_status = "possible"

    return LaunchFeedItem(
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
        launch_quality=_derive_launch_quality(report),
        copycat_status=copycat_status,
        updated_at=report.created_at,
        initial_live_estimate=_is_initial_live_estimate(report),
        summary=report.summary,
        rug_risk_drivers=[factor.label for factor in report.risk_increasers[:2]],
        trade_caution_drivers=(report.trade_caution.drivers[:3] if report.trade_caution else []),
        top_reducer=(report.risk_reducers[0].label if report.risk_reducers else None),
        deployer_short_address=_shorten_address(report.entity_id),
    )


def _build_launch_feed_item_from_record(record: models.LaunchFeedToken, now: datetime) -> LaunchFeedItem:
    report_created_at = _coerce_utc_datetime(record.report_created_at)
    age_minutes = max(0, int((now - report_created_at).total_seconds() // 60))
    return LaunchFeedItem(
        mint=record.mint,
        report_id=record.report_id,
        name=record.name,
        symbol=record.symbol,
        logo_url=record.logo_url,
        age_minutes=age_minutes,
        liquidity_usd=float(record.liquidity_usd),
        market_cap_usd=float(record.market_cap_usd),
        rug_probability=float(record.rug_probability),
        rug_risk_level=record.rug_risk_level,
        trade_caution_level=record.trade_caution_level,
        launch_quality=record.launch_quality,
        copycat_status=record.copycat_status,
        updated_at=report_created_at,
        initial_live_estimate=record.initial_live_estimate,
        summary=record.summary,
        rug_risk_drivers=list(record.rug_risk_drivers or []),
        trade_caution_drivers=list(record.trade_caution_drivers or []),
        top_reducer=record.top_reducer,
        deployer_short_address=record.deployer_short_address,
    )


def _build_launch_feed_snapshot_signature(item: LaunchFeedItem) -> str:
    payload = {
        "copycat_status": item.copycat_status,
        "deployer_short_address": item.deployer_short_address,
        "initial_live_estimate": item.initial_live_estimate,
        "launch_quality": item.launch_quality,
        "liquidity_usd": round(float(item.liquidity_usd), 4),
        "market_cap_usd": round(float(item.market_cap_usd), 4),
        "mint": item.mint,
        "name": item.name,
        "report_created_at": _coerce_utc_datetime(item.updated_at).isoformat(),
        "report_id": item.report_id,
        "rug_probability": round(float(item.rug_probability), 4),
        "rug_risk_drivers": list(item.rug_risk_drivers),
        "rug_risk_level": item.rug_risk_level,
        "summary": item.summary,
        "symbol": item.symbol,
        "top_reducer": item.top_reducer,
        "trade_caution_drivers": list(item.trade_caution_drivers),
        "trade_caution_level": item.trade_caution_level,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _append_launch_feed_snapshot(
    db,
    *,
    item: LaunchFeedItem,
    snapshot_signature: str,
    observed_at: datetime,
) -> None:
    latest_snapshot = (
        db.query(models.LaunchFeedSnapshot)
        .filter(models.LaunchFeedSnapshot.mint == item.mint)
        .order_by(models.LaunchFeedSnapshot.observed_at.desc())
        .first()
    )
    if latest_snapshot is not None and latest_snapshot.snapshot_signature == snapshot_signature:
        return

    db.add(
        models.LaunchFeedSnapshot(
            mint=item.mint,
            report_id=item.report_id,
            name=item.name,
            symbol=item.symbol,
            logo_url=item.logo_url,
            liquidity_usd=item.liquidity_usd,
            market_cap_usd=item.market_cap_usd,
            rug_probability=item.rug_probability,
            rug_risk_level=item.rug_risk_level,
            trade_caution_level=item.trade_caution_level,
            launch_quality=item.launch_quality,
            copycat_status=item.copycat_status,
            initial_live_estimate=item.initial_live_estimate,
            summary=item.summary,
            rug_risk_drivers=item.rug_risk_drivers,
            trade_caution_drivers=item.trade_caution_drivers,
            top_reducer=item.top_reducer,
            deployer_short_address=item.deployer_short_address,
            report_created_at=item.updated_at,
            snapshot_signature=snapshot_signature,
            observed_at=observed_at,
        )
    )


def _coerce_utc_datetime(value: datetime | str) -> datetime:
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


def _build_developer_operator_payloads(reports: list[CheckOverview]) -> list[dict]:
    token_reports = [report for report in reports if report.entity_type == "token"]
    grouped: dict[str, list[CheckOverview]] = {}
    meta: dict[str, dict[str, object]] = {}

    for report in token_reports:
        metrics = _module_metrics(report, "developer_cluster")
        shared_funder = metrics.get("shared_funder")
        resolved_funder = shared_funder if isinstance(shared_funder, str) and len(shared_funder) > 8 else None
        operator_key = resolved_funder or f"cluster:{report.id}"
        grouped.setdefault(operator_key, []).append(report)
        if operator_key not in meta:
            if resolved_funder:
                meta[operator_key] = {
                    "kind": "wallet",
                    "label": _shorten_wallet_label(resolved_funder),
                    "wallet_preview": resolved_funder,
                    "unresolved": False,
                }
            else:
                label_seed = report.symbol or report.display_name[:4].upper()
                meta[operator_key] = {
                    "kind": "cluster",
                    "label": f"Signal Cluster {label_seed}",
                    "wallet_preview": "Wallet hidden",
                    "unresolved": True,
                }

    payloads: list[dict] = []
    for operator_key, items in grouped.items():
        ordered = sorted(items, key=lambda item: _coerce_utc_datetime(item.created_at), reverse=True)
        latest = ordered[0]
        details = _derive_developer_profile_details(latest)
        launch_count = len(ordered)
        avg_rug_probability = round(sum(item.rug_probability for item in ordered) / max(launch_count, 1))
        avg_trade_caution = _avg_trade_caution_label(
            [item.trade_caution.level if item.trade_caution is not None else "moderate" for item in ordered]
        )
        critical_count = len([item for item in ordered if item.status == "critical"])
        high_count = len([item for item in ordered if item.status == "high"])
        high_risk_launches = critical_count + high_count
        risky_launch_ratio = round((high_risk_launches / max(launch_count, 1)) * 100)
        operator_score = round(
            _clamp(
                avg_rug_probability * 0.52
                + risky_launch_ratio * 0.28
                + critical_count * 7
                + (12 if details["profile_status"] == "flagged" else 6 if details["profile_status"] == "watch" else 0)
                + _developer_caution_weight(avg_trade_caution),
                0,
                100,
            )
        )
        flags = _unique_strings(
            [
                *details["watchpoints"],
                *[
                    factor.label
                    for item in ordered
                    for factor in item.risk_increasers[:2]
                ],
            ]
        )[:4]
        funding_source = details["funding_source"]
        latest_launches = [
            {
                "id": item.id,
                "name": item.name or item.display_name,
                "symbol": item.symbol or item.display_name[:5].upper(),
                "risk": item.status,
                "page_mode": item.page_mode,
                "age_minutes": item.launch_radar.launch_age_minutes,
                "refreshed_at": _coerce_utc_datetime(item.created_at),
                "launch_pattern": _developer_launch_pattern_label(item),
            }
            for item in ordered[:4]
        ]
        payloads.append(
            {
                "id": operator_key,
                "kind": meta[operator_key]["kind"],
                "label": meta[operator_key]["label"],
                "wallet_preview": meta[operator_key]["wallet_preview"],
                "unresolved": meta[operator_key]["unresolved"],
                "funding_source": funding_source,
                "launches": launch_count,
                "high_risk_launches": high_risk_launches,
                "avg_rug_probability": avg_rug_probability,
                "avg_trade_caution": avg_trade_caution,
                "confidence": _confidence_label(latest.confidence),
                "coverage": details["coverage"],
                "latest_refreshed_at": _coerce_utc_datetime(latest.created_at),
                "operator_score": operator_score,
                "profile_status": details["profile_status"],
                "risky_launch_ratio": risky_launch_ratio,
                "summary": details["summary"],
                "premium_prompt": (
                    "Unlock the full launch wallet profile, related launches, linked addresses, and repeat operator history with Premium."
                    if meta[operator_key]["kind"] == "wallet"
                    else "Unlock the hidden wallet behind this launch cluster, reveal linked addresses, and open the full launch history with Premium."
                ),
                "flags": flags,
                "top_metrics": details["top_metrics"][:4],
                "profile_signals": details["profile_signals"][:4],
                "latest_launches": latest_launches,
            }
        )

    payloads.sort(
        key=lambda item: (
            -int(item["operator_score"]),
            0 if item["kind"] == "wallet" else 1,
            -int(item["launches"]),
            -int(item["avg_rug_probability"]),
        )
    )
    return payloads


def _build_developer_operator_item_from_record(record: models.DeveloperOperatorProfile) -> DeveloperOperatorItem:
    return DeveloperOperatorItem(
        id=record.operator_key,
        kind=record.kind,
        label=record.label,
        wallet_preview=record.wallet_preview,
        unresolved=record.unresolved,
        funding_source=record.funding_source,
        launches=record.launches_count,
        high_risk_launches=record.high_risk_launches,
        avg_rug_probability=round(float(record.avg_rug_probability)),
        avg_trade_caution=record.avg_trade_caution,
        confidence=record.confidence_label,
        coverage=record.coverage_label,
        latest_refreshed_at=_coerce_utc_datetime(record.latest_refreshed_at),
        operator_score=record.operator_score,
        profile_status=record.profile_status,
        risky_launch_ratio=record.risky_launch_ratio,
        summary=record.summary,
        premium_prompt=record.premium_prompt,
        flags=[str(item) for item in (record.flags_json or [])],
        top_metrics=list(record.top_metrics_json or []),
        profile_signals=list(record.profile_signals_json or []),
        latest_launches=[
            {
                **launch,
                "refreshed_at": _coerce_utc_datetime(launch["refreshed_at"]),
            }
            for launch in list(record.latest_launches_json or [])
        ],
    )


def _build_developer_operator_snapshot_signature(payload: dict) -> str:
    return hashlib.sha256(json.dumps(_json_ready(payload), sort_keys=True).encode("utf-8")).hexdigest()


def _append_developer_operator_snapshot(
    db,
    *,
    operator_key: str,
    snapshot_signature: str,
    payload: dict,
    observed_at: datetime,
) -> None:
    latest_snapshot = (
        db.query(models.DeveloperOperatorSnapshot)
        .filter(models.DeveloperOperatorSnapshot.operator_key == operator_key)
        .order_by(models.DeveloperOperatorSnapshot.observed_at.desc())
        .first()
    )
    if latest_snapshot is not None and latest_snapshot.snapshot_signature == snapshot_signature:
        return

    db.add(
        models.DeveloperOperatorSnapshot(
            operator_key=operator_key,
            snapshot_signature=snapshot_signature,
            payload_json=_json_ready(payload),
            observed_at=observed_at,
        )
    )


def _derive_developer_profile_details(report: CheckOverview) -> dict[str, object]:
    behaviour = report.behaviour_analysis_v2
    modules = behaviour.modules if behaviour is not None else {}
    developer = modules.get("developer_cluster")
    insider = modules.get("insider_selling")
    developer_metrics = _module_metrics(report, "developer_cluster")
    insider_metrics = _module_metrics(report, "insider_selling")

    linked_wallets = _read_metric(
        developer_metrics,
        "estimated_cluster_wallet_count",
        "shared_funding_wallet_count",
        "top_wallets_with_common_funder_count",
    )
    cluster_supply = _read_metric(
        developer_metrics,
        "estimated_cluster_supply_share",
        "cluster_supply_control_pct",
    )
    funding_ratio = _read_metric(developer_metrics, "shared_funding_ratio")
    seller_wallets = _read_metric(insider_metrics, "top_holder_exit_density", "seller_wallet_count")
    exit_similarity = _read_metric(
        insider_metrics,
        "wallet_exit_similarity_score",
        "coordinated_exit_window_score",
    )
    funding_source = _read_metric(developer_metrics, "shared_funder")

    profile_status = (
        "flagged"
        if (developer and developer.status == "flagged") or (insider and insider.status == "flagged")
        else "watch"
        if (developer and developer.status == "watch") or (insider and insider.status == "watch")
        else "clean"
    )
    summary = (
        developer.summary
        if developer is not None
        else insider.summary
        if insider is not None
        else "No strong developer-linked wallet coordination is visible yet."
    )
    coverage = _coverage_label_from_breakdown(behaviour.confidence_breakdown if behaviour is not None else None)
    watchpoints = [
        (
            f"Shared funding source resolves to {str(funding_source)[:4]}...{str(funding_source)[-4:]}."
            if isinstance(funding_source, str) and len(str(funding_source)) > 8
            else None
        ),
        "A meaningful share of tracked holder wallets map back into the same funding network."
        if isinstance(funding_ratio, (int, float)) and float(funding_ratio) >= 0.34
        else None,
        "Linked holder wallets control a noticeable share of tracked supply."
        if isinstance(cluster_supply, (int, float)) and float(cluster_supply) >= 12
        else None,
        "Multiple tracked wallets are contributing to current exit pressure."
        if isinstance(seller_wallets, (int, float)) and float(seller_wallets) >= 2
        else None,
    ]

    profile_signals = [
        {
            "label": "Shared funding coverage",
            "value": _format_ratio_percent(funding_ratio),
            "tone": _numeric_tone(_ratio_to_percent(funding_ratio), 34, 55),
        },
        {
            "label": "Cluster supply control",
            "value": _format_percent(cluster_supply),
            "tone": _numeric_tone(cluster_supply, 12, 24),
        },
        {
            "label": "Exit wallet density",
            "value": _format_count(seller_wallets, "n/a"),
            "tone": _numeric_tone(seller_wallets, 2, 3),
        },
        {
            "label": "Exit timing compression",
            "value": _format_ratio_percent(exit_similarity),
            "tone": _numeric_tone(_ratio_to_percent(exit_similarity), 40, 65),
        },
    ]

    return {
        "profile_status": profile_status,
        "summary": summary,
        "coverage": coverage,
        "funding_source": funding_source if isinstance(funding_source, str) else None,
        "watchpoints": [item for item in watchpoints if item],
        "top_metrics": [
            {"label": "Linked wallets", "value": _format_count(linked_wallets)},
            {"label": "Cluster supply", "value": _format_percent(cluster_supply)},
            {"label": "Seller wallets", "value": _format_count(seller_wallets)},
            {"label": "Funding overlap", "value": _format_ratio_percent(funding_ratio)},
        ],
        "profile_signals": sorted(
            profile_signals,
            key=lambda item: {"flagged": 0, "watch": 1, "neutral": 2}[item["tone"]],
        ),
    }


def _module_metrics(report: CheckOverview, key: str) -> dict[str, object]:
    behaviour = report.behaviour_analysis_v2
    if behaviour is None:
        return {}
    module = behaviour.modules.get(key)
    if module is None:
        return {}
    return dict(module.evidence.metrics or {})


def _read_metric(metrics: dict[str, object], *keys: str) -> object | None:
    for key in keys:
        if key in metrics and metrics[key] is not None:
            return metrics[key]
    return None


def _confidence_label(value: float) -> str:
    if value >= 0.75:
        return "High confidence"
    if value >= 0.45:
        return "Moderate confidence"
    return "Limited early data"


def _coverage_label_from_breakdown(breakdown) -> str:
    if breakdown is None:
        return "Limited trace"
    depth = getattr(breakdown, "funding_trace_depth", "shallow")
    if depth == "deep":
        return "Deep trace"
    if depth == "moderate":
        return "Partial trace"
    return "Limited trace"


def _avg_trade_caution_label(levels: list[str]) -> str:
    if "avoid" in levels:
        return "Avoid"
    if "high" in levels:
        return "High caution"
    if "moderate" in levels:
        return "Moderate caution"
    return "Low caution"


def _developer_caution_weight(level: str) -> int:
    if "Avoid" in level:
        return 16
    if "High" in level:
        return 11
    if "Moderate" in level:
        return 6
    return 2


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _shorten_wallet_label(value: str) -> str:
    return f"{value[:4]}...{value[-4:]}"


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _format_count(value: object | None, fallback: str = "0") -> str:
    if isinstance(value, (int, float)):
        return str(int(round(float(value))))
    return fallback


def _format_percent(value: object | None, fallback: str = "n/a") -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.1f}%"
    return fallback


def _format_ratio_percent(value: object | None, fallback: str = "n/a") -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.1f}%"
    return fallback


def _ratio_to_percent(value: object | None) -> float | None:
    if isinstance(value, (int, float)):
        return float(value) * 100
    return None


def _numeric_tone(value: object | None, watch_threshold: float, flagged_threshold: float) -> str:
    if not isinstance(value, (int, float)):
        return "neutral"
    if float(value) >= flagged_threshold:
        return "flagged"
    if float(value) >= watch_threshold:
        return "watch"
    return "neutral"


def _developer_launch_pattern_label(report: CheckOverview) -> str | None:
    if report.entity_type != "token":
        return None
    behaviour = report.behaviour_analysis_v2
    modules = behaviour.modules if behaviour is not None else {}
    developer = modules.get("developer_cluster")
    early_buyers = modules.get("early_buyers")
    insider_selling = modules.get("insider_selling")
    liquidity = modules.get("liquidity_management")

    if liquidity and liquidity.status == "flagged" and (
        (report.trade_caution is not None and report.trade_caution.level in {"high", "avoid"})
        or report.launch_risk.level in {"high", "critical"}
    ):
        return "Liquidity trap"
    if (developer and developer.status == "flagged") or (insider_selling and insider_selling.status == "flagged"):
        return "Insider"
    if (
        (early_buyers and early_buyers.status in {"flagged", "watch"})
        or report.launch_radar.early_cluster_activity != "none"
        or report.launch_radar.early_trade_pressure == "aggressive"
    ):
        return "Sniper"
    return "Organic"


def _json_ready(value):
    if isinstance(value, datetime):
        return _coerce_utc_datetime(value).isoformat()
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _parse_cursor(value: str | None) -> int:
    if not value:
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0
