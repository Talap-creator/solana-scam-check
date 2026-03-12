from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]
TradeCautionLevel = Literal["low", "moderate", "high", "avoid"]


class ScanTokenV2Request(BaseModel):
    token_address: str = Field(min_length=32, max_length=128)
    chain: Literal["solana"] = "solana"
    refresh: bool = True


class TokenFeatureSchema(BaseModel):
    token_address: str
    token_name: str | None = None
    symbol: str | None = None
    decimals: int = 0
    supply_total: float = 0.0
    token_age_seconds: int | None = None
    market_age_seconds: int | None = None
    first_seen_at: datetime | None = None
    mint_authority_enabled: bool = False
    freeze_authority_enabled: bool = False
    update_authority_enabled: bool | None = None
    authority_count: int = 0
    top_1_holder_share: float | None = None
    top_5_holder_share: float | None = None
    top_10_holder_share: float | None = None
    top_20_holder_share: float | None = None
    gini_supply: float | None = None
    herfindahl_index: float | None = None
    largest_holder_is_lp: bool = False
    holder_count_total: int | None = None
    holder_count_verified: int | None = None
    holder_coverage_ratio: float | None = None
    liquidity_usd_total: float | None = None
    largest_pool_liquidity_usd: float | None = None
    pool_count: int = 0
    dex_count: int = 0
    lp_lock_detected: bool | None = None
    lp_lock_duration_seconds: int | None = None
    lp_owner_is_deployer: bool | None = None
    liquidity_to_market_cap_ratio: float | None = None
    liquidity_change_1h_pct: float | None = None
    liquidity_change_24h_pct: float | None = None
    volume_1h_usd: float | None = None
    volume_24h_usd: float | None = None
    trade_count_1h: int | None = None
    trade_count_24h: int | None = None
    price_change_1h_pct: float | None = None
    price_change_24h_pct: float | None = None
    market_cap_usd: float | None = None
    fdv_usd: float | None = None
    listed_on_known_aggregator: bool = False
    listed_on_major_cex: bool = False
    known_project_flag: bool = False
    first_50_buyers_cluster_ratio: float = 0.0
    first_100_buyers_cluster_ratio: float = 0.0
    dev_cluster_share: float = 0.0
    dev_cluster_wallet_count: int = 0
    early_sell_ratio: float = 0.0
    insider_wallet_detected: bool = False
    suspicious_funding_graph_score: float = 0.0
    repeated_wallet_pattern_score: float = 0.0
    wash_trade_score: float = 0.0
    deployer_wallet_age_days: int | None = None
    deployer_tx_count: int | None = None
    deployer_previous_token_count: int | None = None
    deployer_previous_rug_count: int | None = None
    linked_cluster_previous_token_count: int | None = None
    linked_cluster_previous_rug_count: int | None = None
    deployer_reputation_score: float | None = None
    cluster_reputation_score: float | None = None
    transfer_tax_modifiable: bool | None = None
    blacklist_function_detected: bool | None = None
    pause_function_detected: bool | None = None
    mint_after_launch_detected: bool | None = None
    honeypot_simulation_failed: bool | None = None
    metadata_conflict_score: float = 0.0
    missing_market_profile: bool = False
    partial_holder_coverage: bool = False
    stale_data_seconds: int = 0
    source_count: int = 1


class ScoreCategoryScores(BaseModel):
    technical_risk: int
    distribution_risk: int
    market_execution_risk: int
    market_maturity: int
    behaviour_risk: int
    liquidity_rug_component: int | None = None


class ScoreContributor(BaseModel):
    code: str
    severity: Literal["low", "medium", "high"]
    title: str
    description: str
    impact: float


class ScoreExplanation(BaseModel):
    risk_increasers: list[ScoreContributor]
    risk_reducers: list[ScoreContributor]
    summary: str


class BehaviourConfidenceBreakdown(BaseModel):
    holder_coverage: Literal["full", "partial", "limited"] = "limited"
    transaction_coverage: Literal["full", "partial", "limited"] = "limited"
    funding_trace_depth: Literal["shallow", "moderate", "deep"] = "shallow"
    liquidity_data: Literal["full", "partial", "limited"] = "limited"


class BehaviourModuleResult(BaseModel):
    status: Literal["clear", "watch", "flagged"]
    severity: Literal["low", "medium", "high"]
    score: float
    summary: str
    details: list[str] = Field(default_factory=list)
    evidence: dict[str, float | int | str | bool | None] = Field(default_factory=dict)
    confidence: Literal["limited", "medium", "high"] = "limited"


class BehaviourAnalysisResult(BaseModel):
    summary: str
    overall_behaviour_risk: RiskLevel
    confidence: Literal["limited", "medium", "high"]
    score: int
    modules: dict[str, BehaviourModuleResult] = Field(default_factory=dict)
    confidence_breakdown: BehaviourConfidenceBreakdown = Field(default_factory=BehaviourConfidenceBreakdown)
    version: str = "behaviour_v2"
    debug: dict[str, object] | None = None


class TradeCautionDimensions(BaseModel):
    admin_caution: int
    execution_caution: int
    concentration_caution: int
    behavioural_caution: int
    market_structure_strength: int


class TradeCautionResult(BaseModel):
    score: int
    level: TradeCautionLevel
    label: str
    summary: str
    drivers: list[str] = Field(default_factory=list)
    dimensions: TradeCautionDimensions


class ModelVersionInfo(BaseModel):
    version: str
    rule_engine_version: str
    calibration_version: str


class TokenScanV2Response(BaseModel):
    entity_type: Literal["token"] = "token"
    entity_address: str
    score: int
    rug_probability: float
    technical_risk: int
    distribution_risk: int
    market_execution_risk: int
    market_maturity: int
    behaviour_risk: int
    rule_score: float
    ml_probability: float
    final_probability: float
    risk_level: RiskLevel
    confidence: float
    low_confidence: bool = False
    category_scores: ScoreCategoryScores
    top_findings: list[ScoreContributor]
    model: ModelVersionInfo
    explanation: ScoreExplanation
    behaviour_analysis: BehaviourAnalysisResult | None = None
    trade_caution: TradeCautionResult | None = None
    feature_metadata: dict[str, str]
