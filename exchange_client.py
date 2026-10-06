"""Safe exchange credential loader.

Credentials are read only from environment variables.
This module does not connect to an exchange and cannot place orders.
"""

import os


def get_binance_credentials():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret or not api_key.strip() or not api_secret.strip():
        raise RuntimeError("Binance API credentials are not configured.")

    return api_key, api_secret
