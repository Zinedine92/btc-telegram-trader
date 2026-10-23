import unittest

import indicators as ind


class IndicatorTests(unittest.TestCase):
    def test_ema_constant_series(self):
        self.assertEqual(ind.ema([5.0] * 30, 10), [5.0] * 30)

    def test_ema_needs_enough_values(self):
        with self.assertRaises(ValueError):
            ind.ema([1.0] * 3, 10)

    def test_rsi_extremes(self):
        up = [float(i) for i in range(1, 40)]
        self.assertEqual(ind.rsi(up), 100.0)
        self.assertLess(ind.rsi(up[::-1]), 1e-9)
        self.assertEqual(ind.rsi([5.0] * 40), 50.0)

    def test_atr_constant_range(self):
        n = 40
        h, l, c = [11.0] * n, [9.0] * n, [10.0] * n
        self.assertAlmostEqual(ind.atr(h, l, c, 14), 2.0)

    def test_efficiency_ratio(self):
        self.assertAlmostEqual(ind.efficiency_ratio([float(i) for i in range(30)], 20), 1.0)
        zig = [float(i % 2) for i in range(30)]
        self.assertLess(ind.efficiency_ratio(zig, 20), 0.1)

    def test_swings_need_confirmation_bars(self):
        highs = [1, 2, 3, 9, 3, 2, 1, 2, 3, 4]
        lows = [h - 0.5 for h in highs]
        sh, _ = ind.swing_points(highs, lows, 3)
        self.assertEqual(sh, [(3, 9)])
        # a peak in the last k bars is not (yet) a swing -> no look-ahead
        sh2, _ = ind.swing_points([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [0] * 10, 3)
        self.assertEqual(sh2, [])

    def test_volume_ratio(self):
        self.assertAlmostEqual(ind.volume_ratio([1.0] * 20), 1.0)
        self.assertIsNone(ind.volume_ratio([1.0] * 5))


if __name__ == "__main__":
    unittest.main()
