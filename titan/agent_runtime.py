"""TITAN research-only ten-model execution. Never places orders or authorises trades.

Ed25519 receipts attest responses observed by TITAN; model providers do not
sign these receipts. Existing signed gateway and frozen TITAN risk gates remain.
"""
from __future__ import annotations
import asyncio, base64, hashlib, hmac, json, os, re, uuid
from datetime import datetime, timezone
from typing import Any
import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from diagnostics import NODES

router = APIRouter()
PHASE_ROLES = (
    ("fundamental", ("MACRO_ANALYST", "SECTOR_ANALYST")),
    ("technical", ("STRUCTURAL_ANALYST", "QUANT_ANALYST", "VOLATILITY_ANALYST", "SEASONAL_ANALYST")),
    ("sentiment_macro", ("SENTIMENT_ANALYST", "CROSS_ASSET_ANALYST", "GEOPOLITICAL_ANALYST", "ALT_DATA_ANALYST")),
)
PHASE_ORDER = tuple(p for p, _ in PHASE_ROLES) + ("devils_advocate", "risk", "cio_consensus")
REQUIRED_ROLES = tuple(r for _, roles in PHASE_ROLES for r in roles)
NODE_BY_ROLE = {node[0]: node for node in NODES}
assert len(set(REQUIRED_ROLES)) == len(REQUIRED_ROLES) == 10
assert set(NODE_BY_ROLE) == set(REQUIRED_ROLES)

def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def auth(authorization: str | None) -> None:
    secret = os.getenv("TITAN_CONTROL_API_KEY", "")
    if len(secret) < 32:
        raise HTTPException(503, "OWNER_AUTH_NOT_CONFIGURED")
    if not authorization or not hmac.compare_digest(authorization, "Bearer " + secret):
        raise HTTPException(401, "UNAUTHORIZED")

def keys_and_nodes():
    """Reject missing credentials, duplicate models, duplicate signing keys."""
    issues, keys, nodes, used_models, used_keys = [], {}, {}, set(), set()
    for role in REQUIRED_ROLES:
        _, provider, default_model, secret_env, base, region = NODE_BY_ROLE[role]
        model = os.getenv("TITAN_MODEL_" + role, default_model).strip()
        if not model or len(model) > 128 or not re.fullmatch(r"[\w./:-]+", model):
            issues.append(role + ":INVALID_MODEL")
        if not os.getenv(secret_env):
            issues.append(role + ":CREDENTIAL_NOT_CONFIGURED")
        if (provider, model) in used_models:
            issues.append(role + ":DUPLICATE_MODEL")
        used_models.add((provider, model))
        nodes[role] = {"role": role, "provider": provider, "model": model,
                       "credential_env": secret_env, "base": base, "region": region}
        secret = os.getenv("TITAN_AGENT_SIGNING_KEY_" + role, "")
        if not secret:
            issues.append(role + ":SIGNING_KEY_NOT_CONFIGURED")
            continue
        try:
            raw = base64.b64decode(secret, validate=True)
            if len(raw) != 32:
                raise ValueError("invalid length")
            key = Ed25519PrivateKey.from_private_bytes(raw)
            public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            if public in used_keys:
                issues.append(role + ":DUPLICATE_SIGNING_KEY")
            used_keys.add(public)
            keys[role] = key
        except (ValueError, TypeError):
            issues.append(role + ":INVALID_SIGNING_KEY")
    return keys, nodes, issues

class ResearchRequest(BaseModel):
    snapshot: dict[str, Any] = Field(min_length=4)

def validate_snapshot(snapshot: dict[str, Any]) -> str | None:
    try:
        if len(canonical(snapshot)) > 280000:
            return "SNAPSHOT_TOO_LARGE"
    except (ValueError, TypeError):
        return "INVALID_SNAPSHOT"
    if not isinstance(snapshot.get("symbol"), str) or not 2 <= len(snapshot["symbol"]) <= 24:
        return "SYMBOL_REQUIRED"
    if not isinstance(snapshot.get("asset_class"), str) or not snapshot["asset_class"]:
        return "ASSET_CLASS_REQUIRED"
    if not isinstance(snapshot.get("data"), dict) or not snapshot["data"]:
        return "MARKET_DATA_REQUIRED"
    if not isinstance(snapshot.get("sources"), list) or not snapshot["sources"]:
        return "TIMESTAMPED_SOURCES_REQUIRED"
    try:
        as_of = datetime.fromisoformat(snapshot["as_of_utc"].replace("Z", "+00:00"))
        if as_of.tzinfo is None or as_of > datetime.now(timezone.utc):
            return "INVALID_SNAPSHOT_TIMESTAMP"
        for item in snapshot["sources"]:
            if not isinstance(item, dict) or not item.get("name") or not item.get("as_of_utc"):
                return "SOURCE_PROVENANCE_INCOMPLETE"
            t = datetime.fromisoformat(item["as_of_utc"].replace("Z", "+00:00"))
            if t.tzinfo is None or t > datetime.now(timezone.utc):
                return "INVALID_SOURCE_TIMESTAMP"
    except (ValueError, TypeError, KeyError, AttributeError):
        return "INVALID_SNAPSHOT_TIMESTAMP"
    return None

def role_prompt(role: str, snapshot: dict[str, Any], phase: str):
    system = (
        "You are an independently called, research-only TITAN financial analyst. "
        "Analyse only the attached timestamped snapshot. Do not invent prices, "
        "indicator readings, trades, citations, outside-model results or live data. "
        "Report gaps and opposing interpretations. Never approve trades. "
        "Return ONLY JSON with exact keys stance, confidence, evidence, risks, invalidations. "
        "stance: BULLISH, BEARISH, NEUTRAL or INSUFFICIENT_DATA. "
        "confidence: float 0 to 1. evidence: list of {claim,source,as_of_utc} objects "
        "attributed to names/timestamps in snapshot.sources. risks and invalidations: "
        "nonempty string lists. Insufficient evidence means INSUFFICIENT_DATA."
    )
    payload = {"role": role, "phase": phase, "snapshot": snapshot}
    return [{"role": "system", "content": system},
            {"role": "user", "content": canonical(payload).decode()}]

def parse_analysis(content: str, snapshot: dict[str, Any]):
    if len(content) > 25000:
        raise ValueError("OVERSIZED_OUTPUT")
    value = json.loads(content)
    if not isinstance(value, dict) or set(value) != {"stance", "confidence", "evidence", "risks", "invalidations"}:
        raise ValueError("INVALID_ANALYST_SCHEMA")
    if value["stance"] not in {"BULLISH", "BEARISH", "NEUTRAL", "INSUFFICIENT_DATA"}:
        raise ValueError("INVALID_STANCE")
    if isinstance(value["confidence"], bool) or not isinstance(value["confidence"], (float, int)) or not 0 <= value["confidence"] <= 1:
        raise ValueError("INVALID_CONFIDENCE")
    if not isinstance(value["evidence"], list) or len(value["evidence"]) > 12:
        raise ValueError("INVALID_EVIDENCE")
    known_sources = {(s["name"], s["as_of_utc"]) for s in snapshot["sources"]}
    for e in value["evidence"]:
        if (not isinstance(e, dict) or set(e) != {"claim", "source", "as_of_utc"}
            or not isinstance(e["claim"], str) or not e["claim"].strip()
            or (e["source"], e["as_of_utc"]) not in known_sources):
            raise ValueError("EVIDENCE_SOURCE_NOT_IN_SNAPSHOT")
    if value["stance"] != "INSUFFICIENT_DATA" and not value["evidence"]:
        raise ValueError("UNSUPPORTED_STANCE")
    for name in ("risks", "invalidations"):
        if not isinstance(value[name], list) or not value[name] or len(value[name]) > 12 or not all(isinstance(x, str) and x.strip() for x in value[name]):
            raise ValueError("INVALID_" + name.upper())
    return value

def sign_receipt(body: dict[str, Any], key: Ed25519PrivateKey):
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    signature = key.sign(canonical(body))
    return {"body": body, "signature_b64": base64.b64encode(signature).decode(),
            "service_public_key_b64": base64.b64encode(public).decode(),
            "attestation_type": "TITAN_SERVICE_ATTESTS_PROVIDER_RESPONSE_NOT_PROVIDER_SIGNATURE"}

def verify_receipt(receipt, trusted_public_b64: str) -> bool:
    try:
        if receipt.get("attestation_type") != "TITAN_SERVICE_ATTESTS_PROVIDER_RESPONSE_NOT_PROVIDER_SIGNATURE":
            return False
        if not hmac.compare_digest(receipt["service_public_key_b64"], trusted_public_b64):
            return False
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(trusted_public_b64, validate=True))
        key.verify(base64.b64decode(receipt["signature_b64"], validate=True), canonical(receipt["body"]))
        return True
    except Exception:
        return False

async def call_agent(role, phase, snapshot, snapshot_sha, run_id, node, key, client, semaphore):
    async with semaphore:
        try:
            response = await client.post(
                node["base"] + "/chat/completions",
                headers={"Authorization": "Bearer " + os.environ[node["credential_env"]]},
                json={"model": node["model"], "messages": role_prompt(role, snapshot, phase),
                      "temperature": 0, "max_tokens": 1100})
            response.raise_for_status()
            if len(response.content) > 120000:
                raise ValueError("OVERSIZED_PROVIDER_RESPONSE")
            record = response.json()
            request_id = record.get("id", "")
            returned_model = record.get("model")
            choices = record.get("choices", [])
            if (not isinstance(request_id, str) or len(request_id) < 8
                or returned_model != node["model"] or not isinstance(choices, list)
                or len(choices) != 1 or choices[0].get("finish_reason") not in ("stop", None)):
                raise ValueError("UNVERIFIED_REMOTE_RESPONSE")
            content = choices[0]["message"].get("content")
            if not isinstance(content, str):
                raise ValueError("INVALID_MODEL_CONTENT")
            analysis = parse_analysis(content, snapshot)
            body = {"schema_version": "1.0", "run_id": run_id, "phase": phase,
                    "role": role, "provider": node["provider"], "requested_model": node["model"],
                    "returned_model": returned_model, "provider_request_id": request_id,
                    "snapshot_sha256": snapshot_sha, "provider_response_sha256": digest(record),
                    "analysis": analysis, "observed_at_utc": utc_now()}
            receipt = sign_receipt(body, key)
            pub = base64.b64encode(key.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()
            if not verify_receipt(receipt, pub):
                raise ValueError("LOCAL_ATTESTATION_FAILED")
            return {"role": role, "status": "PROVIDER_RESPONSE_OBSERVED", "receipt": receipt}
        except httpx.HTTPStatusError as exc:
            return {"role": role, "status": "BLOCKED", "reason": "UPSTREAM_HTTP_" + str(exc.response.status_code)}
        except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError):
            return {"role": role, "status": "BLOCKED", "reason": "PROVIDER_RESPONSE_NOT_VERIFIED"}

async def run_research(snapshot: dict[str, Any], client: httpx.AsyncClient | None = None):
    run_id = str(uuid.uuid4())
    base = {"run_id": run_id, "created_at_utc": utc_now(), "symbol": snapshot.get("symbol"),
            "status": "BLOCKED", "trade_authorized": False, "orders_submitted": 0,
            "frozen_risk_gates_passed": False, "research_quorum_verified": False,
            "provider_native_signatures": 0, "phases": [], "receipts": []}
    invalid = validate_snapshot(snapshot)
    if invalid:
        return {**base, "reason": invalid}
    if os.getenv("TITAN_AGENT_RESEARCH_ENABLED") != "1":
        return {**base, "reason": "RESEARCH_DISABLED"}
    keys, nodes, issues = keys_and_nodes()
    if issues:
        return {**base, "reason": "AGENT_PREFLIGHT_FAILED", "preflight_issues": issues}
    snapshot_sha = digest(snapshot)
    base["snapshot_sha256"] = snapshot_sha
    semaphore = asyncio.Semaphore(3)
    receipts, phases = [], []

    async def execute(http_client):
        for phase, roles in PHASE_ROLES:
            results = await asyncio.gather(*(call_agent(role, phase, snapshot, snapshot_sha, run_id,
                                       nodes[role], keys[role], http_client, semaphore) for role in roles))
            ok = all(item["status"] == "PROVIDER_RESPONSE_OBSERVED" for item in results)
            phases.append({"phase": phase, "roles": list(roles), "state": "COMPLETE" if ok else "BLOCKED"})
            receipts.extend(item["receipt"] for item in results if "receipt" in item)
            if not ok:
                return {**base, "reason": "INDEPENDENT_AGENT_EXECUTION_FAILED", "phases": phases,
                        "receipts": receipts, "failed_roles": [r for r in results if r["status"] == "BLOCKED"]}
        roles = [r["body"]["role"] for r in receipts]
        models = [(r["body"]["provider"], r["body"]["returned_model"]) for r in receipts]
        requests = [(r["body"]["provider"], r["body"]["provider_request_id"]) for r in receipts]
        public_keys = [r["service_public_key_b64"] for r in receipts]
        signed = all(verify_receipt(r, base64.b64encode(keys[r["body"]["role"]].public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()) for r in receipts)
        distinct = (len(receipts) == 10 and set(roles) == set(REQUIRED_ROLES)
                    and len(set(models)) == len(set(requests)) == len(set(public_keys)) == 10)
        if not (distinct and signed and all(r["body"]["snapshot_sha256"] == snapshot_sha for r in receipts)):
            return {**base, "reason": "RECEIPT_QUORUM_FAILED", "phases": phases, "receipts": receipts}
        bullish = [r["body"]["role"] for r in receipts if r["body"]["analysis"]["stance"] == "BULLISH"]
        bearish = [r["body"]["role"] for r in receipts if r["body"]["analysis"]["stance"] == "BEARISH"]
        phases.append({"phase": "devils_advocate", "state": "COMPLETE",
                       "method": "deterministic opposing-view aggregation, not an additional model",
                       "bullish_agents": bullish, "bearish_agents": bearish})
        phases.append({"phase": "risk", "state": "BLOCKED",
                       "reason": "FROZEN_STRATEGY_AND_BROKER_EXECUTION_GATES_NOT_PROVEN"})
        phases.append({"phase": "cio_consensus", "state": "NO_TRADE",
                       "reason": "NO_VALIDATED_EXECUTION_CONSENSUS"})
        assert tuple(p["phase"] for p in phases) == PHASE_ORDER
        return {**base, "status": "TEN_EXTERNAL_RESPONSES_ATTESTED_RESEARCH_ONLY",
                "reason": "RESEARCH_QUORUM_ONLY_TRADE_GATES_NOT_PASSED",
                "research_quorum_verified": True, "phases": phases, "receipts": receipts,
                "decision": "NOT VALIDATED — NO TRADE"}
    if client is not None:
        return await execute(client)
    async with httpx.AsyncClient(timeout=httpx.Timeout(40, connect=10), follow_redirects=False) as owned:
        return await execute(owned)

@router.get("/v1/analysts/readiness")
def readiness(authorization: str | None = Header(default=None)):
    auth(authorization)
    keys, nodes, issues = keys_and_nodes()
    return {"status": "CONFIGURATION_ONLY_NOT_LIVE_INFERENCE",
            "enabled": os.getenv("TITAN_AGENT_RESEARCH_ENABLED") == "1",
            "candidate_agents": len(nodes), "configured_unique_signers": len(keys),
            "preflight_ready": not issues, "preflight_issues": issues,
            "trade_authorized": False}

@router.post("/v1/analysts/research")
async def analyst_research(request: ResearchRequest, authorization: str | None = Header(default=None)):
    auth(authorization)
    return await run_research(request.snapshot)
