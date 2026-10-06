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


from urllib.parse import urlencode

KLINES_URL = "https://api.binance.com/api/v3/klines"

@dataclass(frozen=True)
class Candle:
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

def get_btcusdt_candles(interval: str = "1h", limit: int = 100, timeout: float = 5.0) -> list[Candle]:
    if interval not in {"15m", "1h", "4h"}: raise ValueError("Unsupported interval.")
    if not 20 <= limit <= 1000: raise ValueError("Candle limit must be between 20 and 1000.")
    url = KLINES_URL + "?" + urlencode({"symbol":"BTCUSDT","interval":interval,"limit":limit})
    request = Request(url, headers={"User-Agent":"btc-telegram-trader/1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200: raise RuntimeError(f"Market-data HTTP status: {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    candles=[]
    for row in payload:
        if len(row) < 6: raise RuntimeError("Malformed candle response.")
        candles.append(Candle(Decimal(str(row[1])),Decimal(str(row[2])),Decimal(str(row[3])),Decimal(str(row[4])),Decimal(str(row[5]))))
    if len(candles) < 20: raise RuntimeError("Insufficient candle data.")
    return candles
