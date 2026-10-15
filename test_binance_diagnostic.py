#!/usr/bin/env python3
"""Safe, read-only Binance TESTNET connectivity diagnostic.

Checks configuration, TESTNET public connectivity, and authenticated account
access using the repository's existing read-only client. It never prints
credentials, signatures, account data, or raw server response bodies. It
refuses to run authenticated checks unless BINANCE_MODE is TESTNET.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def test_configuration():
    """Validate that credentials exist and this diagnostic is TESTNET-only."""
    print("[1/3] CONFIGURATION")
    missing = [
        name for name in ("BINANCE_API_KEY", "BINANCE_API_SECRET")
        if not os.getenv(name)
    ]
    if missing:
        print("FAIL: Missing required environment variable(s): " + ", ".join(missing))
        return False

    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()
    if mode != "TESTNET":
        print("FAIL: Diagnostic is TESTNET-only; set BINANCE_MODE=TESTNET.")
        print("No Binance authenticated request was sent.")
        return False

    print("PASS: Binance credentials are present (values not displayed).")
    print("PASS: Mode is TESTNET; live trading remains untouched.")
    return True


def test_public_connectivity():
    """Check only the Binance TESTNET public server-time endpoint."""
    print("[2/3] TESTNET PUBLIC CONNECTIVITY")
    request = Request("https://testnet.binance.vision/api/v3/time", method="GET")
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            if response.status != 200 or "serverTime" not in payload:
                print("FAIL: TESTNET returned an unexpected response.")
                return False
        print("PASS: Binance TESTNET public endpoint responded.")
        return True
    except HTTPError as exc:
        print(f"FAIL: TESTNET HTTP error (status {exc.code}); response body hidden.")
    except URLError:
        print("FAIL: Network/DNS connection to Binance TESTNET failed.")
    except TimeoutError:
        print("FAIL: Connection to Binance TESTNET timed out.")
    except (ValueError, UnicodeError):
        print("FAIL: TESTNET response could not be validated.")
    except Exception:
        print("FAIL: Unexpected TESTNET connectivity error; details hidden.")
    return False


def test_authenticated_access():
    """Verify authenticated read-only access using the existing client."""
    print("[3/3] AUTHENTICATED TESTNET ACCESS (READ-ONLY)")
    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()
    if mode != "TESTNET":
        print("SKIP: TESTNET-only safety guard blocked the authenticated request.")
        return False
    if not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET"):
        print("SKIP: Required credentials are missing.")
        return False

    try:
        # Existing client performs only GET /api/v3/account and uses
        # exchange_config.py for the TESTNET base URL.
        from binance_readonly_client import get_account_info
        payload = json.loads(get_account_info())
        if not isinstance(payload, dict) or "balances" not in payload:
            print("FAIL: Binance response did not match the expected account schema.")
            return False
        print("PASS: Authenticated read-only TESTNET request succeeded.")
        print("Account details were intentionally not displayed.")
        return True
    except HTTPError as exc:
        if exc.code in (401, 403):
            print(f"FAIL: Binance rejected authentication/permissions (HTTP {exc.code}).")
        else:
            print(f"FAIL: Binance TESTNET returned HTTP {exc.code}; response body hidden.")
    except URLError:
        print("FAIL: Network/DNS connection failed during authenticated TESTNET access.")
    except TimeoutError:
        print("FAIL: Authenticated TESTNET request timed out.")
    except RuntimeError:
        print("FAIL: Binance configuration blocked the request.")
    except (ValueError, UnicodeError):
        print("FAIL: Binance returned an unreadable response.")
    except Exception:
        print("FAIL: Authenticated TESTNET check failed; details hidden.")
    return False


def main():
    print("BINANCE SAFE DIAGNOSTIC — TESTNET ONLY")
    config_ok = test_configuration()
    if not config_ok:
        print("\nRESULT: FAIL — configuration must be corrected before network checks.")
        return 1

    public_ok = test_public_connectivity()
    auth_ok = test_authenticated_access()
    print("\nSUMMARY")
    print("Configuration: " + ("PASS" if config_ok else "FAIL"))
    print("TESTNET public connectivity: " + ("PASS" if public_ok else "FAIL"))
    print("Authenticated TESTNET access: " + ("PASS" if auth_ok else "FAIL"))
    print("Trading actions: NOT AVAILABLE; no orders were sent.")
    return 0 if config_ok and public_ok and auth_ok else 2


if __name__ == "__main__":
    sys.exit(main())
