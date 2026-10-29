"""TITAN approved cloud bridge. No trading; fail closed if independent receipts absent."""
import hmac,os
from datetime import datetime,timezone
from urllib.parse import urlparse
from typing import Any
import httpx
from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel,Field
app=FastAPI(title="TITAN Cloud Bridge",docs_url=None,redoc_url=None,openapi_url=None)
# Verified from original-language provider documentation on 2026-10-28.
# Adding providers does not assert credentials or successful inference.
# Chinese providers use independent provider accounts: never equate these
# to Scaleway-hosted models or to ten independently executed TITAN agents.
PROVIDERS={
    "mistral":("https://api.mistral.ai/v1","MISTRAL_API_KEY","TITAN_MISTRAL_MODEL"),
    "scaleway":("https://api.scaleway.ai/v1","SCW_SECRET_KEY","TITAN_SCW_MODEL"),
    "qwen_singapore":("https://dashscope-intl.aliyuncs.com/compatible-mode/v1","QWEN_SINGAPORE_API_KEY","TITAN_QWEN_MODEL"),
    "deepseek":("https://api.deepseek.com/v1","DEEPSEEK_API_KEY","TITAN_DEEPSEEK_MODEL")
}
def authenticate(auth):
    key=os.getenv("TITAN_CONTROL_API_KEY","")
    if len(key)<32:raise HTTPException(503,"OWNER_AUTH_NOT_CONFIGURED")
    if auth is None or not hmac.compare_digest(auth,"Bearer "+key):raise HTTPException(401,"UNAUTHORIZED")
def upstream_url():
    url=os.getenv("TITAN_SIGNED_GATEWAY_URL","").rstrip("/")
    p=urlparse(url)
    pin=os.getenv("TITAN_GATEWAY_HOST_PIN","titan-signed-agent-runtime-staging.onrender.com")
    if p.scheme!="https" or not p.hostname or p.hostname!=pin or p.username or p.password or p.query or p.fragment or p.path:raise HTTPException(503,"GATEWAY_UNPINNED_OR_UNSAFE")
    return url
@app.get("/health")
def health():
    return {"service":"TITAN approved Render-Scaleway-Mistral bridge","utc":datetime.now(timezone.utc).isoformat(),"owner_auth_configured":len(os.getenv("TITAN_CONTROL_API_KEY",""))>=32,"gateway_configured":bool(os.getenv("TITAN_SIGNED_GATEWAY_URL")) and bool(os.getenv("TITAN_BRIDGE_API_KEY")),"providers_configured":{k:bool(os.getenv(v[1])) and bool(os.getenv(v[2])) for k,v in PROVIDERS.items()},"verified_agents":0,"consensus_verified":False,"status":"BLOCKED","trade_authorized":False,"replit_used":False}
class Probe(BaseModel):
    provider:str
    challenge:str=Field(default="Reply with TITAN_PROBE only. This is not financial research.",min_length=20,max_length=200)
@app.post("/v1/provider-probe")
async def probe(x:Probe,authorization:str|None=Header(default=None)):
    authenticate(authorization)
    if x.provider not in PROVIDERS:raise HTTPException(422,"UNAPPROVED_PROVIDER")
    base,key_name,model_name=PROVIDERS[x.provider]
    key,model=os.getenv(key_name,""),os.getenv(model_name,"")
    if not key or not model:return {"status":"BLOCKED","reason":"PROVIDER_NOT_CONFIGURED","verified_runs":0}
    try:
        async with httpx.AsyncClient(timeout=30,follow_redirects=False) as c:
            r=await c.post(base+"/chat/completions",headers={"Authorization":"Bearer "+key},json={"model":model,"messages":[{"role":"user","content":x.challenge}],"max_tokens":64})
        r.raise_for_status()
        d=r.json();msg=d["choices"][0]["message"]["content"]
        if not d.get("id") or not d.get("model") or not msg or d["model"]!=model:raise ValueError("UNVERIFIED_MODEL_RESPONSE")
        return {"status":"EXTERNAL_PROBE_RETURNED","provider":x.provider,"model":model,"request_id":d["id"],"verified_probe_runs":1,"consensus_verified":False,"trade_authorized":False}
    except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError) as exc:return {"status":"BLOCKED","reason":"PROVIDER_FAILED:"+type(exc).__name__,"verified_probe_runs":0}
class Research(BaseModel):
    snapshot:dict[str,Any]=Field(min_length=1)
@app.post("/v1/research")
async def research(x:Research,authorization:str|None=Header(default=None)):
    authenticate(authorization)
    url=upstream_url();key=os.getenv("TITAN_BRIDGE_API_KEY","")
    if len(key)<24:raise HTTPException(503,"UPSTREAM_AUTH_NOT_CONFIGURED")
    try:
        async with httpx.AsyncClient(timeout=150,follow_redirects=False) as c:
            r=await c.post(url+"/v1/run-signed",headers={"Authorization":"Bearer "+key},json={"snapshot":x.snapshot})
        r.raise_for_status();d=r.json()
    except (httpx.HTTPError,ValueError,TypeError):return {"status":"BLOCKED","reason":"SIGNED_GATEWAY_UNAVAILABLE","verified_nodes":0,"trade_authorized":False}
    if d.get("status")=="RESEARCH_COMPLETE_MANUAL_ONLY":return {"status":"BLOCKED","reason":"RAW_SIGNED_RECEIPTS_NOT_EXPOSED","reported_signatures":d.get("research_signatures",0),"verified_nodes":0,"trade_authorized":False}
    return {"status":"BLOCKED","reason":"SIGNED_GATEWAY:"+str(d.get("reason","NO_VERIFIED_RESULT"))[:180],"verified_nodes":0,"trade_authorized":False}

# Read-only probe registry: no trading or research authorization.
from diagnostics import router as diagnostic_router
app.include_router(diagnostic_router)

# Cloud-first read-only research watchlist; never sends orders.
from proactive_routes import router as proactive_router
app.include_router(proactive_router)
