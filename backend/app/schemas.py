from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


EntityType = Literal["token", "wallet", "project"]
RiskStatus = Literal["low", "medium", "high", "critical"]
TradeCautionLevel = Literal["low", "moderate", "high", "avoid"]
ReviewState = Literal["Clear", "Watching", "Queued", "Escalated"]
TimelineTone = Literal["danger", "warn", "neutral"]
OverrideVerdict = Literal["whitelist", "blacklist"]
LaunchQuality = Literal["organic", "noisy", "coordinated", "likely_wash", "unknown"]
CopycatStatus = Literal["none", "possible", "collision"]
PageMode = Literal["early_launch", "early_market", "mature"]
LaunchRiskLevel = Literal["unknown", "low", "medium", "high", "critical"]
EarlyTradePressure = Literal["low", "balanced", "aggressive"]
LaunchConcentration = Literal["low", "medium", "high"]
EarlyClusterActivity = Literal["none", "watch", "suspicious"]


class RiskFactor(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    label: str
    explanation: str
    weight: int


class MetricItem(BaseModel):
    label: str
    value: str


class TimelineEvent(BaseModel):
    label: str
    value: str
    tone: TimelineTone = "neutral"


class BehaviourInsightItem(BaseModel):
    key: str
    title: str
    status: str
    summary: str
    tone: Literal["green", "yellow", "orange", "red"] = "green"
    details: list[str] = Field(default_factory=list)


class BehaviourConfidenceBreakdown(BaseModel):
    holder_coverage: Literal["full", "partial", "limited"] = "limited"
    transaction_coverage: Literal["full", "partial", "limited"] = "limited"
    funding_trace_depth: Literal["shallow", "moderate", "deep"] = "shallow"
    liquidity_data: Literal["full", "partial", "limited"] = "limited"


class BehaviourModuleEvidence(BaseModel):
    metrics: dict[str, float | int | str | bool | None] = Field(default_factory=dict)


class BehaviourModuleOverview(BaseModel):
    key: str
    title: str
    status: Literal["clear", "watch", "flagged"]
    severity: Literal["low", "medium", "high"]
    score: float
    summary: str
    details: list[str] = Field(default_factory=list)
    evidence: BehaviourModuleEvidence = Field(default_factory=BehaviourModuleEvidence)
    confidence: Literal["limited", "medium", "high"] = "limited"


class BehaviourAnalysisOverview(BaseModel):
    summary: str
    overall_behaviour_risk: Literal["low", "medium", "high", "critical"]
    confidence: Literal["limited", "medium", "high"]
    score: int
    modules: dict[str, BehaviourModuleOverview] = Field(default_factory=dict)
    confidence_breakdown: BehaviourConfidenceBreakdown = Field(default_factory=BehaviourConfidenceBreakdown)
    version: str = "behaviour_v2"
    debug: dict[str, object] | None = None


class TradeCautionDimensions(BaseModel):
    admin_caution: int
    execution_caution: int
    concentration_caution: int
    behavioural_caution: int
    market_structure_strength: int


class TradeCautionOverview(BaseModel):
    score: int
    level: TradeCautionLevel
    label: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    dimensions: TradeCautionDimensions


class RiskBreakdownItem(BaseModel):
    block: str
    score: int
    weight: float
    weighted_score: float
    kind: Literal["risk", "positive"] = "risk"


class LaunchRiskOverview(BaseModel):
    score: int
    level: LaunchRiskLevel
    summary: str
    drivers: list[str] = Field(default_factory=list)


class LaunchRadarOverview(BaseModel):
    launch_age_minutes: int | None = None
    initial_liquidity_band: str
    early_trade_pressure: EarlyTradePressure
    launch_concentration: LaunchConcentration
    copycat_status: CopycatStatus
    early_cluster_activity: EarlyClusterActivity
    summary: str


class CheckOverview(BaseModel):
    id: str
    entity_type: EntityType
    entity_id: str
    display_name: str
    name: str | None = None
    symbol: str | None = None
    logo_url: str | None = None
    status: RiskStatus
    score: int
    rug_probability: int
    technical_risk: int
    distribution_risk: int
    market_execution_risk: int
    behaviour_risk: int
    market_maturity: int
    trade_caution: TradeCautionOverview | None = None
    confidence: float
    page_mode: PageMode = "mature"
    launch_risk: LaunchRiskOverview = Field(
        default_factory=lambda: LaunchRiskOverview(score=0, level="unknown", summary="Launch stage not available.")
    )
    early_warnings: list[str] = Field(default_factory=list)
    launch_radar: LaunchRadarOverview = Field(
        default_factory=lambda: LaunchRadarOverview(
            launch_age_minutes=None,
            initial_liquidity_band="Unknown",
            early_trade_pressure="balanced",
            launch_concentration="medium",
            copycat_status="none",
            early_cluster_activity="none",
            summary="Launch-stage radar is not available for this report.",
        )
    )
    market_source: str | None = None
    summary: str
    refreshed_at: str
    liquidity: str
    top_holder_share: str
    review_state: ReviewState
    risk_breakdown: list[RiskBreakdownItem]
    factors: list[RiskFactor]
    risk_increasers: list[RiskFactor] = Field(default_factory=list)
    risk_reducers: list[RiskFactor] = Field(default_factory=list)
    behaviour_analysis: list[BehaviourInsightItem] = Field(default_factory=list)
    behaviour_analysis_v2: BehaviourAnalysisOverview | None = None
    metrics: list[MetricItem]
    timeline: list[TimelineEvent]
    created_at: datetime


class WatchlistItem(BaseModel):
    name: str
    delta: str
    state: str


class AccountWatchlistItem(BaseModel):
    entity_type: EntityType
    entity_id: str
    report_id: str | None = None
    name: str
    symbol: str | None = None
    delta: str
    state: str
    status: RiskStatus | None = None
    score: int | None = None
    refreshed_at: str
    tracked_at: datetime


class ReviewQueueItem(BaseModel):
    id: str
    display_name: str
    entity_type: EntityType
    severity: RiskStatus
    score: int
    owner: str
    updated_at: str


class OverviewResponse(BaseModel):
    product: str
    network: str
    supported_entities: list[EntityType]
    status_model: list[RiskStatus]
    totals: dict[str, int]
    freshness: str
    active_rules: int


class MostScannedTokenItem(BaseModel):
    token_address: str
    scan_count: int
    average_risk_score: float


class TrendingRugItem(BaseModel):
    token_address: str
    risk_score: int
    confidence: float
    scan_time: datetime


class InsightsResponse(BaseModel):
    most_scanned_tokens: list[MostScannedTokenItem]
    trending_rugs: list[TrendingRugItem]


class ChecksResponse(BaseModel):
    items: list[CheckOverview]


class LaunchFeedItem(BaseModel):
    mint: str
    report_id: str
    name: str
    symbol: str
    logo_url: str | None = None
    age_minutes: int
    liquidity_usd: float
    market_cap_usd: float
    rug_probability: float
    rug_risk_level: RiskStatus
    trade_caution_level: TradeCautionLevel
    launch_quality: LaunchQuality
    copycat_status: CopycatStatus
    updated_at: datetime
    initial_live_estimate: bool = False
    summary: str
    rug_risk_drivers: list[str] = Field(default_factory=list)
    trade_caution_drivers: list[str] = Field(default_factory=list)
    top_reducer: str | None = None
    deployer_short_address: str | None = None


class LaunchFeedResponse(BaseModel):
    items: list[LaunchFeedItem]
    next_cursor: str | None = None


class WatchlistResponse(BaseModel):
    items: list[WatchlistItem]


class AccountWatchlistResponse(BaseModel):
    items: list[AccountWatchlistItem]


class WatchlistStatusResponse(BaseModel):
    tracked: bool


class WatchlistToggleRequest(BaseModel):
    entity_type: EntityType
    entity_id: str = Field(min_length=3, max_length=200)
    display_name: str | None = Field(default=None, max_length=200)


class WatchlistToggleResponse(BaseModel):
    tracked: bool
    item: AccountWatchlistItem | None = None


class ReviewQueueResponse(BaseModel):
    items: list[ReviewQueueItem]


class AddressRequest(BaseModel):
    address: str = Field(min_length=3, max_length=200)


class ProjectRequest(BaseModel):
    query: str = Field(min_length=3, max_length=300)


class SubmissionResponse(BaseModel):
    queued: bool
    entity_type: EntityType
    requested_value: str
    check_id: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    plan: Literal["free", "pro", "enterprise"] = "free"


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    plan: str
    role: str
    created_at: datetime
    last_login: datetime | None


class UserUsageResponse(BaseModel):
    plan: str
    used_today: int
    daily_limit: int
    remaining_today: int
    limit_source: Literal["plan", "custom"]
    reset_at: datetime


class UserScanItem(BaseModel):
    id: str
    token_address: str
    risk_score: int
    confidence: float
    scan_time: datetime


class UserScansResponse(BaseModel):
    items: list[UserScanItem]


class AdminPopularToken(BaseModel):
    token_address: str
    scan_count: int


class AdminDashboardResponse(BaseModel):
    users_count: int
    daily_scans: int
    popular_tokens: list[AdminPopularToken]
    average_risk_score: float


class AdminUserItem(BaseModel):
    id: str
    email: EmailStr
    plan: str
    custom_daily_scan_limit: int | None
    effective_daily_limit: int
    scans: int
    created_at: datetime


class AdminUsersResponse(BaseModel):
    items: list[AdminUserItem]


class AdminUserLimitUpdateRequest(BaseModel):
    plan: Literal["free", "pro", "enterprise"]
    custom_daily_scan_limit: int | None = Field(default=None, ge=1, le=100000)


class AdminBulkUserLimitUpdateRequest(BaseModel):
    user_ids: list[str] = Field(min_length=1)
    plan: Literal["free", "pro", "enterprise"]
    custom_daily_scan_limit: int | None = Field(default=None, ge=1, le=100000)


class AdminBulkUserLimitUpdateResponse(BaseModel):
    updated_count: int


class AdminScanItem(BaseModel):
    id: str
    user_email: EmailStr
    token_address: str
    risk_score: int
    confidence: float
    scan_time: datetime


class AdminScansResponse(BaseModel):
    items: list[AdminScanItem]


class AdminTokenItem(BaseModel):
    token_address: str
    scan_count: int
    average_risk_score: float
    last_scanned: datetime


class AdminTokensResponse(BaseModel):
    items: list[AdminTokenItem]


class TokenOverrideRequest(BaseModel):
    token_address: str = Field(min_length=32, max_length=128)
    verdict: OverrideVerdict
    reason: str | None = Field(default=None, max_length=300)


class TokenOverrideItem(BaseModel):
    token_address: str
    chain: str
    verdict: OverrideVerdict
    reason: str | None
    updated_at: datetime


class TokenOverridesResponse(BaseModel):
    items: list[TokenOverrideItem]
