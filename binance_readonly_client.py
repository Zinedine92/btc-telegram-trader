"""Read-only Binance authenticated client.

This module is intentionally limited to account/testnet inspection.
It never creates, modifies, cancels, or withdraws orders.
"""

import hashlib
import hmac
import json
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


def describe_http_error(exc):
    """Return a short, secret-free description of a Binance HTTPError.

    Includes only the HTTP status and Binance's own error code/message, which
    never contain API keys, secrets, or signatures.
    """
    text = f"HTTP {exc.code}"
    try:
        body = json.loads(exc.read().decode("utf-8", "replace"))
        code = body.get("code")
        if code is not None:
            text += f" (Binance code {code}: {str(body.get('msg', ''))[:200]})"
    except Exception:
        pass
    return text


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
