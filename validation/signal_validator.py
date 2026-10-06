"""Deterministic signal validation before the Risk Engine.

This layer validates signal quality and trade geometry. It never executes trades
and must never bypass the Risk Engine.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Signal:
    side: str
    score: float
    entry_price: float
    stop_loss: float
    take_profit: float
    market_regime: str
    structure_confirmed: bool
    setup_confirmed: bool


@dataclass(frozen=True)
class SignalValidationResult:
    valid: bool
    reason: str


class SignalValidator:
    """Hard validation gate for AI/strategy-generated signals."""

    MIN_SCORE = 70.0
    VALID_SIDES = {"LONG", "SHORT"}
    VALID_REGIMES = {"TRENDING", "RANGING", "VOLATILE", "UNKNOWN"}

    def validate(self, signal: Signal) -> SignalValidationResult:
        side = signal.side.upper().strip()
        regime = signal.market_regime.upper().strip()

        if side not in self.VALID_SIDES:
            return SignalValidationResult(False, "Invalid signal side.")

        values = (
            signal.score,
            signal.entry_price,
            signal.stop_loss,
            signal.take_profit,
        )
        if not all(isinstance(v, (int, float)) for v in values):
            return SignalValidationResult(False, "Signal contains invalid numeric values.")

        if not 0 <= signal.score <= 100:
            return SignalValidationResult(False, "Signal score must be between 0 and 100.")

        if signal.score < self.MIN_SCORE:
            return SignalValidationResult(False, "Signal score is below minimum threshold.")

        if signal.entry_price <= 0 or signal.stop_loss <= 0 or signal.take_profit <= 0:
            return SignalValidationResult(False, "Prices must be positive.")

        if regime not in self.VALID_REGIMES:
            return SignalValidationResult(False, "Invalid market regime.")

        if not signal.structure_confirmed:
            return SignalValidationResult(False, "Market structure is not confirmed.")

        if not signal.setup_confirmed:
            return SignalValidationResult(False, "Trade setup is not confirmed.")

        if side == "LONG":
            if signal.stop_loss >= signal.entry_price:
                return SignalValidationResult(False, "LONG stop-loss must be below entry.")
            if signal.take_profit <= signal.entry_price:
                return SignalValidationResult(False, "LONG take-profit must be above entry.")
        else:
            if signal.stop_loss <= signal.entry_price:
                return SignalValidationResult(False, "SHORT stop-loss must be above entry.")
            if signal.take_profit >= signal.entry_price:
                return SignalValidationResult(False, "SHORT take-profit must be below entry.")

        return SignalValidationResult(True, "PASS: signal satisfies validation rules.")
