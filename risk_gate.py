"""Single fail-closed gate: SignalValidator -> RiskEngine.

This module is analysis/risk only. It never places, modifies, or cancels orders.
"""

from strategy import Analysis
from validation.signal_validator import Signal, SignalValidator
from risk.risk_engine import RiskEngine, TradeRequest, RiskResult


def evaluate_analysis(analysis: Analysis, equity: float, leverage: int = 20):
    if analysis.bias == "NO_TRADE":
        return False, "NO_TRADE: strategy did not produce an actionable setup.", None

    signal = Signal(
        side=analysis.bias,
        score=analysis.score,
        entry_price=float(analysis.entry),
        stop_loss=float(analysis.stop_loss),
        take_profit=float(analysis.take_profit),
        market_regime="TRENDING",
        structure_confirmed=True,
        setup_confirmed=True,
    )

    signal_result = SignalValidator().validate(signal)
    if not signal_result.valid:
        return False, f"SIGNAL BLOCKED: {signal_result.reason}", None

    risk_result = RiskEngine().validate(
        TradeRequest(
            side=signal.side,
            equity=float(equity),
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            leverage=int(leverage),
        )
    )
    if not risk_result.approved:
        return False, f"RISK BLOCKED: {risk_result.reason}", risk_result

    return True, "PASS: signal and all hard risk limits passed. Execution remains disabled.", risk_result
