"""Durable research alert journal; never uses trades, broker credentials or orders."""
from __future__ import annotations
import json
import math
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from proactive import validate_bars, timestamp

def connection(db_path: str) -> sqlite3.Connection:
    if not db_path:
        raise ValueError("Durable TITAN_JOURNAL_DB_PATH required")
    p = Path(db_path)
    if not p.parent.exists():
        raise ValueError("Journal data directory not mounted/created")
    db = sqlite3.connect(str(p), timeout=10)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("""CREATE TABLE IF NOT EXISTS alerts (
       alert_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, direction TEXT NOT NULL,
       as_of TEXT NOT NULL, source TEXT NOT NULL, state TEXT NOT NULL,
       signal_close REAL NOT NULL, alert_json TEXT NOT NULL,
       outcome_json TEXT)""")
    return db

def record_alert(db_path: str, alert: dict) -> str:
    required = ("alert_id", "symbol", "direction", "as_of", "source", "state", "signal_close")
    if not isinstance(alert, dict) or any(k not in alert for k in required):
        raise ValueError("Missing alert fields")
    if alert["direction"] not in ("LONG", "SHORT") or alert["state"] not in ("EARLY WATCH", "ARMED", "INVALID", "CONFIRMED TRIGGER"):
        raise ValueError("Invalid direction or watch state")
    if not isinstance(alert["symbol"], str) or not alert["symbol"] or len(alert["symbol"]) > 40:
        raise ValueError("Invalid symbol")
    stamp = timestamp(alert["as_of"])
    close = float(alert["signal_close"])
    if close <= 0 or not math.isfinite(close):
        raise ValueError("Invalid price")
    if not isinstance(alert["alert_id"], str) or not 1 <= len(alert["alert_id"]) <= 100:
        raise ValueError("Invalid ID")
    if not isinstance(alert["source"], str) or not alert["source"]:
        raise ValueError("Missing source")
    with closing(connection(db_path)) as db:
        with db:
            db.execute("INSERT OR IGNORE INTO alerts VALUES (?,?,?,?,?,?,?, ?,NULL)",
                       (alert["alert_id"], alert["symbol"], alert["direction"],
                        stamp.isoformat(), alert["source"], alert["state"], close,
                        json.dumps(alert, sort_keys=True)))
    return alert["alert_id"]

def evaluate_outcome(db_path: str, alert_id: str, bars: list[dict], timeframe: str,
                     as_of: str, stop: float | None = None, tp1: float | None = None) -> dict:
    """Close-to-alert MFE/MAE; no entry/fill assumption. Intrabar collisions ambiguous."""
    with closing(connection(db_path)) as db:
        row = db.execute("SELECT direction,as_of,signal_close FROM alerts WHERE alert_id=?", (alert_id,)).fetchone()
        if row is None:
            raise ValueError("Alert not found")
        direction, alarm, price = row
        clean = validate_bars(bars, timeframe, timestamp(as_of))
        after = [b for b in clean if b["time"] > timestamp(alarm)]
        if not after:
            raise ValueError("No completed future bars")
        mult = 1 if direction == "LONG" else -1
        excursions = [(mult * (b["high"] - price) if mult == 1 else mult * (b["low"] - price),
                       mult * (b["low"] - price) if mult == 1 else mult * (b["high"] - price)) for b in after]
        result = {"state": "RESEARCH_OBSERVATION_ONLY", "bars_observed": len(after),
                  "mfe_percent": round(100 * max(0, max(x[0] for x in excursions)) / price, 4),
                  "mae_percent": round(100 * max(0, -min(x[1] for x in excursions)) / price, 4),
                  "observed_until": after[-1]["time"].isoformat(),
                  "fill_verified": False, "costs_verified": False}
        if stop is not None and tp1 is not None:
            stop, tp1 = float(stop), float(tp1)
            if not all(math.isfinite(v) and v > 0 for v in (stop, tp1)):
                raise ValueError("Invalid levels")
            if not (stop < price < tp1 if mult == 1 else tp1 < price < stop):
                raise ValueError("Invalid direction and levels")
            result["barrier_event"] = "NEITHER"
            for b in after:
                stop_hit = (b["low"] <= stop) if mult == 1 else (b["high"] >= stop)
                tp_hit = (b["high"] >= tp1) if mult == 1 else (b["low"] <= tp1)
                if stop_hit or tp_hit:
                    result["barrier_event"] = "AMBIGUOUS_SAME_BAR" if stop_hit and tp_hit else ("STOP_FIRST_BAR" if stop_hit else "TP1_FIRST_BAR")
                    break
        with db:
            db.execute("UPDATE alerts SET outcome_json=? WHERE alert_id=?",
                       (json.dumps(result, sort_keys=True), alert_id))
        return result

def metrics(db_path: str) -> dict:
    """Research journal counts only; not a portfolio P&L or trade success rate."""
    with closing(connection(db_path)) as db:
        rows = db.execute("SELECT state,outcome_json FROM alerts").fetchall()
    outcomes = [json.loads(x[1]) for x in rows if x[1]]
    return {"alerts_total": len(rows), "evaluated": len(outcomes),
            "early_watch": sum(x[0] == "EARLY WATCH" for x in rows),
            "armed": sum(x[0] == "ARMED" for x in rows),
            "tp1_first_bar": sum(x.get("barrier_event") == "TP1_FIRST_BAR" for x in outcomes),
            "stop_first_bar": sum(x.get("barrier_event") == "STOP_FIRST_BAR" for x in outcomes),
            "ambiguous_same_bar": sum(x.get("barrier_event") == "AMBIGUOUS_SAME_BAR" for x in outcomes),
            "trade_pnl_verified": False}
