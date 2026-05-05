from __future__ import annotations

import math
from statistics import pstdev


def _moving_average(values: list[float], window: int) -> float:
    if not values:
        return 0.0
    if len(values) < window:
        return round(sum(values) / len(values), 2)
    return round(sum(values[-window:]) / window, 2)


def _rsi(values: list[float], period: int = 14) -> float:
    if len(values) <= period:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for idx in range(len(values) - period, len(values)):
        change = values[idx] - values[idx - 1]
        if change >= 0:
            gains.append(change)
        else:
            losses.append(abs(change))
    avg_gain = sum(gains) / period if gains else 0.0
    avg_loss = sum(losses) / period if losses else 0.0
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _pct(a: float, b: float) -> float:
    if not b:
        return 0.0
    return round(((a - b) / b) * 100, 2)


def analyze_price_action(candles: list[dict]) -> dict:
    closes = [float(c["close"]) for c in candles if c.get("close") is not None]
    volumes = [float(c.get("volume", 0)) for c in candles]

    if len(closes) < 30:
        fallback = closes[-1] if closes else 0.0
        return {
            "signal": "HOLD",
            "bias_score": 50,
            "rsi": 50.0,
            "ma20": fallback,
            "ma50": fallback,
            "momentum_20d": 0.0,
            "volatility_20d": 0.0,
            "support": fallback,
            "resistance": fallback,
            "summary": "Not enough candle history for a stronger model view yet.",
        }

    current = closes[-1]
    ma20 = _moving_average(closes, 20)
    ma50 = _moving_average(closes, 50)
    rsi = _rsi(closes, 14)
    momentum_20d = _pct(current, closes[-20])

    returns = []
    for idx in range(1, min(len(closes), 21)):
        previous = closes[-idx - 1]
        if previous:
            returns.append((closes[-idx] - previous) / previous)
    volatility_20d = round(pstdev(returns) * math.sqrt(252) * 100, 2) if len(returns) > 1 else 0.0

    recent_window = closes[-20:]
    support = round(min(recent_window), 2)
    resistance = round(max(recent_window), 2)
    avg_volume = sum(volumes[-20:]) / max(1, min(len(volumes), 20))
    volume_boost = 6 if volumes and volumes[-1] > avg_volume * 1.2 else 0

    score = 50
    score += 15 if current > ma20 else -12
    score += 12 if ma20 > ma50 else -10
    score += 10 if momentum_20d > 2 else (-10 if momentum_20d < -2 else 0)
    score += 8 if 42 <= rsi <= 62 else (-10 if rsi > 72 else 10 if rsi < 32 else 0)
    score += volume_boost
    score = max(0, min(100, score))

    if score >= 67:
        signal = "BUY"
    elif score <= 38:
        signal = "SELL"
    else:
        signal = "HOLD"

    trend_note = "above both moving averages" if current > ma20 and ma20 > ma50 else "below trend support" if current < ma20 < ma50 else "inside a mixed trend"
    rsi_note = "RSI is stretched" if rsi > 70 or rsi < 30 else "RSI is balanced"
    volume_note = "with strong participation" if volume_boost else "with normal participation"

    return {
        "signal": signal,
        "bias_score": int(round(score)),
        "rsi": rsi,
        "ma20": ma20,
        "ma50": ma50,
        "momentum_20d": momentum_20d,
        "volatility_20d": volatility_20d,
        "support": support,
        "resistance": resistance,
        "summary": f"Price is {trend_note}; {rsi_note} {volume_note}.",
    }
