"""TITAN PROACTIVE 1.0: read-only opportunity scouting, not execution approval.

All prices must originate from complete, externally supplied historical bars.
Neither a user-supplied provenance string nor this scanner authenticates a provider.
The separate signed TITAN runner remains the sole research-consensus authority.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev
from typing import Any

TIMEFRAMES = {
    "M1": 60, "M2": 120, "M3": 180, "M4": 240, "M5": 300,
    "M6": 360, "M10": 600, "M12": 720, "M15": 900, "M20": 1200,
    "M30": 1800, "H1": 3600, "H2": 7200, "H3": 10800,
    "H4": 14400, "H6": 21600, "H8": 28800, "H12": 43200,
    "D1": 86400, "W1": 604800, "MN1": None,
}
CORE = ("D1", "H4", "H1", "M15")
MIN_BARS = 90  # accommodates historical Ichimoku leading-span displacement


def timestamp(value: Any) -> datetime:
    if isinstance(value, bool):
        raise ValueError("invalid timestamp")
    try:
        if isinstance(value, (int, float)):
            result = datetime.fromtimestamp(value, timezone.utc)
        else:
            result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("invalid timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp must include UTC offset")
    return result.astimezone(timezone.utc)


def _finite(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("invalid price")
    try:
        v = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid price") from exc
    if not math.isfinite(v) or v <= 0:
        raise ValueError("price must be finite and positive")
    return v


def validate_bars(bars: list[dict], timeframe: str, as_of: datetime) -> list[dict]:
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    if not isinstance(bars, list) or len(bars) < MIN_BARS or len(bars) > 5000:
        raise ValueError(f"{timeframe}: require between {MIN_BARS} and 5000 completed bars")
    clean = []
    prev = None
    for bar in bars:
        if not isinstance(bar, dict):
            raise ValueError("bar must be an object")
        t = timestamp(bar.get("time"))
        if prev is not None and t <= prev:
            raise ValueError(f"{timeframe}: timestamps must be strictly ascending")
        # Monthly bars require independent exchange-calendar completion validation.
        # They are never accepted as trading signals in this research scanner.
        secs = TIMEFRAMES[timeframe]
        if secs is None:
            raise ValueError("MN1 requires exchange-calendar close verification")
        if t + timedelta(seconds=secs) > as_of:
            raise ValueError(f"{timeframe}: open or future bar rejected")
        o, h, l, c = [_finite(bar.get(x)) for x in ("open", "high", "low", "close")]
        if not (l <= o <= h and l <= c <= h):
            raise ValueError(f"{timeframe}: invalid OHLC bounds")
        clean.append({"time": t, "open": o, "high": h, "low": l, "close": c})
        prev = t
    return clean


def ema(values: list[float], period: int) -> float:
    if len(values) < period:
        raise ValueError("insufficient EMA history")
    result = mean(values[:period])
    k = 2.0 / (period + 1)
    for value in values[period:]:
        result += k * (value - result)
    return result


def ema_series(values: list[float], period: int) -> list[float]:
    if len(values) < period:
        raise ValueError("insufficient EMA history")
    result = [mean(values[:period])]
    k = 2.0 / (period + 1)
    for value in values[period:]:
        result.append(result[-1] + k * (value - result[-1]))
    return result


def rsi(closes: list[float], period: int = 14) -> float:
    diffs = [b - a for a, b in zip(closes, closes[1:])]
    gains = [max(x, 0.0) for x in diffs]
    losses = [max(-x, 0.0) for x in diffs]
    ag, al = mean(gains[:period]), mean(losses[:period])
    for g, l in zip(gains[period:], losses[period:]):
        ag = (ag * (period - 1) + g) / period
        al = (al * (period - 1) + l) / period
    if al == 0:
        return 100.0 if ag else 50.0
    return 100 - 100 / (1 + ag / al)


def atr(bars: list[dict], period: int = 14) -> float:
    tr = [max(b["high"] - b["low"], abs(b["high"] - prior["close"]),
              abs(b["low"] - prior["close"])) for prior, b in zip(bars, bars[1:])]
    result = mean(tr[:period])
    for v in tr[period:]:
        result = (result * (period - 1) + v) / period
    return result


def tsi(closes: list[float]) -> float:
    # Signed and absolute close-to-close momentum, EMA(25) then EMA(13).
    diff = [b - a for a, b in zip(closes, closes[1:])]
    numerator = ema(ema_series(diff, 25), 13)
    denominator = ema(ema_series([abs(v) for v in diff], 25), 13)
    return 100 * numerator / denominator if denominator else 0.0


def cloud_regime(bars: list[dict]) -> str:
    # At observation t, the cloud plotted at t was calculated at t-26.
    def mid(window: list[dict]) -> float:
        return (max(x["high"] for x in window) + min(x["low"] for x in window)) / 2
    historic = bars[:-26]
    span_a = (mid(historic[-9:]) + mid(historic[-26:])) / 2
    span_b = mid(historic[-52:])
    close = bars[-1]["close"]
    return "ABOVE" if close > max(span_a, span_b) else ("BELOW" if close < min(span_a, span_b) else "INSIDE")


def features(bars: list[dict]) -> dict:
    c = [b["close"] for b in bars]
    last = bars[-1]
    prior = bars[-21:-1]
    recent_high, recent_low = max(b["high"] for b in prior), min(b["low"] for b in prior)
    a = atr(bars)
    std = pstdev(c[-20:])
    bb_width = 4 * std
    kc_width = 3 * a
    return {
        "last_completed_bar_utc": last["time"].isoformat(),
        "close": last["close"],
        "rsi14": round(rsi(c), 4), "tsi_25_13": round(tsi(c), 4),
        "atr14": round(a, 7), "ema21": round(ema(c, 21), 7),
        "ema55": round(ema(c, 55), 7), "ichimoku": cloud_regime(bars),
        "squeeze": bb_width < kc_width,
        "sweep_high": last["high"] > recent_high and last["close"] < recent_high,
        "sweep_low": last["low"] < recent_low and last["close"] > recent_low,
        "break_high": last["close"] > recent_high,
        "break_low": last["close"] < recent_low,
    }


def net_rr(direction: str, levels: dict | None, costs: dict | None) -> dict:
    """Research-only side-price R:R, never claims fill probability or authorization.

    Prices must already be executable-side entry/exit levels; the caller is
    responsible for verifying side, marketable quote, stop constraints and costs.
    """
    if not isinstance(levels, dict) or not isinstance(costs, dict):
        return {"state": "UNVERIFIED", "reason": "NO_SIDE_SPECIFIC_LEVELS_OR_COSTS"}
    needed = ("entry", "stop", "tp1")
    if any(x not in levels for x in needed) or any(x not in costs for x in ("round_trip_commission_price", "round_trip_slippage_price", "financing_price")):
        return {"state": "UNVERIFIED", "reason": "MISSING_LEVELS_OR_TOTAL_COSTS"}
    try:
        entry, stop, tp = (_finite(levels[x]) for x in needed)
        fees = sum(float(costs[x]) for x in ("round_trip_commission_price", "round_trip_slippage_price", "financing_price"))
        if not math.isfinite(fees) or fees < 0 or any(float(costs[x]) < 0 for x in ("round_trip_commission_price", "round_trip_slippage_price", "financing_price")):
            raise ValueError("invalid costs")
    except (ValueError, TypeError):
        return {"state": "UNVERIFIED", "reason": "INVALID_LEVELS_OR_COSTS"}
    valid = (stop < entry < tp) if direction == "LONG" else (tp < entry < stop)
    if not valid:
        return {"state": "UNVERIFIED", "reason": "INCORRECT_STOP_TARGET_ORDER"}
    risk = abs(entry - stop) + fees
    reward = abs(tp - entry) - fees
    ratio = round(max(reward, 0) / risk, 4)
    return {"state": "CALCULATED_FROM_UNVERIFIED_INPUT", "net_rr_tp1": ratio,
            "passes_numerical_rr_only": ratio >= 2.5,
            "warning": "Not executable: source, bid/ask, stops, margin, live costs and signed TITAN gates unverified"}


def scan(snapshot: dict) -> dict:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    instrument = snapshot.get("instrument")
    if not isinstance(instrument, dict) or not all(isinstance(instrument.get(k), str) and instrument[k].strip() for k in ("name", "symbol", "asset_class", "market")):
        raise ValueError("instrument name, symbol, asset class and market required")
    as_of = timestamp(snapshot.get("as_of"))
    frames = snapshot.get("frames")
    if not isinstance(frames, dict) or not frames:
        raise ValueError("frames required")
    if any(tf not in TIMEFRAMES for tf in frames):
        raise ValueError("unknown timeframe")
    frame_features, gaps = {}, []
    for tf, raw in frames.items():
        frame_features[tf] = features(validate_bars(raw, tf, as_of))
    for tf in CORE:
        if tf not in frame_features:
            gaps.append(f"MISSING_{tf}")
    c = frame_features.get("H4") or frame_features.get("D1") or next(iter(frame_features.values()))
    candidates = []
    for direction in ("LONG", "SHORT"):
        desired = "ABOVE" if direction == "LONG" else "BELOW"
        aligned = sum(frame_features[tf]["ichimoku"] == desired for tf in CORE if tf in frame_features)
        full_cloud = not gaps and aligned == len(CORE)
        trend = (c["ema21"] > c["ema55"]) if direction == "LONG" else (c["ema21"] < c["ema55"])
        momentum = (c["tsi_25_13"] > 0) if direction == "LONG" else (c["tsi_25_13"] < 0)
        extreme = c["rsi14"] < 35 if direction == "LONG" else c["rsi14"] > 65
        sweep = c["sweep_low"] if direction == "LONG" else c["sweep_high"]
        breakout = c["break_high"] if direction == "LONG" else c["break_low"]
        # Transparent research ranking, NOT a calibrated probability.
        score = 10 * aligned + 15 * trend + 10 * momentum + 10 * extreme + 15 * sweep + 10 * breakout
        armed = bool(score >= 50 and (sweep or breakout) and not gaps)
        if aligned == 0 and not (extreme or sweep):
            state = "INVALID"
        else:
            state = "ARMED" if armed else "EARLY WATCH"
        levels = snapshot.get("levels", {})
        rr = net_rr(direction, levels.get(direction.lower()) if isinstance(levels, dict) else None, snapshot.get("costs"))
        candidates.append({"direction": direction, "status": state,
                           "score_heuristic_0_100": score,
                           "baseline_ichimoku_D1_H4_H1_M15": "ALIGNED" if full_cloud else "NOT_ALIGNED_OR_INCOMPLETE",
                           "evidence": {"aligned_cloud_frames": aligned, "ema_trend": trend,
                                        "tsi_direction": momentum, "rsi_extreme": extreme,
                                        "sweep": sweep, "breakout": breakout},
                           "tp1_net_rr_research": rr,
                           "execution_eligible": False})
    candidates.sort(key=lambda c: (-c["score_heuristic_0_100"], c["direction"]))
    return {"instrument": instrument, "as_of": as_of.isoformat(),
            "source_claim": str(snapshot.get("source", "UNSPECIFIED"))[:150],
            "source_authenticated": False,
            "frame_features": frame_features, "missing_core_frames": gaps,
            "candidates": candidates, "top_watch": candidates[0]["direction"] if candidates[0]["status"] != "INVALID" else None,
            "status": "RESEARCH_WATCHLIST_ONLY", "signed_agents_verified": 0,
            "six_phases_completed": False, "orders_sent": 0,
            "trade_authorized": False,
            "required_next_step": "Independent signed TITAN research, broker executable prices, events, account/position risk and full six-phase gates"}
