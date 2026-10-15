"""Mock-only tests for safe TESTNET diagnostic behavior."""
import contextlib
import io
import json
import os
import unittest
from unittest.mock import patch
import test_binance_diagnostic as diagnostic


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps({"serverTime": 1}).encode()


class SafeDiagnosticTests(unittest.TestCase):
    def test_live_mode_is_rejected_without_network_access(self):
        env = {"BINANCE_API_KEY": "dummy", "BINANCE_API_SECRET": "dummy",
               "BINANCE_MODE": "LIVE", "ENABLE_LIVE_TRADING": "YES"}
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), contextlib.redirect_stdout(output):
            self.assertFalse(diagnostic.test_configuration())
        self.assertIn("TESTNET-only", output.getvalue())
        self.assertNotIn("dummy", output.getvalue())

    def test_public_endpoint_is_testnet_only(self):
        seen = {}
        def fake(request, timeout=10):
            seen["url"] = request.full_url
            return Response()
        with patch("test_binance_diagnostic.urlopen", side_effect=fake):
            self.assertTrue(diagnostic.test_public_connectivity())
        self.assertTrue(seen["url"].startswith("https://testnet.binance.vision/"))

    def test_live_mode_blocks_authenticated_client(self):
        env = {"BINANCE_API_KEY": "dummy", "BINANCE_API_SECRET": "dummy",
               "BINANCE_MODE": "LIVE", "ENABLE_LIVE_TRADING": "YES"}
        with patch.dict(os.environ, env, clear=True), patch(
            "binance_readonly_client.get_account_info"
        ) as client:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(diagnostic.test_authenticated_access())
            client.assert_not_called()

    def test_account_data_is_not_printed(self):
        env = {"BINANCE_API_KEY": "dummy", "BINANCE_API_SECRET": "dummy",
               "BINANCE_MODE": "TESTNET"}
        response = json.dumps({"balances": [{"asset": "BTC", "free": "9"}]})
        output = io.StringIO()
        with patch.dict(os.environ, env, clear=True), patch(
            "binance_readonly_client.get_account_info", return_value=response
        ):
            with contextlib.redirect_stdout(output):
                self.assertTrue(diagnostic.test_authenticated_access())
        self.assertNotIn("BTC", output.getvalue())
        self.assertNotIn("balances", output.getvalue())


if __name__ == "__main__":
    unittest.main()
