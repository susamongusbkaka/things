#!/usr/bin/env python3
"""TITAN SDRC-MTF 1.1 — fail-closed, research-only zone scanner and chart.

Inputs are authentic *user-supplied* candle rows, not independently authenticated
market data. All results remain research candidates and are never order signals.
No broker orders, automatic live feeds, agent receipt simulation or approvals.

Examples:
  python titan_gbt_agent_v1_1.py --demo --output demo.png
  python titan_gbt_agent_v1_1.py --csv EURUSD_H4.csv --symbol EURUSD --timeframe H4 --htf-csv EURUSD_D1.csv --tick-size 0.00001 --pip-size 0.0001 --spread-pips 1.2 --slippage-pips 0.4 --commission-pips 0.6

CSV columns: close_time_utc,open,high,low,close,is_complete,source
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

FROZEN_MIN_NET_RR = 2.5

@dataclass(frozen=True)
class Config:
    atr_period: int = 14
    base_min_len: int = 1
    base_max_len: int = 4
    base_max_range_atr: float = 1.5
    departure_min_body_atr: float = 1.8
    departure_max_len: int = 4
    zone_max_age_bars: int = 500
    stop_buffer_atr: float = 0.25
    max_entry_distance_atr: float = 3.0  # candidate discovery only, not an execution trigger
    min_net_rr: float = FROZEN_MIN_NET_RR
    chart_candles: int = 120
    chart_dpi: int = 150
    w_trend: float = 25.0
    w_freshness: float = 20.0
    w_departure: float = 20.0
    w_rr: float = 20.0
    w_confluence: float = 15.0

@dataclass(frozen=True)
class Candle:
    close_time_utc: datetime
    open: float
    high: float
    low: float
    close: float
    is_complete: bool
    source: str

@dataclass
class Zone:
    kind: str
    lower: float
    upper: float
    origin_idx: int
    confirmed_idx: int
    departure_strength: float
    base_width_atr: float
    touches: int = 0
    invalidated: bool = False

    @property
    def proximal(self) -> float:
        return self.upper if self.kind == "demand" else self.lower

    @property
    def distal(self) -> float:
        return self.lower if self.kind == "demand" else self.upper

@dataclass
class Candidate:
    direction: str
    zone: Zone
    entry_mid: float
    stop_mid: float
    tp1_mid: float
    tp2_mid: Optional[float]
    gross_rr_tp1: float
    gross_rr_tp2: Optional[float]
    net_rr_tp1_est: Optional[float]
    net_rr_tp2_est: Optional[float]
    score: Optional[float]
    score_breakdown: dict
    opposing1: Zone
    opposing2: Optional[Zone]


def parse_utc(value: str) -> datetime:
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None or d.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be UTC with Z or +00:00")
    return d.astimezone(timezone.utc)


def load_csv(path: str) -> list[Candle]:
    required = {"close_time_utc", "open", "high", "low", "close", "is_complete", "source"}
    result = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"CSV missing columns: {sorted(required - set(reader.fieldnames or []))}")
        for row_no, row in enumerate(reader, 2):
            flag = (row["is_complete"] or "").strip().lower()
            if flag not in ("true", "false"):
                raise ValueError(f"CSV line {row_no}: is_complete must be true or false")
            result.append(Candle(parse_utc(row["close_time_utc"]),
                                 *[float(row[k]) for k in ("open", "high", "low", "close")],
                                 flag == "true", row["source"].strip()))
    return result


def validate_candles(candles: list[Candle], min_count: int = 25) -> list[str]:
    errors = []
    if len(candles) < min_count:
        errors.append(f"Need at least {min_count} completed candles, received {len(candles)}")
    previous = None
    for i, c in enumerate(candles):
        values = (c.open, c.high, c.low, c.close)
        if not c.is_complete:
            errors.append(f"Candle {i} is incomplete")
        if not all(math.isfinite(v) and v > 0 for v in values):
            errors.append(f"Candle {i} contains non-finite/non-positive prices")
        elif c.high < max(c.open, c.close) or c.low > min(c.open, c.close) or c.low > c.high:
            errors.append(f"Candle {i} has invalid OHLC bounds")
        if not c.source:
            errors.append(f"Candle {i} is missing source attribution")
        if previous is not None and c.close_time_utc <= previous:
            errors.append(f"Candle {i} has non-increasing close timestamp")
        previous = c.close_time_utc
    return errors[:20]


def atr_wilder(candles: list[Candle], period: int) -> np.ndarray:
    result = np.full(len(candles), np.nan)
    if len(candles) < period:
        return result
    tr = []
    for i, c in enumerate(candles):
        tr.append(max(c.high - c.low,
                      abs(c.high - candles[i - 1].close) if i else 0.0,
                      abs(c.low - candles[i - 1].close) if i else 0.0))
    result[period - 1] = float(np.mean(tr[:period]))
    for i in range(period, len(tr)):
        result[i] = (result[i - 1] * (period - 1) + tr[i]) / period
    return result


def htf_trend(htf: list[Candle]) -> Optional[str]:
    """Explicit separate higher timeframe; EMA20 slope is provisional context only."""
    if len(htf) < 35:
        return None
    values = np.array([c.close for c in htf], dtype=float)
    ema = np.full(len(values), np.nan)
    ema[19] = float(np.mean(values[:20]))
    for i in range(20, len(values)):
        ema[i] = values[i] * (2 / 21) + ema[i - 1] * (19 / 21)
    slope = (ema[-1] - ema[-11]) / ema[-11]
    if slope > 0.001:
        return "bullish"
    if slope < -0.001:
        return "bearish"
    return "neutral"


def scan_zones(candles: list[Candle], atr: np.ndarray, cfg: Config) -> list[Zone]:
    zones = []
    n = len(candles)
    # A zone is known only at confirmed_idx, never at its original base.
    for origin in range(max(0, n - cfg.zone_max_age_bars), n - 1):
        for blen in range(cfg.base_min_len, cfg.base_max_len + 1):
            base_end = origin + blen - 1
            if base_end + 1 >= n or not math.isfinite(atr[base_end]) or atr[base_end] <= 0:
                continue
            base = candles[origin:base_end + 1]
            lower, upper = min(c.low for c in base), max(c.high for c in base)
            width_atr = (upper - lower) / atr[base_end]
            if width_atr > cfg.base_max_range_atr:
                continue
            best = None
            for di in range(base_end + 1, min(n, base_end + 1 + cfg.departure_max_len)):
                c = candles[di]
                if not math.isfinite(atr[di]) or atr[di] <= 0:
                    continue
                strength = abs(c.close - c.open) / atr[di]
                if strength < cfg.departure_min_body_atr:
                    continue
                kind = ("demand" if c.close > upper and c.close > c.open else
                        "supply" if c.close < lower and c.close < c.open else None)
                if kind and (best is None or strength > best[2]):
                    best = (kind, di, strength)
            if best is None:
                continue
            kind, confirmed, strength = best
            z = Zone(kind, lower, upper, origin, confirmed, strength, width_atr)
            was_inside = False
            for k in range(confirmed + 1, n):
                bar = candles[k]
                if (kind == "demand" and bar.close < lower) or (kind == "supply" and bar.close > upper):
                    z.invalidated = True
                    break
                inside = bar.low <= upper and bar.high >= lower
                if inside and not was_inside:
                    z.touches += 1
                was_inside = inside
            if not z.invalidated:
                zones.append(z)
            break  # avoid multiple overlapping base-length hypotheses for same origin
    # Resolve nearly identical overlapping bases while keeping the earliest valid origin.
    unique = []
    for z in zones:
        def equivalent(p):
            if z.kind != p.kind or abs(z.confirmed_idx-p.confirmed_idx) > 4:
                return False
            overlap = max(0.0, min(z.upper,p.upper)-max(z.lower,p.lower))
            shorter = min(z.upper-z.lower,p.upper-p.lower)
            return shorter > 0 and overlap / shorter >= .65
        if any(equivalent(p) for p in unique):
            continue
        unique.append(z)
    return unique


def quantize(value: float, tick: float, mode: str) -> float:
    units = value / tick
    units = math.floor(units + 1e-9) if mode == "down" else math.ceil(units - 1e-9)
    return round(units * tick, max(0, -int(math.floor(math.log10(tick)))) + 2)


def cost_adjusted_rr(direction: str, entry: float, stop: float, target: float,
                     spread_px: float, slippage_px: float, commission_px: float) -> float:
    """Cost-adjusted estimate; not a verified broker execution or audited net R."""
    half = spread_px / 2
    if direction == "LONG":
        entry_exec = entry + half
        stop_exec = stop - half - slippage_px
        target_exec = target - half - slippage_px
        reward = target_exec - entry_exec - commission_px
        risk = entry_exec - stop_exec + commission_px
    else:
        entry_exec = entry - half
        stop_exec = stop + half + slippage_px
        target_exec = target + half + slippage_px
        reward = entry_exec - target_exec - commission_px
        risk = stop_exec - entry_exec + commission_px
    return reward / risk if risk > 0 else float("-inf")


def define_candidates(candles: list[Candle], zones: list[Zone], atr: np.ndarray,
                      cfg: Config, tick: float, costs: Optional[tuple[float, float, float]],
                      trend: Optional[str]) -> list[Candidate]:
    result = []
    close = candles[-1].close
    for z in zones:
        entry = quantize(z.proximal, tick, "up" if z.kind == "demand" else "down")
        # Only a future retest from the correct side: no blind in-zone order.
        distance = close - z.upper if z.kind == "demand" else z.lower - close
        if distance < 0 or distance > cfg.max_entry_distance_atr * atr[-1]:
            continue
        stop = quantize(z.distal + (-1 if z.kind == "demand" else 1) *
                        cfg.stop_buffer_atr * atr[-1], tick,
                        "down" if z.kind == "demand" else "up")
        opp = [x for x in zones if x.kind != z.kind and x.confirmed_idx < len(candles)]
        if z.kind == "demand":
            opp = sorted((x for x in opp if x.lower > entry), key=lambda x: x.lower)
            targets = [quantize(x.lower, tick, "down") for x in opp]
            direction = "LONG"
            valid = stop < z.lower <= entry
        else:
            opp = sorted((x for x in opp if x.upper < entry), key=lambda x: -x.upper)
            targets = [quantize(x.upper, tick, "up") for x in opp]
            direction = "SHORT"
            valid = stop > z.upper >= entry
        if not opp or not valid:
            continue
        risk = abs(entry - stop)
        if risk <= 0 or (direction == "LONG" and targets[0] <= entry) or (direction == "SHORT" and targets[0] >= entry):
            continue
        tp1, tp2 = targets[0], targets[1] if len(targets) >= 2 else None
        if tp2 is not None and not (tp2 > tp1 if direction == "LONG" else tp2 < tp1):
            tp2 = None
        gross1 = abs(tp1 - entry) / risk
        gross2 = abs(tp2 - entry) / risk if tp2 is not None else None
        net1 = cost_adjusted_rr(direction, entry, stop, tp1, *costs) if costs is not None else None
        net2 = cost_adjusted_rr(direction, entry, stop, tp2, *costs) if costs is not None and tp2 is not None else None
        bd = {}
        score = None
        if trend is not None and net1 is not None and z.origin_idx >= 20:
            aligned = ((trend == "bullish" and direction == "LONG") or
                       (trend == "bearish" and direction == "SHORT"))
            bd["trend"] = cfg.w_trend * (1.0 if aligned else 0.5 if trend == "neutral" else 0.0)
            bd["freshness"] = cfg.w_freshness * {0: 1.0, 1: 0.6, 2: 0.2}.get(z.touches, 0.0)
            bd["departure"] = cfg.w_departure * min(z.departure_strength / 4, 1.0)
            bd["rr_tp1"] = cfg.w_rr * max(0.0, min(net1 / 4, 1.0))
            # Confluence measured by close breaking previous 20 completed candles.
            if z.origin_idx >= 20:
                previous = candles[z.origin_idx - 20:z.origin_idx]
                break_level = max(x.high for x in previous) if direction == "LONG" else min(x.low for x in previous)
                break_confirmed = (candles[z.confirmed_idx].close > break_level if direction == "LONG"
                                   else candles[z.confirmed_idx].close < break_level)
                bd["confluence"] = cfg.w_confluence if break_confirmed else 0.0
            else:
                bd["confluence"] = 0.0
            score = sum(bd.values())
        result.append(Candidate(direction, z, entry, stop, tp1, tp2, gross1, gross2,
                                net1, net2, score, bd, opp[0], opp[1] if tp2 is not None else None))
    return result


def fmt_price(v: Optional[float], tick: float) -> str:
    if v is None:
        return "N/A"
    decimals = max(0, len(f"{tick:.12f}".rstrip("0").split(".")[-1]))
    return f"{v:.{decimals}f}"


def make_chart(candles: list[Candle], zones: list[Zone], best: Optional[Candidate],
               symbol: str, timeframe: str, output: str, cfg: Config, synthetic: bool,
               tick: float) -> None:
    display = candles[-cfg.chart_candles:]
    offset, n = len(candles) - len(display), len(display)
    fig, ax = plt.subplots(figsize=(15, 8))
    fig.patch.set_facecolor("white")
    for i, c in enumerate(display):
        color = "#1b917a" if c.close >= c.open else "#c94b51"
        ax.vlines(i, c.low, c.high, colors=color, linewidth=.9, zorder=3)
        ax.add_patch(Rectangle((i-.3, min(c.open,c.close)), .6,
                               max(abs(c.close-c.open), tick*.2),
                               color=color, zorder=4))
    selected_zones = []
    if best is not None:
        selected_zones = [best.zone, best.opposing1] + ([best.opposing2] if best.opposing2 else [])
    else:
        for z in sorted(zones, key=lambda q: q.confirmed_idx, reverse=True):
            if any(z.kind == p.kind and
                   max(0, min(z.upper,p.upper)-max(z.lower,p.lower)) >=
                   .5 * min(z.upper-z.lower,p.upper-p.lower)
                   for p in selected_zones):
                continue
            selected_zones.append(z)
            if len(selected_zones) >= 4:
                break
    for z in selected_zones:
        a = max(0, z.origin_idx - offset)
        if z.origin_idx >= len(candles):
            continue
        color = "#228b52" if z.kind == "demand" else "#d04444"
        ax.add_patch(Rectangle((a, z.lower), max(0, n+7-a), z.upper-z.lower,
                               facecolor=color, edgecolor=color, alpha=.14, zorder=1))
        ax.text(n+8, (z.lower+z.upper)/2,
                f"{z.kind.title()} {fmt_price(z.lower,tick)}–{fmt_price(z.upper,tick)}",
                fontsize=7, color=color, va="center")
    if best is not None:
        ax.axhline(best.entry_mid, color="#1855ab", lw=1.5, label=f"Hypothetical entry {fmt_price(best.entry_mid,tick)}")
        ax.axhline(best.stop_mid, color="#c42626", ls="--", lw=1.5, label=f"Stop {fmt_price(best.stop_mid,tick)}")
        ax.axhline(best.tp1_mid, color="#288c42", ls="--", lw=1.5, label=f"TP1 {fmt_price(best.tp1_mid,tick)}")
        if best.tp2_mid is not None:
            ax.axhline(best.tp2_mid, color="#288c42", ls=":", lw=1.5, label=f"TP2 {fmt_price(best.tp2_mid,tick)}")
        end = best.tp2_mid if best.tp2_mid is not None else best.tp1_mid
        path = [(n+1, best.entry_mid), (n+5, best.tp1_mid)]
        if best.tp2_mid is not None:
            path.append((n+9, end))
        for a, b in zip(path, path[1:]):
            ax.add_patch(FancyArrowPatch(a,b,arrowstyle="->", color="#f28b00",
                                         lw=2, mutation_scale=13, linestyle="--", zorder=7))
        title = f"{symbol} {timeframe} — {best.direction} from {best.zone.kind.title()} | NET RR NOT VERIFIED"
        ax.legend(loc="upper left", fontsize=8, framealpha=.9)
    else:
        title = f"{symbol} {timeframe} — ZONES ONLY | NO TRADE VALIDATED"
    ax.set_title(title, fontweight="bold")
    ax.text(.98, .03, "SYNTHETIC DEMONSTRATION — NOT MARKET DATA" if synthetic else
            "HYPOTHETICAL SCENARIO — NOT OBSERVED / NOT A FORECAST",
            transform=ax.transAxes, ha="right", va="bottom", color="#b03812",
            fontsize=10, fontweight="bold", bbox={"facecolor":"white","alpha":.88,"edgecolor":"none"})
    indices = np.unique(np.linspace(0, n-1, min(9,n)).astype(int))
    ax.set_xticks(indices)
    ax.set_xticklabels([display[i].close_time_utc.strftime("%Y-%m-%d\n%H:%M") for i in indices], fontsize=8)
    ax.set_xlabel("Completed candle close (UTC)")
    ax.set_ylabel("Quote-currency price")
    ax.grid(alpha=.2)
    ax.set_xlim(-1, n+25)
    fig.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=cfg.chart_dpi, bbox_inches="tight")
    plt.close(fig)


def make_demo(n: int = 180) -> list[Candle]:
    """Deterministic synthetic fixtures ONLY. Explicit opt-in is compulsory."""
    rng = np.random.default_rng(17)
    t0 = datetime(2026, 5, 1, tzinfo=timezone.utc)
    close = 1.10
    rows = []
    for i in range(n):
        drift = (0.00005 if i < 38 else 0.0009 if 38 <= i < 46 else
                 -0.00005 if i < 75 else -0.0010 if i < 82 else
                 0.00002 if i < 112 else 0.0010 if i < 120 else -0.00004)
        new_close = max(.1, close + drift + rng.normal(0, .00023))
        hi = max(close, new_close) + .00012
        lo = min(close, new_close) - .00012
        rows.append(Candle(t0 + timedelta(hours=4*(i+1)), close, hi, lo,
                           new_close, True, "SYNTHETIC_DEMO_ONLY"))
        close = new_close
    return rows


def analyze(candles: list[Candle], htf: Optional[list[Candle]], symbol: str,
            timeframe: str, cfg: Config, output: str, tick: float,
            costs: Optional[tuple[float,float,float]], synthetic: bool = False,
            render_chart: bool = True) -> dict:
    errors = validate_candles(candles)
    if htf is not None:
        errors += ["HTF: " + e for e in validate_candles(htf, min_count=35)]
        if htf and candles and htf[-1].close_time_utc > candles[-1].close_time_utc:
            errors.append("HTF data contains candles later than entry timeframe vintage")
    if errors:
        return {"status": "NOT_VALIDATED_NO_TRADE", "errors": errors, "chart": None}
    atr = atr_wilder(candles, cfg.atr_period)
    zones = scan_zones(candles, atr, cfg)
    trend = htf_trend(htf) if htf is not None else None
    candidates = define_candidates(candles, zones, atr, cfg, tick, costs, trend)
    eligible = [c for c in candidates if c.net_rr_tp1_est is not None and
                c.net_rr_tp1_est >= cfg.min_net_rr and c.score is not None]
    best = max(eligible, key=lambda c:(c.score, c.net_rr_tp1_est)) if eligible else None
    if render_chart:
        make_chart(candles, zones, best, symbol, timeframe, output, cfg, synthetic, tick)
    status = "SYNTHETIC_DEMO_ONLY" if synthetic else "RESEARCH_CANDIDATE_ONLY" if best else "NOT_VALIDATED_NO_TRADE"
    result = {"status": status, "chart": str(output) if render_chart else None, "symbol": symbol,
              "timeframe": timeframe, "last_completed_utc": candles[-1].close_time_utc.isoformat(),
              "input_source": sorted(set(c.source for c in candles)),
              "zone_count": len(zones), "candidate_count": len(candidates),
              "limitations": ["No ten independently authenticated agent receipts", "Six TITAN stages not independently completed",
                              "No verified broker executable bid/ask or account/exposure gate", "No trade authorisation"],
              "score_method": "Provisional SDRC-MTF 25/20/20/20/15, not calibrated",
              "decision": "NOT VALIDATED — NO TRADE"}
    if htf is None: result["limitations"].append("Separate higher-timeframe candles absent")
    if costs is None: result["limitations"].append("Broker-specific spread/slippage/commission inputs absent")
    if best:
        result["candidate"] = {"direction": best.direction,
              "score": round(best.score, 2),
              "score_breakdown": {k:round(v,2) for k,v in best.score_breakdown.items()},
              "zone": {"kind":best.zone.kind, "lower":best.zone.lower, "upper":best.zone.upper,
                        "confirmed_utc":candles[best.zone.confirmed_idx].close_time_utc.isoformat(),
                        "touches":best.zone.touches},
              "entry_mid":best.entry_mid, "stop_mid":best.stop_mid, "tp1_mid":best.tp1_mid,
              "tp2_mid":best.tp2_mid, "gross_rr_tp1":round(best.gross_rr_tp1,3),
              "cost_adjusted_rr_tp1_est":round(best.net_rr_tp1_est,3),
              "cost_adjusted_rr_tp2_est":round(best.net_rr_tp2_est,3) if best.net_rr_tp2_est is not None else None}
        result["explanation"] = (
            f"The provisional {symbol} {timeframe} {best.direction} candidate scored {best.score:.1f}/100 using the documented SDRC research rubric. "
            f"Its {best.zone.kind} zone was confirmed at {candles[best.zone.confirmed_idx].close_time_utc.isoformat()} and has {best.zone.touches} subsequent retest(s). "
            f"The hypothetical entry at {fmt_price(best.entry_mid,tick)} places its protective stop beyond the distal zone edge at {fmt_price(best.stop_mid,tick)}. "
            f"TP1 is the nearest surviving opposing zone at {fmt_price(best.tp1_mid,tick)}, with a cost-adjusted estimated ratio of 1:{best.net_rr_tp1_est:.2f}; a second target is only shown if evidenced. "
            f"A zone breach, opposing structure change or a failed mandatory TITAN gate would invalidate this research idea. "
            f"No independent agent quorum or broker execution has been validated, so this is not an approved trade.")
    else:
        result["explanation"] = "No setup passed the required TP1 cost-adjusted 2.5:1 filter with genuine independent higher-timeframe input; zones, if any, are displayed only for research."
    return result


def scan_manifest(path: str, cfg: Config, output: str) -> dict:
    """Rank eligible research candidates across instruments; render one chart only."""
    manifest_path = Path(path).resolve()
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = obj.get("instruments", [])
    if not isinstance(items, list) or not items:
        raise ValueError("manifest must contain a non-empty instruments list")
    scans = []
    failures = []
    for item in items:
        symbol = item.get("symbol", "")
        timeframe = item.get("timeframe", "")
        if not symbol or not timeframe:
            failures.append({"instrument":str(symbol),"reason":"symbol/timeframe are required"})
            continue
        try:
            def resolve(p):
                return str((manifest_path.parent / p).resolve())
            candles = load_csv(resolve(item["csv"]))
            htf = load_csv(resolve(item["htf_csv"])) if item.get("htf_csv") else None
            tick = float(item["tick_size"])
            pip = float(item["pip_size"])
            if not all(math.isfinite(v) and v > 0 for v in (tick,pip)):
                raise ValueError("tick_size and pip_size must be positive finite")
            values = [item.get(k) for k in ("spread_pips","slippage_pips","commission_pips")]
            if any(x is not None for x in values) and not all(x is not None for x in values):
                raise ValueError("all three trading-cost fields are required together")
            if all(x is not None for x in values):
                values = [float(x) for x in values]
                if any(not math.isfinite(x) or x < 0 for x in values):
                    raise ValueError("trading costs must be non-negative finite")
                costs = tuple(x*pip for x in values)
            else:
                costs = None
            result = analyze(candles, htf, symbol, timeframe, cfg, output,
                             tick, costs, render_chart=False)
            scans.append({"metadata":item, "result":result})
        except (KeyError,ValueError,OSError) as e:
            failures.append({"instrument":symbol,"reason":str(e)})
    eligible = [x for x in scans if x["result"].get("candidate")]
    if not eligible:
        return {"status":"NOT_VALIDATED_NO_TRADE", "decision":"NOT VALIDATED — NO TRADE",
                "chart":None, "instruments_checked":len(items),
                "candidates_ranked":[], "input_errors":failures,
                "rejections":[{"symbol":x["result"]["symbol"],"explanation":x["result"].get("explanation"),
                               "errors":x["result"].get("errors",[])} for x in scans]}
    eligible.sort(key=lambda x:(x["result"]["candidate"]["score"],
                                x["result"]["candidate"]["cost_adjusted_rr_tp1_est"]),reverse=True)
    selected = eligible[0]
    item = selected["metadata"]
    candles = load_csv(str((manifest_path.parent/item["csv"]).resolve()))
    htf = load_csv(str((manifest_path.parent/item["htf_csv"]).resolve()))
    costs = tuple(float(item[k])*float(item["pip_size"]) for k in
                  ("spread_pips","slippage_pips","commission_pips"))
    winning = analyze(candles, htf, item["symbol"], item["timeframe"], cfg,
                      output, float(item["tick_size"]), costs, render_chart=True)
    winning["instruments_checked"] = len(items)
    winning["ranked_alternatives"] = [{"symbol":x["result"]["symbol"],
                                       "direction":x["result"]["candidate"]["direction"],
                                       "score":x["result"]["candidate"]["score"]}
                                      for x in eligible[1:]]
    winning["input_errors"] = failures
    if len(eligible) > 1:
        runner = eligible[1]["result"]
        b1 = winning["candidate"]["score_breakdown"]
        b2 = runner["candidate"]["score_breakdown"]
        factor = max(b1, key=lambda key: b1[key] - b2.get(key,0.0))
        edge = b1[factor] - b2.get(factor,0.0)
        opening, rest = winning["explanation"].split(". ", 1)
        winning["explanation"] = (opening +
            f"; the closest eligible rival, {runner['symbol']}, scored {runner['candidate']['score']:.1f}/100, "
            f"with a {edge:+.1f}-point difference on {factor}. " + rest)
    else:
        opening, rest = winning["explanation"].split(". ", 1)
        winning["explanation"] = opening + "; no other scanned instrument met the research filters. " + rest
    return winning


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--csv", help="Completed entry-timeframe OHLC CSV")
    group.add_argument("--demo", action="store_true", help="Explicit synthetic illustration only")
    group.add_argument("--manifest", help="JSON manifest for ranking multiple instruments")
    p.add_argument("--htf-csv", help="Separate, completed higher-timeframe OHLC CSV")
    p.add_argument("--symbol", default="EURUSD")
    p.add_argument("--timeframe", default="H4")
    p.add_argument("--tick-size", type=float, default=.00001)
    p.add_argument("--pip-size", type=float, default=.0001)
    p.add_argument("--spread-pips", type=float)
    p.add_argument("--slippage-pips", type=float)
    p.add_argument("--commission-pips", type=float)
    p.add_argument("--min-rr", type=float, default=FROZEN_MIN_NET_RR)
    p.add_argument("--output", default="titan_sdrc_chart.png")
    args = p.parse_args()
    if args.min_rr < FROZEN_MIN_NET_RR or not math.isfinite(args.min_rr):
        p.error("min-rr may not be less than TITAN's frozen 2.5")
    if not all(math.isfinite(v) and v > 0 for v in (args.tick_size,args.pip_size)):
        p.error("tick-size and pip-size must be positive finite numbers")
    values = (args.spread_pips,args.slippage_pips,args.commission_pips)
    if any(x is not None for x in values) and not all(x is not None for x in values):
        p.error("supply spread-pips, slippage-pips, and commission-pips together")
    if any(x is not None and (not math.isfinite(x) or x < 0) for x in values):
        p.error("trading costs must be non-negative finite numbers")
    costs = tuple(x*args.pip_size for x in values) if all(x is not None for x in values) else None
    try:
        if args.manifest:
            result = scan_manifest(args.manifest, Config(min_net_rr=args.min_rr), args.output)
        else:
            candles = make_demo() if args.demo else load_csv(args.csv)
            htf = load_csv(args.htf_csv) if args.htf_csv else None
            result = analyze(candles, htf, args.symbol, args.timeframe,
                             Config(min_net_rr=args.min_rr), args.output,
                             args.tick_size, costs, synthetic=args.demo)
    except (OSError, ValueError) as e:
        p.error(str(e))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("Educational research only; not financial advice or authorisation to trade.")

if __name__ == "__main__":
    main()