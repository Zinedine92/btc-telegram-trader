#!/usr/bin/env python3
"""Safe Binance connection test.

This script verifies Binance API connectivity and account access.
It is READ-ONLY and never places, cancels, or modifies orders.

Usage:
    python binance_connection_test.py

Exit codes:
    0 = Connection successful, account info retrieved
    1 = Configuration error (missing credentials or environment)
    2 = Connection error (network, timeout, or API unavailable)
    3 = Authentication error (invalid credentials)
"""

import sys
import json

from exchange_client import get_binance_credentials
from exchange_config import get_binance_base_url
from binance_readonly_client import get_account_info


def test_connection():
    """Test Binance connection and retrieve account info in read-only mode."""
    print("=" * 70)
    print("BINANCE CONNECTION TEST (READ-ONLY MODE)")
    print("=" * 70)
    print()

    # Step 1: Check configuration
    print("[1/3] Checking configuration...")
    try:
        base_url = get_binance_base_url()
        api_key, api_secret = get_binance_credentials()
        print(f"  ✓ Base URL: {base_url}")
        print(f"  ✓ API Key: {api_key[:8]}...{api_key[-4:]}")
        print(f"  ✓ API Secret: {'***' * 10} (length: {len(api_secret)})")
        print()
    except RuntimeError as exc:
        print(f"  ✗ Configuration Error: {exc}")
        return 1

    # Step 2: Attempt connection
    print("[2/3] Connecting to Binance API...")
    try:
        account_info_json = get_account_info()
        print(f"  ✓ HTTP request succeeded (200 OK)")
        print()
    except ConnectionError as exc:
        print(f"  ✗ Network Error: {exc}")
        return 2
    except TimeoutError as exc:
        print(f"  ✗ Connection Timeout: {exc}")
        return 2
    except RuntimeError as exc:
        if "HTTP" in str(exc) or "status" in str(exc).lower():
            print(f"  ✗ HTTP Error: {exc}")
            return 3
        print(f"  ✗ Error: {exc}")
        return 2

    # Step 3: Parse and display account info
    print("[3/3] Parsing account information...")
    try:
        account_info = json.loads(account_info_json)
        account_type = account_info.get("accountType", "UNKNOWN")
        print(f"  ✓ Account Type: {account_type}")

        balances = account_info.get("balances", [])
        non_zero = [
            b for b in balances
            if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0
        ]
        if non_zero:
            print(f"  ✓ Non-zero balances: {len(non_zero)} asset(s)")
            for b in non_zero[:5]:
                asset = b.get("asset")
                free = float(b.get("free", 0))
                locked = float(b.get("locked", 0))
                print(f"      - {asset}: free={free}, locked={locked}")
            if len(non_zero) > 5:
                print(f"      ... and {len(non_zero) - 5} more")
        else:
            print(f"  ✓ No non-zero balances (account may be empty)")
        print()
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"  ✗ Parse Error: {exc}")
        return 2

    print("=" * 70)
    print("✓ BINANCE CONNECTION TEST PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • API credentials are valid and configured")
    print("  • Network connectivity to Binance API is working")
    print("  • Authentication succeeded")
    print("  • Account info retrieved in READ-ONLY mode")
    print()
    print("⚠️  This test verifies connectivity only.")
    print("⚠️  Real trading remains DISABLED.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(test_connection())
