"""Walk-forward backtester for the strategy (offline, read-only, no exchange access).

At each bar the strategy only sees candles up to and including that bar. A
signal is entered at the NEXT bar's open (+slippage); stop/target are checked
from that bar onward. If a bar touches both stop and target the stop is assumed
to hit first (conservative). Results are expressed in R multiples net of costs.

Usage:  python backtest.py klines.csv [--compare]
CSV: Binance kline layout (open_time, open, high, low, close, volume, ...) with
or without a header row.
"""

import csv
import random
import sys
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, List, Optional, Sequence

from market_data import Candle
from risk_gate import evaluate_analysis

FEE_PCT = 0.04        # per side (taker)
SLIPPAGE_PCT = 0.02   # per side
MAX_HOLD_BARS = 48
WINDOW = 300


@dataclass(frozen=True)
class Trade:
    side: str
    entry_index: int
    exit_index: int
    r_multiple: float
    exit_reason: str


@dataclass(frozen=True)
class Stats:
    trades: int
    win_rate: float
    avg_r: float
    profit_factor: float
    total_r: float
    max_drawdown_r: float
    longs: int
    shorts: int


def load_csv(path: str) -> List[Candle]:
    candles = []
    with open(path, newline="") as fh:
        for row in csv.reader(fh):
            try:
                o, h, l, c, v = (Decimal(x) for x in row[1:6])
            except Exception:
                continue  # header or malformed row
            candles.append(Candle(o, h, l, c, v))
    return candles


def synthetic_candles(n: int = 2000, seed: int = 7, start: float = 30000.0, trending: bool = True) -> List[Candle]:
    """Deterministic regime-switching random walk, for tests and demos only."""
    rng = random.Random(seed)
    price, out, drift, left = start, [], 0.0, 0
    for _ in range(n):
        if left <= 0:
            drift = rng.choice([-0.0012, -0.0004, 0.0, 0.0004, 0.0012]) if trending else 0.0
            left = rng.randint(40, 200)
        left -= 1
        o = price
        c = o * (1 + drift + rng.gauss(0, 0.004))
        hi = max(o, c) * (1 + abs(rng.gauss(0, 0.0015)))
        lo = min(o, c) * (1 - abs(rng.gauss(0, 0.0015)))
        out.append(Candle(*(Decimal(str(round(x, 2))) for x in (o, hi, lo, c)),
                          Decimal(str(round(rng.uniform(50, 150), 2)))))
        price = c
    return out


def _r_net(side: str, entry: float, stop: float, exit_price: float) -> float:
    risk = abs(entry - stop)
    gross = (exit_price - entry) if side == "LONG" else (entry - exit_price)
    cost = entry * 2 * (FEE_PCT + SLIPPAGE_PCT) / 100.0   # round trip, fee + slippage
    return (gross - cost) / risk


def run_backtest(candles: Sequence[Candle], analyze: Callable, equity: float = 10000.0,
                 use_risk_gate: bool = True, warmup: int = 100) -> List[Trade]:
    trades: List[Trade] = []
    i = warmup
    n = len(candles)
    while i < n - 1:
        window = candles[max(0, i + 1 - WINDOW): i + 1]
        try:
            a = analyze(window)
        except ValueError:
            i += 1
            continue
        if a.bias == "NO_TRADE":
            i += 1
            continue
        if use_risk_gate and not evaluate_analysis(a, equity, 20)[0]:
            i += 1
            continue
        side = a.bias
        stop, target = float(a.stop_loss), float(a.take_profit)
        slip = SLIPPAGE_PCT / 100.0
        entry = float(candles[i + 1].open) * (1 + slip if side == "LONG" else 1 - slip)
        # Entry gap beyond the stop invalidates the setup.
        if (side == "LONG" and entry <= stop) or (side == "SHORT" and entry >= stop):
            i += 1
            continue
        exit_idx, exit_price, reason = None, None, "timeout"
        for j in range(i + 1, min(n, i + 1 + MAX_HOLD_BARS)):
            hi, lo = float(candles[j].high), float(candles[j].low)
            hit_stop = lo <= stop if side == "LONG" else hi >= stop
            hit_tp = hi >= target if side == "LONG" else lo <= target
            if hit_stop:
                exit_idx, exit_price, reason = j, stop, "stop"
                break
            if hit_tp:
                exit_idx, exit_price, reason = j, target, "target"
                break
        if exit_idx is None:
            exit_idx = min(n, i + 1 + MAX_HOLD_BARS) - 1
            exit_price = float(candles[exit_idx].close)
        trades.append(Trade(side, i + 1, exit_idx, _r_net(side, entry, stop, exit_price), reason))
        i = exit_idx + 1   # one position at a time
    return trades


def summarize(trades: Sequence[Trade]) -> Stats:
    if not trades:
        return Stats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)
    rs = [t.r_multiple for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [-r for r in rs if r <= 0]
    peak = equity = dd = 0.0
    for r in rs:
        equity += r
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    pf = (sum(wins) / sum(losses)) if losses and sum(losses) > 0 else float("inf")
    return Stats(len(rs), len(wins) / len(rs), sum(rs) / len(rs), pf, sum(rs), dd,
                 sum(t.side == "LONG" for t in trades), sum(t.side == "SHORT" for t in trades))


def format_stats(name: str, s: Stats) -> str:
    return (f"{name}: trades={s.trades} (L{s.longs}/S{s.shorts}) win={s.win_rate*100:.1f}% "
            f"avgR={s.avg_r:+.3f} PF={s.profit_factor:.2f} totalR={s.total_r:+.1f} maxDD={s.max_drawdown_r:.1f}R")


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    paths = [a for a in argv if not a.startswith("--")]
    if paths:
        candles = load_csv(paths[0])
        print(f"Loaded {len(candles)} candles from {paths[0]}")
    else:
        candles = synthetic_candles()
        print("No CSV given: using SYNTHETIC data (results are meaningless for real markets).")
    if len(candles) < 200:
        print("Need at least 200 candles.")
        return 1
    import strategy, strategy_legacy
    print(format_stats("v2    ", summarize(run_backtest(candles, strategy.analyze))))
    if "--compare" in argv:
        print(format_stats("legacy", summarize(run_backtest(candles, strategy_legacy.analyze))))
    print("Costs: fee 0.04%/side + slippage 0.02%/side. Past results do not predict future returns.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
