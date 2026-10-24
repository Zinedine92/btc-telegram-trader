import csv
import os
import tempfile
import unittest
from unittest.mock import patch

import fetch_history as fh


class FetchHistoryTests(unittest.TestCase):
    def test_gate_page_maps_columns_and_skips_open_candle(self):
        rows = [["1700000000", "9", "101", "102", "99", "100", "5", "true"],
                ["1700003600", "9", "1", "1", "1", "1", "1", "false"]]
        with patch.object(fh, "_get", return_value=rows):
            out = fh.gate_page("1h", 1700000000000, 1700010000000)
        self.assertEqual(out, [(1700000000000, "100", "102", "99", "101", "5")])

    def test_main_writes_csv_loadable_by_backtest(self):
        import backtest
        from decimal import Decimal
        data = [(i * 3600000, "100", "102", "99", "101", "5") for i in range(300)]
        with tempfile.TemporaryDirectory() as d, patch.object(fh, "fetch", return_value=(data, "Gate.io")):
            path = os.path.join(d, "k.csv")
            self.assertEqual(fh.main(["30", path]), 0)
            candles = backtest.load_csv(path)
        self.assertEqual(len(candles), 300)
        self.assertEqual(candles[0].close, Decimal("101"))

    def test_bad_args_rejected(self):
        self.assertEqual(fh.main(["0"]), 1)
        self.assertEqual(fh.main(["30", "x.csv", "5m"]), 1)


if __name__ == "__main__":
    unittest.main()
