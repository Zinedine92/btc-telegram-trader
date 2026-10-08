#!/usr/bin/env python3
"""Startup configuration validator.

Checks that all required environment variables are present and valid
before the bot attempts to use them. This prevents silent failures
and provides clear guidance on what needs to be configured.

This module does NOT connect to Binance or make any API calls.
It only validates that the environment is properly configured.
"""

import os
import sys


def validate_binance_configuration():
    """Validate Binance API credentials and mode configuration.
    
    Returns:
        tuple: (is_valid, missing_vars, config_dict)
        - is_valid: True if all required vars are present
        - missing_vars: list of missing variable names
        - config_dict: dict with current configuration (safe to log)
    """
    missing = []
    
    # Check required credentials
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key:
        missing.append("BINANCE_API_KEY")
    if not api_secret:
        missing.append("BINANCE_API_SECRET")
    
    # Check optional mode configuration
    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()
    enable_live = os.getenv("ENABLE_LIVE_TRADING", "NO").strip().upper()
    
    config = {
        "binance_mode": mode,
        "enable_live_trading": enable_live,
        "credentials_present": len(missing) == 0,
        "missing_credentials": missing,
    }
    
    return len(missing) == 0, missing, config


def validate_telegram_configuration():
    """Validate Telegram bot token configuration.
    
    Returns:
        tuple: (is_valid, missing_vars)
    """
    missing = []
    bot_token = os.getenv("BOT_TOKEN")
    
    if not bot_token:
        missing.append("BOT_TOKEN")
    
    return len(missing) == 0, missing


def validate_all_configuration():
    """Validate all required configuration.
    
    Returns:
        tuple: (is_valid, error_message_or_none)
    """
    binance_valid, binance_missing, binance_config = validate_binance_configuration()
    telegram_valid, telegram_missing = validate_telegram_configuration()
    
    all_valid = binance_valid and telegram_valid
    all_missing = binance_missing + telegram_missing
    
    if all_valid:
        return True, None
    
    # Build error message
    error_lines = [
        "\n" + "=" * 70,
        "CONFIGURATION ERROR: Missing required environment variables",
        "=" * 70,
        "",
    ]
    
    if telegram_missing:
        error_lines.append("TELEGRAM CONFIGURATION:")
        for var in telegram_missing:
            error_lines.append(f"  ✗ {var} is not set")
        error_lines.append("")
    
    if binance_missing:
        error_lines.append("BINANCE CONFIGURATION:")
        for var in binance_missing:
            error_lines.append(f"  ✗ {var} is not set")
        error_lines.append("")
    
    error_lines.extend([
        "NEXT STEPS IN NAMECHEAP/CPANEL:",
        "  1. Log in to your cPanel",
        "  2. Navigate to: Setup Python App / Environment Variables",
        "  3. Add each missing variable with its value",
        "",
        "Required Binance variables:",
        "  - BINANCE_API_KEY",
        "  - BINANCE_API_SECRET",
        "",
        "Optional Binance configuration (advanced):",
        "  - BINANCE_MODE (default: TESTNET)",
        "  - ENABLE_LIVE_TRADING (default: NO)",
        "",
        "Required Telegram variable:",
        "  - BOT_TOKEN",
        "",
        "After setting these variables in cPanel, restart the Python app.",
        "=" * 70,
        "",
    ])
    
    error_message = "\n".join(error_lines)
    return False, error_message


def print_configuration_status():
    """Print the current configuration status (safe info only).
    
    Never prints actual keys, secrets, or sensitive values.
    """
    binance_valid, binance_missing, binance_config = validate_binance_configuration()
    telegram_valid, telegram_missing = validate_telegram_configuration()
    
    print("\n" + "=" * 70)
    print("STARTUP CONFIGURATION STATUS")
    print("=" * 70)
    print()
    
    # Telegram
    print("TELEGRAM:")
    if telegram_valid:
        print("  ✓ BOT_TOKEN is set")
    else:
        print(f"  ✗ Missing: {', '.join(telegram_missing)}")
    print()
    
    # Binance
    print("BINANCE:")
    if binance_config["credentials_present"]:
        print("  ✓ BINANCE_API_KEY is set")
        print("  ✓ BINANCE_API_SECRET is set")
    else:
        for var in binance_config["missing_credentials"]:
            print(f"  ✗ {var} is not set")
    print()
    
    print("BINANCE MODE:")
    mode = binance_config["binance_mode"]
    enable_live = binance_config["enable_live_trading"]
    print(f"  Mode: {mode}")
    print(f"  Live Trading Enabled: {enable_live}")
    
    if mode == "LIVE" and enable_live != "YES":
        print("  ⚠️  LIVE mode requires ENABLE_LIVE_TRADING=YES")
    
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    is_valid, error_msg = validate_all_configuration()
    print_configuration_status()
    
    if not is_valid:
        print(error_msg)
        sys.exit(1)
    else:
        print("✓ All required configuration is present.")
        print()
        sys.exit(0)
