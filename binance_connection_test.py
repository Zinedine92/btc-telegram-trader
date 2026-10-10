#!/usr/bin/env python3
"""Safe Binance connectivity test.

This script only reads account information. It never prints API credentials,
account balances, or other private account details, and never places orders.
"""
import json
import sys
from urllib.error import HTTPError, URLError
from socket import timeout as SocketTimeout

from exchange_client import get_binance_credentials
from exchange_config import get_binance_base_url
from binance_readonly_client import get_account_info


def test_connection():
    """Verify read-only Binance authentication without exposing account data."""
    print("=" * 64)
    print("BINANCE CONNECTION TEST (READ-ONLY)")
    print("=" * 64)

    print("[1/3] Checking configuration...")
    try:
        base_url = get_binance_base_url()
        get_binance_credentials()
        print("  Credentials: configured (values hidden)")
        print(f"  API endpoint: {base_url}")
    except RuntimeError as exc:
        print(f"  CONFIGURATION ERROR: {exc}")
        return 1

    print("[2/3] Connecting to Binance...")
    try:
        account_info_json = get_account_info()
    except HTTPError as exc:
        # Do not print the URL or request headers; keep response text bounded.
        print(f"  HTTP ERROR: Binance returned status {exc.code}.")
        return 3 if exc.code in (401, 403) else 2
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        print(f"  NETWORK ERROR: {type(reason).__name__ if reason else 'connection failed'}.")
        return 2
    except (TimeoutError, SocketTimeout):
        print("  TIMEOUT: Binance did not respond in time.")
        return 2
    except (ConnectionError, OSError) as exc:
        print(f"  CONNECTION ERROR: {type(exc).__name__}.")
        return 2
    except Exception as exc:
        # Avoid dumping exception strings which can include URLs or request data.
        print(f"  REQUEST FAILED: {type(exc).__name__}.")
        return 2

    print("  Authenticated read-only request: OK")

    print("[3/3] Validating response...")
    try:
        account_info = json.loads(account_info_json)
        if not isinstance(account_info, dict) or not isinstance(account_info.get("balances"), list):
            print("  INVALID RESPONSE: account data format was unexpected.")
            return 2
        account_type = account_info.get("accountType", "UNKNOWN")
        print(f"  Account response: valid (account type: {account_type})")
        print("  Balance details: hidden")
    except (json.JSONDecodeError, TypeError, ValueError):
        print("  INVALID RESPONSE: could not parse account data.")
        return 2

    print("=" * 64)
    print("BINANCE READ-ONLY CONNECTION TEST PASSED")
    print("No orders, transfers, or withdrawals were performed.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(test_connection())
