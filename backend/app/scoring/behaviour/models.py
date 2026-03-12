from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BehaviourModuleComputation:
    key: str
    title: str
    status: str
    severity: str
    score: float
    summary: str
    details: list[str] = field(default_factory=list)
    evidence: dict[str, float | int | str | bool | None] = field(default_factory=dict)
    confidence: str = "limited"


@dataclass
class BehaviourComputation:
    summary: str
    overall_behaviour_risk: str
    confidence: str
    score: int
    modules: dict[str, BehaviourModuleComputation]
    confidence_breakdown: dict[str, str]
    version: str = "behaviour_v2"
    debug: dict[str, object] | None = None
