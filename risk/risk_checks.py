"""Independent safety checks for trade requests.

This layer provides a clear, reusable pre-validation interface around the
deterministic RiskEngine. It does not execute trades.
"""

from dataclasses import dataclass

from .risk_engine import RiskEngine, RiskResult, TradeRequest


@dataclass(frozen=True)
class RiskCheckReport:
    passed: bool
    result: RiskResult


class RiskChecks:
    """Reusable gate for any future signal/execution pipeline."""

    def __init__(self, engine: RiskEngine | None = None):
        self.engine = engine or RiskEngine()

    def evaluate(self, trade: TradeRequest) -> RiskCheckReport:
        result = self.engine.validate(trade)
        return RiskCheckReport(
            passed=result.approved,
            result=result,
        )

    def can_execute(self, trade: TradeRequest) -> bool:
        """Return True only when every hard RiskEngine rule passes."""
        return self.evaluate(trade).passed
