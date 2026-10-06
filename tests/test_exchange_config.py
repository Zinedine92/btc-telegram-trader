"""Tests for safe Binance environment configuration."""

import os
import unittest
from unittest.mock import patch

from exchange_config import (
    BINANCE_LIVE_URL,
    BINANCE_TESTNET_URL,
    get_binance_base_url,
)


class ExchangeConfigTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_testnet_is_the_default(self):
        self.assertEqual(get_binance_base_url(), BINANCE_TESTNET_URL)

    @patch.dict(os.environ, {"BINANCE_MODE": "TESTNET"}, clear=True)
    def test_testnet_is_selected(self):
        self.assertEqual(get_binance_base_url(), BINANCE_TESTNET_URL)

    @patch.dict(
        os.environ,
        {"BINANCE_MODE": "LIVE"},
        clear=True,
    )
    def test_live_is_blocked_without_explicit_opt_in(self):
        with self.assertRaises(RuntimeError):
            get_binance_base_url()

    @patch.dict(
        os.environ,
        {"BINANCE_MODE": "LIVE", "ENABLE_LIVE_TRADING": "YES"},
        clear=True,
    )
    def test_live_requires_explicit_opt_in(self):
        self.assertEqual(get_binance_base_url(), BINANCE_LIVE_URL)


if __name__ == "__main__":
    unittest.main()
