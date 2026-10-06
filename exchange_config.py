"""Safe Binance environment configuration.

This module only prepares configuration. It does not place orders.
Testnet is the default and real trading cannot be enabled by omission.
"""

import os


BINANCE_TESTNET_URL = "https://testnet.binance.vision"
BINANCE_LIVE_URL = "https://api.binance.com"


def get_binance_base_url():
    """Return the configured Binance API base URL.

    TESTNET is the safe default. LIVE requires an explicit opt-in flag.
    """
    mode = os.getenv("BINANCE_MODE", "TESTNET").strip().upper()

    if mode == "TESTNET":
        return BINANCE_TESTNET_URL

    if mode == "LIVE":
        if os.getenv("ENABLE_LIVE_TRADING", "").strip().upper() != "YES":
            raise RuntimeError(
                "LIVE mode is blocked. Set ENABLE_LIVE_TRADING=YES only after "
                "explicitly enabling live trading."
            )
        return BINANCE_LIVE_URL

    raise RuntimeError("BINANCE_MODE must be TESTNET or LIVE.")
