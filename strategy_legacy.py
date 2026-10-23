"""Legacy SMA20/SMA50 strategy, kept as a baseline for backtest comparison."""

from dataclasses import dataclass
from decimal import Decimal
from market_data import Candle
from strategy import Analysis

def _sma(values, period):
    return sum(values[-period:]) / Decimal(period)

def analyze(candles):
    if len(candles) < 50: raise ValueError("At least 50 candles are required.")
    closes=[c.close for c in candles]
    current=closes[-1]; sma20=_sma(closes,20); sma50=_sma(closes,50)
    atr=sum((c.high-c.low) for c in candles[-20:]) / Decimal(20)
    if atr <= 0: raise ValueError("Invalid volatility data.")
    if current > sma20 > sma50:
        return Analysis("LONG",75.0,current,current-atr*Decimal("1.5"),current+atr*Decimal("3.0"),"Price > SMA20 > SMA50; trend filter aligned.")
    if current < sma20 < sma50:
        return Analysis("SHORT",75.0,current,current+atr*Decimal("1.5"),current-atr*Decimal("3.0"),"Price < SMA20 < SMA50; trend filter aligned.")
    return Analysis("NO_TRADE",0.0,current,current,current,"Trend filters are not aligned.")
