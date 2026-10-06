"""Binance client configuration.
Credentials are loaded only from environment variables.
No secrets are stored in source code.
"""

import os


def get_binance_credentials():
    api_key = os.getenv(fTSbZQrmyQjXpBc9Afh7PAxZ9YXIe0PX2wkQGrzOLIh26IM4vYcw1ywjOaLjNrpR)
    api_secret = os.getenv(ixKhcalYIfkhm1DAfrBlsBJy1rjwp1oxQu08eAihjzwh0FYOw82Qgm4BBrVLTq4w)

    if not api_key or not api_secret:
        raise RuntimeError("Binance API credentials are not configured.")

    return api_key, api_secret
