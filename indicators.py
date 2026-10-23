"""Pure-Python technical indicators (float math). Read-only analysis helpers."""

from typing import List, Optional, Sequence, Tuple


def ema(values: Sequence[float], period: int) -> List[float]:
    """Exponential moving average series, same length as input (seeded with SMA)."""
    if period < 1:
        raise ValueError("period must be >= 1")
    n = len(values)
    if n < period:
        raise ValueError("not enough values for EMA")
    k = 2.0 / (period + 1)
    out = [0.0] * n
    seed = sum(values[:period]) / period
    for i in range(period):
        out[i] = seed
    for i in range(period, n):
        out[i] = values[i] * k + out[i - 1] * (1 - k)
    return out


def rsi(closes: Sequence[float], period: int = 14) -> float:
    """Wilder RSI of the last close (0-100)."""
    if len(closes) < period + 1:
        raise ValueError("not enough values for RSI")
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0.0)
        losses += max(-d, 0.0)
    avg_g, avg_l = gains / period, losses / period
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        avg_g = (avg_g * (period - 1) + max(d, 0.0)) / period
        avg_l = (avg_l * (period - 1) + max(-d, 0.0)) / period
    if avg_l == 0:
        return 100.0 if avg_g > 0 else 50.0
    rs = avg_g / avg_l
    return 100.0 - 100.0 / (1.0 + rs)


def true_ranges(highs, lows, closes) -> List[float]:
    out = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        out.append(max(highs[i] - lows[i],
                       abs(highs[i] - closes[i - 1]),
                       abs(lows[i] - closes[i - 1])))
    return out


def atr(highs, lows, closes, period: int = 14) -> float:
    """Wilder ATR of the last bar."""
    if len(closes) < period + 1:
        raise ValueError("not enough values for ATR")
    tr = true_ranges(highs, lows, closes)
    value = sum(tr[1:period + 1]) / period
    for i in range(period + 1, len(tr)):
        value = (value * (period - 1) + tr[i]) / period
    return value


def efficiency_ratio(closes: Sequence[float], period: int = 20) -> float:
    """Kaufman efficiency ratio: 1 = straight trend, 0 = pure chop."""
    if len(closes) < period + 1:
        raise ValueError("not enough values for efficiency ratio")
    window = closes[-(period + 1):]
    net = abs(window[-1] - window[0])
    path = sum(abs(window[i] - window[i - 1]) for i in range(1, len(window)))
    return 0.0 if path == 0 else net / path


def swing_points(highs, lows, k: int = 3) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    """Confirmed fractal swings: a bar whose high/low beats k bars on each side.

    The last k bars can never be swings (not yet confirmed), so there is no
    look-ahead when this runs on a window ending at the decision bar.
    """
    sh: List[Tuple[int, float]] = []
    sl: List[Tuple[int, float]] = []
    for i in range(k, len(highs) - k):
        if all(highs[i] > highs[i - j] and highs[i] > highs[i + j] for j in range(1, k + 1)):
            sh.append((i, highs[i]))
        if all(lows[i] < lows[i - j] and lows[i] < lows[i + j] for j in range(1, k + 1)):
            sl.append((i, lows[i]))
    return sh, sl


def volume_ratio(volumes: Sequence[float], recent: int = 5, base: int = 20) -> Optional[float]:
    if len(volumes) < base:
        return None
    b = sum(volumes[-base:]) / base
    if b <= 0:
        return None
    return (sum(volumes[-recent:]) / recent) / b
