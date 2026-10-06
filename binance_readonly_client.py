"""Read-only Binance authenticated client.

This module is intentionally limited to account/testnet inspection.
It never creates, modifies, cancels, or withdraws orders.
"""

import hashlib
import hmac
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from exchange_client import get_binance_credentials
from exchange_config import get_binance_base_url


def _signed_query(params, secret):
    query = urlencode(params)
    signature = hmac.new(
        secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return query + "&signature=" + signature


def get_account_info(opener=urlopen):
    """Fetch authenticated account info from Binance TESTNET by default."""
    api_key, api_secret = get_binance_credentials()
    base_url = get_binance_base_url()

    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000,
    }
    query = _signed_query(params, api_secret)
    request = Request(
        f"{base_url}/api/v3/account?{query}",
        headers={"X-MBX-APIKEY": api_key},
        method="GET",
    )

    with opener(request, timeout=10) as response:
        return response.read().decode("utf-8")
