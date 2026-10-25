"""Read-only Binance Spot dashboard data + Telegram text formatting.

Only GET calls through binance_readonly_client (allowlisted endpoints) and the
public price ticker. Nothing here can create, change or cancel orders.
"""
import json
from urllib.request import Request, urlopen

from binance_balance import parse_balances
from binance_readonly_client import get_account_info, get_open_orders
from exchange_config import get_binance_base_url

STABLES = {"USDT", "USDC", "FDUSD", "BUSD", "TUSD"}


def get_prices(opener=urlopen):
    """Public prices for all symbols: {'BTCUSDT': 80000.0, ...}."""
    request = Request(get_binance_base_url() + "/api/v3/ticker/price",
                      headers={"User-Agent": "btc-telegram-trader/1.0"})
    with opener(request, timeout=10) as response:
        rows = json.loads(response.read().decode("utf-8"))
    return {r["symbol"]: float(r["price"]) for r in rows}


def value_assets(balances, prices):
    """Return (rows, total_usdt). rows: (asset, free, locked, value_usdt or None)."""
    btc_usdt = prices.get("BTCUSDT")
    rows, total = [], 0.0
    for asset, b in balances.items():
        amount = b["free"] + b["locked"]
        if asset in STABLES:
            price = 1.0
        elif f"{asset}USDT" in prices:
            price = prices[f"{asset}USDT"]
        elif f"{asset}BTC" in prices and btc_usdt:
            price = prices[f"{asset}BTC"] * btc_usdt
        else:
            price = None
        value = amount * price if price is not None else None
        if value is not None:
            total += value
        rows.append((asset, b["free"], b["locked"], value))
    rows.sort(key=lambda r: -(r[3] or 0.0))
    return rows, total


def fetch_portfolio():
    balances = parse_balances(get_account_info())
    return value_assets(balances, get_prices())


def fetch_open_orders():
    return json.loads(get_open_orders())


def _num(x, digits=8):
    return f"{x:.{digits}f}".rstrip("0").rstrip(".") or "0"


def format_portfolio(rows, total, limit=10):
    if not rows:
        return "💰 PORTFOLIO (Spot)\n\nNo assets with a balance."
    lines = ["💰 PORTFOLIO (Spot)", "", f"Total ≈ {total:,.2f} USDT", ""]
    for asset, free, locked, value in rows[:limit]:
        val = f"≈ {value:,.2f} USDT" if value is not None else "price n/a"
        lock = f" (locked {_num(locked)})" if locked else ""
        lines.append(f"{asset}: {_num(free + locked)}{lock} {val}")
    if len(rows) > limit:
        lines.append(f"... and {len(rows) - limit} more")
    lines += ["", "🔒 READ-ONLY. Spot only; Futures positions are not shown."]
    return "\n".join(lines)


def format_open_orders(orders, limit=10):
    if not orders:
        return "📋 OPEN ORDERS (Spot)\n\nNo open orders.\n\n🔒 READ-ONLY."
    lines = ["📋 OPEN ORDERS (Spot)", ""]
    for o in orders[:limit]:
        lines.append(f"{o.get('symbol')} {o.get('side')} {o.get('type')} "
                     f"price {o.get('price')} qty {o.get('origQty')} filled {o.get('executedQty')}")
    if len(orders) > limit:
        lines.append(f"... and {len(orders) - limit} more")
    lines += ["", "🔒 READ-ONLY. Orders cannot be changed from this bot."]
    return "\n".join(lines)
