import unittest
from decimal import Decimal

import backtest
import strategy
from strategy import Analysis
from market_data import Candle


def cd(o, h, l, c):
    return Candle(*(Decimal(str(x)) for x in (o, h, l, c, 100)))


class BacktestTests(unittest.TestCase):
    def test_stop_assumed_first_when_bar_touches_both(self):
        candles = [cd(100, 101, 99, 100)] * 5 + [cd(100, 110, 90, 100)] + [cd(100, 101, 99, 100)] * 5
        calls = {"n": 0}

        def fake(window):
            calls["n"] += 1
            if len(window) == 5:
                return Analysis("LONG", 80, Decimal(100), Decimal(95), Decimal(110), "t")
            return Analysis("NO_TRADE", 0, Decimal(100), Decimal(100), Decimal(100), "t")

        trades = backtest.run_backtest(candles, fake, use_risk_gate=False, warmup=4)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].exit_reason, "stop")
        self.assertLess(trades[0].r_multiple, -1.0)   # -1R minus costs

    def test_target_hit_gives_positive_r_net_of_costs(self):
        candles = [cd(100, 101, 99, 100)] * 5 + [cd(100, 112, 99.5, 111)] + [cd(111, 112, 110, 111)] * 3

        def fake(window):
            if len(window) == 5:
                return Analysis("LONG", 80, Decimal(100), Decimal(95), Decimal(110), "t")
            return Analysis("NO_TRADE", 0, Decimal(100), Decimal(100), Decimal(100), "t")

        t = backtest.run_backtest(candles, fake, use_risk_gate=False, warmup=4)
        self.assertEqual(t[0].exit_reason, "target")
        self.assertTrue(1.5 < t[0].r_multiple < 2.0)   # 2R minus costs

    def test_summarize_empty_and_values(self):
        self.assertEqual(backtest.summarize([]).trades, 0)
        T = backtest.Trade
        s = backtest.summarize([T("LONG", 1, 2, 2.0, "target"), T("SHORT", 3, 4, -1.0, "stop"),
                                T("LONG", 5, 6, -1.0, "stop")])
        self.assertEqual(s.trades, 3)
        self.assertAlmostEqual(s.total_r, 0.0)
        self.assertAlmostEqual(s.max_drawdown_r, 2.0)
        self.assertAlmostEqual(s.profit_factor, 1.0)

    def test_full_run_on_synthetic_data_is_deterministic(self):
        c = backtest.synthetic_candles(1200, seed=3)
        a = backtest.summarize(backtest.run_backtest(c, strategy.analyze))
        b = backtest.summarize(backtest.run_backtest(c, strategy.analyze))
        self.assertEqual(a, b)
        self.assertGreater(a.trades, 0)


if __name__ == "__main__":
    unittest.main()
