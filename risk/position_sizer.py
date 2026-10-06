"""Position sizing utilities for BTC/USDT risk-controlled trades."""

from dataclasses import dataclass

from .risk_config import RiskConfig


@dataclass(frozen=True)
class PositionSizeResult:
    risk_amount: float
    stop_distance: float
    position_size: float
    notional_value: float
    margin_required: float


class PositionSizer:
    """Calculate size from account risk, independent of leverage-based sizing."""

    def __init__(self, config: RiskConfig | None = None):
        self.config = config or RiskConfig()

    def calculate(
        self,
        equity: float,
        entry_price: float,
        stop_loss: float,
        leverage: int,
    ) -> PositionSizeResult:
        if equity <= 0:
            raise ValueError("Equity must be positive.")
        if entry_price <= 0 or stop_loss <= 0:
            raise ValueError("Entry price and stop-loss must be positive.")
        if leverage < 1 or leverage > self.config.max_leverage:
            raise ValueError(
                f"Leverage must be between 1x and {self.config.max_leverage}x."
            )

        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            raise ValueError("Stop-loss must differ from entry price.")

        risk_amount = equity * (self.config.max_risk_per_trade_pct / 100.0)
        position_size = risk_amount / stop_distance
        notional_value = position_size * entry_price
        margin_required = notional_value / leverage

        return PositionSizeResult(
            risk_amount=risk_amount,
            stop_distance=stop_distance,
            position_size=position_size,
            notional_value=notional_value,
            margin_required=margin_required,
        )
