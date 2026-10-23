"""Read-only deterministic BTC/USDT market analysis (strategy v2). No order execution.

Pipeline (per config/system_prompt.md): regime -> structure -> factor score
(0-100) -> stop/target. A setup is only actionable when the regime is a trend
in the trade direction and the score is >= MIN_SCORE. The result still has to
pass SignalValidator and RiskEngine (see risk_gate.py).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Sequence, Tuple

from indicators import (atr, efficiency_ratio, ema, rsi, swing_points,
                        volume_ratio)
from market_data import Candle

MIN_SCORE = 70.0
MIN_CANDLES = 50
TARGET_RR = 2.2          # slightly above the 2.0 hard minimum


@dataclass(frozen=True)
class Analysis:
    bias: str
    score: float
    entry: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    reason: str
    regime: str = "TRENDING"          # SignalValidator vocabulary
    structure_confirmed: bool = True
    factors: Tuple[Tuple[str, float, float], ...] = ()   # (name, points, max)


def _dec(x: float) -> Decimal:
    return Decimal(str(round(x, 2)))


def classify_regime(closes, highs, lows) -> str:
    """STRONG_BULL / WEAK_BULL / RANGE / WEAK_BEAR / STRONG_BEAR / VOLATILE / UNCLEAR."""
    if len(closes) < MIN_CANDLES:
        return "UNCLEAR"
    a_now = atr(highs, lows, closes, 14)
    base_len = min(len(closes) - 1, 100)
    a_base = atr(highs[-base_len - 1:], lows[-base_len - 1:], closes[-base_len - 1:], 14)
    price = closes[-1]
    if a_base > 0 and a_now / a_base > 2.0 or a_now / price > 0.05:
        return "VOLATILE"
    e20 = ema(closes, 20)[-1]
    e50 = ema(closes, 50)[-1]
    er = efficiency_ratio(closes, 20)
    if price > e20 > e50:
        direction = 1
    elif price < e20 < e50:
        direction = -1
    else:
        direction = 0
    if direction == 0 or er < 0.15:
        return "RANGE" if er < 0.25 else "UNCLEAR"
    if er >= 0.35:
        return "STRONG_BULL" if direction > 0 else "STRONG_BEAR"
    return "WEAK_BULL" if direction > 0 else "WEAK_BEAR"


_VALIDATOR_REGIME = {
    "STRONG_BULL": "TRENDING", "WEAK_BULL": "TRENDING",
    "STRONG_BEAR": "TRENDING", "WEAK_BEAR": "TRENDING",
    "RANGE": "RANGING", "VOLATILE": "VOLATILE", "UNCLEAR": "UNKNOWN",
}


def _structure_score(side, closes, sh, sl, e20, e50):
    """Max 20. Returns (points, confirmed)."""
    d = 1 if side == "LONG" else -1
    price = closes[-1]
    pts, confirmed = 0.0, False
    if len(sh) >= 2 and len(sl) >= 2:
        highs_ok = (sh[-1][1] > sh[-2][1]) if d > 0 else (sh[-1][1] < sh[-2][1])
        lows_ok = (sl[-1][1] > sl[-2][1]) if d > 0 else (sl[-1][1] < sl[-2][1])
        if highs_ok and lows_ok:
            pts, confirmed = 14.0, True
        elif highs_ok or lows_ok:
            pts = 7.0
        bos = price > sh[-1][1] if d > 0 else price < sl[-1][1]
        if bos and confirmed:
            pts += 6.0
        elif bos:
            pts += 3.0
    else:
        aligned = (price > e20 > e50) if d > 0 else (price < e20 < e50)
        pts = 8.0 if aligned else 0.0
    return min(pts, 20.0), confirmed


def _score_side(side, candles, closes, highs, lows, vols, a, e20s, e50s, sh, sl, htf):
    d = 1 if side == "LONG" else -1
    price = closes[-1]
    e20, e50 = e20s[-1], e50s[-1]
    factors = []

    # Stop / target (structure first, volatility-bounded)
    if d > 0:
        refs = [p for _, p in sl if p < price]
        struct_dist = (price - (refs[-1] - 0.25 * a)) if refs else 0.0
    else:
        refs = [p for _, p in sh if p > price]
        struct_dist = ((refs[-1] + 0.25 * a) - price) if refs else 0.0
    risk = min(max(struct_dist, 1.5 * a), 3.0 * a)
    stop = price - d * risk
    target = price + d * risk * TARGET_RR

    pts, confirmed = _structure_score(side, closes, sh, sl, e20, e50)
    factors.append(("structure", pts, 20.0))

    # Higher-timeframe alignment (max 15; capped at 10 when only proxied)
    if htf is not None and len(htf) >= MIN_CANDLES:
        hc = [float(c.close) for c in htf]
        h20, h50 = ema(hc, 20)[-1], ema(hc, 50)[-1]
        if (hc[-1] > h50 and h20 > h50) if d > 0 else (hc[-1] < h50 and h20 < h50):
            pts = 15.0
        elif (hc[-1] > h50) if d > 0 else (hc[-1] < h50):
            pts = 6.0
        else:
            pts = 0.0
    else:
        slope = d * (e50s[-1] - e50s[-11]) / a if len(e50s) > 11 else 0.0
        pts = 10.0 if slope >= 1.0 else 6.0 if slope > 0 else 0.0
    factors.append(("htf", pts, 15.0))

    # Support/resistance room to the nearest opposing swing
    opp = [p for _, p in sh if p > price] if d > 0 else [p for _, p in sl if p < price]
    if not opp:
        pts = 15.0
    else:
        nearest = min(opp) if d > 0 else max(opp)
        room = abs(nearest - price) / risk
        pts = 15.0 if room >= TARGET_RR else 8.0 if room >= 1.5 else 0.0
    factors.append(("support_resistance", pts, 15.0))

    # Entry trigger: not extended from EMA20, candle closes in trade direction
    dist = d * (price - e20) / a
    if dist < 0:
        pts = 0.0
    elif dist <= 1.5:
        pts = 15.0
    elif dist <= 2.5:
        pts = 8.0
    else:
        pts = 2.0
    last = candles[-1]
    if (d > 0 and last.close <= last.open) or (d < 0 and last.close >= last.open):
        pts = max(pts - 5.0, 0.0)
    factors.append(("trigger", pts, 15.0))

    # Momentum (RSI, mirrored for shorts)
    r = rsi(closes, 14)
    r = r if d > 0 else 100.0 - r
    pts = 10.0 if 50 <= r <= 68 else 6.0 if 68 < r <= 75 else 4.0 if 40 <= r < 50 else 2.0 if r > 75 else 0.0
    factors.append(("momentum", pts, 10.0))

    vr = volume_ratio(vols)
    pts = 5.0 if vr is None else 10.0 if vr >= 1.0 else 6.0 if vr >= 0.7 else 3.0
    factors.append(("volume", pts, 10.0))

    ap = a / price * 100.0
    pts = 5.0 if 0.2 <= ap <= 3.0 else 2.0 if ap <= 5.0 and ap > 3.0 else 1.0 if ap < 0.2 else 0.0
    factors.append(("volatility", pts, 5.0))

    rr = abs(target - price) / abs(price - stop)
    factors.append(("risk_reward", 10.0 if rr >= 2.0 else rr * 5.0, 10.0))

    score = sum(f[1] for f in factors)
    return score, price, stop, target, confirmed, tuple(factors)


def analyze(candles: Sequence[Candle], htf_candles: Optional[Sequence[Candle]] = None) -> Analysis:
    if len(candles) < MIN_CANDLES:
        raise ValueError("At least 50 candles are required.")
    closes = [float(c.close) for c in candles]
    highs = [float(c.high) for c in candles]
    lows = [float(c.low) for c in candles]
    vols = [float(c.volume) for c in candles]
    price = closes[-1]
    a = atr(highs, lows, closes, 14)
    if a <= 0 or price <= 0:
        raise ValueError("Invalid volatility data.")

    regime = classify_regime(closes, highs, lows)
    flat = Analysis("NO_TRADE", 0.0, _dec(price), _dec(price), _dec(price), "", _VALIDATOR_REGIME[regime], False)
    side = {"STRONG_BULL": "LONG", "WEAK_BULL": "LONG",
            "STRONG_BEAR": "SHORT", "WEAK_BEAR": "SHORT"}.get(regime)
    if side is None:
        from dataclasses import replace
        return replace(flat, reason=f"Regime {regime}: no trend to trade.")

    sh, sl = swing_points(highs, lows, 3)
    e20s, e50s = ema(closes, 20), ema(closes, 50)
    score, entry, stop, target, confirmed, factors = _score_side(
        side, candles, closes, highs, lows, vols, a, e20s, e50s, sh, sl, htf_candles)
    summary = ", ".join(f"{n} {p:.0f}/{m:.0f}" for n, p, m in factors)
    if score < MIN_SCORE:
        from dataclasses import replace
        return replace(flat, score=0.0, reason=f"{regime} but {side} score {score:.0f} < {MIN_SCORE:.0f} ({summary}).")
    return Analysis(side, round(score, 1), _dec(entry), _dec(stop), _dec(target),
                    f"{regime}; score {score:.0f}/100 ({summary}).",
                    _VALIDATOR_REGIME[regime], confirmed, factors)
