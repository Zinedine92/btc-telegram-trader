"""Tests for safe Binance balance parsing."""

import json
import unittest
from unittest.mock import patch

from binance_balance import get_btc_usdt_balances, parse_balances


class BinanceBalanceTests(unittest.TestCase):
    def test_parse_balances_filters_zero_assets(self):
        payload = {
            "balances": [
                {"asset": "BTC", "free": "0.010000", "locked": "0"},
                {"asset": "USDT", "free": "25.50", "locked": "1.5"},
                {"asset": "ETH", "free": "0", "locked": "0"},
            ]
        }
        result = parse_balances(json.dumps(payload))
        self.assertEqual(result["BTC"]["free"], 0.01)
        self.assertEqual(result["USDT"]["locked"], 1.5)
        self.assertNotIn("ETH", result)

    @patch("binance_balance.get_account_info")
    def test_btc_usdt_helper_is_read_only(self, mock_account):
        mock_account.return_value = json.dumps(
            {
                "balances": [
                    {"asset": "BTC", "free": "0.02", "locked": "0"},
                    {"asset": "USDT", "free": "100", "locked": "0"},
                    {"asset": "ETH", "free": "5", "locked": "0"},
                ]
            }
        )
        self.assertEqual(
            get_btc_usdt_balances(),
            {
                "BTC": {"free": 0.02, "locked": 0.0},
                "USDT": {"free": 100.0, "locked": 0.0},
            },
        )
        mock_account.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
