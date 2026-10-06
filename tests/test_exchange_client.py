import os
import unittest
from unittest.mock import patch

from exchange_client import get_binance_credentials


class ExchangeCredentialTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials_are_rejected(self):
        with self.assertRaises(RuntimeError):
            get_binance_credentials()

    @patch.dict(
        os.environ,
        {"BINANCE_API_KEY": "test-key", "BINANCE_API_SECRET": "test-secret"},
        clear=True,
    )
    def test_credentials_are_loaded_from_environment(self):
        self.assertEqual(
            get_binance_credentials(),
            ("test-key", "test-secret"),
        )


if __name__ == "__main__":
    unittest.main()
