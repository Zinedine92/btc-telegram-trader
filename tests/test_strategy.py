import unittest
from decimal import Decimal
from market_data import Candle
from strategy import analyze

class StrategyTests(unittest.TestCase):
    def test_uptrend_analysis(self):
        candles=[Candle(Decimal(i),Decimal(i+2),Decimal(i-1),Decimal(i+1),Decimal("1")) for i in range(1,61)]
        self.assertEqual(analyze(candles).bias,"LONG")
    def test_requires_enough_candles(self):
        with self.assertRaises(ValueError): analyze([])

if __name__ == "__main__": unittest.main()
