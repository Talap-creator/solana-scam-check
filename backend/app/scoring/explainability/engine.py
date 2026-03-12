from __future__ import annotations

from ..schemas import ScoreContributor, ScoreExplanation


class ExplanationEngine:
    def build_explanation(
        self,
        *,
        risk_increasers: list[ScoreContributor],
        risk_reducers: list[ScoreContributor],
        summary: str,
    ) -> ScoreExplanation:
        return ScoreExplanation(
            risk_increasers=risk_increasers[:6],
            risk_reducers=risk_reducers[:6],
            summary=summary,
        )
