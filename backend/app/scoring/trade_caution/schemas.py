from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TradeCautionDimensions:
    admin_caution: int
    execution_caution: int
    concentration_caution: int
    behavioural_caution: int
    market_structure_strength: int


@dataclass
class TradeCautionComputation:
    score: int
    level: str
    label: str
    summary: str
    drivers: list[str] = field(default_factory=list)
    dimensions: TradeCautionDimensions | None = None
