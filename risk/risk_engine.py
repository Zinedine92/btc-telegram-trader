"""Hard risk barrier for BTC/USDT trade decisions.

This module is independent of AI-generated signals. A trade must pass
RiskEngine.validate() before any future execution layer is allowed to act.
"""

from dataclasses import dataclass
from math import isfinite
from typing import Optional, Tuple

from .risk_config import RiskConfig


@dataclass(frozen=True)
class TradeRequest:
    side: str
    equity: float
    entry_price: float
    stop_loss: float
    take_profit: float
    leverage: int
    daily_loss_pct: float = 0.0
    total_open_risk_pct: float = 0.0
    open_positions: int = 0
    consecutive_losses: int = 0
    liquidation_distance_pct: float = 100.0


@dataclass(frozen=True)
class RiskResult:
    approved: bool
    reason: str
    risk_amount: float = 0.0
    position_size: float = 0.0
    reward_risk: float = 0.0
    stop_distance_pct: float = 0.0


class RiskEngine:
    """Deterministic hard-limit gate between signals and execution."""

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()

    @staticmethod
    def _valid_number(value: float) -> bool:
        return isinstance(value, (int, float)) and isfinite(float(value))

    @staticmethod
    def _blocked(reason: str, rr: float = 0.0, stop_pct: float = 0.0) -> RiskResult:
        return RiskResult(
            approved=False,
            reason=reason,
            reward_risk=rr,
            stop_distance_pct=stop_pct,
        )

    def calculate_stop_distance_pct(
        self, entry_price: float, stop_loss: float
    ) -> float:
        return abs(entry_price - stop_loss) / entry_price * 100.0

    def calculate_reward_risk(
        self,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> float:
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        if risk <= 0:
            return 0.0
        return reward / risk

    def calculate_position_size(
        self,
        equity: float,
        entry_price: float,
        stop_loss: float,
    ) -> Tuple[float, float]:
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            return 0.0, 0.0

        risk_amount = equity * (self.config.max_risk_per_trade_pct / 100.0)
        position_size = risk_amount / stop_distance
        return risk_amount, position_size

    def check_liquidation_distance(self, liquidation_distance_pct: float) -> bool:
        return liquidation_distance_pct >= self.config.min_liquidation_distance_pct

    def validate(self, trade: TradeRequest) -> RiskResult:
        """Return PASS only when every hard safety check succeeds."""
        side = trade.side.upper().strip()

        numeric_fields = (
            trade.equity,
            trade.entry_price,
            trade.stop_loss,
            trade.take_profit,
            trade.leverage,
            trade.daily_loss_pct,
            trade.total_open_risk_pct,
            trade.open_positions,
            trade.consecutive_losses,
            trade.liquidation_distance_pct,
        )

        if not all(self._valid_number(value) for value in numeric_fields):
            return self._blocked("Invalid or non-finite risk input.")

        if side not in {"LONG", "SHORT"}:
            return self._blocked("Invalid trade side.")

        if trade.equity <= 0:
            return self._blocked("Equity must be positive.")

        if trade.entry_price <= 0 or trade.stop_loss <= 0 or trade.take_profit <= 0:
            return self._blocked(
                "Entry, stop-loss and take-profit must be positive."
            )

        if trade.leverage < 1 or trade.leverage > self.config.max_leverage:
            return self._blocked(
                f"Leverage exceeds hard limit of {self.config.max_leverage}x."
            )

        if side == "LONG":
            if trade.stop_loss >= trade.entry_price:
                return self._blocked("LONG stop-loss must be below entry.")
            if trade.take_profit <= trade.entry_price:
                return self._blocked("LONG take-profit must be above entry.")
        else:
            if trade.stop_loss <= trade.entry_price:
                return self._blocked("SHORT stop-loss must be above entry.")
            if trade.take_profit >= trade.entry_price:
                return self._blocked("SHORT take-profit must be below entry.")

        if trade.daily_loss_pct >= self.config.max_daily_loss_pct:
            return self._blocked("Daily loss limit reached.")

        if trade.total_open_risk_pct >= self.config.max_total_open_risk_pct:
            return self._blocked("Total open risk limit reached.")

        if trade.open_positions >= self.config.max_open_positions:
            return self._blocked("Maximum open positions reached.")

        if trade.consecutive_losses >= self.config.max_consecutive_losses:
            return self._blocked("Maximum consecutive losses reached.")

        stop_distance_pct = self.calculate_stop_distance_pct(
            trade.entry_price, trade.stop_loss
        )

        if stop_distance_pct < self.config.min_stop_distance_pct:
            return self._blocked(
                "Stop-loss distance is too tight.",
                stop_pct=stop_distance_pct,
            )

        if stop_distance_pct > self.config.max_stop_distance_pct:
            return self._blocked(
                "Stop-loss distance is too wide.",
                stop_pct=stop_distance_pct,
            )

        reward_risk = self.calculate_reward_risk(
            side,
            trade.entry_price,
            trade.stop_loss,
            trade.take_profit,
        )

        if reward_risk < self.config.min_reward_risk:
            return self._blocked(
                f"Reward/Risk below minimum {self.config.min_reward_risk:.2f}.",
                rr=reward_risk,
                stop_pct=stop_distance_pct,
            )

        if not self.check_liquidation_distance(trade.liquidation_distance_pct):
            return self._blocked(
                "Liquidation distance is below the hard safety minimum.",
                rr=reward_risk,
                stop_pct=stop_distance_pct,
            )

        risk_amount, position_size = self.calculate_position_size(
            trade.equity,
            trade.entry_price,
            trade.stop_loss,
        )

        if risk_amount <= 0 or position_size <= 0:
            return self._blocked(
                "Calculated position size is invalid.",
                rr=reward_risk,
                stop_pct=stop_distance_pct,
            )

        return RiskResult(
            approved=True,
            reason="PASS: trade satisfies all hard risk limits.",
            risk_amount=risk_amount,
            position_size=position_size,
            reward_risk=reward_risk,
            stop_distance_pct=stop_distance_pct,
        )
