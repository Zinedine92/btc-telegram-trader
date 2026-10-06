"""Read-only decision pipeline: Signal Validator -> Risk Engine.

This module never sends orders. It only produces an auditable PASS/BLOCK decision.
"""

from dataclasses import dataclass

from validation.signal_validator import Signal, SignalValidator
from risk.risk_engine import RiskEngine, TradeRequest, RiskResult


@dataclass(frozen=True)
class DecisionResult:
    approved: bool
    stage: str
    reason: str
    risk: RiskResult | None = None


class DecisionPipeline:
    def __init__(self, validator=None, risk_engine=None):
        self.validator = validator or SignalValidator()
        self.risk_engine = risk_engine or RiskEngine()

    def evaluate(self, signal: Signal, equity: float, leverage: int,
                 daily_loss_pct: float = 0.0, total_open_risk_pct: float = 0.0,
                 open_positions: int = 0, consecutive_losses: int = 0,
                 liquidation_distance_pct: float = 100.0) -> DecisionResult:
        validation = self.validator.validate(signal)
        if not validation.valid:
            return DecisionResult(False, "SIGNAL_VALIDATION", validation.reason)

        trade = TradeRequest(
            side=signal.side,
            equity=equity,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            leverage=leverage,
            daily_loss_pct=daily_loss_pct,
            total_open_risk_pct=total_open_risk_pct,
            open_positions=open_positions,
            consecutive_losses=consecutive_losses,
            liquidation_distance_pct=liquidation_distance_pct,
        )
        risk = self.risk_engine.validate(trade)
        if not risk.approved:
            return DecisionResult(False, "RISK_ENGINE", risk.reason, risk)

        return DecisionResult(True, "RISK_ENGINE", "PASS: signal and risk gates passed.", risk)
