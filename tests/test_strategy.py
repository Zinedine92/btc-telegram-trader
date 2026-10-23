import math
import unittest
from decimal import Decimal

from market_data import Candle
from strategy import analyze, classify_regime, MIN_SCORE
from risk_gate import evaluate_analysis


def c(o, h, l, cl, v=100):
    return Candle(*(Decimal(str(round(x, 2))) for x in (o, h, l, cl, v)))


def zigzag(n=160, slope=12.0, amp=250.0, base=30000.0, period=24, sign=1):
    """Trend with pullbacks (pullback-then-resume), deterministic."""
    out, prev = [], base
    for i in range(n):
        close = base + sign * slope * i + amp * math.sin(2 * math.pi * i / period)
        o = prev
        out.append(c(o, max(o, close) + 25, min(o, close) - 25, close))
        prev = close
    return out


def straight(n=60):
    return [Candle(Decimal(i), Decimal(i + 2), Decimal(i - 1), Decimal(i + 1), Decimal("1"))
            for i in range(1, n + 1)]


class StrategyTests(unittest.TestCase):
    def test_requires_enough_candles(self):
        with self.assertRaises(ValueError):
            analyze([])

    def test_uptrend_with_pullbacks_is_long_and_geometry_valid(self):
        candles = zigzag()
        found = None
        for end in range(60, len(candles) + 1):
            a = analyze(candles[:end])
            if a.bias == "LONG":
                found = a
                break
        self.assertIsNotNone(found, "expected at least one LONG in a clean uptrend")
        self.assertGreaterEqual(found.score, MIN_SCORE)
        self.assertLess(found.stop_loss, found.entry)
        self.assertGreater(found.take_profit, found.entry)
        rr = (found.take_profit - found.entry) / (found.entry - found.stop_loss)
        self.assertGreaterEqual(rr, Decimal("2.0"))
        self.assertEqual(len(found.factors), 8)
        self.assertEqual(sum(m for _, _, m in found.factors), 100.0)

    def test_downtrend_can_be_short(self):
        candles = zigzag(sign=-1, base=60000.0)
        biases = {analyze(candles[:e]).bias for e in range(60, len(candles) + 1)}
        self.assertIn("SHORT", biases)
        self.assertNotIn("LONG", biases)

    def test_vertical_overextended_move_is_not_chased(self):
        self.assertEqual(analyze(straight()).bias, "NO_TRADE")

    def test_range_market_is_no_trade(self):
        candles = zigzag(slope=0.0, amp=200.0)
        self.assertEqual(classify_regime(
            [float(x.close) for x in candles], [float(x.high) for x in candles],
            [float(x.low) for x in candles]), "RANGE")
        self.assertEqual(analyze(candles).bias, "NO_TRADE")

    def test_actionable_signal_can_pass_risk_gate_or_be_blocked_but_never_crash(self):
        candles = zigzag()
        for end in range(60, len(candles) + 1):
            a = analyze(candles[:end])
            approved, message, _ = evaluate_analysis(a, 1000, 20)
            self.assertIsInstance(approved, bool)
            self.assertTrue(message)


if __name__ == "__main__":
    unittest.main()
