#!/usr/bin/env python3
"""Comprehensive Binance API diagnostic.

This script verifies Binance API connectivity at multiple levels:
1. Public API connectivity (no credentials required)
2. Configuration validation (environment variables present)
3. Authenticated account access (read-only only)

This is READ-ONLY and never places, cancels, or modifies orders.

Usage:
    python test_binance_diagnostic.py

Exit codes:
    0 = All tests passed
    1 = Configuration error (missing credentials or environment)
    2 = Network or API error
    3 = Authentication error (invalid credentials)
"""

import sys
import json
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def test_public_connectivity():
    """Test public Binance API connectivity (no credentials needed)."""
    print("\n" + "=" * 70)
    print("[TEST 1/3] PUBLIC BINANCE API CONNECTIVITY")
    print("=" * 70)
    print()

    try:
        # Use public endpoint: server time
        print("[1a] Checking Binance Testnet public endpoint...")
        testnet_url = "https://testnet.binance.vision/api/v3/time"
        request = Request(testnet_url, method="GET")

        with urlopen(request, timeout=10) as response:
            data = response.read().decode("utf-8")
            time_data = json.loads(data)
            print(f"  ✓ Testnet HTTP 200 OK")
            print(f"  ✓ Server time (testnet): {time_data.get('serverTime')}")

        print()
        print("[1b] Checking Binance Live public endpoint...")
        live_url = "https://api.binance.com/api/v3/time"
        request = Request(live_url, method="GET")

        with urlopen(request, timeout=10) as response:
            data = response.read().decode("utf-8")
            time_data = json.loads(data)
            print(f"  ✓ Live HTTP 200 OK")
            print(f"  ✓ Server time (live): {time_data.get('serverTime')}")

        print()
        return True
    except HTTPError as e:
        print(f"  ✗ HTTP Error {e.code}: {e.reason}")
        print(f"     Response: {e.read().decode('utf-8')}")
        return False
    except URLError as e:
        print(f"  ✗ Network Error: {e.reason}")
        return False
    except TimeoutError as e:
        print(f"  ✗ Connection Timeout: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected Error: {e}")
        return False


def test_configuration():
    """Test environment variable configuration."""
    print("\n" + "=" * 70)
    print("[TEST 2/3] CONFIGURATION VALIDATION")
    print("=" * 70)
    print()

    import os

    print("[2a] Checking required environment variables...")

    # Check API credentials
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key:
        print("  ✗ BINANCE_API_KEY is not set")
        return False
    if not api_secret:
        print("  ✗ BINANCE_API_SECRET is not set")
        return False

    print(f"  ✓ BINANCE_API_KEY is set (length: {len(api_key)})")
    print(f"  ✓ BINANCE_API_SECRET is set (length: {len(api_secret)})")

    print()
    print("[2b] Checking Binance mode configuration...")

    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()
    enable_live = os.getenv("ENABLE_LIVE_TRADING", "NO").strip().upper()

    print(f"  ✓ BINANCE_MODE: {mode} (default: TESTNET)")
    print(f"  ✓ ENABLE_LIVE_TRADING: {enable_live} (default: NO)")

    if mode == "LIVE" and enable_live != "YES":
        print("  ⚠️  LIVE mode is blocked without ENABLE_LIVE_TRADING=YES")

    print()
    return True


def test_authenticated_access():
    """Test authenticated Binance API access (read-only only)."""
    print("\n" + "=" * 70)
    print("[TEST 3/3] AUTHENTICATED ACCOUNT ACCESS (READ-ONLY)")
    print("=" * 70)
    print()

    import os
    import hashlib
    import hmac
    from urllib.parse import urlencode

    print("[3a] Retrieving credentials...")
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("  ✗ Credentials not available")
        return False

    print(f"  ✓ API Key: {api_key[:8]}...{api_key[-4:]}")
    print(f"  ✓ API Secret: {'*' * (len(api_secret))} (masked)")

    print()
    print("[3b] Building authenticated request...")

    # Determine which base URL to use
    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()
    base_url = (
        "https://testnet.binance.vision"
        if mode == "TESTNET"
        else "https://api.binance.com"
    )

    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 5000,
    }

    # Build signed query
    query_string = urlencode(params)
    signature = hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    signed_query = query_string + "&signature=" + signature
    url = f"{base_url}/api/v3/account?{signed_query}"

    print(f"  ✓ Target URL: {base_url}/api/v3/account")
    print(f"  ✓ Mode: {mode}")

    print()
    print("[3c] Sending authenticated request...")

    try:
        request = Request(
            url,
            headers={"X-MBX-APIKEY": api_key},
            method="GET",
        )

        with urlopen(request, timeout=10) as response:
            account_data = response.read().decode("utf-8")
            account_info = json.loads(account_data)

            print(f"  ✓ HTTP 200 OK - Authentication successful")

            # Parse account info
            account_type = account_info.get("accountType", "UNKNOWN")
            print(f"  ✓ Account Type: {account_type}")

            # Show balances
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
                    print(f"      - {asset}: free={free:.8f}, locked={locked:.8f}")
                if len(non_zero) > 5:
                    print(f"      ... and {len(non_zero) - 5} more")
            else:
                print(f"  ✓ No non-zero balances (account may be empty)")

            print()
            return True

    except HTTPError as e:
        if e.code == 401:
            print(f"  ✗ HTTP 401 Unauthorized - Invalid API credentials")
        else:
            print(f"  ✗ HTTP {e.code}: {e.reason}")
        try:
            response_body = e.read().decode("utf-8")
            print(f"     Response: {response_body}")
        except:
            pass
        return False

    except URLError as e:
        print(f"  ✗ Network Error: {e.reason}")
        return False

    except TimeoutError as e:
        print(f"  ✗ Connection Timeout: {e}")
        return False

    except Exception as e:
        print(f"  ✗ Unexpected Error: {e}")
        return False


def main():
    """Run all diagnostics."""
    print("\n" + "=" * 70)
    print("BINANCE API DIAGNOSTIC SUITE")
    print("=" * 70)

    results = {
        "public_connectivity": test_public_connectivity(),
        "configuration": test_configuration(),
        "authenticated_access": test_authenticated_access(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)
    print()

    print(f"Public Binance Connectivity:     {'PASS ✓' if results['public_connectivity'] else 'FAIL ✗'}")
    print(f"Configuration Validation:        {'PASS ✓' if results['configuration'] else 'FAIL ✗'}")
    print(f"Authenticated Account Access:    {'PASS ✓' if results['authenticated_access'] else 'NOT TESTED / FAIL ✗'}")

    print()

    if all(results.values()):
        print("✓ ALL DIAGNOSTICS PASSED")
        print()
        print("✓ Public API connectivity: CONFIRMED")
        print("✓ Authenticated access: CONFIRMED")
        print()
        print("⚠️  This test verifies READ-ONLY connectivity only.")
        print("⚠️  Real trading remains DISABLED.")
        print()
        return 0
    else:
        print("✗ SOME DIAGNOSTICS FAILED - See details above")
        print()

        if not results["configuration"]:
            print("NEXT STEP:")
            print("  1. Set the following environment variables in cPanel:")
            print("     - BINANCE_API_KEY")
            print("     - BINANCE_API_SECRET")
            print("  2. Verify via: python test_binance_diagnostic.py")
            print()

        if not results["authenticated_access"] and results["configuration"]:
            print("NEXT STEP:")
            print("  1. Check your Binance API credentials at https://www.binance.com/en/account/api-management")
            print("  2. Verify the API key and secret are correct")
            print("  3. Rerun: python test_binance_diagnostic.py")
            print()

        return 1 if not results["configuration"] else 3


if __name__ == "__main__":
    sys.exit(main())
