from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
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
