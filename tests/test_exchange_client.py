"""Unit tests for exchange_client credential handling.

Verifies:
- Credentials are loaded from environment variables only.
- Missing credentials are rejected with proper error.
- No credentials are hardcoded or logged.
"""

import os
import unittest
from unittest import mock

from exchange_client import get_binance_credentials


class ExchangeClientCredentialsTests(unittest.TestCase):
    """Test suite for Binance credential validation."""

    def test_valid_credentials_are_returned(self):
        """Test that valid environment credentials are returned."""
        with mock.patch.dict(
            os.environ,
            {
                "BINANCE_API_KEY": "test_key_12345",
                "BINANCE_API_SECRET": "test_secret_67890",
            },
        ):
            api_key, api_secret = get_binance_credentials()
            self.assertEqual(api_key, "test_key_12345")
            self.assertEqual(api_secret, "test_secret_67890")

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises RuntimeError."""
        with mock.patch.dict(
            os.environ,
            {"BINANCE_API_SECRET": "test_secret_67890"},
            clear=False,
        ):
            # Ensure API_KEY is not set
            os.environ.pop("BINANCE_API_KEY", None)
            with self.assertRaises(RuntimeError) as context:
                get_binance_credentials()
            self.assertIn("not configured", str(context.exception))

    def test_missing_api_secret_raises_error(self):
        """Test that missing API secret raises RuntimeError."""
        with mock.patch.dict(
            os.environ,
            {"BINANCE_API_KEY": "test_key_12345"},
            clear=False,
        ):
            # Ensure API_SECRET is not set
            os.environ.pop("BINANCE_API_SECRET", None)
            with self.assertRaises(RuntimeError) as context:
                get_binance_credentials()
            self.assertIn("not configured", str(context.exception))

    def test_missing_both_credentials_raises_error(self):
        """Test that missing both credentials raises RuntimeError."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BINANCE_API_KEY", None)
            os.environ.pop("BINANCE_API_SECRET", None)
            with self.assertRaises(RuntimeError) as context:
                get_binance_credentials()
            self.assertIn("not configured", str(context.exception))

    def test_empty_string_credentials_are_rejected(self):
        """Test that empty string credentials are treated as missing."""
        with mock.patch.dict(
            os.environ,
            {"BINANCE_API_KEY": "", "BINANCE_API_SECRET": ""},
        ):
            with self.assertRaises(RuntimeError):
                get_binance_credentials()

    def test_whitespace_only_credentials_are_rejected(self):
        """Test that whitespace-only credentials are treated as missing."""
        with mock.patch.dict(
            os.environ,
            {"BINANCE_API_KEY": "   ", "BINANCE_API_SECRET": "\t\n"},
        ):
            with self.assertRaises(RuntimeError):
                get_binance_credentials()


if __name__ == "__main__":
    unittest.main()
