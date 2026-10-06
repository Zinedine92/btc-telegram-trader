"""Unit tests for the deterministic risk barrier and position sizing."""

import unittest

from risk.position_sizer import PositionSizer
from risk.risk_engine import RiskEngine, TradeRequest


class RiskEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine()

    def valid_trade(self):
        return TradeRequest(
            side="LONG",
            equity=1000.0,
            entry_price=100000.0,
            stop_loss=99000.0,
            take_profit=102000.0,
            leverage=20,
            liquidation_distance_pct=10.0,
        )

    def test_valid_trade_passes(self):
        result = self.engine.validate(self.valid_trade())
        self.assertTrue(result.approved)
        self.assertAlmostEqual(result.risk_amount, 5.0)
        self.assertAlmostEqual(result.reward_risk, 2.0)

    def test_leverage_above_limit_is_blocked(self):
        trade = self.valid_trade()
        trade = TradeRequest(**{**trade.__dict__, "leverage": 21})
        result = self.engine.validate(trade)
        self.assertFalse(result.approved)
        self.assertIn("Leverage exceeds", result.reason)

    def test_bad_long_stop_is_blocked(self):
        trade = self.valid_trade()
        trade = TradeRequest(**{**trade.__dict__, "stop_loss": 101000.0})
        result = self.engine.validate(trade)
        self.assertFalse(result.approved)

    def test_low_reward_risk_is_blocked(self):
        trade = self.valid_trade()
        trade = TradeRequest(**{**trade.__dict__, "take_profit": 101000.0})
        result = self.engine.validate(trade)
        self.assertFalse(result.approved)
        self.assertIn("Reward/Risk", result.reason)

    def test_daily_loss_limit_is_blocked(self):
        trade = self.valid_trade()
        trade = TradeRequest(**{**trade.__dict__, "daily_loss_pct": 2.0})
        result = self.engine.validate(trade)
        self.assertFalse(result.approved)

    def test_liquidation_distance_is_blocked(self):
        trade = self.valid_trade()
        trade = TradeRequest(**{**trade.__dict__, "liquidation_distance_pct": 4.9})
        result = self.engine.validate(trade)
        self.assertFalse(result.approved)

    def test_position_sizer_uses_risk_not_leverage(self):
        sizer = PositionSizer()
        result = sizer.calculate(
            equity=1000.0,
            entry_price=100000.0,
            stop_loss=99000.0,
            leverage=20,
        )
        self.assertAlmostEqual(result.risk_amount, 5.0)
        self.assertAlmostEqual(result.position_size, 0.005)
        self.assertAlmostEqual(result.notional_value, 500.0)
        self.assertAlmostEqual(result.margin_required, 25.0)


if __name__ == "__main__":
    unittest.main()
