"""Authenticated cloud-only research endpoints; zero order or execution APIs."""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from diagnostics import control_auth
from cloud_market_data import cloud_scan
from proactive_journal import metrics
import os

router = APIRouter()
class ScanRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=2)

@router.post("/v1/opportunities/cloud-scan")
async def scan_from_vendor(x: ScanRequest, authorization: str | None = Header(default=None)):
    control_auth(authorization)
    try:
        return await cloud_scan(x.symbols)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc

@router.get("/v1/opportunities/journal-metrics")
def journal_metrics(authorization: str | None = Header(default=None)):
    control_auth(authorization)
    path = os.getenv("TITAN_JOURNAL_DB_PATH", "")
    if not path:
        return {"status": "BLOCKED", "reason": "DURABLE_JOURNAL_NOT_CONFIGURED",
                "trade_authorized": False}
    try:
        return {"status": "RESEARCH_JOURNAL", **metrics(path), "trade_authorized": False}
    except (ValueError, OSError) as exc:
        return {"status": "BLOCKED", "reason": type(exc).__name__, "trade_authorized": False}
