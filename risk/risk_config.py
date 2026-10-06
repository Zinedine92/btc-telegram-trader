"""
BTC/USDT Trading Bot - Risk Configuration
Version: 1.0

Centralized hard limits for the Risk Engine.
These values are safety controls, not trading signals.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    max_risk_per_trade_pct: float = 0.5
    max_total_open_risk_pct: float = 1.5
    max_daily_loss_pct: float = 2.0
    max_leverage: int = 20
    min_reward_risk: float = 2.0
    min_stop_distance_pct: float = 0.20
    max_stop_distance_pct: float = 5.0
    min_liquidation_distance_pct: float = 5.0
    max_open_positions: int = 1
    max_consecutive_losses: int = 3
