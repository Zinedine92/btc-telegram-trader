"""Binance exchange client configuration.

Credentials are loaded ONLY from environment variables.
No secrets are stored in source code.
No secrets are printed to logs or console.
Real trading is disabled by design.
"""

import os


def get_binance_credentials():
    """Load Binance API credentials from environment variables only.
    
    Returns:
        tuple: (api_key, api_secret)
        
    Raises:
        RuntimeError: If credentials are not set in environment variables.
    """
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise RuntimeError(
            "Binance API credentials are not configured. "
            "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables."
        )

    return api_key, api_secret
