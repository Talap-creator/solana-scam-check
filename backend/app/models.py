from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import uuid

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
    custom_daily_scan_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scans: Mapped[list["TokenScan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    watchlist_entries: Mapped[list["UserWatchlistEntry"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    billing_events: Mapped[list["BillingEvent"]] = relationship(back_populates="user")


class TokenScan(Base):
    __tablename__ = "token_scans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    token_address: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    chain: Mapped[str] = mapped_column(String(32), default="solana", nullable=False)
    scan_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)

    user: Mapped[User] = relationship(back_populates="scans")


class UserWatchlistEntry(Base):
    __tablename__ = "user_watchlist_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_user_watchlist_entity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User] = relationship(back_populates="watchlist_entries")


class TokenStat(Base):
    __tablename__ = "token_stats"

    token_address: Mapped[str] = mapped_column(String(128), primary_key=True)
    scan_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_scanned: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class TokenOverride(Base):
    __tablename__ = "token_overrides"

    token_address: Mapped[str] = mapped_column(String(128), primary_key=True)
    chain: Mapped[str] = mapped_column(String(32), default="solana", nullable=False)
    verdict: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class TokenFeatureSnapshot(Base):
    __tablename__ = "token_feature_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_address: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    feature_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    rule_score: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    ml_probability: Mapped[float] = mapped_column(Numeric(7, 6), nullable=False)
    final_score: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False, default="features_v1")
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="ml_v1_heuristic")


class TokenBehaviourSnapshot(Base):
    __tablename__ = "token_behaviour_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_address: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    developer_cluster_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    early_buyers_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    insider_selling_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    liquidity_management_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence_breakdown_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    behaviour_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    behaviour_confidence: Mapped[str] = mapped_column(String(16), nullable=False, default="limited")
    feature_version: Mapped[str] = mapped_column(String(32), nullable=False, default="behaviour_v2")


class LaunchFeedToken(Base):
    __tablename__ = "launch_feed_tokens"

    mint: Mapped[str] = mapped_column(String(128), primary_key=True)
    report_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    liquidity_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    market_cap_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    rug_probability: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    rug_risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    trade_caution_level: Mapped[str] = mapped_column(String(16), nullable=False)
    launch_quality: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    copycat_status: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    initial_live_estimate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str] = mapped_column(String(600), nullable=False)
    rug_risk_drivers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    trade_caution_drivers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    top_reducer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    deployer_short_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    report_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class LaunchFeedSnapshot(Base):
    __tablename__ = "launch_feed_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mint: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    report_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    liquidity_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    market_cap_usd: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    rug_probability: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    rug_risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    trade_caution_level: Mapped[str] = mapped_column(String(16), nullable=False)
    launch_quality: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    copycat_status: Mapped[str] = mapped_column(String(16), nullable=False, default="none")
    initial_live_estimate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str] = mapped_column(String(600), nullable=False)
    rug_risk_drivers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    trade_caution_drivers: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    top_reducer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    deployer_short_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    report_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    snapshot_signature: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DeveloperOperatorProfile(Base):
    __tablename__ = "developer_operator_profiles"

    operator_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    wallet_preview: Mapped[str] = mapped_column(String(200), nullable=False)
    funding_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    unresolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    launches_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_risk_launches: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_rug_probability: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False, default=0)
    avg_trade_caution: Mapped[str] = mapped_column(String(32), nullable=False, default="Moderate caution")
    confidence_label: Mapped[str] = mapped_column(String(64), nullable=False, default="Limited early data")
    coverage_label: Mapped[str] = mapped_column(String(64), nullable=False, default="Limited trace")
    operator_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profile_status: Mapped[str] = mapped_column(String(16), nullable=False, default="clean")
    risky_launch_ratio: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str] = mapped_column(String(900), nullable=False)
    premium_prompt: Mapped[str] = mapped_column(String(500), nullable=False)
    flags_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    top_metrics_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    profile_signals_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    latest_launches_json: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    latest_refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DeveloperOperatorSnapshot(Base):
    __tablename__ = "developer_operator_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operator_key: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    snapshot_signature: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class PersistedCheckReport(Base):
    __tablename__ = "persisted_check_reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class BillingEvent(Base):
    __tablename__ = "billing_events"

    event_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="helio")
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan: Mapped[str | None] = mapped_column(String(32), nullable=True)
    paylink_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subscription_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount_usd: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    user_email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    upgraded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[User | None] = relationship(back_populates="billing_events")


def build_billing_event_key(
    *,
    event_id: str | None,
    transaction_id: str | None,
    subscription_id: str | None,
    event_type: str | None,
    status: str | None,
    payload_json: dict,
) -> str:
    if event_id:
        return event_id
    if transaction_id:
        return f"txn:{transaction_id}"
    if subscription_id and event_type:
        return f"sub:{subscription_id}:{event_type}"
    payload_hash = hashlib.sha256(
        json.dumps(
            {
                "event_type": event_type or "",
                "status": status or "",
                "payload": payload_json,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return f"hash:{payload_hash}"
