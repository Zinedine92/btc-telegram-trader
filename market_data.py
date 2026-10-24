"""Read-only public BTC/USDT market data. No API key or paid service is required."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

@dataclass(frozen=True)
class PriceResult:
    symbol: str
    price: Decimal

def get_btcusdt_price(timeout: float = 5.0) -> PriceResult:
    request = Request(BINANCE_TICKER_URL, headers={"User-Agent": "btc-telegram-trader/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise RuntimeError(f"Market-data HTTP status: {response.status}")
            payload = json.loads(response.read().decode("utf-8"))
        _set_source("Binance")
    except (HTTPError, URLError):
        # Binance blocked/unreachable: Gate.io BTC_USDT public ticker.
        _set_source("Gate.io")
        rows = _get_json(GATE_TICKER_URL, timeout)
        if not rows or "last" not in rows[0]:
            raise RuntimeError("Invalid fallback price response.")
        payload = {"symbol": "BTCUSDT", "price": rows[0]["last"]}
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

GATE_KLINES_URL = "https://api.gateio.ws/api/v4/spot/candlesticks"
GATE_TICKER_URL = "https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT"
LAST_SOURCE = "Binance"   # which public source served the latest request
_HEADERS = {"User-Agent": "Mozilla/5.0 btc-telegram-trader/1.0"}


def _set_source(name: str) -> None:
    global LAST_SOURCE
    LAST_SOURCE = name


def _get_json(url: str, timeout: float):
    with urlopen(Request(url, headers=_HEADERS), timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Market-data HTTP status: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def _binance_candles(interval, limit, timeout):
    url = KLINES_URL + "?" + urlencode({"symbol": "BTCUSDT", "interval": interval, "limit": limit})
    candles = []
    for row in _get_json(url, timeout):
        if len(row) < 6:
            raise RuntimeError("Malformed candle response.")
        candles.append(Candle(*(Decimal(str(row[k])) for k in (1, 2, 3, 4, 5))))
    return candles


def _gate_candles(interval, limit, timeout):
    """Gate.io rows: [time, quote_vol, close, high, low, open, base_vol, closed]."""
    url = GATE_KLINES_URL + "?" + urlencode({"currency_pair": "BTC_USDT", "interval": interval, "limit": limit})
    candles = []
    for row in _get_json(url, timeout):
        if len(row) < 7:
            raise RuntimeError("Malformed candle response.")
        if len(row) > 7 and str(row[7]).lower() == "false":
            continue  # skip the still-forming candle
        candles.append(Candle(Decimal(str(row[5])), Decimal(str(row[3])), Decimal(str(row[4])),
                              Decimal(str(row[2])), Decimal(str(row[6]))))
    return candles


def get_btcusdt_candles(interval: str = "1h", limit: int = 100, timeout: float = 5.0) -> list[Candle]:
    """Binance first; if the host is blocked/unreachable (e.g. HTTP 451), use Gate.io BTC_USDT."""
    if interval not in {"15m", "1h", "4h"}: raise ValueError("Unsupported interval.")
    if not 20 <= limit <= 1000: raise ValueError("Candle limit must be between 20 and 1000.")
    try:
        candles = _binance_candles(interval, limit, timeout)
        _set_source("Binance")
    except (HTTPError, URLError):
        candles = _gate_candles(interval, limit, timeout)
        _set_source("Gate.io")
    if len(candles) < 20: raise RuntimeError("Insufficient candle data.")
    return candles
