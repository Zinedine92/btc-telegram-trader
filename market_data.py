"""Read-only public BTC/USDT market data. No API key or paid service is required."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.request import Request, urlopen
import json

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

@dataclass(frozen=True)
class PriceResult:
    symbol: str
    price: Decimal

def get_btcusdt_price(timeout: float = 5.0) -> PriceResult:
    request = Request(BINANCE_TICKER_URL, headers={"User-Agent": "btc-telegram-trader/1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Market-data HTTP status: {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("symbol") != "BTCUSDT":
        raise RuntimeError("Unexpected market-data symbol.")
    try:
        price = Decimal(str(payload["price"]))
    except (KeyError, InvalidOperation) as exc:
        raise RuntimeError("Invalid BTCUSDT price response.") from exc
    if price <= 0:
        raise RuntimeError("BTCUSDT price must be positive.")
    return PriceResult(symbol="BTCUSDT", price=price)
