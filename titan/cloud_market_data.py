"""TITAN cloud-only external market feed. No desktop/MT4/MT5 dependency.

Twelve Data is a research-data vendor, not a broker quote. Every external call
uses a fixed HTTPS host. No user-provided URL or broker order endpoint exists.
"""
from __future__ import annotations
import asyncio
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any
import httpx
from proactive import scan

HOST = "https://api.twelvedata.com"
INTERVALS = {"D1": "1day", "H4": "4h", "H1": "1h", "M15": "15min"}
SYM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9./:_-]{0,29}$")
# A maximum of TWO instruments x FOUR intervals is selected to respect the
# vendor's common free-tier 8-credit/minute allowance, not a guarantee.
MAX_SYMBOLS = 2

class MarketDataError(Exception):
    pass

def _timestamp(raw: str, tz: str) -> str:
    """Convert vendor exchange-local naive datetime to unambiguous UTC."""
    try:
        date = datetime.fromisoformat(raw)
        if date.tzinfo is None:
            date = date.replace(tzinfo=ZoneInfo(tz))
        return date.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, KeyError, OverflowError) as exc:
        raise MarketDataError("INVALID_PROVIDER_TIMESTAMP") from exc

async def _series(client: httpx.AsyncClient, symbol: str, tf: str, key: str, as_of: datetime) -> tuple[list[dict], dict]:
    # timezone=UTC affects intraday; daily remains exchange-local by vendor design.
    params = {"symbol": symbol, "interval": INTERVALS[tf], "timezone": "UTC",
              "outputsize": 180, "apikey": key, "format": "JSON"}
    try:
        r = await client.get(HOST + "/time_series", params=params)
        r.raise_for_status()
        data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise MarketDataError("VENDOR_REQUEST_FAILED") from exc
    if not isinstance(data, dict) or data.get("status") == "error" or not isinstance(data.get("values"), list):
        raise MarketDataError("VENDOR_DATA_UNAVAILABLE")
    meta = data.get("meta", {})
    if not isinstance(meta, dict) or meta.get("symbol", "").casefold() != symbol.casefold():
        raise MarketDataError("VENDOR_SYMBOL_MISMATCH")
    if str(meta.get("interval", "")) != INTERVALS[tf]:
        raise MarketDataError("VENDOR_INTERVAL_MISMATCH")
    # Intraday requested UTC; daily explicitly reports exchange time.
    zone = "UTC" if tf != "D1" else meta.get("exchange_timezone")
    if not zone:
        raise MarketDataError("MISSING_EXCHANGE_TIMEZONE")
    try:
        ZoneInfo(zone)
    except (KeyError, ValueError) as exc:
        raise MarketDataError("INVALID_EXCHANGE_TIMEZONE") from exc
    bars = []
    for value in data["values"]:
        if not isinstance(value, dict):
            raise MarketDataError("INVALID_VENDOR_BAR")
        bars.append({"time": _timestamp(value.get("datetime"), zone),
                     **{k: value.get(k) for k in ("open", "high", "low", "close")}})
    # Do not silently discard incomplete bars: the scanner rejects them.
    bars.sort(key=lambda b: b["time"])
    if len(bars) > 180:
        raise MarketDataError("EXCESS_VENDOR_BARS")
    return bars, meta

async def cloud_scan(symbols: list[str], client: httpx.AsyncClient | None = None) -> dict:
    """Fetch all CORE frames from an external cloud feed and score both sides.

    Vendor truth is NOT independently authenticated; checks detect malformed or
    mismatched metadata. No bid/ask, model agents, execution permission or orders.
    """
    if not isinstance(symbols, list) or not 1 <= len(symbols) <= MAX_SYMBOLS:
        raise ValueError("Supply one or two symbols")
    if any(not isinstance(s, str) or not SYM.fullmatch(s) for s in symbols):
        raise ValueError("Invalid market symbol")
    if len({s.upper() for s in symbols}) != len(symbols):
        raise ValueError("Duplicate symbol")
    key = os.getenv("TITAN_TWELVEDATA_API_KEY", "")
    if not key:
        return {"status": "BLOCKED", "reason": "EXTERNAL_FEED_KEY_NOT_CONFIGURED",
                "trade_authorized": False, "instruments": []}
    as_of = datetime.now(timezone.utc)
    owned = client is None
    if owned:
        client = httpx.AsyncClient(timeout=18, follow_redirects=False)
    try:
        output = []
        for symbol in symbols:
            try:
                # Deliberately sequential: enforce one research fetch per instrument.
                frames, metas = {}, {}
                for tf in ("D1", "H4", "H1", "M15"):
                    frames[tf], metas[tf] = await _series(client, symbol, tf, key, as_of)
                meta = metas["H4"]
                # Do not invent actual security names: vendor symbol+asset type only.
                inst = {"name": str(meta.get("name") or symbol),
                        "symbol": symbol, "asset_class": str(meta.get("type") or "NOT_VERIFIED"),
                        "market": str(meta.get("exchange") or "NOT_VERIFIED")}
                result = scan({"instrument": inst, "frames": frames,
                               "as_of": as_of.isoformat(),
                               "source": "Twelve Data /time_series UTC-normalized completed bars"})
                result["retrieved_at_utc"] = as_of.isoformat()
                result["vendor_symbol_confirmed"] = True
                result["broker_executable_prices_verified"] = False
                output.append(result)
            except (ValueError, MarketDataError) as exc:
                output.append({"symbol": symbol, "status": "NOT_VALIDATED_NO_TRADE",
                               "reason": str(exc), "trade_authorized": False})
        return {"status": "EXTERNAL_DATA_RESEARCH_ONLY",
                "provider": "Twelve Data", "as_of": as_of.isoformat(),
                "instruments": output, "signed_agents_verified": 0,
                "trade_authorized": False}
    finally:
        if owned:
            await client.aclose()
