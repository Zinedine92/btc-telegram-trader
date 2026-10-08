"""Tests for the read-only Binance authenticated client."""

import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch

import binance_readonly_client


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"accountType": "SPOT", "balances": []}).encode()


class BinanceReadonlyClientTests(unittest.TestCase):
    def test_signed_query_and_headers_are_built(self):
        captured = {}

        def fake_opener(request, timeout=10):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            return FakeResponse()

        with patch.dict(
            os.environ,
            {
                "BINANCE_API_KEY": "test-key",
                "BINANCE_API_SECRET": "test-secret",
            },
            clear=True,
        ):
            result = binance_readonly_client.get_account_info(opener=fake_opener)

        self.assertEqual(json.loads(result)["accountType"], "SPOT")
        self.assertEqual(captured["method"], "GET")
        self.assertEqual(captured["timeout"], 10)
        # Binance requires uppercase header name X-MBX-APIKEY
        self.assertEqual(captured["headers"]["X-MBX-APIKEY"], "test-key")

        query = captured["url"].split("?", 1)[1]
        unsigned = query.split("&signature=", 1)[0]
        expected = hmac.new(
            b"test-secret",
            unsigned.encode(),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(query.split("&signature=", 1)[1], expected)

    def test_client_has_no_order_method(self):
        self.assertFalse(hasattr(binance_readonly_client, "create_order"))
        self.assertFalse(hasattr(binance_readonly_client, "cancel_order"))


if __name__ == "__main__":
    unittest.main()
