"""Tests for the read-only public market-data adapter."""

import unittest
from unittest.mock import patch
import io
import json
from urllib.error import HTTPError
from market_data import get_btcusdt_price, get_btcusdt_candles


class FakeResp:
    status = 200
    def __init__(self, obj): self._b = json.dumps(obj).encode()
    def read(self): return self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False


def blocked(*a, **k):
    raise HTTPError("https://x", 451, "Unavailable", {}, io.BytesIO(b""))

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

class FallbackTests(unittest.TestCase):
    @patch("market_data.urlopen")
    def test_candles_fall_back_to_gate_when_binance_blocked(self, mock_urlopen):
        rows = [[str(1700000000 + i * 3600), "1000", "101", "102", "99", "100", "5", "true"] for i in range(25)]
        rows.append(["1700090000", "1", "1", "1", "1", "1", "1", "false"])  # forming candle
        calls = []

        def fake(request, timeout=5):
            calls.append(request.full_url)
            if "binance" in request.full_url:
                blocked()
            return FakeResp(rows)

        mock_urlopen.side_effect = fake
        candles = get_btcusdt_candles("1h", 50)
        self.assertEqual(len(candles), 25)             # forming candle dropped
        c = candles[0]
        self.assertEqual((str(c.open), str(c.high), str(c.low), str(c.close), str(c.volume)),
                         ("100", "102", "99", "101", "5"))
        self.assertTrue(any("gateio" in u for u in calls))

    @patch("market_data.urlopen")
    def test_price_falls_back_to_gate(self, mock_urlopen):
        def fake(request, timeout=5):
            if "binance" in request.full_url:
                blocked()
            return FakeResp([{"currency_pair": "BTC_USDT", "last": "77777.5"}])
        mock_urlopen.side_effect = fake
        self.assertEqual(str(get_btcusdt_price().price), "77777.5")


if __name__ == "__main__":
    unittest.main()
