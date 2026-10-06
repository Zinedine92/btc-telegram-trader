"""Tests for the read-only public market-data adapter."""

import unittest
from unittest.mock import patch
from market_data import get_btcusdt_price

class MarketDataTests(unittest.TestCase):
    @patch("market_data.urlopen")
    def test_valid_price_response(self, mock_urlopen):
        class Response:
            status = 200
            def read(self): return b'{"symbol":"BTCUSDT","price":"100000.12"}'
            def __enter__(self): return self
            def __exit__(self, *args): return False
        mock_urlopen.return_value = Response()
        result = get_btcusdt_price()
        self.assertEqual(result.symbol, "BTCUSDT")
        self.assertEqual(str(result.price), "100000.12")

    @patch("market_data.urlopen")
    def test_bad_symbol_is_rejected(self, mock_urlopen):
        class Response:
            status = 200
            def read(self): return b'{"symbol":"ETHUSDT","price":"1000"}'
            def __enter__(self): return self
            def __exit__(self, *args): return False
        mock_urlopen.return_value = Response()
        with self.assertRaises(RuntimeError):
            get_btcusdt_price()

if __name__ == "__main__":
    unittest.main()
