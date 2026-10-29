"""TITAN PACE-MTF 1.0: precursor -> acceptance -> confluence, RESEARCH ONLY.

This deterministic, read-only module supplies context to the existing TITAN
six-phase system. It neither amends frozen strategies nor authorises an order.
All market bars must be independently supplied, completed and timestamped.
The early pattern remains statistically INCONCLUSIVE, not a proven edge.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
FRAMES = ("D1", "H4", "H1", "M15")
VERSION = "PACE-MTF-1.0-RESEARCH"


def parse_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("TIMESTAMP_REQUIRED")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("UTC_OFFSET_REQUIRED")
    return t.astimezone(timezone.utc)


def parse_bars(items: Any, as_of: datetime) -> list[dict]:
    if not isinstance(items, list) or len(items) > 1600:
        raise ValueError("INVALID_BAR_COLLECTION")
    out: list[dict] = []
    last = None
    for row in items:
        if not isinstance(row, dict) or row.get("closed") is not True:
            raise ValueError("UNCONFIRMED_CANDLE")
        timestamp = parse_time(row.get("closed_at_utc"))
        if timestamp > as_of or (last is not None and timestamp <= last):
            raise ValueError("FUTURE_DUPLICATE_OR_UNSORTED_CANDLE")
        last = timestamp
        values = []
        for key in ("open", "high", "low", "close"):
            v = row.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError("NON_FINITE_OR_NON_NUMERIC_PRICE")
            values.append(float(v))
        o, h, l, c = values
        if l <= 0 or not (l <= o <= h and l <= c <= h):
            raise ValueError("INCONSISTENT_OHLC")
        out.append({"t": timestamp, "o": o, "h": h, "l": l, "c": c})
    return out


def midpoint(b: list[dict], at: int, period: int) -> float:
    z = b[at-period+1:at+1]
    return (max(x["h"] for x in z) + min(x["l"] for x in z)) / 2


def cloud_direction(b: list[dict], at: int) -> int:
    """Visible Ichimoku cloud at bar at; origins at at-26 (no future leak)."""
    if at < 77:
        return 0
    span_a = (midpoint(b, at-26, 9) + midpoint(b, at-26, 26)) / 2
    span_b = midpoint(b, at-26, 52)
    return 1 if b[at]["c"] > max(span_a, span_b) else -1 if b[at]["c"] < min(span_a, span_b) else 0


def atr(b: list[dict], at: int, period: int) -> float:
    if at < period:
        return float("nan")
    tr = [max(b[i]["h"]-b[i]["l"], abs(b[i]["h"]-b[i-1]["c"]),
              abs(b[i]["l"]-b[i-1]["c"])) for i in range(at-period+1, at+1)]
    return sum(tr)/period


def twenty_day_boundary(b: list[dict], at: int, direction: int) -> float:
    prior = b[at-20:at]
    return max(x["h"] for x in prior) if direction == 1 else min(x["l"] for x in prior)


def precursor(b: list[dict], at: int, direction: int) -> list[dict]:
    """Previous seven CLOSED daily candles; excludes candidate bar at."""
    hits = []
    for k in range(max(110, at-7), at):
        a14, a50 = atr(b,k,14), atr(b,k,50)
        if not (a14 > 0 and a50 > 0 and a14 < .9*a50):
            continue
        boundary = twenty_day_boundary(b,k,direction)
        distance = direction*(boundary-b[k]["c"])
        if 0 <= distance < .65*a14:
            hits.append({"closed_at_utc":b[k]["t"].isoformat(),
                         "atr14_over_atr50":round(a14/a50,5),
                         "distance_atr14":round(distance/a14,5)})
    return hits


def evaluate(snapshot: dict[str, Any], now: datetime | None = None) -> dict:
    base = {"module": VERSION, "status": "BLOCKED", "stage": "INVALID",
            "trade_authorized": False, "orders_submitted": 0,
            "decision": "NOT VALIDATED — NO TRADE",
            "signed_agent_quorum_verified": False, "six_phases_completed": False,
            "frozen_strategy_gates_passed": False, "net_rr_verified": False,
            "independent_data_verified": False}
    try:
        if not isinstance(snapshot, dict):
            raise ValueError("SNAPSHOT_REQUIRED")
        if len(json.dumps(snapshot, allow_nan=False).encode()) > 750000:
            raise ValueError("SNAPSHOT_TOO_LARGE")
        symbol = snapshot.get("symbol")
        asset = snapshot.get("asset_class")
        source = snapshot.get("source")
        if not isinstance(symbol, str) or not 2 <= len(symbol.strip()) <= 32:
            raise ValueError("INSTRUMENT_NOT_VERIFIED")
        if not isinstance(asset, str) or not asset.strip():
            raise ValueError("ASSET_CLASS_REQUIRED")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("SOURCE_PROVENANCE_REQUIRED")
        current = now or datetime.now(timezone.utc)
        as_of = parse_time(snapshot.get("as_of_utc"))
        observed = parse_time(snapshot.get("source_observed_at_utc"))
        if as_of > current or observed > current or observed < as_of:
            raise ValueError("INVALID_SOURCE_OR_SNAPSHOT_TIME")
        data = snapshot.get("bars")
        if not isinstance(data, dict) or "D1" not in data or not set(data).issubset(FRAMES):
            raise ValueError("D1_REQUIRED_OR_UNKNOWN_TIMEFRAME")
        bars = {f:parse_bars(items,as_of) for f,items in data.items()}
        d1 = bars["D1"]
        if len(d1) < 112:
            raise ValueError("INSUFFICIENT_DAILY_HISTORY")
        if (as_of-d1[-1]["t"]).total_seconds() > 5*86400:
            raise ValueError("STALE_DAILY_DATA")
        for f in FRAMES:
            if f in bars and len(bars[f]) < 78:
                raise ValueError(f+"_INSUFFICIENT_CLOUD_HISTORY")
            if f in bars and (as_of-bars[f][-1]["t"]).total_seconds()>5*86400:
                raise ValueError(f+"_STALE_DATA")
    except (ValueError, TypeError, OverflowError) as exc:
        return {**base, "reason": str(exc)}

    i = len(d1)-1
    direction = cloud_direction(d1,i)
    mdir = {f:(cloud_direction(bars[f],len(bars[f])-1) if f in bars else None) for f in FRAMES}
    last = d1[i]
    a14 = atr(d1,i-1,14)
    if not a14 > 0:
        return {**base, "reason": "INVALID_ATR"}

    hits = precursor(d1,i,direction) if direction else []
    boundary = twenty_day_boundary(d1,i,direction) if direction else None
    is_breakout = bool(direction and direction*(last["c"]-boundary)>0)
    close_position = (last["c"]-last["l"])/(last["h"]-last["l"]) if last["h"]>last["l"] else .5
    acceptance = bool(is_breakout and (last["h"]-last["l"])>.85*a14 and
                      (close_position>.75 if direction==1 else close_position<.25))
    a_now, a50_now = atr(d1,i,14), atr(d1,i,50)
    distance = direction*(boundary-last["c"]) if direction else None
    near = bool(direction and a_now>0 and a50_now>0 and a_now<.9*a50_now and
                0<=distance<.65*a_now)
    missing = [f for f in FRAMES if f not in bars]
    conflicts = [f for f in FRAMES if mdir[f] is not None and mdir[f]!=direction]
    mtf_agreed = bool(direction and not missing and not conflicts)

    if direction==0:
        stage="CLOUD_NEUTRAL"
    elif acceptance and hits and mtf_agreed:
        stage="MTF_CONFLUENCE_RESEARCH_ONLY"
    elif acceptance and hits:
        stage="MTF_CONFLICT" if conflicts else "D1_ACCEPTED_MTF_UNVERIFIED"
    elif is_breakout:
        stage="BREAKOUT_WITHOUT_BOTH_CONFIRMATIONS"
    elif near:
        stage="EARLY_WATCH"
    elif hits:
        stage="ARMED_AWAITING_ACCEPTANCE"
    else:
        stage="NO_ANTICIPATORY_PATTERN"
    additional = snapshot.get("independent_context", [])
    if not isinstance(additional,list) or len(additional)>10:
        return {**base,"reason":"INVALID_INDEPENDENT_CONTEXT"}
    # External inputs are always advisory until a separately trusted adapter
    # authenticates point-in-time macro/ECN/futures feeds. Never count these
    # reports as independent confirmation or signed agent votes.
    return {**base,"status":"RESEARCH_ONLY_NOT_VALIDATED", "stage":stage,
            "symbol":symbol,"asset_class":asset,"as_of_utc":as_of.isoformat(),
            "source":source,"source_observed_at_utc":observed.isoformat(),
            "direction":"LONG" if direction==1 else "SHORT" if direction==-1 else "NONE",
            "timeframe_clouds":{f:("ABOVE" if d==1 else "BELOW" if d==-1 else "INSIDE" if d==0 else "MISSING") for f,d in mdir.items()},
            "missing_timeframes":missing,"conflicting_timeframes":conflicts,
            "precursor_count_last_7_d1":len(hits),"precursor_evidence":hits,
            "accepted_daily_breakout":acceptance,"near_boundary_compression":near,
            "research_confluence_observed":stage=="MTF_CONFLUENCE_RESEARCH_ONLY",
            "independent_context_items_received":len(additional),
            "independent_context_status":"UNAUTHENTICATED_AND_NOT_SCORED",
            "controls_remaining":["AUTHENTIC_BROKER_BID_ASK_AND_SPREAD",
                "INDEPENDENT_TEN_AGENT_RECEIPTS","COMPLETE_SIX_PHASES",
                "FROZEN_STRATEGIES_AND_21_TF_WHERE_AVAILABLE",
                "CONFIRMED_MACRO_EVENT_BLACKOUTS","VERIFIED_OPPOSING_SUPPLY_DEMAND_TARGET",
                "NET_RR_AT_LEAST_2_5_TO_FIRST_TARGET","ONE_ACTIVE_TRADE_NO_PENDING_OVERLAP"]}


class AnticipationRequest(BaseModel):
    snapshot: dict[str, Any] = Field(min_length=5)


@router.post("/v1/anticipation/evaluate")
def anticipation_route(request: AnticipationRequest,
                       authorization: str | None = Header(default=None)) -> dict:
    token = os.getenv("TITAN_CONTROL_API_KEY", "")
    if len(token) < 32:
        raise HTTPException(503,"OWNER_AUTH_NOT_CONFIGURED")
    if not authorization or not hmac.compare_digest(authorization,"Bearer "+token):
        raise HTTPException(401,"UNAUTHORIZED")
    return evaluate(request.snapshot)