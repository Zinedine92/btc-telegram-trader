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


# Hard allowlist: this client can only call these read-only GET endpoints.
ALLOWED_PATHS = frozenset({"/api/v3/account", "/api/v3/openOrders"})


def signed_get(path, params=None, opener=urlopen):
    """Signed GET to an allowlisted read-only endpoint; returns the raw JSON text."""
    if path not in ALLOWED_PATHS:
        raise ValueError("Endpoint is not allowed in the read-only client.")
    api_key, api_secret = get_binance_credentials()
    base_url = get_binance_base_url()

    query_params = dict(params or {})
    query_params.update({"timestamp": int(time.time() * 1000), "recvWindow": 5000})
    query = _signed_query(query_params, api_secret)
    request = Request(
        f"{base_url}{path}?{query}",
        headers={"X-MBX-APIKEY": api_key},
        method="GET",
    )
    with opener(request, timeout=10) as response:
        return response.read().decode("utf-8")


def get_account_info(opener=urlopen):
    """Fetch authenticated account info from Binance TESTNET by default."""
    return signed_get("/api/v3/account", opener=opener)


def get_open_orders(opener=urlopen):
    """List currently open Spot orders (read-only)."""
    return signed_get("/api/v3/openOrders", opener=opener)
