from __future__ import annotations

from dataclasses import dataclass

from ..schemas import CheckOverview
from .explainability import ExplanationEngine
from .feature_extractor import TokenFeatureExtractor
from .ml.inference import MLInferenceEngine, get_ml_engine
from .schemas import (
    BehaviourAnalysisResult,
    ModelVersionInfo,
    ScoreCategoryScores,
    ScoreContributor,
    TradeCautionResult,
    TokenFeatureSchema,
    TokenScanV2Response,
)


def _metric_value(report: CheckOverview, label: str) -> str | None:
    for metric in report.metrics:
        if metric.label.lower() == label.lower():
            return metric.value
    return None


def _severity_from_status(status: str) -> str:
    if status == "critical":
        return "high"
    if status in {"high", "medium"}:
        return "medium"
    return "low"


def _to_contributor(code: str, label: str, explanation: str, weight: int, severity: str) -> ScoreContributor:
    return ScoreContributor(
        code=code,
        severity=severity if severity in {"low", "medium", "high"} else "medium",
        title=label,
        description=explanation,
        impact=round(weight / 100.0, 4),
    )


def _map_behaviour_analysis(report: CheckOverview) -> BehaviourAnalysisResult | None:
    if report.behaviour_analysis_v2 is None:
        return None

    source = report.behaviour_analysis_v2
    return BehaviourAnalysisResult(
        summary=source.summary,
        overall_behaviour_risk=source.overall_behaviour_risk,
        confidence=source.confidence,
        score=source.score,
        modules={
            key: {
                "status": module.status,
                "severity": module.severity,
                "score": module.score,
                "summary": module.summary,
                "details": module.details,
                "evidence": module.evidence.metrics,
                "confidence": module.confidence,
            }
            for key, module in source.modules.items()
        },
        confidence_breakdown=source.confidence_breakdown.model_dump(mode="json"),
        version=source.version,
        debug=source.debug,
    )


def _map_trade_caution(report: CheckOverview) -> TradeCautionResult | None:
    if report.trade_caution is None:
        return None

    source = report.trade_caution
    return TradeCautionResult(
        score=source.score,
        level=source.level,
        label=source.label,
        summary=source.summary,
        drivers=source.drivers,
        dimensions=source.dimensions.model_dump(mode="json"),
    )


@dataclass
class PipelineResult:
    response: TokenScanV2Response
    features: TokenFeatureSchema


class TokenScoringPipeline:
    def __init__(self) -> None:
        self.extractor = TokenFeatureExtractor()
        self.explanation = ExplanationEngine()
        self.ml_engine = get_ml_engine()
        self.version = "live_report_adapter_v21"

    def run(self, *, report: CheckOverview) -> PipelineResult:
        features = self.extractor.from_report(report)
        rule_score = float(_metric_value(report, "Rule rug score") or report.score)
        liquidity_rug_component = _metric_value(report, "Liquidity rug component")
        liquidity_rug_component_value = (
            int(liquidity_rug_component) if liquidity_rug_component and liquidity_rug_component.isdigit() else None
        )

        # ML model prediction
        ml_probability = self.ml_engine.predict_probability(features, rule_score)
        base_rug_probability = report.rug_probability / 100.0
        if self.ml_engine.has_model:
            # Blend rule-based probability with ML model
            final_probability = 0.6 * base_rug_probability + 0.4 * ml_probability
        else:
            final_probability = base_rug_probability

        risk_increasers = [
            _to_contributor(
                factor.code,
                factor.label,
                factor.explanation,
                factor.weight,
                factor.severity,
            )
            for factor in report.risk_increasers
        ]
        risk_reducers = [
            _to_contributor(
                factor.code,
                factor.label,
                factor.explanation,
                factor.weight,
                "low",
            )
            for factor in report.risk_reducers
        ]
        explanation = self.explanation.build_explanation(
            risk_increasers=risk_increasers,
            risk_reducers=risk_reducers,
            summary=report.summary,
        )

        blended_score = int(final_probability * 100)

        response = TokenScanV2Response(
            entity_address=features.token_address,
            score=blended_score,
            rug_probability=round(final_probability * 100, 2),
            technical_risk=report.technical_risk,
            distribution_risk=report.distribution_risk,
            market_execution_risk=report.market_execution_risk,
            market_maturity=report.market_maturity,
            behaviour_risk=report.behaviour_risk,
            rule_score=round(rule_score, 2),
            ml_probability=round(ml_probability, 4),
            final_probability=round(final_probability, 4),
            risk_level=report.status,
            confidence=report.confidence,
            low_confidence=report.confidence < 0.45,
            category_scores=ScoreCategoryScores(
                technical_risk=report.technical_risk,
                distribution_risk=report.distribution_risk,
                market_execution_risk=report.market_execution_risk,
                market_maturity=report.market_maturity,
                behaviour_risk=report.behaviour_risk,
                liquidity_rug_component=liquidity_rug_component_value,
            ),
            top_findings=risk_increasers[:6],
            model=ModelVersionInfo(
                version=self.ml_engine.version if self.ml_engine.has_model else self.version,
                rule_engine_version=self.version,
                calibration_version="ml_blended" if self.ml_engine.has_model else "integrated_maturity_correction",
            ),
            explanation=explanation,
            behaviour_analysis=_map_behaviour_analysis(report),
            trade_caution=_map_trade_caution(report),
            feature_metadata={
                "feature_version": self.extractor.feature_version,
                "model_version": self.ml_engine.version,
                "scoring_source": "backend.app.services.analyzer.compute_token_scoring_v21",
                "summary_source": "backend.app.services.analyzer.build_token_summary",
            },
        )
        return PipelineResult(response=response, features=features)
