"""Safe Binance balance helpers.

Parses authenticated account info and exposes read-only BTC/USDT balances.
No order, transfer, or withdrawal operation is implemented here.
"""

import json

from binance_readonly_client import get_account_info


def parse_balances(account_info):
    """Return non-zero asset balances as {asset: {free, locked}}."""
    if isinstance(account_info, str):
        account_info = json.loads(account_info)

    balances = account_info.get("balances", [])
    result = {}
    for item in balances:
        asset = item.get("asset")
        if not asset:
            continue
        free = float(item.get("free", 0))
        locked = float(item.get("locked", 0))
        if free != 0 or locked != 0:
            result[asset] = {"free": free, "locked": locked}
    return result


def get_btc_usdt_balances():
    """Fetch and return only BTC and USDT balances."""
    balances = parse_balances(get_account_info())
    return {
        asset: balances[asset]
        for asset in ("BTC", "USDT")
        if asset in balances
    }
