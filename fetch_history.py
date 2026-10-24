#!/usr/bin/env python3
"""Download historical BTCUSDT candles to a CSV for backtest.py (public data, no keys).

Usage: python fetch_history.py [days=180] [out=klines.csv] [interval=1h] [symbol=BTCUSDT]
Symbols: BTCUSDT, ETHUSDT, SOLUSDT (spot).
Tries Binance first; if blocked (HTTP 451) uses Gate.io BTC_USDT.
CSV columns: open_time_ms, open, high, low, close, volume (Binance kline order).
"""
import csv
import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STEP = {"15m": 900, "1h": 3600, "4h": 14400}
SYMBOLS = {"BTCUSDT": "BTC_USDT", "ETHUSDT": "ETH_USDT", "SOLUSDT": "SOL_USDT"}
HEADERS = {"User-Agent": "Mozilla/5.0 btc-telegram-trader/1.0"}


def _get(url):
    with urlopen(Request(url, headers=HEADERS), timeout=15) as r:
        return json.loads(r.read().decode())


def binance_page(interval, start_ms, end_ms, symbol="BTCUSDT"):
    q = urlencode({"symbol": symbol, "interval": interval, "startTime": start_ms,
                   "endTime": end_ms, "limit": 1000})
    return [(int(r[0]), r[1], r[2], r[3], r[4], r[5])
            for r in _get("https://api.binance.com/api/v3/klines?" + q)]


def gate_page(interval, start_ms, end_ms, symbol="BTCUSDT"):
    q = urlencode({"currency_pair": SYMBOLS[symbol], "interval": interval,
                   "from": start_ms // 1000, "to": end_ms // 1000})
    out = []
    for r in _get("https://api.gateio.ws/api/v4/spot/candlesticks?" + q):
        if len(r) > 7 and str(r[7]).lower() == "false":
            continue
        out.append((int(r[0]) * 1000, r[5], r[3], r[4], r[2], r[6]))
    return out


def fetch(days, interval, symbol="BTCUSDT"):
    step_ms = STEP[interval] * 1000
    end = int(time.time() * 1000)
    start = end - days * 86400 * 1000
    rows, page = {}, binance_page
    cur = start
    while cur < end:
        nxt = min(cur + 999 * step_ms, end)
        try:
            got = page(interval, cur, nxt, symbol)
        except (HTTPError, URLError):
            if page is gate_page:
                raise
            print("Binance unavailable, using Gate.io...", flush=True)
            page = gate_page
            # Gate.io only serves the most recent ~10000 candles.
            limit_start = end - 9990 * step_ms
            if cur < limit_start:
                print("Gate.io history limit: starting from the oldest available candle.", flush=True)
                cur = limit_start
            continue
        for r in got:
            rows[r[0]] = r
        cur = nxt + step_ms
        time.sleep(0.3)
    return [rows[k] for k in sorted(rows)], ("Gate.io" if page is gate_page else "Binance")


def main(argv):
    days = int(argv[0]) if argv else 180
    out = argv[1] if len(argv) > 1 else "klines.csv"
    interval = argv[2] if len(argv) > 2 else "1h"
    symbol = argv[3].upper() if len(argv) > 3 else "BTCUSDT"
    if interval not in STEP or not 1 <= days <= 1500 or symbol not in SYMBOLS:
        print("Usage: python fetch_history.py [days 1-1500] [out.csv] [15m|1h|4h] [BTCUSDT|ETHUSDT|SOLUSDT]")
        return 1
    rows, source = fetch(days, interval, symbol)
    with open(out, "w", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print(f"Saved {len(rows)} {symbol} {interval} candles from {source} to {out}")
    return 0 if len(rows) >= 200 else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
