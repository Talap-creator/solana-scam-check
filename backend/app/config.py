from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


PUBLIC_SOLANA_RPC_URLS = (
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
)

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://solanatrust.vercel.app",
)

ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"


@dataclass(frozen=True)
class Settings:
    app_title: str = "RugSignal API"
    app_description: str = (
        "Backend API for RugSignal.io, focused on Solana rug-risk detection and explainable scoring."
    )
    app_version: str = "0.2.0"
    cors_allow_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    active_rules: int = 128
    solana_rpc_urls: tuple[str, ...] = PUBLIC_SOLANA_RPC_URLS
    token_holders_max_pages: int = 25
    dexscreener_base_url: str = "https://api.dexscreener.com"
    database_url: str = "sqlite:///./rugsignal.db"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    admin_bootstrap_email: str | None = None
    free_daily_scan_limit: int = 5
    pro_daily_scan_limit: int = 200
    enterprise_daily_scan_limit: int = 1000
    feed_live_source_enabled: bool = True
    feed_live_profiles_limit: int = 2
    feed_live_sync_ttl_seconds: int = 60
    behaviour_snapshot_ttl_seconds: int = 60 * 60 * 6
    behaviour_shared_funding_ratio_warn: float = 0.34
    behaviour_shared_funding_ratio_high: float = 0.55
    behaviour_cluster_supply_warn: float = 12.0
    behaviour_cluster_supply_high: float = 24.0
    behaviour_timing_similarity_warn: float = 0.40
    behaviour_timing_similarity_high: float = 0.70
    behaviour_early_same_window_seconds: int = 3600
    behaviour_early_buy_size_similarity_warn: float = 0.60
    behaviour_early_buyer_overlap_warn: float = 0.35
    behaviour_coordinated_exit_window_seconds: int = 7200
    behaviour_large_holder_sell_warn: float = 8.0
    behaviour_dev_cluster_sell_high: float = 18.0
    behaviour_sell_before_collapse_threshold: float = 0.55
    behaviour_rapid_liquidity_drop_warn_pct: float = 0.20
    behaviour_rapid_liquidity_drop_high_pct: float = 0.45
    behaviour_boost_multiplier: float = 1.15


def split_env_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def normalize_database_url(value: str) -> str:
    url = value.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def load_env_file() -> None:
    if not ENV_FILE_PATH.exists():
        return

    for raw_line in ENV_FILE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_solana_rpc_urls() -> tuple[str, ...]:
    explicit_urls = split_env_list(os.getenv("SOLANA_RPC_URLS"))
    explicit_url = os.getenv("SOLANA_RPC_URL", "").strip()
    quicknode_url = os.getenv("QUICKNODE_URL", "").strip()
    helius_api_key = os.getenv("HELIUS_API_KEY", "").strip()

    rpc_urls: list[str] = []

    if explicit_urls:
        rpc_urls.extend(explicit_urls)
    elif explicit_url:
        rpc_urls.append(explicit_url)
    else:
        if quicknode_url:
            rpc_urls.append(quicknode_url)
        if helius_api_key:
            rpc_urls.append(f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}")
        rpc_urls.extend(PUBLIC_SOLANA_RPC_URLS)

    deduped_urls: list[str] = []
    for url in rpc_urls:
        if url and url not in deduped_urls:
            deduped_urls.append(url)

    return tuple(deduped_urls) or PUBLIC_SOLANA_RPC_URLS


def get_settings() -> Settings:
    load_env_file()
    configured_origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOW_ORIGINS",
            ",".join(DEFAULT_CORS_ORIGINS),
        ).split(",")
        if origin.strip()
    )
    origins = tuple(dict.fromkeys((*DEFAULT_CORS_ORIGINS, *configured_origins)))
    return Settings(
        cors_allow_origins=origins or Settings.cors_allow_origins,
        solana_rpc_urls=build_solana_rpc_urls(),
        token_holders_max_pages=int(os.getenv("TOKEN_HOLDERS_MAX_PAGES", str(Settings.token_holders_max_pages))),
        dexscreener_base_url=os.getenv("DEXSCREENER_BASE_URL", Settings.dexscreener_base_url),
        database_url=normalize_database_url(os.getenv("DATABASE_URL", Settings.database_url)),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", Settings.jwt_secret_key),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", Settings.jwt_algorithm),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", str(Settings.jwt_expire_minutes))),
        admin_bootstrap_email=os.getenv("ADMIN_BOOTSTRAP_EMAIL"),
        free_daily_scan_limit=int(os.getenv("FREE_DAILY_SCAN_LIMIT", str(Settings.free_daily_scan_limit))),
        pro_daily_scan_limit=int(os.getenv("PRO_DAILY_SCAN_LIMIT", str(Settings.pro_daily_scan_limit))),
        enterprise_daily_scan_limit=int(
            os.getenv("ENTERPRISE_DAILY_SCAN_LIMIT", str(Settings.enterprise_daily_scan_limit))
        ),
        feed_live_source_enabled=os.getenv("FEED_LIVE_SOURCE_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"},
        feed_live_profiles_limit=int(
            os.getenv("FEED_LIVE_PROFILES_LIMIT", str(Settings.feed_live_profiles_limit))
        ),
        feed_live_sync_ttl_seconds=int(
            os.getenv("FEED_LIVE_SYNC_TTL_SECONDS", str(Settings.feed_live_sync_ttl_seconds))
        ),
        behaviour_snapshot_ttl_seconds=int(
            os.getenv("BEHAVIOUR_SNAPSHOT_TTL_SECONDS", str(Settings.behaviour_snapshot_ttl_seconds))
        ),
        behaviour_shared_funding_ratio_warn=float(
            os.getenv(
                "BEHAVIOUR_SHARED_FUNDING_RATIO_WARN",
                str(Settings.behaviour_shared_funding_ratio_warn),
            )
        ),
        behaviour_shared_funding_ratio_high=float(
            os.getenv(
                "BEHAVIOUR_SHARED_FUNDING_RATIO_HIGH",
                str(Settings.behaviour_shared_funding_ratio_high),
            )
        ),
        behaviour_cluster_supply_warn=float(
            os.getenv("BEHAVIOUR_CLUSTER_SUPPLY_WARN", str(Settings.behaviour_cluster_supply_warn))
        ),
        behaviour_cluster_supply_high=float(
            os.getenv("BEHAVIOUR_CLUSTER_SUPPLY_HIGH", str(Settings.behaviour_cluster_supply_high))
        ),
        behaviour_timing_similarity_warn=float(
            os.getenv(
                "BEHAVIOUR_TIMING_SIMILARITY_WARN",
                str(Settings.behaviour_timing_similarity_warn),
            )
        ),
        behaviour_timing_similarity_high=float(
            os.getenv(
                "BEHAVIOUR_TIMING_SIMILARITY_HIGH",
                str(Settings.behaviour_timing_similarity_high),
            )
        ),
        behaviour_early_same_window_seconds=int(
            os.getenv(
                "BEHAVIOUR_EARLY_SAME_WINDOW_SECONDS",
                str(Settings.behaviour_early_same_window_seconds),
            )
        ),
        behaviour_early_buy_size_similarity_warn=float(
            os.getenv(
                "BEHAVIOUR_EARLY_BUY_SIZE_SIMILARITY_WARN",
                str(Settings.behaviour_early_buy_size_similarity_warn),
            )
        ),
        behaviour_early_buyer_overlap_warn=float(
            os.getenv(
                "BEHAVIOUR_EARLY_BUYER_OVERLAP_WARN",
                str(Settings.behaviour_early_buyer_overlap_warn),
            )
        ),
        behaviour_coordinated_exit_window_seconds=int(
            os.getenv(
                "BEHAVIOUR_COORDINATED_EXIT_WINDOW_SECONDS",
                str(Settings.behaviour_coordinated_exit_window_seconds),
            )
        ),
        behaviour_large_holder_sell_warn=float(
            os.getenv(
                "BEHAVIOUR_LARGE_HOLDER_SELL_WARN",
                str(Settings.behaviour_large_holder_sell_warn),
            )
        ),
        behaviour_dev_cluster_sell_high=float(
            os.getenv(
                "BEHAVIOUR_DEV_CLUSTER_SELL_HIGH",
                str(Settings.behaviour_dev_cluster_sell_high),
            )
        ),
        behaviour_sell_before_collapse_threshold=float(
            os.getenv(
                "BEHAVIOUR_SELL_BEFORE_COLLAPSE_THRESHOLD",
                str(Settings.behaviour_sell_before_collapse_threshold),
            )
        ),
        behaviour_rapid_liquidity_drop_warn_pct=float(
            os.getenv(
                "BEHAVIOUR_RAPID_LIQUIDITY_DROP_WARN_PCT",
                str(Settings.behaviour_rapid_liquidity_drop_warn_pct),
            )
        ),
        behaviour_rapid_liquidity_drop_high_pct=float(
            os.getenv(
                "BEHAVIOUR_RAPID_LIQUIDITY_DROP_HIGH_PCT",
                str(Settings.behaviour_rapid_liquidity_drop_high_pct),
            )
        ),
        behaviour_boost_multiplier=float(
            os.getenv("BEHAVIOUR_BOOST_MULTIPLIER", str(Settings.behaviour_boost_multiplier))
        ),
    )
