from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import re
import time
from urllib.parse import urlparse

from ..config import get_settings
from ..scoring.behaviour import build_behaviour_analysis_v2
from ..scoring.trade_caution import build_trade_caution_overview
from ..schemas import (
    BehaviourAnalysisOverview,
    BehaviourInsightItem,
    CheckOverview,
    EntityType,
    LaunchRadarOverview,
    LaunchRiskOverview,
    MetricItem,
    PageMode,
    ReviewState,
    RiskBreakdownItem,
    RiskFactor,
    RiskStatus,
    TimelineEvent,
    TimelineTone,
)
from .dexscreener import DexScreenerClient, DexScreenerError, extract_token_profile, pick_most_liquid_pair
from .solana_rpc import SolanaRpcClient, SolanaRpcError


SOLANA_BASE58_ALPHABET = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
RISK_BLOCK_WEIGHTS: dict[str, float] = {
    "Technical risk": 0.30,
    "Distribution risk": 0.25,
    "Market / execution risk": 0.25,
    "Behaviour risk": 0.20,
    "Market maturity": 1.00,
}
KNOWN_BLUECHIP_SYMBOLS = {
    "SOL",
    "USDC",
    "USDT",
    "JUP",
    "PYTH",
    "BONK",
    "JTO",
    "RAY",
    "WIF",
}
settings = get_settings()
_BEHAVIOUR_RPC_CACHE: dict[str, tuple[float, object]] = {}
_BEHAVIOUR_CACHE_STATS: dict[str, int] = {"hits": 0, "misses": 0}


def _behaviour_cache_key(prefix: str, identifier: str, *parts: object) -> str:
    suffix = ":".join(str(part) for part in parts)
    return f"{prefix}:{identifier}:{suffix}"


def _behaviour_cache_get(key: str) -> object | None:
    cached = _BEHAVIOUR_RPC_CACHE.get(key)
    if cached is None:
        _BEHAVIOUR_CACHE_STATS["misses"] = _BEHAVIOUR_CACHE_STATS.get("misses", 0) + 1
        return None
    expires_at, value = cached
    if time.time() >= expires_at:
        _BEHAVIOUR_RPC_CACHE.pop(key, None)
        _BEHAVIOUR_CACHE_STATS["misses"] = _BEHAVIOUR_CACHE_STATS.get("misses", 0) + 1
        return None
    _BEHAVIOUR_CACHE_STATS["hits"] = _BEHAVIOUR_CACHE_STATS.get("hits", 0) + 1
    return value


def _behaviour_cache_set(key: str, value: object) -> object:
    _BEHAVIOUR_RPC_CACHE[key] = (time.time() + settings.behaviour_snapshot_ttl_seconds, value)
    return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def relative_time(timestamp: datetime) -> str:
    delta_seconds = int((utc_now() - timestamp).total_seconds())
    if delta_seconds < 60:
        return "just now"
    if delta_seconds < 3600:
        minutes = max(1, delta_seconds // 60)
        unit = "minute" if minutes == 1 else "minutes"
        return f"{minutes} {unit} ago"
    if delta_seconds < 86400:
        hours = max(1, delta_seconds // 3600)
        unit = "hour" if hours == 1 else "hours"
        return f"{hours} {unit} ago"
    days = max(1, delta_seconds // 86400)
    unit = "day" if days == 1 else "days"
    return f"{days} {unit} ago"


def risk_status(score: int) -> RiskStatus:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def review_state_for(status: RiskStatus) -> ReviewState:
    if status == "critical":
        return "Escalated"
    if status == "high":
        return "Queued"
    if status == "medium":
        return "Watching"
    return "Clear"


def normalize_entity_id(entity_type: EntityType, raw_value: str) -> str:
    value = raw_value.strip()
    if entity_type == "project":
        parsed = urlparse(value if "://" in value else f"https://{value}")
        host = parsed.netloc or parsed.path
        return host.lower().strip("/") or value.lower()
    return value


def is_valid_solana_address(value: str) -> bool:
    trimmed = value.strip()
    return 32 <= len(trimmed) <= 44 and all(char in SOLANA_BASE58_ALPHABET for char in trimmed)


def display_name_for(entity_type: EntityType, entity_id: str) -> str:
    if entity_type == "token":
        return f"Token / {entity_id[:4]}...{entity_id[-4:]}"
    if entity_type == "wallet":
        return f"Wallet / {entity_id[:4]}...{entity_id[-4:]}"
    return f"Project / {entity_id}"


def base_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "check"


def money_value(seed: int) -> str:
    amount = 4_000 + (seed % 240_000)
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    return f"${amount}"


def pick_seed(entity_type: EntityType, entity_id: str, version: int) -> int:
    digest = hashlib.sha256(f"{entity_type}:{entity_id}:{version}".encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def token_factors(seed: int) -> list[RiskFactor]:
    factors: list[RiskFactor] = []
    if seed % 5 != 0:
        factors.append(
            RiskFactor(
                code="TOKEN_ACTIVE_MINT_AUTHORITY",
                severity="high",
                label="Mint authority still enabled",
                explanation="Token supply can still be changed after launch.",
                weight=21,
            )
        )
    if seed % 7 in {1, 2, 3, 4}:
        factors.append(
            RiskFactor(
                code="TOKEN_HOLDER_CONCENTRATION",
                severity="high",
                label="Holder concentration above normal",
                explanation="A small group of wallets controls a large share of supply.",
                weight=18,
            )
        )
    if seed % 4 in {0, 1}:
        factors.append(
            RiskFactor(
                code="TOKEN_LOW_LIQUIDITY",
                severity="medium",
                label="Thin liquidity profile",
                explanation="Exit liquidity is shallow compared with recent activity.",
                weight=12,
            )
        )
    if seed % 6 in {0, 2, 5}:
        factors.append(
            RiskFactor(
                code="TOKEN_METADATA_MISMATCH",
                severity="medium",
                label="Metadata mismatch",
                explanation="Project branding and onchain metadata do not fully align.",
                weight=9,
            )
        )
    if not factors:
        factors.append(
            RiskFactor(
                code="TOKEN_FRESH_SAMPLE",
                severity="low",
                label="No major token red flags detected",
                explanation="Initial scan found only weak signals and normal liquidity behavior.",
                weight=8,
            )
        )
    return factors


def wallet_factors(seed: int) -> list[RiskFactor]:
    factors: list[RiskFactor] = []
    if seed % 3 != 0:
        factors.append(
            RiskFactor(
                code="WALLET_LINKED_FLAGGED",
                severity="high",
                label="Linked to flagged wallets",
                explanation="Transfers overlap with addresses previously marked as risky.",
                weight=17,
            )
        )
    if seed % 5 in {1, 2, 4}:
        factors.append(
            RiskFactor(
                code="WALLET_LAUNCH_DUMP",
                severity="high",
                label="Launch-dump behavior",
                explanation="Wallet repeatedly enters early and exits shortly after liquidity events.",
                weight=19,
            )
        )
    if seed % 4 in {0, 2}:
        factors.append(
            RiskFactor(
                code="WALLET_DEPLOYER_HISTORY",
                severity="medium",
                label="Suspicious deployer history",
                explanation="Related deployments contain a high ratio of short-lived tokens.",
                weight=11,
            )
        )
    if not factors:
        factors.append(
            RiskFactor(
                code="WALLET_LIMITED_RISK",
                severity="low",
                label="Limited historical risk",
                explanation="Observed wallet behavior is currently within normal boundaries.",
                weight=7,
            )
        )
    return factors


def project_factors(seed: int) -> list[RiskFactor]:
    factors: list[RiskFactor] = []
    if seed % 4 in {1, 2, 3}:
        factors.append(
            RiskFactor(
                code="PROJECT_THIN_SOCIALS",
                severity="medium",
                label="Thin social footprint",
                explanation="Public channels show low engagement for the claimed audience size.",
                weight=10,
            )
        )
    if seed % 6 in {0, 1, 4}:
        factors.append(
            RiskFactor(
                code="PROJECT_NEW_DOMAIN",
                severity="medium",
                label="Young domain age",
                explanation="Primary domain was registered recently and lacks long-lived reputation signals.",
                weight=9,
            )
        )
    if seed % 5 in {2, 3, 4}:
        factors.append(
            RiskFactor(
                code="PROJECT_TOKEN_SIGNAL",
                severity="high",
                label="Underlying token signal elevated",
                explanation="Associated token behavior increases the project-level risk score.",
                weight=16,
            )
        )
    if not factors:
        factors.append(
            RiskFactor(
                code="PROJECT_LOW_SIGNAL",
                severity="low",
                label="Low project risk signal",
                explanation="Current project-level indicators are mostly stable.",
                weight=8,
            )
        )
    return factors


def build_metrics(
    entity_type: EntityType,
    score: int,
    confidence: float,
    seed: int,
    top_holder_share: str,
    liquidity: str,
) -> list[MetricItem]:
    metrics = [
        MetricItem(label="Score", value=str(score)),
        MetricItem(label="Confidence", value=f"{confidence:.2f}"),
    ]
    if entity_type == "wallet":
        metrics.append(MetricItem(label="Linked flags", value=str(1 + seed % 6)))
        metrics.append(MetricItem(label="Active days", value=str(20 + seed % 120)))
    elif entity_type == "project":
        metrics.append(MetricItem(label="Domain age", value=f"{12 + seed % 320} days"))
        metrics.append(MetricItem(label="Liquidity", value=liquidity))
    else:
        metrics.append(MetricItem(label="Top holders", value=top_holder_share))
        metrics.append(MetricItem(label="Liquidity", value=liquidity))
    return metrics


def build_timeline(entity_type: EntityType, factors: list[RiskFactor], seed: int) -> list[TimelineEvent]:
    events: list[TimelineEvent] = []
    for factor in factors[:3]:
        tone: TimelineTone = "danger" if factor.severity == "high" else "warn" if factor.severity == "medium" else "neutral"
        value = "Detected" if tone != "neutral" else "Stable"
        events.append(TimelineEvent(label=factor.label, value=value, tone=tone))
    if entity_type == "project":
        events.append(TimelineEvent(label="Moderation labels", value=f"{seed % 3} pending", tone="neutral"))
    else:
        events.append(TimelineEvent(label="Background refresh", value="Completed", tone="neutral"))
    return events


def build_summary(entity_type: EntityType, status: RiskStatus, factors: list[RiskFactor]) -> str:
    if not factors:
        return "Initial scan completed with limited signal."
    top_signal = factors[0]
    if top_signal.severity == "high" and status in {"low", "medium"}:
        return (
            f"{entity_type.title()} scan has mixed signals. "
            f"Strong warning present: {top_signal.label.lower()}."
        )
    factor_labels = ", ".join(factor.label.lower() for factor in factors[:2])
    return f"{entity_type.title()} scan marked as {status} risk based on {factor_labels}."


def build_token_summary(
    *,
    page_mode: PageMode,
    rug_probability: int,
    trade_caution_level: str | None,
    technical_risk: int,
    market_execution_risk: int,
    market_maturity: int,
    behaviour_risk: int,
    usd_liquidity: float | None,
    risk_increasers: list[RiskFactor],
    has_live_exploit_signal: bool,
    confidence: float,
) -> str:
    if page_mode == "early_launch":
        if (usd_liquidity or 0.0) < 5_000:
            return (
                "Initial launch conditions show a thin liquidity profile. No strong behavioural anomalies "
                "have emerged yet, but the token remains too early for a stable low-risk verdict."
            )
        if confidence < 0.45:
            return (
                "This token is still in its earliest trading window. Current verdict is based on limited "
                "launch-time signals and may change as more data appears."
            )
        return (
            "Live launch profile detected. This is an early-stage assessment based on launch age, "
            "liquidity, and emerging market structure."
        )

    if page_mode == "early_market":
        return (
            "This token is still within its first day of trading. Current assessment combines early "
            "market structure with the limited behavioural evidence available so far."
        )

    if confidence < 0.30:
        return "Token risk estimate is based on partial data and should be treated as preliminary."

    if rug_probability <= 25 and trade_caution_level in {"high", "avoid"}:
        return (
            "No strong scam-specific behaviour was detected, but market structure and contract controls "
            "warrant caution."
        )

    if has_live_exploit_signal and rug_probability >= 60:
        return (
            "Token shows multiple scam-linked signals, including concentrated control, "
            "suspicious wallet behaviour, and weak liquidity ownership structure."
        )

    if technical_risk >= 60 and market_maturity >= 60:
        return (
            "Token has elevated administrative control flags, but strong market maturity and known-project "
            "signals significantly reduce overall rug probability."
        )

    if market_execution_risk >= 65 and rug_probability <= 40:
        return (
            "Market depth is limited in the detected pool, which may increase execution risk, "
            "but no strong scam-specific behaviour signals were found."
        )

    if rug_probability <= 25 and market_maturity >= 70:
        return (
            "Token has some administrative permissions or local market friction, but established market "
            "presence materially lowers overall rug probability."
        )

    if rug_probability >= 60 and trade_caution_level in {"high", "avoid"}:
        return (
            "Multiple scam-linked and trading-risk signals were detected, including concentrated control, "
            "suspicious behaviour, and weak liquidity structure."
        )

    if behaviour_risk >= 60 and rug_probability >= 45:
        return (
            "Token shows elevated behaviour-linked risk signals that increase rug probability beyond "
            "normal technical or market-structure concerns."
        )

    if risk_increasers:
        return (
            f"Rug probability is mainly influenced by {risk_increasers[0].label.lower()}, "
            f"while market maturity currently scores {market_maturity}/100."
        )
    return "Token scan completed with no major scam-specific signal."


def format_token_amount(value: float) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:.2f}K"
    return f"{value:.2f}"


def format_share(value: float | None) -> str:
    if value is None:
        return "n/a"
    if 0 < value < 0.1:
        return "<0.1%"
    return f"{value:.1f}%"


def format_usd_liquidity(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.2f}"


def liquidity_band(value: float | None) -> str:
    if value is None:
        return "Unknown"
    if value < 1_000:
        return "under $1k"
    if value < 5_000:
        return "$1k-$5k"
    if value < 20_000:
        return "$5k-$20k"
    return "above $20k"


def token_age_snapshot(block_time: int | None) -> tuple[str, int | None, int | None]:
    if not block_time:
        return "Unknown", None, None

    age_seconds = max(0, int(utc_now().timestamp()) - block_time)
    age_minutes = age_seconds // 60
    age_days = age_minutes // 1440

    if age_minutes < 60:
        return f"{max(1, age_minutes)}m", age_days, age_minutes

    if age_minutes < 1440:
        hours = age_minutes // 60
        if age_minutes < 360 and age_minutes % 60:
            return f"{hours}h {age_minutes % 60}m", age_days, age_minutes
        return f"{hours}h", age_days, age_minutes

    if age_days < 30:
        return f"{age_days}d", age_days, age_minutes

    if age_days < 365:
        return f"{max(1, age_days // 30)}mo", age_days, age_minutes

    return f"{max(1, age_days // 365)}y", age_days, age_minutes


def token_confidence(
    *,
    has_supply: bool,
    has_liquidity: bool,
    has_holder_distribution: bool,
    has_market_profile: bool,
) -> float:
    confidence = 0.55
    if has_supply:
        confidence += 0.12
    if has_liquidity:
        confidence += 0.12
    if has_holder_distribution:
        confidence += 0.13
    if has_market_profile:
        confidence += 0.08
    return round(min(confidence, 0.98), 2)


def adjusted_token_confidence(
    *,
    base_confidence: float,
    page_mode: PageMode,
    holder_scan_complete: bool,
    has_liquidity: bool,
    has_market_profile: bool,
    usd_liquidity: float | None,
    has_live_exploit_signal: bool,
) -> float:
    confidence = base_confidence

    if page_mode == "early_launch":
        confidence = min(confidence, 0.68)
        if not holder_scan_complete or not has_liquidity or not has_market_profile:
            confidence = min(confidence, 0.42)
        if (usd_liquidity or 0.0) < 5_000:
            confidence = min(confidence, 0.38)
        if has_live_exploit_signal:
            confidence = min(confidence, 0.58)
    elif page_mode == "early_market":
        if not holder_scan_complete:
            confidence = min(confidence, 0.74)
        if (usd_liquidity or 0.0) < 5_000:
            confidence = min(confidence, 0.66)

    return round(max(0.10, confidence), 2)


def resolve_page_mode(
    *,
    launch_age_minutes: int | None,
    listed_on_known_aggregator: bool,
) -> PageMode:
    if launch_age_minutes is None:
        return "early_launch" if not listed_on_known_aggregator else "early_market"
    if launch_age_minutes < 60:
        return "early_launch"
    if launch_age_minutes < 1440:
        return "early_market"
    return "mature"


def launch_concentration_label(top_10_share: float | None, top_1_share: float | None) -> str:
    if top_10_share is None and top_1_share is None:
        return "medium"
    if (top_10_share or 0.0) >= 75 or (top_1_share or 0.0) >= 25:
        return "high"
    if (top_10_share or 0.0) >= 45 or (top_1_share or 0.0) >= 10:
        return "medium"
    return "low"


def early_cluster_activity_label(
    *,
    developer_cluster_signal: dict[str, float | int | bool | str | None],
    early_buyer_cluster_signal: dict[str, float | int | bool | str | None],
    insider_selling_signal: dict[str, float | int | bool | str | None],
) -> str:
    suspicious = bool(
        developer_cluster_signal.get("detected")
        or early_buyer_cluster_signal.get("detected")
        or insider_selling_signal.get("detected")
    )
    if suspicious:
        return "suspicious"

    watch_signal = (
        float(developer_cluster_signal.get("confidence") or 0.0) >= 0.30
        or float(early_buyer_cluster_signal.get("confidence") or 0.0) >= 0.30
        or float(insider_selling_signal.get("confidence") or 0.0) >= 0.30
    )
    return "watch" if watch_signal else "none"


def early_trade_pressure_label(
    *,
    trade_caution_level: str | None,
    market_execution_risk: int,
    volume_24h_usd: float | None,
) -> str:
    if trade_caution_level in {"high", "avoid"} or market_execution_risk >= 70:
        return "aggressive"
    if trade_caution_level == "moderate" or market_execution_risk >= 45 or (volume_24h_usd or 0.0) > 100_000:
        return "balanced"
    return "low"


def build_launch_risk_overview(
    *,
    page_mode: PageMode,
    launch_age_minutes: int | None,
    usd_liquidity: float | None,
    top_10_share: float | None,
    top_1_share: float | None,
    trade_caution_level: str | None,
    market_execution_risk: int,
    copycat_status: str,
    early_cluster_activity: str,
    holder_scan_complete: bool,
) -> LaunchRiskOverview:
    if launch_age_minutes is None and usd_liquidity is None:
        return LaunchRiskOverview(
            score=0,
            level="unknown",
            summary="Launch-stage data is not available yet, so this token cannot be classified from launch conditions alone.",
            drivers=[],
        )

    score = 0
    drivers: list[str] = []
    concentration = launch_concentration_label(top_10_share, top_1_share)

    if launch_age_minutes is not None:
        if launch_age_minutes < 15:
            score += 36
            drivers.append("Launch is still within the first 15 minutes.")
        elif launch_age_minutes < 60:
            score += 24
            drivers.append("Launch is still within the first hour.")
        elif launch_age_minutes < 1440:
            score += 10
            drivers.append("Token is still within the first 24 hours of trading.")

    if usd_liquidity is None or usd_liquidity < 1_000:
        score += 24
        drivers.append("Initial liquidity remains under $1k.")
    elif usd_liquidity < 5_000:
        score += 16
        drivers.append("Initial liquidity remains under $5k.")
    elif usd_liquidity < 20_000:
        score += 8
        drivers.append("Liquidity is still shallow for a fresh launch.")

    if concentration == "high":
        score += 18
        drivers.append("Holder concentration is still elevated.")
    elif concentration == "medium":
        score += 8
        drivers.append("Launch concentration is still forming.")

    if early_cluster_activity == "suspicious":
        score += 18
        drivers.append("Early wallet clustering looks suspicious.")
    elif early_cluster_activity == "watch":
        score += 9
        drivers.append("Early cluster activity warrants monitoring.")

    if copycat_status == "collision":
        score += 16
        drivers.append("A name collision was detected in the market.")
    elif copycat_status == "possible":
        score += 8
        drivers.append("Possible copycat behaviour was detected.")

    if trade_caution_level == "avoid":
        score += 18
        drivers.append("Trade setup is currently in avoid territory.")
    elif trade_caution_level == "high":
        score += 12
        drivers.append("Trade caution remains elevated.")
    elif trade_caution_level == "moderate":
        score += 6
        drivers.append("Trade conditions are still unstable.")

    if market_execution_risk >= 70:
        score += 12
        drivers.append("Market execution risk is elevated for the current pool.")
    elif market_execution_risk >= 55:
        score += 6
        drivers.append("Pool execution quality still looks unstable.")

    if not holder_scan_complete:
        score += 8
        drivers.append("Holder coverage is still partial.")

    if page_mode == "mature":
        score = max(8, score - 22)
    elif page_mode == "early_market":
        score = max(score, 18)

    score = clamp_score(score)
    if score >= 85:
        level = "critical"
    elif score >= 65:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    if page_mode == "early_launch":
        summary = (
            "Launch-stage risk is still elevated because the token is new, liquidity is still forming, "
            "and early market structure can change quickly."
        )
    elif page_mode == "early_market":
        summary = (
            "Launch conditions are stabilizing, but first-day trading structure can still change quickly and "
            "should not be treated as final."
        )
    else:
        summary = (
            "Initial launch instability has mostly passed. Remaining launch risk is driven by leftover "
            "concentration or liquidity concerns rather than the first minutes of trading."
        )

    return LaunchRiskOverview(score=score, level=level, summary=summary, drivers=drivers[:4])


def build_launch_radar_overview(
    *,
    page_mode: PageMode,
    launch_age_minutes: int | None,
    usd_liquidity: float | None,
    top_10_share: float | None,
    top_1_share: float | None,
    trade_caution_level: str | None,
    market_execution_risk: int,
    volume_24h_usd: float | None,
    copycat_status: str,
    developer_cluster_signal: dict[str, float | int | bool | str | None],
    early_buyer_cluster_signal: dict[str, float | int | bool | str | None],
    insider_selling_signal: dict[str, float | int | bool | str | None],
) -> LaunchRadarOverview:
    trade_pressure = early_trade_pressure_label(
        trade_caution_level=trade_caution_level,
        market_execution_risk=market_execution_risk,
        volume_24h_usd=volume_24h_usd,
    )
    concentration = launch_concentration_label(top_10_share, top_1_share)
    early_cluster_activity = early_cluster_activity_label(
        developer_cluster_signal=developer_cluster_signal,
        early_buyer_cluster_signal=early_buyer_cluster_signal,
        insider_selling_signal=insider_selling_signal,
    )

    if page_mode == "early_launch":
        summary = (
            "This token is in its earliest launch stage. Initial liquidity is thin, and early market "
            "structure remains unstable. Use caution until broader holder and trading patterns emerge."
        )
    elif page_mode == "early_market":
        summary = (
            "This token is still in its first day of trading. Launch conditions are clearer than the first "
            "minutes, but holder structure and trade flow can still change rapidly."
        )
    else:
        summary = (
            "Launch radar is mostly contextual for mature tokens. It is useful as history, but current "
            "behavioural and market structure signals matter more than first-launch conditions."
        )

    return LaunchRadarOverview(
        launch_age_minutes=launch_age_minutes,
        initial_liquidity_band=liquidity_band(usd_liquidity),
        early_trade_pressure=trade_pressure,
        launch_concentration=concentration,
        copycat_status=copycat_status,
        early_cluster_activity=early_cluster_activity,
        summary=summary,
    )


def build_early_warnings(
    *,
    launch_age_minutes: int | None,
    usd_liquidity: float | None,
    holder_scan_complete: bool,
    trade_pressure: str,
    copycat_status: str,
    early_cluster_activity: str,
    listed_on_known_aggregator: bool,
) -> list[str]:
    warnings: list[str] = []

    if launch_age_minutes is not None and launch_age_minutes < 15:
        warnings.append("New launch under 15 minutes")
    elif launch_age_minutes is not None and launch_age_minutes < 60:
        warnings.append("Launch remains under 60 minutes old")

    if usd_liquidity is None or usd_liquidity < 1_000:
        warnings.append("Thin liquidity profile")
    elif usd_liquidity < 5_000:
        warnings.append("Liquidity still shallow")

    if not holder_scan_complete:
        warnings.append("Limited holder visibility")

    if trade_pressure == "aggressive":
        warnings.append("Early volatility elevated")

    if copycat_status == "collision":
        warnings.append("Name collision detected")
    elif copycat_status == "possible":
        warnings.append("Possible copycat pattern detected")

    if early_cluster_activity == "suspicious":
        warnings.append("Deployer history unavailable or suspicious")
    elif not listed_on_known_aggregator:
        warnings.append("Market source still limited")

    return warnings[:6]


def build_token_timeline(
    *,
    page_mode: PageMode,
    market_age: str,
    launch_age_minutes: int | None,
    market_source: str,
    usd_liquidity: float | None,
    top_10_share: float | None,
    holder_scan_complete: bool,
    largest_accounts_available: bool,
    early_warnings: list[str],
    mint_authority_enabled: bool,
    freeze_authority_enabled: bool,
) -> list[TimelineEvent]:
    refresh_value = (
        "Fetched from Solana RPC"
        if largest_accounts_available and holder_scan_complete
        else "Fetched with partial holder scan"
        if largest_accounts_available
        else "Fetched with partial RPC coverage"
    )

    if page_mode in {"early_launch", "early_market"}:
        first_trade_value = (
            "Earliest launch trades are still forming"
            if launch_age_minutes is not None and launch_age_minutes < 15
            else "Launch trade flow is now visible"
            if launch_age_minutes is not None and launch_age_minutes < 60
            else "Ongoing first-day trading activity"
            if launch_age_minutes is not None and launch_age_minutes < 1440
            else "Trade flow snapshot is still forming"
        )
        warnings_value = ", ".join(early_warnings[:3]) if early_warnings else "No acute early warnings were triggered"
        warning_tone: TimelineTone = (
            "danger"
            if any(
                warning in {"Thin liquidity profile", "Name collision detected", "Deployer history unavailable or suspicious"}
                for warning in early_warnings
            )
            else "warn"
            if early_warnings
            else "neutral"
        )
        return [
            TimelineEvent(label="Token detected", value=f"Launch age {market_age}", tone="neutral"),
            TimelineEvent(
                label="Pair / pool detected",
                value=market_source,
                tone="neutral" if "not available" not in market_source.lower() else "warn",
            ),
            TimelineEvent(
                label="Liquidity added",
                value=format_usd_liquidity(usd_liquidity),
                tone="warn" if (usd_liquidity or 0.0) < 5_000 else "neutral",
            ),
            TimelineEvent(label="First trades observed", value=first_trade_value, tone="neutral"),
            TimelineEvent(label="Background refresh completed", value=refresh_value, tone="neutral"),
            TimelineEvent(label="Early warnings triggered", value=warnings_value, tone=warning_tone),
        ]

    return [
        TimelineEvent(
            label="Mint authority",
            value="Enabled" if mint_authority_enabled else "Revoked",
            tone="danger" if mint_authority_enabled else "neutral",
        ),
        TimelineEvent(
            label="Freeze authority",
            value="Enabled" if freeze_authority_enabled else "Revoked",
            tone="warn" if freeze_authority_enabled else "neutral",
        ),
        TimelineEvent(label="Market age", value=market_age, tone="neutral"),
        TimelineEvent(
            label="Top 10 holder share",
            value=(
                format_share(top_10_share)
                if top_10_share is not None and holder_scan_complete
                else f"{format_share(top_10_share)} (partial scan)"
                if top_10_share is not None
                else "Unavailable from RPC"
            ),
            tone=(
                "danger"
                if top_10_share is not None and top_10_share >= 80
                else "warn"
                if top_10_share is not None and top_10_share >= 50
                else "neutral"
            ),
        ),
        TimelineEvent(label="Background refresh", value=refresh_value, tone="neutral"),
        TimelineEvent(label="Market source", value=market_source, tone="neutral"),
    ]


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def norm(value: float | None, lower: float, upper: float) -> float:
    if value is None:
        return 0.5
    if upper <= lower:
        return 0.0
    return clamp_unit((value - lower) / (upper - lower))


def norm_inverse_log(value: float | None, lower: float, upper: float) -> float:
    if value is None or value <= 0:
        return 1.0
    if lower <= 0:
        lower = 1.0
    if upper <= lower:
        return 0.0

    from math import log10

    value_c = max(lower, min(upper, value))
    normalized = (log10(value_c) - log10(lower)) / (log10(upper) - log10(lower))
    return clamp_unit(1 - normalized)


def build_weighted_risk_breakdown(
    *,
    technical_risk: int,
    distribution_risk: int,
    market_execution_risk: int,
    behaviour_risk: int,
    market_maturity: int,
) -> list[RiskBreakdownItem]:
    score_map: dict[str, tuple[int, str]] = {
        "Technical risk": (technical_risk, "risk"),
        "Distribution risk": (distribution_risk, "risk"),
        "Market / execution risk": (market_execution_risk, "risk"),
        "Behaviour risk": (behaviour_risk, "risk"),
        "Market maturity": (market_maturity, "positive"),
    }
    items: list[RiskBreakdownItem] = []
    for block, weight in RISK_BLOCK_WEIGHTS.items():
        score, kind = score_map.get(block, (0, "risk"))
        weighted_score = round(score * weight, 2)
        items.append(
            RiskBreakdownItem(
                block=block,
                score=score,
                weight=weight,
                weighted_score=weighted_score,
                kind=kind,
            )
        )
    return items


def build_behaviour_analysis(
    *,
    dev_cluster_share: float,
    developer_cluster_detected: bool,
    developer_cluster_wallet_count: int,
    developer_cluster_supply_control_pct: float,
    developer_cluster_shared_funder: str | None,
    early_buyer_cluster_detected: bool,
    early_buyer_cluster_wallet_count: int,
    early_buyer_cluster_supply_pct: float,
    early_buyer_cluster_shared_funder: str | None,
    insider_selling_detected: bool,
    insider_liquidity_correlation: bool,
    insider_seller_wallet_count: int,
    insider_seller_supply_control_pct: float,
    early_dump_detected: bool,
    liquidity_management_detected: bool,
    liquidity_management_summary: str,
    liquidity_management_details: str,
    liquidity_management_severity: str,
    lp_owner_is_deployer: bool,
    lp_lock_missing: bool,
    liquidity_removal_pattern: bool,
    suspicious_liquidity_control: bool,
) -> list[BehaviourInsightItem]:
    cluster_detected = developer_cluster_detected or dev_cluster_share >= 0.35
    cluster_size = (
        developer_cluster_wallet_count
        if developer_cluster_detected
        else max(2, int(round(dev_cluster_share * 12))) if cluster_detected else 0
    )
    supply_control_pct = int(round(
        developer_cluster_supply_control_pct if developer_cluster_detected else (dev_cluster_share * 100)
    ))

    developer_cluster = BehaviourInsightItem(
        key="developer_wallet_cluster",
        title="Developer wallet cluster",
        status="Developer-linked cluster detected" if cluster_detected else "No clear developer cluster detected",
        summary=(
            (
                "Multiple holder wallets appear linked through a shared funding source."
                if developer_cluster_detected and developer_cluster_shared_funder
                else "Wallet concentration and control patterns suggest a connected developer-linked cluster."
            )
            if cluster_detected
            else "No strong evidence of multi-wallet developer control was detected from current holder behaviour."
        ),
        tone="red" if developer_cluster_detected and supply_control_pct >= 20 else "orange" if cluster_detected else "green",
        details=(
            [
                f"Cluster size: approximately {cluster_size} wallets",
                f"Estimated supply control: {supply_control_pct}%",
                (
                    f"Shared funding source detected: {developer_cluster_shared_funder[:4]}...{developer_cluster_shared_funder[-4:]}"
                    if developer_cluster_detected and developer_cluster_shared_funder
                    else "Funding-source overlap and wallet timing should be reviewed together."
                ),
            ]
            if cluster_detected
            else ["No meaningful wallet-overlap or coordinated-control pattern was inferred from available holder data."]
        ),
    )

    early_buyer_clustered = early_buyer_cluster_detected or dev_cluster_share >= 0.45 or early_dump_detected
    early_buyer = BehaviourInsightItem(
        key="early_buyer_concentration",
        title="Early buyer concentration",
        status="Elevated early-buyer clustering" if early_buyer_clustered else "No major early-buyer concentration detected",
        summary=(
            (
                "Multiple early holder wallets appear linked through shared funding and closely aligned activity timing."
                if early_buyer_cluster_detected
                else "Early buyers appear clustered and may reflect coordinated initial accumulation."
            )
            if early_buyer_clustered
            else "No material clustering pattern was detected among early buyers."
        ),
        tone="red" if early_buyer_cluster_detected and early_buyer_cluster_supply_pct >= 20 else "orange" if early_buyer_clustered else "green",
        details=(
            [
                (
                    f"Estimated supply bought by clustered early wallets: {early_buyer_cluster_supply_pct:.1f}%"
                    if early_buyer_cluster_detected
                    else f"Estimated supply bought by clustered early wallets: {max(12, supply_control_pct)}%"
                ),
                (
                    f"Cluster size: approximately {early_buyer_cluster_wallet_count} wallets"
                    if early_buyer_cluster_detected
                    else "Wallet timing and shared funding routes should be reviewed for coordination."
                ),
                (
                    f"Shared funding source detected: {early_buyer_cluster_shared_funder[:4]}...{early_buyer_cluster_shared_funder[-4:]}"
                    if early_buyer_cluster_detected and early_buyer_cluster_shared_funder
                    else "No shared early-buyer funding source was confirmed from available data."
                ),
            ]
            if early_buyer_clustered
            else ["Available data does not indicate abnormal early concentration or block-level clustering."]
        ),
    )

    insider_pattern = insider_selling_detected or (early_dump_detected and dev_cluster_share >= 0.35)
    insider_selling = BehaviourInsightItem(
        key="insider_selling_patterns",
        title="Insider selling patterns",
        status="Possible insider exit pattern detected" if insider_pattern else "No insider selling pattern detected",
        summary=(
            (
                "Multiple large holder wallets recently executed outgoing token transfers while liquidity conditions also appear weak."
                if insider_liquidity_correlation
                else "Multiple large holder wallets recently executed outgoing token transfers consistent with a coordinated exit pattern."
                if insider_selling_detected
                else "Large or related wallets show behaviour consistent with a coordinated exit pattern."
            )
            if insider_pattern
            else "No coordinated insider-selling pattern was detected from current behaviour signals."
        ),
        tone="red" if insider_liquidity_correlation else "red" if insider_pattern else "green",
        details=(
            [
                (
                    f"Tracked seller wallets: {insider_seller_wallet_count}"
                    if insider_selling_detected
                    else "Large-holder behaviour suggests selling pressure from related wallets."
                ),
                (
                    f"Estimated supply represented by recent seller wallets: {insider_seller_supply_control_pct:.1f}%"
                    if insider_selling_detected
                    else "Exit timing should be reviewed against liquidity weakness and market deterioration."
                ),
                (
                    "Recent selling activity overlaps with weak liquidity or LP protection signals."
                    if insider_liquidity_correlation
                    else "No direct liquidity-stress correlation was confirmed from current market-structure data."
                ),
            ]
            if insider_pattern
            else ["No meaningful pre-collapse exit signal was inferred from observed wallet behaviour."]
        ),
    )

    liquidity_behaviour_risky = liquidity_management_detected or (
        lp_owner_is_deployer or lp_lock_missing or liquidity_removal_pattern or suspicious_liquidity_control
    )
    liquidity_behaviour = BehaviourInsightItem(
        key="liquidity_management_behaviour",
        title="Liquidity management behaviour",
        status="Potentially risky liquidity management" if liquidity_behaviour_risky else "No unusual liquidity management detected",
        summary=(
            liquidity_management_summary
            if liquidity_management_detected
            else "Liquidity ownership, lock status, or withdrawal behaviour shows patterns that warrant closer review."
            if liquidity_behaviour_risky
            else "No clear add-remove or developer-controlled liquidity pattern was detected."
        ),
        tone=(
            "red"
            if liquidity_management_severity == "red"
            else "orange"
            if liquidity_behaviour_risky
            else "green"
        ),
        details=(
            [
                liquidity_management_details,
                "LP ownership appears concentrated around a controlling wallet." if lp_owner_is_deployer else "No direct deployer LP control was inferred.",
                "LP burn or lock protection appears weak." if lp_lock_missing else "No missing LP lock signal was detected.",
                "Liquidity removal behaviour appears suspicious." if liquidity_removal_pattern else "No rapid liquidity withdrawal pattern was detected.",
            ]
            if liquidity_behaviour_risky
            else ["Liquidity behaviour does not currently match a classic rug liquidity pattern."]
        ),
    )

    return [developer_cluster, early_buyer, insider_selling, liquidity_behaviour]


def flatten_behaviour_analysis_v2(
    behaviour_analysis: BehaviourAnalysisOverview | None,
) -> list[BehaviourInsightItem]:
    if behaviour_analysis is None:
        return []

    tone_map = {
        "clear": "green",
        "watch": "yellow",
        "flagged": "red",
    }
    ordered_keys = (
        "developer_cluster",
        "early_buyers",
        "insider_selling",
        "liquidity_management",
    )
    items: list[BehaviourInsightItem] = []
    for key in ordered_keys:
        module = behaviour_analysis.modules.get(key)
        if module is None:
            continue
        items.append(
            BehaviourInsightItem(
                key=module.key,
                title=module.title,
                status=module.status.replace("_", " ").title(),
                summary=module.summary,
                tone=tone_map.get(module.status, "green"),  # type: ignore[arg-type]
                details=module.details,
            )
        )
    return items


def token_age_label(block_time: int | None) -> tuple[str, int | None]:
    label, age_days, _ = token_age_snapshot(block_time)
    return label, age_days


def fetch_token_asset_profile(
    rpc_client: SolanaRpcClient,
    mint_address: str,
) -> tuple[str | None, str | None, str | None]:
    helius_url = next((url for url in rpc_client.rpc_urls if "helius" in url), None)
    if helius_url is None:
        return None, None, None

    try:
        asset = rpc_client.call_with_url(helius_url, "getAsset", {"id": mint_address})
    except SolanaRpcError:
        return None, None, None

    content = asset.get("content") or {}
    metadata = content.get("metadata") or {}
    links = content.get("links") or {}
    token_info = asset.get("token_info") or {}

    name = metadata.get("name")
    symbol = token_info.get("symbol") or metadata.get("symbol")
    logo_url = links.get("image")
    return name, symbol, logo_url


def extract_holder_shares_from_program_accounts(
    rpc_client: SolanaRpcClient,
    token_program_id: str,
    mint_address: str,
    ui_supply: float,
) -> tuple[float | None, float | None]:
    if ui_supply <= 0:
        return None, None

    program_accounts = rpc_client.call(
        "getProgramAccounts",
        [
            token_program_id,
            {
                "encoding": "jsonParsed",
                "filters": [
                    {"memcmp": {"offset": 0, "bytes": mint_address}},
                ],
            },
        ],
    )

    holder_amounts: list[float] = []
    for account in program_accounts:
        parsed = account.get("account", {}).get("data", {}).get("parsed", {})
        if parsed.get("type") != "account":
            continue
        token_amount = parsed.get("info", {}).get("tokenAmount", {})
        ui_amount = float(token_amount.get("uiAmount") or 0)
        if ui_amount > 0:
            holder_amounts.append(ui_amount)

    if not holder_amounts:
        return None, None

    holder_amounts.sort(reverse=True)
    top_10_total = sum(holder_amounts[:10])
    top_1_total = holder_amounts[0]
    return (top_10_total / ui_supply * 100), (top_1_total / ui_supply * 100)


def extract_holder_shares_from_helius_token_accounts(
    rpc_client: SolanaRpcClient,
    mint_address: str,
    ui_supply: float,
    decimals: int,
    max_pages: int,
) -> tuple[float | None, float | None, bool]:
    if ui_supply <= 0:
        return None, None, True

    owner_amounts: dict[str, int] = {}
    cursor: str | None = None
    page = 1
    is_complete = True

    while page <= max_pages:
        params: dict[str, object] = {
            "mint": mint_address,
            "limit": 1000,
        }
        if cursor:
            params["cursor"] = cursor
        else:
            params["page"] = page

        result = rpc_client.call("getTokenAccounts", params)

        token_accounts = result.get("token_accounts", [])
        total_accounts = int(result.get("total") or 0)
        limit = int(result.get("limit") or 1000)
        current_page = int(result.get("page") or page)
        if not token_accounts:
            break

        for token_account in token_accounts:
            owner = token_account.get("owner")
            amount = int(token_account.get("amount") or 0)
            if owner and amount > 0:
                owner_amounts[owner] = owner_amounts.get(owner, 0) + amount

        cursor = result.get("cursor")
        has_more_by_cursor = bool(cursor)
        has_more_by_page = total_accounts > current_page * limit
        if len(token_accounts) < limit or (not has_more_by_cursor and not has_more_by_page):
            break

        page += 1
    else:
        is_complete = False

    if not owner_amounts:
        return None, None, is_complete

    sorted_amounts = sorted(owner_amounts.values(), reverse=True)
    scale = 10**decimals
    top_10_total = sum(sorted_amounts[:10]) / scale
    top_1_total = sorted_amounts[0] / scale
    return (top_10_total / ui_supply * 100), (top_1_total / ui_supply * 100), is_complete


def extract_top_holder_owner_shares(
    rpc_client: SolanaRpcClient,
    largest_accounts: list[dict],
    ui_supply: float,
    *,
    limit: int = 6,
) -> dict[str, float]:
    if ui_supply <= 0:
        return {}

    owner_shares: dict[str, float] = {}
    for item in largest_accounts[:limit]:
        token_account = item.get("address")
        if not token_account:
            continue
        try:
            token_account_info = rpc_client.call(
                "getAccountInfo",
                [token_account, {"encoding": "jsonParsed", "commitment": "confirmed"}],
            )
        except SolanaRpcError:
            continue

        parsed = ((token_account_info.get("value") or {}).get("data") or {}).get("parsed") or {}
        owner = (((parsed.get("info") or {}).get("owner")) or "").strip()
        ui_amount = float(item.get("uiAmount") or 0)
        if not owner or ui_amount <= 0:
            continue
        owner_shares[owner] = owner_shares.get(owner, 0.0) + ((ui_amount / ui_supply) * 100)
    return owner_shares


def extract_inbound_funding_sources(
    rpc_client: SolanaRpcClient,
    wallet_address: str,
    *,
    signature_limit: int = 6,
    transaction_limit: int = 4,
) -> set[str]:
    cache_key = _behaviour_cache_key("inbound_funders", wallet_address, signature_limit, transaction_limit)
    cached = _behaviour_cache_get(cache_key)
    if isinstance(cached, set):
        return cached

    try:
        signatures = rpc_client.call(
            "getSignaturesForAddress",
            [wallet_address, {"limit": signature_limit, "commitment": "confirmed"}],
        )
    except SolanaRpcError:
        return set()

    funders: set[str] = set()
    for item in signatures[:transaction_limit]:
        signature = item.get("signature")
        if not signature:
            continue
        try:
            transaction = rpc_client.call(
                "getTransaction",
                [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            )
        except SolanaRpcError:
            continue

        instructions = (((transaction.get("transaction") or {}).get("message")) or {}).get("instructions") or []
        for instruction in instructions:
            if instruction.get("program") != "system":
                continue
            parsed = instruction.get("parsed") or {}
            info = parsed.get("info") or {}
            if parsed.get("type") == "transfer" and info.get("destination") == wallet_address:
                source = (info.get("source") or "").strip()
                if source and source != wallet_address:
                    funders.add(source)
    return _behaviour_cache_set(cache_key, funders)  # type: ignore[return-value]


def extract_multi_hop_funding_sources(
    rpc_client: SolanaRpcClient,
    wallet_address: str,
    *,
    depth: int = 2,
) -> dict[int, set[str]]:
    cache_key = _behaviour_cache_key("multi_hop_funders", wallet_address, depth)
    cached = _behaviour_cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    hops: dict[int, set[str]] = {}
    current_level = extract_inbound_funding_sources(rpc_client, wallet_address, signature_limit=8, transaction_limit=5)
    if current_level:
        hops[1] = set(current_level)

    visited = set(current_level)
    for level in range(2, depth + 1):
        next_level: set[str] = set()
        for source_wallet in hops.get(level - 1, set()):
            parent_sources = extract_inbound_funding_sources(
                rpc_client,
                source_wallet,
                signature_limit=6,
                transaction_limit=4,
            )
            for parent in parent_sources:
                if parent != wallet_address and parent not in visited:
                    next_level.add(parent)
                    visited.add(parent)
        if not next_level:
            break
        hops[level] = next_level

    return _behaviour_cache_set(cache_key, hops)  # type: ignore[return-value]


def extract_recent_wallet_activity_times(
    rpc_client: SolanaRpcClient,
    wallet_address: str,
    *,
    signature_limit: int = 6,
) -> list[int]:
    cache_key = _behaviour_cache_key("activity_times", wallet_address, signature_limit)
    cached = _behaviour_cache_get(cache_key)
    if isinstance(cached, list):
        return cached

    try:
        signatures = rpc_client.call(
            "getSignaturesForAddress",
            [wallet_address, {"limit": signature_limit, "commitment": "confirmed"}],
        )
    except SolanaRpcError:
        return []

    times: list[int] = []
    for item in signatures:
        block_time = item.get("blockTime")
        if isinstance(block_time, int) and block_time > 0:
            times.append(block_time)
    return _behaviour_cache_set(cache_key, sorted(times))  # type: ignore[return-value]


def extract_recent_wallet_transfer_partners(
    rpc_client: SolanaRpcClient,
    wallet_address: str,
    *,
    signature_limit: int = 6,
    transaction_limit: int = 4,
) -> set[str]:
    cache_key = _behaviour_cache_key("transfer_partners", wallet_address, signature_limit, transaction_limit)
    cached = _behaviour_cache_get(cache_key)
    if isinstance(cached, set):
        return cached

    try:
        signatures = rpc_client.call(
            "getSignaturesForAddress",
            [wallet_address, {"limit": signature_limit, "commitment": "confirmed"}],
        )
    except SolanaRpcError:
        return set()

    partners: set[str] = set()
    for item in signatures[:transaction_limit]:
        signature = item.get("signature")
        if not signature:
            continue
        try:
            transaction = rpc_client.call(
                "getTransaction",
                [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            )
        except SolanaRpcError:
            continue

        instructions = (((transaction.get("transaction") or {}).get("message")) or {}).get("instructions") or []
        for instruction in instructions:
            parsed = instruction.get("parsed") or {}
            info = parsed.get("info") or {}
            source = (info.get("source") or "").strip()
            destination = (info.get("destination") or "").strip()
            authority = (info.get("authority") or info.get("owner") or "").strip()
            if source == wallet_address and destination:
                partners.add(destination)
            elif destination == wallet_address and source:
                partners.add(source)
            elif authority == wallet_address:
                if destination:
                    partners.add(destination)
                elif source and source != wallet_address:
                    partners.add(source)
    return _behaviour_cache_set(cache_key, partners)  # type: ignore[return-value]


def compute_time_similarity_score(activity_times: dict[str, list[int]], wallets: list[str]) -> float:
    first_seen = [activity_times[wallet][0] for wallet in wallets if activity_times.get(wallet)]
    if len(first_seen) < 2:
        return 0.0
    time_span = max(first_seen) - min(first_seen)
    if time_span <= 300:
        return 1.0
    if time_span <= 1800:
        return 0.75
    if time_span <= 3600:
        return 0.55
    if time_span <= 21600:
        return 0.30
    return 0.10


def detect_developer_wallet_cluster(
    rpc_client: SolanaRpcClient,
    owner_shares: dict[str, float],
) -> dict[str, float | int | bool | str | None]:
    owners = [owner for owner, share in sorted(owner_shares.items(), key=lambda item: item[1], reverse=True) if share > 0]
    if len(owners) < 2:
        return {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "confidence": 0.0,
        }

    funding_map: dict[str, set[str]] = {}
    multi_hop_funding_map: dict[str, dict[int, set[str]]] = {}
    activity_map: dict[str, list[int]] = {}
    partner_map: dict[str, set[str]] = {}
    for owner in owners[:4]:
        funders = extract_inbound_funding_sources(rpc_client, owner)
        if funders:
            funding_map[owner] = funders
        multi_hop_sources = extract_multi_hop_funding_sources(rpc_client, owner, depth=2)
        if multi_hop_sources:
            multi_hop_funding_map[owner] = multi_hop_sources
        activity_times = extract_recent_wallet_activity_times(rpc_client, owner, signature_limit=8)
        if activity_times:
            activity_map[owner] = activity_times
        partners = extract_recent_wallet_transfer_partners(rpc_client, owner, signature_limit=8, transaction_limit=5)
        if partners:
            partner_map[owner] = partners

    best_funder: str | None = None
    best_cluster: list[str] = []
    for owner, funders in funding_map.items():
        for funder in funders:
            cluster_wallets = [candidate for candidate, sources in funding_map.items() if funder in sources]
            if len(cluster_wallets) > len(best_cluster):
                best_cluster = cluster_wallets
                best_funder = funder

    tracked_wallets = max(1, len(funding_map) or len(owners[:4]))
    if len(best_cluster) < 2:
        return {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "shared_funding_ratio": 0.0,
            "timing_similarity_score": 0.0,
            "direct_wallet_overlap_count": 0,
            "shared_outgoing_wallets_count": 0,
            "multi_hop_shared_funder_count": 0,
            "funding_trace_depth_avg": 0.0,
            "confidence": 0.0,
        }

    cluster_supply_control = sum(owner_shares.get(owner, 0.0) for owner in best_cluster)
    shared_funding_ratio = len(best_cluster) / tracked_wallets
    timing_similarity_score = compute_time_similarity_score(activity_map, best_cluster)
    direct_wallet_overlap_count = 0
    shared_outgoing_wallets_count = 0
    multi_hop_shared_funder_count = 0
    funding_trace_depth_avg = 1.0 if best_funder else 0.0
    if partner_map:
        direct_wallet_overlap_count = sum(
            1
            for owner in best_cluster
            for candidate in best_cluster
            if owner != candidate and candidate in partner_map.get(owner, set())
        )
        partner_sets = [partner_map.get(owner, set()) for owner in best_cluster if partner_map.get(owner)]
        if len(partner_sets) >= 2:
            shared_outgoing_wallets_count = len(set.intersection(*partner_sets)) if partner_sets else 0
    if multi_hop_funding_map:
        second_hop_sets = [multi_hop_funding_map.get(owner, {}).get(2, set()) for owner in best_cluster if multi_hop_funding_map.get(owner, {}).get(2)]
        if len(second_hop_sets) >= 2:
            shared_second_hop = set.intersection(*second_hop_sets)
            multi_hop_shared_funder_count = len(shared_second_hop)
            if multi_hop_shared_funder_count > 0:
                funding_trace_depth_avg = 2.0
    composite_signal = (
        0.45 * shared_funding_ratio
        + 0.25 * min(1.0, cluster_supply_control / 30.0)
        + 0.20 * timing_similarity_score
        + 0.10 * min(1.0, direct_wallet_overlap_count / 2.0)
        + 0.05 * min(1.0, multi_hop_shared_funder_count / 2.0)
    )
    detected = (
        shared_funding_ratio >= settings.behaviour_shared_funding_ratio_warn
        and (
            cluster_supply_control >= settings.behaviour_cluster_supply_warn
            or timing_similarity_score >= settings.behaviour_timing_similarity_warn
            or direct_wallet_overlap_count > 0
        )
    ) or composite_signal >= 0.58
    confidence = min(
        0.95,
        0.30
        + (0.25 * shared_funding_ratio)
        + (0.20 * timing_similarity_score)
        + (0.15 * min(1.0, cluster_supply_control / 25.0))
        + (0.10 * min(1.0, direct_wallet_overlap_count / 2.0)),
    ) if detected else 0.0
    return {
        "detected": detected,
        "cluster_wallet_count": len(best_cluster),
        "cluster_supply_control_pct": round(cluster_supply_control, 1),
        "shared_funder": best_funder,
        "lead_wallet": best_cluster[0] if best_cluster else None,
        "shared_funding_ratio": round(shared_funding_ratio, 4),
        "timing_similarity_score": round(timing_similarity_score, 4),
        "direct_wallet_overlap_count": direct_wallet_overlap_count,
        "shared_outgoing_wallets_count": shared_outgoing_wallets_count,
        "multi_hop_shared_funder_count": multi_hop_shared_funder_count,
        "funding_trace_depth_avg": round(funding_trace_depth_avg, 2),
        "confidence": round(confidence, 4),
    }


def detect_early_buyer_clustering(
    rpc_client: SolanaRpcClient,
    owner_shares: dict[str, float],
    market_age_days: int | None,
) -> dict[str, float | int | bool | str | None]:
    if market_age_days is None or market_age_days > 45:
        return {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "confidence": 0.0,
        }

    owners = [owner for owner, share in sorted(owner_shares.items(), key=lambda item: item[1], reverse=True) if share > 0]
    if len(owners) < 2:
        return {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "confidence": 0.0,
        }

    funding_map: dict[str, set[str]] = {}
    multi_hop_funding_map: dict[str, dict[int, set[str]]] = {}
    activity_map: dict[str, list[int]] = {}
    for owner in owners[:4]:
        funders = extract_inbound_funding_sources(rpc_client, owner, signature_limit=8, transaction_limit=5)
        activity_times = extract_recent_wallet_activity_times(rpc_client, owner, signature_limit=8)
        if funders:
            funding_map[owner] = funders
        multi_hop_sources = extract_multi_hop_funding_sources(rpc_client, owner, depth=2)
        if multi_hop_sources:
            multi_hop_funding_map[owner] = multi_hop_sources
        if activity_times:
            activity_map[owner] = activity_times

    best_funder: str | None = None
    best_cluster: list[str] = []
    best_time_span: int | None = None

    for owner, funders in funding_map.items():
        for funder in funders:
            cluster_wallets = [candidate for candidate, sources in funding_map.items() if funder in sources]
            if len(cluster_wallets) < 2:
                continue
            observed_times = [activity_map[candidate][0] for candidate in cluster_wallets if activity_map.get(candidate)]
            if len(observed_times) < 2:
                continue
            time_span = max(observed_times) - min(observed_times)
            if time_span <= 3600 and (
                len(cluster_wallets) > len(best_cluster)
                or (len(cluster_wallets) == len(best_cluster) and (best_time_span is None or time_span < best_time_span))
            ):
                best_cluster = cluster_wallets
                best_funder = funder
                best_time_span = time_span

    tracked_wallets = max(1, len(funding_map) or len(owners[:4]))
    if len(best_cluster) < 2:
        return {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "shared_funding_ratio": 0.0,
            "same_window_buy_density": 0.0,
            "buy_size_similarity_score": 0.0,
            "overlap_with_top_holders": 0.0,
            "multi_hop_shared_funder_count": 0,
            "funding_trace_depth_avg": 0.0,
            "confidence": 0.0,
        }

    cluster_supply_control = sum(owner_shares.get(owner, 0.0) for owner in best_cluster)
    shared_funding_ratio = len(best_cluster) / tracked_wallets
    same_window_buy_density = (
        min(1.0, (settings.behaviour_early_same_window_seconds / max(best_time_span, 1)))
        if best_time_span is not None and best_time_span > 0
        else 0.0
    )
    cluster_wallet_shares = [owner_shares.get(owner, 0.0) for owner in best_cluster]
    share_spread = (max(cluster_wallet_shares) - min(cluster_wallet_shares)) if cluster_wallet_shares else 0.0
    buy_size_similarity_score = max(0.0, min(1.0, 1.0 - (share_spread / 20.0)))
    overlap_with_top_holders = cluster_supply_control / max(sum(owner_shares.values()), 1.0)
    multi_hop_shared_funder_count = 0
    funding_trace_depth_avg = 1.0 if best_funder else 0.0
    second_hop_sets = [multi_hop_funding_map.get(owner, {}).get(2, set()) for owner in best_cluster if multi_hop_funding_map.get(owner, {}).get(2)]
    if len(second_hop_sets) >= 2:
        shared_second_hop = set.intersection(*second_hop_sets)
        multi_hop_shared_funder_count = len(shared_second_hop)
        if multi_hop_shared_funder_count > 0:
            funding_trace_depth_avg = 2.0
    detected = (
        shared_funding_ratio >= settings.behaviour_shared_funding_ratio_warn
        and same_window_buy_density >= 0.50
    ) or (
        buy_size_similarity_score >= settings.behaviour_early_buy_size_similarity_warn
        and overlap_with_top_holders >= settings.behaviour_early_buyer_overlap_warn
    ) or (
        multi_hop_shared_funder_count > 0
        and same_window_buy_density >= 0.40
    )
    confidence = min(
        0.95,
        0.25
        + (0.25 * shared_funding_ratio)
        + (0.20 * same_window_buy_density)
        + (0.15 * buy_size_similarity_score)
        + (0.15 * overlap_with_top_holders),
    ) if detected else 0.0
    return {
        "detected": detected,
        "cluster_wallet_count": len(best_cluster),
        "cluster_supply_control_pct": round(cluster_supply_control, 1),
        "shared_funder": best_funder,
        "lead_wallet": best_cluster[0] if best_cluster else None,
        "shared_funding_ratio": round(shared_funding_ratio, 4),
        "same_window_buy_density": round(same_window_buy_density, 4),
        "buy_size_similarity_score": round(buy_size_similarity_score, 4),
        "overlap_with_top_holders": round(overlap_with_top_holders, 4),
        "multi_hop_shared_funder_count": multi_hop_shared_funder_count,
        "funding_trace_depth_avg": round(funding_trace_depth_avg, 2),
        "confidence": round(confidence, 4),
    }


def detect_insider_selling_pattern(
    rpc_client: SolanaRpcClient,
    largest_accounts: list[dict],
    ui_supply: float,
    mint_address: str,
    *,
    limit: int = 4,
    signature_limit: int = 6,
) -> dict[str, float | int | bool]:
    if ui_supply <= 0 or not largest_accounts:
        return {
            "detected": False,
            "seller_wallet_count": 0,
            "seller_supply_control_pct": 0.0,
            "confidence": 0.0,
        }

    seller_wallets: set[str] = set()
    seller_supply_control = 0.0
    sell_times: list[int] = []

    for item in largest_accounts[:limit]:
        token_account = item.get("address")
        ui_amount = float(item.get("uiAmount") or 0)
        if not token_account or ui_amount <= 0:
            continue
        try:
            signatures = rpc_client.call(
                "getSignaturesForAddress",
                [token_account, {"limit": signature_limit, "commitment": "confirmed"}],
            )
        except SolanaRpcError:
            continue

        token_account_owner = ""
        try:
            token_account_info = rpc_client.call(
                "getAccountInfo",
                [token_account, {"encoding": "jsonParsed", "commitment": "confirmed"}],
            )
            parsed = ((token_account_info.get("value") or {}).get("data") or {}).get("parsed") or {}
            token_account_owner = (((parsed.get("info") or {}).get("owner")) or "").strip()
        except SolanaRpcError:
            token_account_owner = ""

        outgoing_detected = False
        first_sell_time: int | None = None
        for signature_item in signatures[:signature_limit]:
            signature = signature_item.get("signature")
            if not signature:
                continue
            block_time = signature_item.get("blockTime")
            try:
                transaction = rpc_client.call(
                    "getTransaction",
                    [
                        signature,
                        {
                            "encoding": "jsonParsed",
                            "commitment": "confirmed",
                            "maxSupportedTransactionVersion": 0,
                        },
                    ],
                )
            except SolanaRpcError:
                continue

            instructions = (((transaction.get("transaction") or {}).get("message")) or {}).get("instructions") or []
            for instruction in instructions:
                program = instruction.get("program")
                if program not in {"spl-token", "spl-token-2022"}:
                    continue
                parsed = instruction.get("parsed") or {}
                info = parsed.get("info") or {}
                if parsed.get("type") not in {"transfer", "transferChecked"}:
                    continue
                source = (info.get("source") or "").strip()
                mint = (info.get("mint") or "").strip()
                authority = (info.get("authority") or info.get("owner") or "").strip()
                if source == token_account and (not mint or mint == mint_address):
                    if not token_account_owner or not authority or authority == token_account_owner:
                        outgoing_detected = True
                        if isinstance(block_time, int) and block_time > 0:
                            first_sell_time = block_time
                        break
            if outgoing_detected:
                break

        if outgoing_detected:
            seller_wallets.add(token_account_owner or token_account)
            seller_supply_control += (ui_amount / ui_supply) * 100
            if first_sell_time is not None:
                sell_times.append(first_sell_time)

    time_span = (max(sell_times) - min(sell_times)) if len(sell_times) >= 2 else None
    coordinated_exit_window_score = (
        1.0
        if time_span is not None and time_span <= settings.behaviour_coordinated_exit_window_seconds
        else 0.65
        if time_span is not None and time_span <= (settings.behaviour_coordinated_exit_window_seconds * 3)
        else 0.0
    )
    large_holder_sell_ratio_recent = seller_supply_control / 100.0
    detected = (
        len(seller_wallets) >= 2
        and seller_supply_control >= settings.behaviour_large_holder_sell_warn
        and coordinated_exit_window_score >= 0.65
    ) or (len(seller_wallets) >= 3 and seller_supply_control >= (settings.behaviour_large_holder_sell_warn * 0.75))
    confidence = min(
        0.95,
        0.25
        + (0.25 * min(1.0, len(seller_wallets) / 3.0))
        + (0.25 * coordinated_exit_window_score)
        + (0.25 * min(1.0, seller_supply_control / max(settings.behaviour_dev_cluster_sell_high, 1.0))),
    ) if detected else 0.0
    return {
        "detected": detected,
        "seller_wallet_count": len(seller_wallets),
        "seller_supply_control_pct": round(seller_supply_control, 1),
        "large_holder_sell_ratio_recent": round(large_holder_sell_ratio_recent, 4),
        "coordinated_exit_window_score": round(coordinated_exit_window_score, 4),
        "sell_window_span_seconds": time_span if time_span is not None else 0,
        "confidence": round(confidence, 4),
    }


def analyze_liquidity_management_behaviour(
    pair: dict | None,
    *,
    usd_liquidity: float | None,
    market_age_days: int | None,
    lp_lock_missing: bool,
    suspicious_liquidity_control: bool,
) -> dict[str, float | int | bool | str]:
    if pair is None:
        return {
            "detected": bool(lp_lock_missing or suspicious_liquidity_control),
            "severity": "orange" if (lp_lock_missing or suspicious_liquidity_control) else "green",
            "summary": (
                "Liquidity ownership or lock structure shows patterns that warrant closer review."
                if (lp_lock_missing or suspicious_liquidity_control)
                else "No clear liquidity-management anomaly was detected from available market data."
            ),
            "details": "LP structure data is limited for this market.",
            "rapid_liquidity_drop_score": 0.0,
            "liquidity_volatility_score": 0.0,
            "lp_owner_deployer_link_score": 1.0 if suspicious_liquidity_control else 0.0,
            "liquidity_change_vs_holder_exits_score": 0.0,
            "short_window_sell_pressure_score": 0.0,
            "short_window_price_drop_score": 0.0,
            "short_window_volume_acceleration_score": 0.0,
        }

    txns_h1 = ((pair.get("txns") or {}).get("h1") or {})
    txns_h24 = ((pair.get("txns") or {}).get("h24") or {})
    buys_h1 = int(txns_h1.get("buys") or 0)
    sells_h1 = int(txns_h1.get("sells") or 0)
    buys_h24 = int(txns_h24.get("buys") or 0)
    sells_h24 = int(txns_h24.get("sells") or 0)
    volume_h1 = float(((pair.get("volume") or {}).get("h1")) or 0.0)
    volume_h24 = float(((pair.get("volume") or {}).get("h24")) or 0.0)
    price_change_h1 = float(((pair.get("priceChange") or {}).get("h1")) or 0.0)
    price_change_h24 = float(((pair.get("priceChange") or {}).get("h24")) or 0.0)
    fdv = float(pair.get("fdv") or 0.0)
    labels = pair.get("labels") or []

    liquidity_to_fdv = ((usd_liquidity or 0.0) / fdv) if fdv > 0 else 0.0
    sell_pressure = sells_h24 > max(buys_h24 * 1.2, buys_h24 + 3)
    short_window_sell_pressure_score = (
        min(1.0, sells_h1 / max(float(buys_h1 + 1), 1.0))
        if (buys_h1 or sells_h1)
        else 0.0
    )
    short_window_price_drop_score = min(1.0, abs(price_change_h1) / 25.0) if price_change_h1 < 0 else 0.0
    short_window_volume_acceleration_score = (
        min(1.0, (volume_h1 * 24.0) / max(volume_h24, 1.0))
        if volume_h1 > 0 and volume_h24 > 0
        else 0.0
    )
    low_depth_vs_volume = bool((usd_liquidity or 0.0) > 0 and volume_h24 > (usd_liquidity or 0.0) * 0.75)
    young_thin_pair = bool((market_age_days or 9999) <= 30 and (usd_liquidity or 0.0) < 50_000)
    structural_risk = bool(liquidity_to_fdv < 0.01 and (usd_liquidity or 0.0) < 100_000)
    rapid_liquidity_drop_score = 1.0 if sell_pressure and structural_risk else 0.70 if structural_risk else 0.35 if young_thin_pair else 0.0
    liquidity_volatility_score = min(1.0, ((sells_h24 + buys_h24) / max(10.0, ((usd_liquidity or 0.0) / 5000.0)))) if (usd_liquidity or 0.0) > 0 else 0.0
    lp_owner_deployer_link_score = 1.0 if suspicious_liquidity_control else 0.50 if lp_lock_missing else 0.0
    liquidity_change_vs_holder_exits_score = (
        1.0
        if (sell_pressure and low_depth_vs_volume and short_window_price_drop_score >= 0.40)
        else 0.70
        if (sell_pressure and short_window_sell_pressure_score >= 0.90)
        else 0.45
        if sell_pressure
        else 0.0
    )

    detected = bool(
        lp_lock_missing
        or suspicious_liquidity_control
        or sell_pressure
        or low_depth_vs_volume
        or young_thin_pair
        or structural_risk
        or short_window_price_drop_score >= 0.45
        or short_window_volume_acceleration_score >= 0.85
    )
    severity = "red" if (sell_pressure and structural_risk) or suspicious_liquidity_control else "orange" if detected else "green"
    detail_parts = []
    if liquidity_to_fdv > 0:
        detail_parts.append(f"Liquidity/FDV ratio: {liquidity_to_fdv * 100:.2f}%")
    if buys_h1 or sells_h1:
        detail_parts.append(f"1h buys/sells: {buys_h1}/{sells_h1}")
    if buys_h24 or sells_h24:
        detail_parts.append(f"24h buys/sells: {buys_h24}/{sells_h24}")
    if volume_h1 > 0:
        detail_parts.append(f"1h volume: ${volume_h1:.2f}")
    if volume_h24 > 0:
        detail_parts.append(f"24h volume: ${volume_h24:.2f}")
    if price_change_h1:
        detail_parts.append(f"1h price change: {price_change_h1:.2f}%")
    if price_change_h24:
        detail_parts.append(f"24h price change: {price_change_h24:.2f}%")
    if labels:
        detail_parts.append(f"Pair labels: {', '.join(str(label) for label in labels)}")

    if sell_pressure and structural_risk and short_window_price_drop_score >= 0.40:
        summary = "Short-window selling pressure overlaps with thin liquidity and visible market deterioration."
    elif sell_pressure and structural_risk:
        summary = "Recent sell pressure overlaps with thin liquidity structure and weak market depth."
    elif suspicious_liquidity_control:
        summary = "Liquidity ownership and market structure suggest a potentially controllable LP setup."
    elif short_window_price_drop_score >= 0.45 and short_window_volume_acceleration_score >= 0.75:
        summary = "Short-window price deterioration and volume acceleration suggest unstable liquidity behaviour."
    elif young_thin_pair:
        summary = "The detected trading pair is still young and thin, which increases liquidity-management risk."
    elif detected:
        summary = "Liquidity structure shows stress signals that warrant closer review."
    else:
        summary = "No clear liquidity-management anomaly was detected from current pair behaviour."

    return {
        "detected": detected,
        "severity": severity,
        "summary": summary,
        "details": " | ".join(detail_parts) if detail_parts else "Pair behaviour appears stable from currently available market data.",
        "rapid_liquidity_drop_score": round(rapid_liquidity_drop_score, 4),
        "liquidity_volatility_score": round(liquidity_volatility_score, 4),
        "lp_owner_deployer_link_score": round(lp_owner_deployer_link_score, 4),
        "liquidity_change_vs_holder_exits_score": round(liquidity_change_vs_holder_exits_score, 4),
        "short_window_sell_pressure_score": round(short_window_sell_pressure_score, 4),
        "short_window_price_drop_score": round(short_window_price_drop_score, 4),
        "short_window_volume_acceleration_score": round(short_window_volume_acceleration_score, 4),
    }


def compute_token_scoring_v21(
    *,
    mint_authority_enabled: bool,
    freeze_authority_enabled: bool,
    update_authority_enabled: bool,
    dangerous_contract_capability_score: float,
    top_10_share: float | None,
    top_1_share: float | None,
    usd_liquidity: float | None,
    market_age_days: int | None,
    market_cap_usd: float | None,
    volume_24h_usd: float | None,
    listed_on_known_aggregator: bool,
    listed_on_major_cex: bool,
    known_project_flag: bool,
    metadata_mismatch: bool,
    holder_scan_complete: bool,
    has_market_profile: bool,
) -> dict[str, float | int | bool]:
    token_age_days = market_age_days or 0
    liquidity_usd_total = usd_liquidity
    largest_pool_liquidity_usd = usd_liquidity
    mature_token = token_age_days > 180
    thin_liquidity = (liquidity_usd_total or 0.0) < 80_000

    # Authority risk (control flags), not direct rug score.
    authority_risk = 100 * (
        0.50 * float(mint_authority_enabled)
        + 0.20 * float(freeze_authority_enabled)
        + 0.20 * float(update_authority_enabled)
        + 0.10 * clamp_unit(dangerous_contract_capability_score)
    )
    if token_age_days > 180:
        authority_risk *= 0.85
    if known_project_flag:
        authority_risk *= 0.75
    if listed_on_major_cex:
        authority_risk *= 0.70
    authority_risk = clamp_score(authority_risk)

    # Distribution risk with maturity-aware holder adjustment.
    if known_project_flag or listed_on_major_cex:
        top_1_adjusted = (top_1_share or 0.0) * 0.60
        top_10_adjusted = (top_10_share or 0.0) * 0.80
    else:
        top_1_adjusted = top_1_share or 0.0
        top_10_adjusted = top_10_share or 0.0

    gini_supply = clamp_unit(
        (norm(top_1_adjusted, 5, 55) * 0.55) + (norm(top_10_adjusted, 30, 95) * 0.45)
    )
    dev_cluster_share = 0.0
    if top_1_share is not None and top_10_share is not None:
        cluster_base = max(0.0, (top_10_share - 35) / 65)
        young_multiplier = 1.2 if token_age_days <= 45 else 0.75 if token_age_days >= 365 else 1.0
        dev_cluster_share = clamp_unit(cluster_base * young_multiplier)

    distribution_risk = 100 * clamp_unit(
        (0.25 * norm(top_1_adjusted, 5, 45))
        + (0.35 * norm(top_10_adjusted, 25, 90))
        + (0.20 * gini_supply)
        + (0.20 * dev_cluster_share)
    )
    distribution_risk = clamp_score(distribution_risk)

    # Market / execution risk: liquidity depth and structure, not direct rug likelihood.
    lp_structure_score = clamp_unit(
        (0.45 if mint_authority_enabled else 0.20)
        + (0.20 if token_age_days <= 30 else 0.0)
        + (0.15 if not listed_on_known_aggregator else 0.0)
        + (0.15 if not known_project_flag and thin_liquidity else 0.0)
    )
    low_pool_count_score = 1.0 if not listed_on_known_aggregator else 0.30
    low_dex_coverage_score = 1.0 if not listed_on_known_aggregator else 0.20

    market_execution_risk = 100 * clamp_unit(
        (0.45 * norm_inverse_log(liquidity_usd_total, 5_000, 50_000_000))
        + (0.20 * norm_inverse_log(largest_pool_liquidity_usd, 5_000, 20_000_000))
        + (0.15 * lp_structure_score)
        + (0.10 * low_pool_count_score)
        + (0.10 * low_dex_coverage_score)
    )
    market_execution_risk = clamp_score(market_execution_risk)

    # Positive maturity score.
    old_token_score = norm(float(token_age_days), 7, 720)
    market_cap_score = norm(market_cap_usd, 20_000_000, 5_000_000_000)
    volume_score = norm(volume_24h_usd, 250_000, 500_000_000)
    dex_coverage_score = 1.0 if listed_on_known_aggregator else 0.0
    known_project_score = 1.0 if known_project_flag else 0.0

    market_maturity = 100 * clamp_unit(
        (0.35 * old_token_score)
        + (0.25 * market_cap_score)
        + (0.20 * volume_score)
        + (0.10 * dex_coverage_score)
        + (0.10 * known_project_score)
    )
    if listed_on_major_cex:
        market_maturity = min(100, market_maturity + 8)
    market_maturity = clamp_score(market_maturity)

    # Behaviour and exploit signals.
    early_dump_detected = bool(dev_cluster_share > 0.65 and token_age_days <= 45 and (top_1_share or 0) > 12)
    suspicious_liquidity_control = bool(
        thin_liquidity
        and token_age_days <= 60
        and mint_authority_enabled
        and not known_project_flag
        and not listed_on_major_cex
        and dev_cluster_share >= 0.35
    )
    mint_after_launch_detected = bool(
        mint_authority_enabled
        and token_age_days >= 14
        and token_age_days <= 120
        and dev_cluster_share >= 0.60
        and not known_project_flag
        and not listed_on_major_cex
    )
    honeypot_simulation_failed = False

    behaviour_risk = 100 * clamp_unit(
        (0.45 * dev_cluster_share)
        + (0.25 * float(early_dump_detected))
        + (0.20 * float(suspicious_liquidity_control))
        + (0.10 * float(mint_after_launch_detected))
    )
    behaviour_risk = clamp_score(behaviour_risk)

    contract_exploit_risk = clamp_score(
        100
        * clamp_unit(
            (0.45 * float(mint_after_launch_detected))
            + (0.35 * float(freeze_authority_enabled and mint_authority_enabled))
            + (0.20 * clamp_unit(dangerous_contract_capability_score))
        )
    )
    data_quality_risk = clamp_score(
        100
        * clamp_unit(
            (0.45 * float(top_10_share is None or not holder_scan_complete))
            + (0.30 * float(not has_market_profile))
            + (0.25 * float(metadata_mismatch))
        )
    )

    lp_owner_is_deployer = bool(suspicious_liquidity_control and dev_cluster_share >= 0.45)
    lp_lock_missing = bool((liquidity_usd_total or 0) < 50_000 and token_age_days <= 45)
    liquidity_removal_pattern = bool(
        lp_owner_is_deployer and token_age_days <= 21 and (top_1_share or 0) >= 15
    )
    liquidity_rug_component = clamp_score(
        100
        * clamp_unit(
            (0.40 * float(lp_owner_is_deployer))
            + (0.30 * float(lp_lock_missing))
            + (0.20 * float(liquidity_removal_pattern))
            + (0.10 * float(suspicious_liquidity_control))
        )
    )

    authority_risk_component = clamp_score(
        authority_risk
        * (0.60 if mature_token and (known_project_flag or listed_on_major_cex) else 0.85)
    )
    rule_rug_score = clamp_score(
        (0.25 * authority_risk_component)
        + (0.20 * distribution_risk)
        + (0.15 * liquidity_rug_component)
        + (0.25 * behaviour_risk)
        + (0.10 * contract_exploit_risk)
        + (0.05 * data_quality_risk)
    )

    ml_probability = clamp_unit(
        (0.30 * (authority_risk_component / 100))
        + (0.25 * (distribution_risk / 100))
        + (0.20 * (liquidity_rug_component / 100))
        + (0.25 * (behaviour_risk / 100))
    )
    behaviour_boost = clamp_unit(
        (0.60 * (behaviour_risk / 100))
        + (0.40 * (1.0 if early_dump_detected else 0.0))
    )
    hybrid_probability = (
        (0.50 * ml_probability)
        + (0.30 * (rule_rug_score / 100))
        + (0.20 * behaviour_boost)
    )
    final_probability = clamp_unit(hybrid_probability - (0.30 * (market_maturity / 100)))
    rug_probability = clamp_score(final_probability * 100)

    hard_critical = (
        honeypot_simulation_failed
        or mint_after_launch_detected
        or (lp_owner_is_deployer and liquidity_removal_pattern)
        or (dev_cluster_share > 0.75 and early_dump_detected)
    )
    mature_soft_protection = (
        known_project_flag
        and mature_token
        and ((market_cap_usd or 0) >= 100_000_000 or (volume_24h_usd or 0) >= 10_000_000)
        and not hard_critical
    )
    if mature_soft_protection:
        rug_probability = min(rug_probability, 49)
    if hard_critical and rug_probability < 75:
        rug_probability = 75

    return {
        "technical_risk": authority_risk,
        "distribution_risk": distribution_risk,
        "market_execution_risk": market_execution_risk,
        "market_maturity": market_maturity,
        "behaviour_risk": behaviour_risk,
        "rug_probability": rug_probability,
        "liquidity_rug_component": liquidity_rug_component,
        "hard_critical": hard_critical,
        "mature_soft_protection": mature_soft_protection,
        "dev_cluster_share": dev_cluster_share,
        "early_dump_detected": early_dump_detected,
        "suspicious_liquidity_control": suspicious_liquidity_control,
        "mint_after_launch_detected": mint_after_launch_detected,
        "lp_lock_missing": lp_lock_missing,
        "lp_owner_is_deployer": lp_owner_is_deployer,
        "liquidity_removal_pattern": liquidity_removal_pattern,
        "rule_rug_score": rule_rug_score,
    }


def build_live_token_report(
    entity_id: str,
    version: int,
    rpc_client: SolanaRpcClient,
    token_holders_max_pages: int,
    dexscreener_client: DexScreenerClient | None,
    forced_id: str | None,
    forced_name: str | None,
    created_at: datetime | None,
) -> CheckOverview:
    account_info = rpc_client.call(
        "getAccountInfo",
        [entity_id, {"encoding": "jsonParsed", "commitment": "confirmed"}],
    )
    account_value = account_info.get("value")
    if not account_value:
        raise SolanaRpcError("Mint account not found")

    parsed = account_value.get("data", {}).get("parsed", {})
    if parsed.get("type") != "mint":
        raise SolanaRpcError("Address is not an SPL token mint")

    mint_info = parsed.get("info", {})
    token_program_id = account_value.get("owner")
    supply_response = rpc_client.call("getTokenSupply", [entity_id, {"commitment": "confirmed"}])
    supply_value = supply_response.get("value", {})
    ui_supply = float(supply_value.get("uiAmount") or 0)
    decimals = int(supply_value.get("decimals") or mint_info.get("decimals") or 0)

    top_10_share: float | None = None
    top_1_share: float | None = None
    largest_holder_accounts: list[dict] = []
    largest_accounts_available = False
    holder_scan_complete = True
    usd_liquidity: float | None = None
    liquidity_source = "Liquidity not available"
    token_name: str | None = None
    token_symbol: str | None = None
    token_logo_url: str | None = None
    market_age = "Unknown"
    market_age_days: int | None = None
    market_age_minutes: int | None = None
    market_cap_usd: float | None = None
    fdv_usd: float | None = None
    volume_24h_usd: float | None = None
    listed_on_known_aggregator = False
    listed_on_major_cex = False
    known_project_flag = False
    dex_name: str | None = None
    dex_symbol: str | None = None
    metadata_mismatch = False
    pairs: list[dict] = []

    helius_name, helius_symbol, helius_logo_url = fetch_token_asset_profile(rpc_client, entity_id)
    if helius_name:
        token_name = helius_name
    if helius_symbol:
        token_symbol = helius_symbol
    if helius_logo_url:
        token_logo_url = helius_logo_url
    try:
        largest_accounts = rpc_client.call("getTokenLargestAccounts", [entity_id, {"commitment": "confirmed"}])
        largest_values = largest_accounts.get("value", [])
        largest_holder_accounts = largest_values
        largest_ui_amounts = [float(item.get("uiAmount") or 0) for item in largest_values]
        top_10_total = sum(largest_ui_amounts[:10])
        top_1_total = largest_ui_amounts[0] if largest_ui_amounts else 0
        top_10_share = (top_10_total / ui_supply * 100) if ui_supply > 0 else 0
        top_1_share = (top_1_total / ui_supply * 100) if ui_supply > 0 else 0
        largest_accounts_available = True
    except SolanaRpcError:
        largest_accounts_available = False
        if token_program_id:
            try:
                top_10_share, top_1_share = extract_holder_shares_from_program_accounts(
                    rpc_client,
                    token_program_id,
                    entity_id,
                    ui_supply,
                )
                largest_accounts_available = top_10_share is not None
            except SolanaRpcError:
                largest_accounts_available = False

    if top_10_share is None:
        try:
            top_10_share, top_1_share, holder_scan_complete = extract_holder_shares_from_helius_token_accounts(
                rpc_client,
                entity_id,
                ui_supply,
                decimals,
                token_holders_max_pages,
            )
            largest_accounts_available = top_10_share is not None
        except SolanaRpcError:
            largest_accounts_available = False

    top_holder_owner_shares = (
        extract_top_holder_owner_shares(rpc_client, largest_holder_accounts, ui_supply)
        if largest_holder_accounts
        else {}
    )
    developer_cluster_signal = (
        detect_developer_wallet_cluster(rpc_client, top_holder_owner_shares)
        if top_holder_owner_shares
        else {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "confidence": 0.0,
        }
    )

    if dexscreener_client is not None:
        try:
            pair = None
            pairs = dexscreener_client.get_token_pairs("solana", entity_id)
            pair = pick_most_liquid_pair(pairs)
            if pair is not None:
                listed_on_known_aggregator = True
                usd_liquidity = float((pair.get("liquidity") or {}).get("usd") or 0)
                market_cap_usd = float(pair.get("marketCap") or 0) or None
                fdv_usd = float(pair.get("fdv") or 0) or None
                volume_24h_usd = float((pair.get("volume") or {}).get("h24") or 0) or None
                liquidity_source = f"DEX Screener / {pair.get('dexId', 'unknown')}"
                dex_name, dex_symbol, dex_logo_url = extract_token_profile(pair, entity_id)
                market_age, market_age_days, market_age_minutes = token_age_snapshot(
                    int(pair.get("pairCreatedAt") / 1000) if pair.get("pairCreatedAt") else None
                )
                token_name = token_name or dex_name
                token_symbol = token_symbol or dex_symbol
                token_logo_url = token_logo_url or dex_logo_url
        except DexScreenerError:
            usd_liquidity = None
            pair = None
    else:
        pair = None

    early_buyer_cluster_signal = (
        detect_early_buyer_clustering(rpc_client, top_holder_owner_shares, market_age_days)
        if top_holder_owner_shares
        else {
            "detected": False,
            "cluster_wallet_count": 0,
            "cluster_supply_control_pct": 0.0,
            "shared_funder": None,
            "lead_wallet": None,
            "confidence": 0.0,
        }
    )
    insider_selling_signal = (
        detect_insider_selling_pattern(rpc_client, largest_holder_accounts, ui_supply, entity_id)
        if largest_holder_accounts
        else {
            "detected": False,
            "seller_wallet_count": 0,
            "seller_supply_control_pct": 0.0,
            "confidence": 0.0,
        }
    )

    canonical_symbol = (token_symbol or dex_symbol or "").upper().strip()
    known_project_flag = canonical_symbol in KNOWN_BLUECHIP_SYMBOLS
    listed_on_major_cex = known_project_flag and (
        (market_cap_usd or 0) >= 300_000_000 or (volume_24h_usd or 0) >= 25_000_000
    )
    metadata_mismatch = (
        helius_name
        and dex_name
        and helius_name.strip().lower() != dex_name.strip().lower()
    ) or (
        helius_symbol
        and dex_symbol
        and helius_symbol.strip().lower() != dex_symbol.strip().lower()
    )
    scoring = compute_token_scoring_v21(
        mint_authority_enabled=bool(mint_info.get("mintAuthority")),
        freeze_authority_enabled=bool(mint_info.get("freezeAuthority")),
        update_authority_enabled=False,
        dangerous_contract_capability_score=0.35 if mint_info.get("mintAuthority") else 0.10,
        top_10_share=top_10_share,
        top_1_share=top_1_share,
        usd_liquidity=usd_liquidity,
        market_age_days=market_age_days,
        market_cap_usd=market_cap_usd or fdv_usd,
        volume_24h_usd=volume_24h_usd,
        listed_on_known_aggregator=listed_on_known_aggregator,
        listed_on_major_cex=listed_on_major_cex,
        known_project_flag=known_project_flag,
        metadata_mismatch=bool(metadata_mismatch),
        holder_scan_complete=holder_scan_complete,
        has_market_profile=bool(token_name or token_symbol),
    )
    liquidity_management_signal = analyze_liquidity_management_behaviour(
        pair,
        usd_liquidity=usd_liquidity,
        market_age_days=market_age_days,
        lp_lock_missing=bool(scoring["lp_lock_missing"]),
        suspicious_liquidity_control=bool(scoring["suspicious_liquidity_control"]),
    )
    technical_risk = int(scoring["technical_risk"])
    distribution_risk = int(scoring["distribution_risk"])
    market_execution_risk = int(scoring["market_execution_risk"])
    base_behaviour_risk = int(scoring["behaviour_risk"])
    market_maturity = int(scoring["market_maturity"])
    base_rug_probability = int(scoring["rug_probability"])
    insider_liquidity_correlation = bool(
        insider_selling_signal["detected"]
        and (
            (usd_liquidity or 0.0) < 100_000
            or bool(scoring["suspicious_liquidity_control"])
            or bool(scoring["lp_lock_missing"])
            or market_execution_risk >= 70
        )
    )
    has_live_exploit_signal = bool(scoring["hard_critical"])
    behaviour_computation, behaviour_analysis_v2 = build_behaviour_analysis_v2(
        settings=settings,
        owner_shares=top_holder_owner_shares,
        market_age_days=market_age_days,
        market_maturity_score=market_maturity,
        known_project_flag=known_project_flag,
        developer_cluster_signal=developer_cluster_signal,
        early_buyer_cluster_signal=early_buyer_cluster_signal,
        insider_selling_signal=insider_selling_signal,
        insider_liquidity_correlation=insider_liquidity_correlation,
        liquidity_management_signal=liquidity_management_signal,
        debug_context={
            "cache": dict(_BEHAVIOUR_CACHE_STATS),
            "source_coverage": {
                "largest_accounts_available": largest_accounts_available,
                "holder_scan_complete": holder_scan_complete,
                "dex_pair_available": pair is not None,
                "market_profile_available": bool(token_name or token_symbol),
            },
        },
    )
    behaviour_risk = clamp_score((0.35 * base_behaviour_risk) + (0.65 * behaviour_computation.score))
    rug_probability = clamp_score((0.85 * base_rug_probability) + (0.15 * behaviour_computation.score))
    if has_live_exploit_signal and rug_probability < 75:
        rug_probability = 75
    pool_count = len(pairs) if pairs else (1 if pair is not None else 0)
    dex_count = len({str(item.get("dexId")) for item in pairs if item.get("dexId")}) if pairs else (1 if pair is not None else 0)
    trade_caution = build_trade_caution_overview(
        rug_probability=rug_probability,
        technical_risk=technical_risk,
        distribution_risk=distribution_risk,
        market_execution_risk=market_execution_risk,
        market_maturity=market_maturity,
        market_age_days=market_age_days,
        market_cap_usd=market_cap_usd or fdv_usd,
        volume_24h_usd=volume_24h_usd,
        usd_liquidity=usd_liquidity,
        largest_pool_liquidity_usd=usd_liquidity,
        pool_count=pool_count,
        dex_count=dex_count,
        top_1_share=top_1_share,
        top_10_share=top_10_share,
        dev_cluster_share=float(scoring["dev_cluster_share"]),
        known_project_flag=known_project_flag,
        listed_on_major_cex=listed_on_major_cex,
        listed_on_known_aggregator=listed_on_known_aggregator,
        mint_authority_enabled=bool(mint_info.get("mintAuthority")),
        freeze_authority_enabled=bool(mint_info.get("freezeAuthority")),
        update_authority_enabled=False,
        dangerous_contract_capability_score=0.35 if mint_info.get("mintAuthority") else 0.10,
        metadata_mismatch=bool(metadata_mismatch),
        lp_lock_missing=bool(scoring["lp_lock_missing"]),
        lp_owner_is_deployer=bool(scoring["lp_owner_is_deployer"]),
        suspicious_liquidity_control=bool(scoring["suspicious_liquidity_control"]),
        honeypot_simulation_failed=False,
        sell_restrictions_detected=False,
        behaviour=behaviour_computation,
    )
    page_mode = resolve_page_mode(
        launch_age_minutes=market_age_minutes,
        listed_on_known_aggregator=listed_on_known_aggregator,
    )
    copycat_status = "possible" if metadata_mismatch else "none"
    launch_radar = build_launch_radar_overview(
        page_mode=page_mode,
        launch_age_minutes=market_age_minutes,
        usd_liquidity=usd_liquidity,
        top_10_share=top_10_share,
        top_1_share=top_1_share,
        trade_caution_level=trade_caution.level,
        market_execution_risk=market_execution_risk,
        volume_24h_usd=volume_24h_usd,
        copycat_status=copycat_status,
        developer_cluster_signal=developer_cluster_signal,
        early_buyer_cluster_signal=early_buyer_cluster_signal,
        insider_selling_signal=insider_selling_signal,
    )
    launch_risk = build_launch_risk_overview(
        page_mode=page_mode,
        launch_age_minutes=market_age_minutes,
        usd_liquidity=usd_liquidity,
        top_10_share=top_10_share,
        top_1_share=top_1_share,
        trade_caution_level=trade_caution.level,
        market_execution_risk=market_execution_risk,
        copycat_status=copycat_status,
        early_cluster_activity=launch_radar.early_cluster_activity,
        holder_scan_complete=holder_scan_complete,
    )
    early_warnings = build_early_warnings(
        launch_age_minutes=market_age_minutes,
        usd_liquidity=usd_liquidity,
        holder_scan_complete=holder_scan_complete,
        trade_pressure=launch_radar.early_trade_pressure,
        copycat_status=copycat_status,
        early_cluster_activity=launch_radar.early_cluster_activity,
        listed_on_known_aggregator=listed_on_known_aggregator,
    )
    status = risk_status(rug_probability)

    risk_increasers: list[RiskFactor] = []
    risk_reducers: list[RiskFactor] = []

    if mint_info.get("mintAuthority"):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_ACTIVE_MINT_AUTHORITY",
                severity="high" if technical_risk >= 70 else "medium",
                label="Mint authority enabled",
                explanation="Administrative control still allows supply-side changes.",
                weight=22,
            )
        )
    if mint_info.get("freezeAuthority"):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_ACTIVE_FREEZE_AUTHORITY",
                severity="medium",
                label="Freeze authority enabled",
                explanation="Token accounts can still be restricted by authority.",
                weight=10,
            )
        )
    if bool(developer_cluster_signal["detected"]):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_DEVELOPER_CLUSTER_DETECTED",
                severity="high" if float(developer_cluster_signal["cluster_supply_control_pct"]) >= 20 else "medium",
                label="Developer-linked wallet cluster detected",
                explanation=(
                    f"Multiple holder wallets appear linked through a shared funding source and control about "
                    f"{float(developer_cluster_signal['cluster_supply_control_pct']):.1f}% of tracked supply."
                ),
                weight=20,
            )
        )
    if bool(early_buyer_cluster_signal["detected"]):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_EARLY_BUYER_CLUSTERING_DETECTED",
                severity="high" if float(early_buyer_cluster_signal["cluster_supply_control_pct"]) >= 20 else "medium",
                label="Early buyer clustering detected",
                explanation=(
                    f"Multiple early holder wallets appear linked through shared funding and aligned activity timing, "
                    f"representing about {float(early_buyer_cluster_signal['cluster_supply_control_pct']):.1f}% of tracked supply."
                ),
                weight=18,
            )
        )
    if bool(insider_selling_signal["detected"]):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_INSIDER_EXIT_PATTERN_DETECTED",
                severity="high",
                label=(
                    "Insider selling pattern detected under weak liquidity"
                    if insider_liquidity_correlation
                    else "Possible insider exit pattern detected"
                ),
                explanation=(
                    f"Recent outgoing token transfers were detected across {int(insider_selling_signal['seller_wallet_count'])} "
                    f"tracked large-holder wallets representing about {float(insider_selling_signal['seller_supply_control_pct']):.1f}% "
                    + (
                        "of tracked supply while current liquidity conditions also appear weak."
                        if insider_liquidity_correlation
                        else "of tracked supply."
                    )
                ),
                weight=22,
            )
        )
    if top_10_share is not None and top_10_share >= 70:
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_TOP10_CONCENTRATION",
                severity="high" if top_10_share >= 85 else "medium",
                label=f"Top 10 holders: {top_10_share:.1f}%",
                explanation="Concentrated supply increases governance and dump risk.",
                weight=18,
            )
        )
    if market_execution_risk >= 60:
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_THIN_MARKET_EXECUTION",
                severity="medium",
                label=f"Thin pool liquidity ({format_usd_liquidity(usd_liquidity)})",
                explanation="Slippage and exit execution can be unstable in current pool depth.",
                weight=14,
            )
        )
    if bool(scoring["lp_lock_missing"]):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_LP_LOCK_MISSING",
                severity="high",
                label="LP lock signal missing",
                explanation="Liquidity ownership protections are weak for this market stage.",
                weight=16,
            )
        )
    if bool(liquidity_management_signal["detected"]) and "stress signals" in str(liquidity_management_signal["summary"]).lower():
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_LIQUIDITY_MANAGEMENT_STRESS",
                severity="high" if str(liquidity_management_signal["severity"]) == "red" else "medium",
                label="Liquidity management stress detected",
                explanation=str(liquidity_management_signal["summary"]),
                weight=16,
            )
        )
    if bool(scoring["mint_after_launch_detected"]):
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_MINT_AFTER_LAUNCH_PATTERN",
                severity="high",
                label="Mint-after-launch pattern risk",
                explanation="Supply-control permissions persisted after launch age threshold.",
                weight=20,
            )
        )
    if metadata_mismatch:
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_METADATA_MISMATCH",
                severity="low",
                label="Metadata mismatch across sources",
                explanation="Onchain metadata differs from detected market profile.",
                weight=6,
            )
        )

    if market_maturity >= 60:
        risk_reducers.append(
            RiskFactor(
                code="TOKEN_MARKET_MATURITY_STRONG",
                severity="low",
                label="Established market presence",
                explanation="Age, activity, and listing breadth reduce baseline rug probability.",
                weight=16,
            )
        )
    if market_age_days is not None and market_age_days >= 180:
        risk_reducers.append(
            RiskFactor(
                code="TOKEN_MATURE_AGE",
                severity="low",
                label="Mature token age",
                explanation="Longer market age reduces the likelihood of an opportunistic short-life rug pattern.",
                weight=12,
            )
        )
    if known_project_flag:
        risk_reducers.append(
            RiskFactor(
                code="TOKEN_KNOWN_PROJECT_PROFILE",
                severity="low",
                label="Known project profile",
                explanation="Known symbol profile reduces the prior probability of scam behaviour.",
                weight=10,
            )
        )
    if listed_on_major_cex:
        risk_reducers.append(
            RiskFactor(
                code="TOKEN_MAJOR_LISTING_SIGNAL",
                severity="low",
                label="Major listing footprint",
                explanation="Large-market listing footprint materially lowers rug baseline.",
                weight=10,
            )
        )
    if not risk_increasers:
        risk_increasers.append(
            RiskFactor(
                code="TOKEN_LOW_SIGNAL",
                severity="low",
                label="No strong rug-specific signal",
                explanation="No direct exploit or scam-linked behaviour signal was detected.",
                weight=4,
            )
        )

    ordered_increasers = sorted(risk_increasers, key=lambda factor: factor.weight, reverse=True)
    ordered_reducers = sorted(risk_reducers, key=lambda factor: factor.weight, reverse=True)
    behaviour_analysis = flatten_behaviour_analysis_v2(behaviour_analysis_v2)
    risk_breakdown = build_weighted_risk_breakdown(
        technical_risk=technical_risk,
        distribution_risk=distribution_risk,
        market_execution_risk=market_execution_risk,
        behaviour_risk=behaviour_risk,
        market_maturity=market_maturity,
    )

    confidence = token_confidence(
        has_supply=ui_supply > 0,
        has_liquidity=usd_liquidity is not None,
        has_holder_distribution=top_10_share is not None,
        has_market_profile=bool(token_name or token_symbol),
    )
    if behaviour_analysis_v2.confidence == "high":
        confidence = min(0.99, confidence + 0.05)
    elif behaviour_analysis_v2.confidence == "limited":
        confidence = max(0.10, confidence - 0.10)
    confidence = adjusted_token_confidence(
        base_confidence=confidence,
        page_mode=page_mode,
        holder_scan_complete=holder_scan_complete,
        has_liquidity=usd_liquidity is not None,
        has_market_profile=bool(token_name or token_symbol),
        usd_liquidity=usd_liquidity,
        has_live_exploit_signal=has_live_exploit_signal,
    )
    timestamp = created_at or utc_now()
    report_id = forced_id or f"{base_slug(entity_id)}-{version + 1}"
    display_name = (
        forced_name
        or f"{token_symbol} / {token_name}"
        if token_symbol and token_name
        else token_name
        or token_symbol
        or f"Token / {entity_id[:4]}...{entity_id[-4:]}"
    )
    liquidity = format_usd_liquidity(usd_liquidity)
    top_holder_share = format_share(top_10_share)
    metrics = [
        MetricItem(label="Rug probability", value=f"{rug_probability}%"),
        MetricItem(label="Trade caution", value=f"{trade_caution.label} ({trade_caution.score})"),
        MetricItem(label="Confidence", value=f"{confidence:.2f}"),
        MetricItem(label="Technical risk", value=str(technical_risk)),
        MetricItem(label="Distribution risk", value=str(distribution_risk)),
        MetricItem(label="Market/execution risk", value=str(market_execution_risk)),
        MetricItem(label="Behaviour risk", value=str(behaviour_risk)),
        MetricItem(label="Market maturity", value=str(market_maturity)),
        MetricItem(label="Supply", value=format_token_amount(ui_supply)),
        MetricItem(label="Decimals", value=str(decimals)),
        MetricItem(label="Market age", value=market_age),
        MetricItem(label="Market source", value=liquidity_source),
        MetricItem(label="Liquidity", value=liquidity),
        MetricItem(label="Top holders", value=top_holder_share),
        MetricItem(label="Largest holder", value=format_share(top_1_share)),
        MetricItem(label="Rule rug score", value=str(int(scoring["rule_rug_score"]))),
        MetricItem(label="Liquidity rug component", value=str(int(scoring["liquidity_rug_component"]))),
    ]
    if not holder_scan_complete:
        metrics.append(MetricItem(label="Holder scan", value=f"Partial ({token_holders_max_pages} pages)"))
    timeline = build_token_timeline(
        page_mode=page_mode,
        market_age=market_age,
        launch_age_minutes=market_age_minutes,
        market_source=liquidity_source,
        usd_liquidity=usd_liquidity,
        top_10_share=top_10_share,
        holder_scan_complete=holder_scan_complete,
        largest_accounts_available=largest_accounts_available,
        early_warnings=early_warnings,
        mint_authority_enabled=bool(mint_info.get("mintAuthority")),
        freeze_authority_enabled=bool(mint_info.get("freezeAuthority")),
    )

    return CheckOverview(
        id=report_id,
        entity_type="token",
        entity_id=entity_id,
        display_name=display_name,
        name=token_name,
        symbol=token_symbol,
        logo_url=token_logo_url,
        status=status,
        score=rug_probability,
        rug_probability=rug_probability,
        technical_risk=technical_risk,
        distribution_risk=distribution_risk,
        market_execution_risk=market_execution_risk,
        behaviour_risk=behaviour_risk,
        market_maturity=market_maturity,
        trade_caution=trade_caution,
        confidence=confidence,
        page_mode=page_mode,
        launch_risk=launch_risk,
        early_warnings=early_warnings,
        launch_radar=launch_radar,
        market_source=liquidity_source,
        summary=build_token_summary(
            page_mode=page_mode,
            rug_probability=rug_probability,
            trade_caution_level=trade_caution.level,
            technical_risk=technical_risk,
            market_execution_risk=market_execution_risk,
            market_maturity=market_maturity,
            behaviour_risk=behaviour_risk,
            usd_liquidity=usd_liquidity,
            risk_increasers=ordered_increasers,
            has_live_exploit_signal=has_live_exploit_signal,
            confidence=confidence,
        ),
        refreshed_at=relative_time(timestamp),
        liquidity=liquidity,
        top_holder_share=top_holder_share,
        review_state=review_state_for(status),
        risk_breakdown=risk_breakdown,
        factors=ordered_increasers,
        risk_increasers=ordered_increasers,
        risk_reducers=ordered_reducers,
        behaviour_analysis=behaviour_analysis,
        behaviour_analysis_v2=behaviour_analysis_v2,
        metrics=metrics,
        timeline=timeline,
        created_at=timestamp,
    )


def generate_report(
    entity_type: EntityType,
    raw_value: str,
    *,
    version: int = 0,
    forced_id: str | None = None,
    forced_name: str | None = None,
    created_at: datetime | None = None,
    rpc_client: SolanaRpcClient | None = None,
    live_token_analysis: bool = True,
    token_holders_max_pages: int = 25,
    dexscreener_client: DexScreenerClient | None = None,
) -> CheckOverview:
    entity_id = normalize_entity_id(entity_type, raw_value)

    if entity_type == "token" and rpc_client is not None and live_token_analysis:
        return build_live_token_report(
            entity_id,
            version,
            rpc_client,
            token_holders_max_pages,
            dexscreener_client,
            forced_id,
            forced_name,
            created_at,
        )

    seed = pick_seed(entity_type, entity_id, version)

    if entity_type == "token":
        factors = token_factors(seed)
    elif entity_type == "wallet":
        factors = wallet_factors(seed)
    else:
        factors = project_factors(seed)

    base = min(sum(factor.weight for factor in factors) + (seed % 9), 100)
    if entity_type == "token":
        technical_risk = clamp_score(base * 0.80)
        distribution_risk = clamp_score(base * 0.72)
        market_execution_risk = clamp_score(base * 0.65)
        behaviour_risk = clamp_score(base * 0.62)
        market_maturity = clamp_score(45 + (seed % 40))
    elif entity_type == "wallet":
        technical_risk = clamp_score(base * 0.25)
        distribution_risk = clamp_score(base * 0.75)
        market_execution_risk = clamp_score(base * 0.60)
        behaviour_risk = clamp_score(base * 0.70)
        market_maturity = clamp_score(25 + (seed % 35))
    else:
        technical_risk = clamp_score(base * 0.40)
        distribution_risk = clamp_score(base * 0.60)
        market_execution_risk = clamp_score(base * 0.55)
        behaviour_risk = clamp_score(base * 0.65)
        market_maturity = clamp_score(35 + (seed % 45))

    rug_probability = clamp_score(
        (0.30 * technical_risk)
        + (0.25 * distribution_risk)
        + (0.25 * behaviour_risk)
        + (0.20 * market_execution_risk)
        - (0.25 * market_maturity)
    )
    risk_breakdown = build_weighted_risk_breakdown(
        technical_risk=technical_risk,
        distribution_risk=distribution_risk,
        market_execution_risk=market_execution_risk,
        behaviour_risk=behaviour_risk,
        market_maturity=market_maturity,
    )
    behaviour_analysis_v2 = None
    behaviour_analysis: list[BehaviourInsightItem] = []
    trade_caution = None
    page_mode: PageMode = "mature"
    launch_risk = LaunchRiskOverview(score=0, level="unknown", summary="Launch stage not available.", drivers=[])
    launch_radar = LaunchRadarOverview(
        launch_age_minutes=None,
        initial_liquidity_band="Unknown",
        early_trade_pressure="balanced",
        launch_concentration="medium",
        copycat_status="none",
        early_cluster_activity="none",
        summary="Launch-stage radar is not available for this report.",
    )
    early_warnings: list[str] = []
    market_source: str | None = None
    market_age = "Unknown"
    market_age_days: int | None = None
    launch_age_minutes: int | None = None
    synthetic_top_10_share: float | None = None
    synthetic_top_1_share: float | None = None
    synthetic_liquidity_value: float | None = None
    synthetic_volume_24h_usd: float | None = None
    listed_on_known_aggregator = False
    holder_scan_complete = True
    largest_accounts_available = True
    has_live_exploit_signal = False
    if entity_type == "token":
        synthetic_behaviour, behaviour_analysis_v2 = build_behaviour_analysis_v2(
            settings=settings,
            owner_shares={
                "synthetic-wallet-a": round(max(5.0, behaviour_risk * 0.22), 1),
                "synthetic-wallet-b": round(max(4.0, behaviour_risk * 0.18), 1),
                "synthetic-wallet-c": round(max(3.0, behaviour_risk * 0.12), 1),
            },
            market_age_days=30 if market_maturity < 55 else 240,
            market_maturity_score=market_maturity,
            known_project_flag=market_maturity >= 65,
            developer_cluster_signal={
                "detected": behaviour_risk >= 70,
                "cluster_wallet_count": max(0, int(round(behaviour_risk / 18))) if behaviour_risk >= 70 else 0,
                "cluster_supply_control_pct": float(min(100, behaviour_risk)),
                "shared_funder": None,
                "lead_wallet": None,
                "confidence": 0.70 if behaviour_risk >= 70 else 0.20,
            },
            early_buyer_cluster_signal={
                "detected": behaviour_risk >= 68,
                "cluster_wallet_count": max(0, int(round(behaviour_risk / 20))) if behaviour_risk >= 68 else 0,
                "cluster_supply_control_pct": float(min(100, behaviour_risk * 0.85)) if behaviour_risk >= 68 else 0.0,
                "shared_funder": None,
                "lead_wallet": None,
                "confidence": 0.65 if behaviour_risk >= 68 else 0.20,
            },
            insider_selling_signal={
                "detected": behaviour_risk >= 75,
                "seller_wallet_count": max(0, int(round(behaviour_risk / 22))) if behaviour_risk >= 75 else 0,
                "seller_supply_control_pct": float(min(100, behaviour_risk * 0.8)) if behaviour_risk >= 75 else 0.0,
                "confidence": 0.70 if behaviour_risk >= 75 else 0.20,
            },
            insider_liquidity_correlation=behaviour_risk >= 75 and market_execution_risk >= 70,
            liquidity_management_signal={
                "detected": market_execution_risk >= 55,
                "summary": (
                    "Liquidity structure shows stress signals that warrant closer review."
                    if market_execution_risk >= 55
                    else "No clear liquidity-management anomaly was detected from current pair behaviour."
                ),
                "details": (
                    "Synthetic fallback path uses market-execution risk as a proxy for liquidity stress."
                    if market_execution_risk >= 55
                    else "Synthetic fallback path does not indicate abnormal liquidity behaviour."
                ),
                "severity": "red" if market_execution_risk >= 75 else "orange" if market_execution_risk >= 55 else "green",
            },
        )
        behaviour_analysis = flatten_behaviour_analysis_v2(behaviour_analysis_v2)
        synthetic_top_10_share = float(f"{28 + (seed % 62):.1f}")
        synthetic_top_1_share = round(synthetic_top_10_share / 5.0, 1)
        synthetic_liquidity_value = 20_000 if market_execution_risk >= 55 else 500_000
        synthetic_volume_24h_usd = 80_000 if market_execution_risk >= 55 else 5_000_000
        listed_on_known_aggregator = market_maturity >= 45
        trade_caution = build_trade_caution_overview(
            rug_probability=rug_probability,
            technical_risk=technical_risk,
            distribution_risk=distribution_risk,
            market_execution_risk=market_execution_risk,
            market_maturity=market_maturity,
            market_age_days=30 if market_maturity < 55 else 240,
            market_cap_usd=5_000_000 if market_maturity < 55 else 500_000_000,
            volume_24h_usd=synthetic_volume_24h_usd,
            usd_liquidity=synthetic_liquidity_value,
            largest_pool_liquidity_usd=synthetic_liquidity_value,
            pool_count=1 if market_execution_risk >= 55 else 3,
            dex_count=1 if market_execution_risk >= 55 else 2,
            top_1_share=synthetic_top_1_share,
            top_10_share=synthetic_top_10_share,
            dev_cluster_share=min(1.0, behaviour_risk / 100),
            known_project_flag=market_maturity >= 65,
            listed_on_major_cex=market_maturity >= 75,
            listed_on_known_aggregator=market_maturity >= 45,
            mint_authority_enabled=technical_risk >= 55,
            freeze_authority_enabled=technical_risk >= 65,
            update_authority_enabled=False,
            dangerous_contract_capability_score=min(1.0, technical_risk / 100),
            metadata_mismatch=False,
            lp_lock_missing=market_execution_risk >= 65,
            lp_owner_is_deployer=behaviour_risk >= 70,
            suspicious_liquidity_control=behaviour_risk >= 60,
            honeypot_simulation_failed=False,
            sell_restrictions_detected=False,
            behaviour=synthetic_behaviour,
        )
        synthetic_launch_timestamp = (
            created_at
            if created_at is not None
            else utc_now() - timedelta(minutes=18 if market_maturity < 40 else 360 if market_maturity < 55 else 60 * 24 * 7)
        )
        market_age, market_age_days, launch_age_minutes = token_age_snapshot(int(synthetic_launch_timestamp.timestamp()))
        page_mode = resolve_page_mode(
            launch_age_minutes=launch_age_minutes,
            listed_on_known_aggregator=listed_on_known_aggregator,
        )
        confidence = round(0.58 + ((seed >> 4) % 33) / 100, 2)
        if behaviour_analysis_v2.confidence == "high":
            confidence = min(0.99, confidence + 0.05)
        elif behaviour_analysis_v2.confidence == "limited":
            confidence = max(0.10, confidence - 0.10)
        confidence = adjusted_token_confidence(
            base_confidence=confidence,
            page_mode=page_mode,
            holder_scan_complete=holder_scan_complete,
            has_liquidity=synthetic_liquidity_value is not None,
            has_market_profile=True,
            usd_liquidity=synthetic_liquidity_value,
            has_live_exploit_signal=False,
        )
        market_source = "Synthetic launch pool"
        copycat_status = "possible" if any(factor.code == "TOKEN_METADATA_MISMATCH" for factor in factors) else "none"
        launch_radar = build_launch_radar_overview(
            page_mode=page_mode,
            launch_age_minutes=launch_age_minutes,
            usd_liquidity=synthetic_liquidity_value,
            top_10_share=synthetic_top_10_share,
            top_1_share=synthetic_top_1_share,
            trade_caution_level=trade_caution.level,
            market_execution_risk=market_execution_risk,
            volume_24h_usd=synthetic_volume_24h_usd,
            copycat_status=copycat_status,
            developer_cluster_signal={
                "detected": behaviour_risk >= 70,
                "lead_wallet": None,
                "confidence": 0.70 if behaviour_risk >= 70 else 0.20,
            },
            early_buyer_cluster_signal={
                "detected": behaviour_risk >= 68,
                "lead_wallet": None,
                "confidence": 0.65 if behaviour_risk >= 68 else 0.20,
            },
            insider_selling_signal={
                "detected": behaviour_risk >= 75,
                "confidence": 0.70 if behaviour_risk >= 75 else 0.20,
            },
        )
        launch_risk = build_launch_risk_overview(
            page_mode=page_mode,
            launch_age_minutes=launch_age_minutes,
            usd_liquidity=synthetic_liquidity_value,
            top_10_share=synthetic_top_10_share,
            top_1_share=synthetic_top_1_share,
            trade_caution_level=trade_caution.level,
            market_execution_risk=market_execution_risk,
            copycat_status=copycat_status,
            early_cluster_activity=launch_radar.early_cluster_activity,
            holder_scan_complete=holder_scan_complete,
        )
        early_warnings = build_early_warnings(
            launch_age_minutes=launch_age_minutes,
            usd_liquidity=synthetic_liquidity_value,
            holder_scan_complete=holder_scan_complete,
            trade_pressure=launch_radar.early_trade_pressure,
            copycat_status=copycat_status,
            early_cluster_activity=launch_radar.early_cluster_activity,
            listed_on_known_aggregator=listed_on_known_aggregator,
        )
    else:
        confidence = round(0.58 + ((seed >> 4) % 33) / 100, 2)
    status = risk_status(rug_probability)
    liquidity = "n/a" if entity_type == "wallet" else money_value(seed)
    if entity_type == "token":
        liquidity = format_usd_liquidity(synthetic_liquidity_value)
    top_holder_share = "n/a" if entity_type != "token" else format_share(synthetic_top_10_share)
    timestamp = created_at or utc_now()
    report_id = forced_id or f"{base_slug(entity_id)}-{version + 1}"

    if entity_type == "token":
        metrics = [
            MetricItem(label="Rug probability", value=f"{rug_probability}%"),
            MetricItem(label="Trade caution", value=f"{trade_caution.label} ({trade_caution.score})"),
            MetricItem(label="Confidence", value=f"{confidence:.2f}"),
            MetricItem(label="Technical risk", value=str(technical_risk)),
            MetricItem(label="Distribution risk", value=str(distribution_risk)),
            MetricItem(label="Market/execution risk", value=str(market_execution_risk)),
            MetricItem(label="Behaviour risk", value=str(behaviour_risk)),
            MetricItem(label="Market maturity", value=str(market_maturity)),
            MetricItem(label="Market age", value=market_age),
            MetricItem(label="Market source", value=market_source or "Synthetic launch pool"),
            MetricItem(label="Liquidity", value=liquidity),
            MetricItem(label="Top holders", value=top_holder_share),
            MetricItem(label="Largest holder", value=format_share(synthetic_top_1_share)),
        ]
        timeline = build_token_timeline(
            page_mode=page_mode,
            market_age=market_age,
            launch_age_minutes=launch_age_minutes,
            market_source=market_source or "Synthetic launch pool",
            usd_liquidity=synthetic_liquidity_value,
            top_10_share=synthetic_top_10_share,
            holder_scan_complete=holder_scan_complete,
            largest_accounts_available=largest_accounts_available,
            early_warnings=early_warnings,
            mint_authority_enabled=technical_risk >= 55,
            freeze_authority_enabled=technical_risk >= 65,
        )
        summary = build_token_summary(
            page_mode=page_mode,
            rug_probability=rug_probability,
            trade_caution_level=trade_caution.level,
            technical_risk=technical_risk,
            market_execution_risk=market_execution_risk,
            market_maturity=market_maturity,
            behaviour_risk=behaviour_risk,
            usd_liquidity=synthetic_liquidity_value,
            risk_increasers=factors,
            has_live_exploit_signal=has_live_exploit_signal,
            confidence=confidence,
        )
    else:
        metrics = build_metrics(entity_type, rug_probability, confidence, seed, top_holder_share, liquidity)
        timeline = build_timeline(entity_type, factors, seed)
        summary = build_summary(entity_type, status, factors)

    return CheckOverview(
        id=report_id,
        entity_type=entity_type,
        entity_id=entity_id,
        display_name=forced_name or display_name_for(entity_type, entity_id),
        name=None,
        symbol=None,
        logo_url=None,
        status=status,
        score=rug_probability,
        rug_probability=rug_probability,
        technical_risk=technical_risk,
        distribution_risk=distribution_risk,
        market_execution_risk=market_execution_risk,
        behaviour_risk=behaviour_risk,
        market_maturity=market_maturity,
        trade_caution=trade_caution,
        confidence=confidence,
        page_mode=page_mode,
        launch_risk=launch_risk,
        early_warnings=early_warnings,
        launch_radar=launch_radar,
        market_source=market_source,
        summary=summary,
        refreshed_at=relative_time(timestamp),
        liquidity=liquidity,
        top_holder_share=top_holder_share,
        review_state=review_state_for(status),
        risk_breakdown=risk_breakdown,
        factors=factors,
        risk_increasers=factors,
        risk_reducers=[],
        behaviour_analysis=behaviour_analysis,
        behaviour_analysis_v2=behaviour_analysis_v2,
        metrics=metrics,
        timeline=timeline,
        created_at=timestamp,
    )
