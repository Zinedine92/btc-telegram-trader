import json
import os
import unittest
from unittest.mock import patch

import binance_readonly_client as client
import dashboard


class Resp:
    def __init__(self, obj): self.b = json.dumps(obj).encode()
    def read(self): return self.b
    def __enter__(self): return self
    def __exit__(self, *a): return False


class DashboardTests(unittest.TestCase):
    def test_value_assets_uses_usdt_btc_and_stable_prices(self):
        balances = {"USDT": {"free": 100.0, "locked": 0.0},
                    "BTC": {"free": 0.5, "locked": 0.1},
                    "ETH": {"free": 2.0, "locked": 0.0},
                    "XYZ": {"free": 1.0, "locked": 0.0}}
        prices = {"BTCUSDT": 80000.0, "ETHBTC": 0.05}
        rows, total = dashboard.value_assets(balances, prices)
        by = {r[0]: r for r in rows}
        self.assertAlmostEqual(by["BTC"][3], 48000.0)
        self.assertAlmostEqual(by["ETH"][3], 2.0 * 0.05 * 80000.0)
        self.assertIsNone(by["XYZ"][3])
        self.assertAlmostEqual(total, 100.0 + 48000.0 + 8000.0)
        self.assertEqual(rows[0][0], "BTC")      # sorted by value

    def test_format_portfolio_and_orders(self):
        text = dashboard.format_portfolio([("BTC", 0.5, 0.0, 40000.0), ("XYZ", 1.0, 0.0, None)], 40000.0)
        self.assertIn("Total ≈ 40,000.00 USDT", text)
        self.assertIn("price n/a", text)
        self.assertIn("READ-ONLY", text)
        self.assertIn("No open orders", dashboard.format_open_orders([]))
        o = [{"symbol": "BTCUSDT", "side": "BUY", "type": "LIMIT", "price": "70000", "origQty": "0.01", "executedQty": "0"}]
        self.assertIn("BTCUSDT BUY LIMIT price 70000", dashboard.format_open_orders(o))

    def test_get_prices_parses_list(self):
        with patch.dict(os.environ, {}, clear=True):
            p = dashboard.get_prices(opener=lambda r, timeout=10: Resp([{"symbol": "BTCUSDT", "price": "1.5"}]))
        self.assertEqual(p, {"BTCUSDT": 1.5})


class ClientGuardTests(unittest.TestCase):
    def test_only_allowlisted_get_endpoints(self):
        with patch.dict(os.environ, {"BINANCE_API_KEY": "k", "BINANCE_API_SECRET": "s"}, clear=True):
            for bad in ("/api/v3/order", "/sapi/v1/capital/withdraw/apply", "/fapi/v1/order"):
                with self.assertRaises(ValueError):
                    client.signed_get(bad, opener=lambda *a, **k: Resp({}))

    def test_open_orders_is_signed_get(self):
        seen = {}

        def opener(request, timeout=10):
            seen["url"], seen["method"] = request.full_url, request.get_method()
            return Resp([])

        with patch.dict(os.environ, {"BINANCE_API_KEY": "k", "BINANCE_API_SECRET": "s"}, clear=True):
            client.get_open_orders(opener=opener)
        self.assertEqual(seen["method"], "GET")
        self.assertIn("/api/v3/openOrders?", seen["url"])
        self.assertIn("signature=", seen["url"])


if __name__ == "__main__":
    unittest.main()
