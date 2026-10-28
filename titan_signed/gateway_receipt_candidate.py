from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import hmac, json, os, hashlib
import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app=FastAPI(title="TITAN International Model Conduit",docs_url=None,redoc_url=None)
ROLES={"STRUCTURAL_ANALYST":.18,"QUANT_ANALYST":.14,"MACRO_ANALYST":.13,
"SENTIMENT_ANALYST":.11,"CROSS_ASSET_ANALYST":.10,"SECTOR_ANALYST":.10,
"VOLATILITY_ANALYST":.08,"SEASONAL_ANALYST":.06,
"GEOPOLITICAL_ANALYST":.05,"ALT_DATA_ANALYST":.05}
PHASES=[
("PHASE_1_FUNDAMENTAL_SWEEP",["MACRO_ANALYST","SECTOR_ANALYST","ALT_DATA_ANALYST"]),
("PHASE_2_TECHNICAL_SWEEP",["STRUCTURAL_ANALYST","QUANT_ANALYST","VOLATILITY_ANALYST"]),
("PHASE_3_SENTIMENT_MACRO_SWEEP",["SENTIMENT_ANALYST","CROSS_ASSET_ANALYST","SEASONAL_ANALYST","GEOPOLITICAL_ANALYST"])]
PROVIDERS={
"MISTRAL":("https://api.mistral.ai/v1","mistral-small-latest","MISTRAL_API_KEY"),
"SCW_QWEN":("https://api.scaleway.ai/v1","qwen3-235b-a22b-instruct-2507","SCW_SECRET_KEY"),
"SCW_DEEPSEEK":("https://api.scaleway.ai/v1","deepseek-v4-flash-0731","SCW_SECRET_KEY"),
"SCW_GLM_CRITIC":("https://api.scaleway.ai/v1","glm-5.3","SCW_SECRET_KEY")
}
ASSIGN={r:("MISTRAL" if r in ["MACRO_ANALYST","SENTIMENT_ANALYST","SECTOR_ANALYST","GEOPOLITICAL_ANALYST"] else "SCW_DEEPSEEK" if r in ["QUANT_ANALYST","VOLATILITY_ANALYST"] else "SCW_QWEN") for r in ROLES}
def auth(header):
    key=os.getenv("TITAN_BRIDGE_API_KEY","")
    if len(key)<24: raise HTTPException(503,"AUTH_NOT_CONFIGURED")
    if not header or not hmac.compare_digest(header,"Bearer "+key):
        raise HTTPException(401,"UNAUTHORIZED")
def configured(p):
    return bool(os.getenv(PROVIDERS[p][2]))
def call(p,role,payload):
    base,model,env=PROVIDERS[p]
    key=os.getenv(env,"")
    if not key: raise RuntimeError("MODEL_NOT_CONFIGURED:"+p)
    started=datetime.now(timezone.utc).isoformat()
    body={"model":model,"messages":[
        {"role":"system","content":"Independent financial researcher. Use input evidence only. No invented prices. Return ONLY a JSON object: score (-3 to 3), stance (BULLISH,BEARISH,NEUTRAL,UNDETERMINED), evidence (list of supplied source identifiers), uncertainty (string). No trading signals."},
        {"role":"user","content":json.dumps({"role":role,**payload},ensure_ascii=False)}],
        "temperature":0,"max_tokens":550,"response_format":{"type":"json_object"}}
    with httpx.Client(timeout=40,follow_redirects=False) as c:
        resp=c.post(base+"/chat/completions",headers={"Authorization":"Bearer "+key},json=body)
        resp.raise_for_status()
        result=resp.json()
    reply=result["choices"][0]["message"]["content"]
    parsed=json.loads(reply)
    if not isinstance(parsed,dict) or not isinstance(parsed.get("score"),(int,float)) or isinstance(parsed["score"],bool) or not -3<=parsed["score"]<=3 or parsed.get("stance") not in {"BULLISH","BEARISH","NEUTRAL","UNDETERMINED"} or not isinstance(parsed.get("evidence"),list) or not parsed["evidence"]:
        raise RuntimeError("UNVERIFIABLE_INFERENCE")
    if not result.get("id"): raise RuntimeError("NO_PROVIDER_EXECUTION_ID")
    return {"role":role,"provider":p,"model":str(result.get("model",model)),
        "provider_request_id":result["id"],"started_utc":started,
        "finished_utc":datetime.now(timezone.utc).isoformat(),
        "digest":hashlib.sha256(reply.encode()).hexdigest(),"result":parsed}
class Probe(BaseModel):
    provider:str=Field(min_length=3,max_length=30)
    ticker:str=Field(min_length=3,max_length=30)
    as_of_utc:str
    supplied_research:str=Field(min_length=30,max_length=5000)
class Research(BaseModel):
    ticker:str=Field(min_length=3,max_length=30)
    as_of_utc:str
    sources:list[dict[str,Any]]=Field(min_length=1)
    candles_by_timeframe:dict[str,list[dict[str,Any]]]=Field(default_factory=dict)
    portfolio:dict[str,Any]|None=None
    proposed_trade:dict[str,Any]|None=None
@app.get("/health")
def health():
    return {"service":"TITAN Signed Research Conduit v3 staging","utc":datetime.now(timezone.utc).isoformat(),
            "bridge_auth_configured":len(os.getenv("TITAN_BRIDGE_API_KEY",""))>=24,
            "provider_configuration":{p:configured(p) for p in PROVIDERS},
            "independent_inference_verified_in_this_request":False,
            "full_numeric_committee_deployed":False,"orders_enabled":False,
            "trade_authorization":"BLOCKED"}
@app.post("/v1/model-probe")
def model_probe(x:Probe,authorization:str|None=Header(default=None)):
    auth(authorization)
    if x.provider not in PROVIDERS:
        raise HTTPException(422,"UNKNOWN_PROVIDER")
    try:
        asof=datetime.fromisoformat(x.as_of_utc.replace("Z","+00:00"))
        if asof.utcoffset() is None or asof.astimezone(timezone.utc)>datetime.now(timezone.utc): raise ValueError()
    except ValueError: raise HTTPException(422,"INVALID_AS_OF")
    try:
        receipt=call(x.provider,"CONNECTION_PROBE",{"ticker":x.ticker,"as_of_utc":x.as_of_utc,
                                                    "evidence":["user_supplied_research"],
                                                    "research":x.supplied_research})
        return {"status":"EXTERNAL_INFERENCE_RETURNED","verified_external_model_runs":1,
                "receipt":receipt,"trade_authorized":False}
    except Exception as exc:
        return {"status":"NO_VALIDATED_TRADE","reason":"MODEL_PROBE_FAILED:"+type(exc).__name__,
                "verified_external_model_runs":0,"trade_authorized":False}
@app.post("/v1/run-all")
def run_all(x:Research,authorization:str|None=Header(default=None)):
    auth(authorization)
    # The full existing numerical-forecast signature-verification and strict
    # consensus implementation is in the separately tested TITAN codebase.
    # This initial hosted conduit must NOT bypass it or authorise a trade.
    if not all(configured(p) for p in PROVIDERS):
        return {"status":"NO_VALIDATED_TRADE","reason":"ONE_OR_MORE_PROVIDERS_NOT_CONFIGURED",
                "completed_phases":[],"verified_external_model_runs":0,"trade_authorized":False}
    try:
        asof=datetime.fromisoformat(x.as_of_utc.replace("Z","+00:00"))
        if asof.utcoffset() is None or asof.astimezone(timezone.utc)>datetime.now(timezone.utc):
            raise ValueError()
        if not x.candles_by_timeframe: raise ValueError()
    except ValueError:
        return {"status":"NO_VALIDATED_TRADE","reason":"DATA_OR_CUTOFF_MISSING",
                "completed_phases":[],"verified_external_model_runs":0,"trade_authorized":False}
    trail={}
    cutoff={"ticker":x.ticker,"as_of_utc":x.as_of_utc,
            "sources":x.sources,"candles_by_timeframe":x.candles_by_timeframe}
    n=0
    try:
        for phase,roles in PHASES:
            trail[phase]={}
            for role in roles:
                trail[phase][role]=call(ASSIGN[role],role,cutoff)
                n+=1
        # Adversarial reviewer requires separately configured model, not the
        # same default Mistral or Scaleway model.
        critic=os.getenv("TITAN_CRITIC_PROVIDER","SCW_GLM_CRITIC")
        if critic not in PROVIDERS:
            raise RuntimeError("INDEPENDENT_CRITIC_NOT_CONFIGURED")
        reviewer_model=PROVIDERS[critic][1]
        if reviewer_model in {v["model"] for phase in trail.values() for v in phase.values()}:
            raise RuntimeError("CRITIC_NOT_INDEPENDENT_MODEL")
        trail["PHASE_4_DEVILS_ADVOCATE_VALIDATION"]=call(critic,"DEVILS_ADVOCATE",
                   {"ticker":x.ticker,"agent_evidence":trail,"proposal":x.proposed_trade})
        n+=1
        # The numerical forecasting committee and risk/portfolio gates must
        # execute in the complete TITAN runtime. Do not simulate completion.
        return {"status":"NO_VALIDATED_TRADE",
                "reason":"AWAITING_SIGNED_NUMERIC_FORECAST_COMMITTEE_AND_RISK_GATE",
                "verified_role_executions":n,
                "completed_phases":[*trail,"PHASE_5_RISK_GATE_PENDING",
                                         "PHASE_6_CIO_CONSENSUS_FUSION_PENDING"],
                "audit":trail,"trade_authorized":False}
    except Exception as exc:
        return {"status":"NO_VALIDATED_TRADE",
                "reason":"MODEL_OR_ADVOCATE_FAILED:"+type(exc).__name__,
                "verified_role_executions_before_failure":n,
                "completed_phases":list(trail),
                "trade_authorized":False}


# Signed external-agent runner; no order-placement functionality.
import base64, secrets, math
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from urllib.parse import urlparse
class SignedInput(BaseModel):
    snapshot: dict[str,Any]
def compact(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sh(x): return hashlib.sha256(compact(x)).hexdigest()
def load_manifest():
    raw=os.getenv("TITAN_APPROVED_MANIFEST_JSON","")
    pin=os.getenv("TITAN_APPROVED_MANIFEST_SHA256","").lower()
    if not raw or not pin or hashlib.sha256(raw.encode()).hexdigest()!=pin:raise ValueError("MANIFEST_NOT_APPROVED")
    m=json.loads(raw)
    if m.get("canonical_roles_verified") is not True:raise ValueError("ORIGINAL_ROSTER_NOT_CERTIFIED")
    rs=m.get("agents",[])
    if len(rs)!=10 or set(r["role"] for r in rs)!=set(ROLES):raise ValueError("NOT_EXACT_TEN")
    wanted={"MACRO_ANALYST":"FUNDAMENTAL","SECTOR_ANALYST":"FUNDAMENTAL","ALT_DATA_ANALYST":"FUNDAMENTAL",
      "STRUCTURAL_ANALYST":"TECHNICAL","QUANT_ANALYST":"TECHNICAL","VOLATILITY_ANALYST":"TECHNICAL",
      "SENTIMENT_ANALYST":"SENTIMENT_MACRO","CROSS_ASSET_ANALYST":"SENTIMENT_MACRO",
      "SEASONAL_ANALYST":"SENTIMENT_MACRO","GEOPOLITICAL_ANALYST":"SENTIMENT_MACRO"}
    for r in rs:
        if r.get("phase")!=wanted[r["role"]]:raise ValueError("ROLE_PHASE_MISMATCH")
    nums=m.get("numerical_committee",[])
    if len(nums)<2:raise ValueError("NUMERIC_COMMITTEE_MISSING")
    extra=[m.get("critic"),*nums,m.get("risk_validator"),m.get("cio")]
    if any(not isinstance(x,dict) for x in extra):raise ValueError("REQUIRED_REVIEWERS_MISSING")
    if [extra[0]["role"],extra[-2]["role"],extra[-1]["role"]]!=["DEVILS_ADVOCATE","RISK_VALIDATOR","CIO_REVIEW"]:
        raise ValueError("REVIEW_ROLE_MISMATCH")
    seen_keys=set();seen_urls=set()
    for r in rs+extra:
        for k in ("role","phase","endpoint","credential_env","model_provider","model_id","public_key_b64"):
            if not r.get(k):raise ValueError("AGENT_INCOMPLETE")
        p=urlparse(r["endpoint"])
        if p.scheme!="https" or not p.hostname or p.username or p.password:raise ValueError("UNSAFE_ENDPOINT")
        if len(base64.b64decode(r["public_key_b64"],validate=True))!=32:raise ValueError("INVALID_SIGNING_KEY")
        if r["public_key_b64"] in seen_keys or r["endpoint"] in seen_urls:raise ValueError("NONINDEPENDENT_SIGNER")
        seen_keys.add(r["public_key_b64"]);seen_urls.add(r["endpoint"])
    research_models={(x["model_provider"],x["model_id"]) for x in rs}
    if (extra[0]["model_provider"],extra[0]["model_id"]) in research_models:raise ValueError("CRITIC_IS_NOT_DISTINCT")
    return m,wanted
def signed_remote(s,snapshot,trail,seen):
    token=os.getenv(s["credential_env"],"")
    if not token:raise ValueError("AGENT_KEY_MISSING")
    nonce=secrets.token_hex(24)
    body={"role":s["role"],"phase":s["phase"],"nonce":nonce,
          "as_of_utc":datetime.now(timezone.utc).isoformat(),
          "snapshot":snapshot,"prior_sha256":sh(trail)}
    request={"request":body,"input_sha256":sh(body)}
    with httpx.Client(timeout=30,follow_redirects=False) as c:
        r=c.post(s["endpoint"],json=request,headers={"Authorization":"Bearer "+token})
        r.raise_for_status();x=r.json()
    rec=x["receipt"];out=x["output"]
    pk=Ed25519PublicKey.from_public_bytes(base64.b64decode(s["public_key_b64"],validate=True))
    pk.verify(base64.b64decode(x["signature_b64"],validate=True),compact({"receipt":rec,"output":out}))
    expected={"role":s["role"],"phase":s["phase"],"model_provider":s["model_provider"],
      "model_id":s["model_id"],"request_nonce":nonce,"input_sha256":request["input_sha256"],
      "output_sha256":sh(out),"actual_inference_executed":True,"execution_environment":"REMOTE","status":"SUCCESS"}
    if any(rec.get(k)!=v for k,v in expected.items()):raise ValueError("RECEIPT_MISMATCH")
    for k in ("run_id","provider_request_id","code_version"):
        if len(str(rec.get(k,"")))<8:raise ValueError("MISSING_EXECUTION_ID")
    unique=(rec["run_id"],rec["provider_request_id"])
    if unique in seen:raise ValueError("REPLAY")
    seen.add(unique)
    started=datetime.fromisoformat(rec["started_at_utc"].replace("Z","+00:00"))
    ended=datetime.fromisoformat(rec["finished_at_utc"].replace("Z","+00:00"))
    age=(datetime.now(timezone.utc)-ended).total_seconds()
    if started.utcoffset()!=timezone.utc.utcoffset(started) or ended.utcoffset()!=timezone.utc.utcoffset(ended):
        raise ValueError("NON_UTC_RECEIPT")
    if ended<started or (ended-started).total_seconds()>120 or not -10<=age<=300:
        raise ValueError("INVALID_RECEIPT_CLOCK")
    return {"role":s["role"],"phase":s["phase"],"provider_id":rec["provider_request_id"],
            "digest":sh(out),"output":out,
            "signed_envelope":{"receipt":rec,"output":out,"signature_b64":x["signature_b64"]}}
def frozen_veto(s):
    v=[]
    for k in ("original_strategy_gates_passed","all_mandatory_timeframes_confirmed",
              "broker_bid_ask_verified","macro_event_clear","spread_slippage_swap_checked","one_trade_limit_clear"):
        if s.get(k) is not True:v.append("FAILED_"+k.upper())
    r=s.get("net_reward_risk_ratio")
    if isinstance(r,bool) or not isinstance(r,(int,float)) or not math.isfinite(r) or r<2.5:v.append("NET_RR_NOT_VERIFIED")
    if not s.get("symbol") or not s.get("market_data_provenance"):v.append("MARKET_DATA_UNVERIFIED")
    try:
        t=datetime.fromisoformat(s["as_of_utc"].replace("Z","+00:00"))
        if t.utcoffset()!=timezone.utc.utcoffset(t) or not -10 <= (datetime.now(timezone.utc)-t).total_seconds() <= 86400:
            v.append("STALE_OR_NON_UTC_DATA")
    except Exception:v.append("DATA_TIME_NOT_VERIFIED")
    return v
@app.post("/v1/run-signed")
def run_signed(x:SignedInput,authorization:str|None=Header(default=None)):
    auth(authorization)
    state={"status":"BLOCKED","trade_authorized":False,"research_signatures":0,"other_signatures":0,
           "completed_phases":[],"reason":"UNKNOWN"}
    try:m,roles=load_manifest()
    except Exception as e:state["reason"]="MANIFEST_"+str(e)[:100];return state
    snapshot=x.snapshot;seen=set();trail=[]
    try:
        for phase,role_names in (("FUNDAMENTAL",["MACRO_ANALYST","SECTOR_ANALYST","ALT_DATA_ANALYST"]),
            ("TECHNICAL",["STRUCTURAL_ANALYST","QUANT_ANALYST","VOLATILITY_ANALYST"]),
            ("SENTIMENT_MACRO",["SENTIMENT_ANALYST","CROSS_ASSET_ANALYST","SEASONAL_ANALYST","GEOPOLITICAL_ANALYST"])):
            for role in role_names:
                spec=next(r for r in m["agents"] if r["role"]==role)
                trail.append(signed_remote(spec,snapshot,trail,seen));state["research_signatures"]+=1
            state["completed_phases"].append(phase)
        trail.append(signed_remote(m["critic"],snapshot,trail,seen))
        state["other_signatures"]+=1;state["completed_phases"].append("DEVILS_ADVOCATE")
        for n in m["numerical_committee"]:
            trail.append(signed_remote(n,snapshot,trail,seen));state["other_signatures"]+=1
        risk=signed_remote(m["risk_validator"],snapshot,trail,seen)
        state["other_signatures"]+=1;trail.append(risk)
        veto=frozen_veto(snapshot)
        if risk["output"].get("verified") is not True or risk["output"].get("decision")!="PASS":
            veto.append("INDEPENDENT_RISK_VETO")
        if veto:state["reason"]="RISK_VETO:"+",".join(veto);return state
        state["completed_phases"].append("RISK")
        cio=signed_remote(m["cio"],snapshot,trail,seen)
        state["other_signatures"]+=1;state["completed_phases"].append("CIO_CONSENSUS")
        if cio["output"].get("decision")!="APPROVE_RESEARCH_ONLY":
            state["reason"]="CIO_VETO";return state
        if len(compact(trail))>1024*1024:
            state["reason"]="RECEIPT_ENVELOPE_TOO_LARGE";return state
        state["signed_receipts"]=trail
        state["approved_manifest_sha256"]=os.getenv("TITAN_APPROVED_MANIFEST_SHA256","")
        state["status"]="RESEARCH_COMPLETE_MANUAL_ONLY";state["reason"]="NO_BROKER_ORDER_CAPABILITY"
        return state
    except Exception as e:
        state["reason"]="REMOTE_AGENT_FAILED:"+type(e).__name__+":"+str(e)[:100]
        return state
