"""TITAN read-only multi-provider diagnostic registry.
This module NEVER returns trading advice or declares signed TITAN consensus.
Provider request IDs are telemetry, not Ed25519 signer receipts.
"""
import asyncio
import hmac
import os
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Header, HTTPException

router=APIRouter()
# All providers/models are candidates; availability MUST be demonstrated by inference.
# Models and original ten canonical roles are deliberately distinct.
NODES=(
("MACRO_ANALYST","mistral","mistral-small-2603","MISTRAL_API_KEY","https://api.mistral.ai/v1","Europe"),
("SECTOR_ANALYST","scaleway","gemma-4-26b-a4b-it","SCW_SECRET_KEY","https://api.scaleway.ai/v1","France"),
("ALT_DATA_ANALYST","alibaba","qwen3.8-max","DASHSCOPE_API_KEY","https://dashscope-intl.aliyuncs.com/compatible-mode/v1","Singapore"),
("STRUCTURAL_ANALYST","scaleway","qwen3.8-27b","SCW_SECRET_KEY","https://api.scaleway.ai/v1","France"),
("QUANT_ANALYST","scaleway","deepseek-v4.1-flash","SCW_SECRET_KEY","https://api.scaleway.ai/v1","France"),
("VOLATILITY_ANALYST","scaleway","glm-5.3","SCW_SECRET_KEY","https://api.scaleway.ai/v1","France"),
("SENTIMENT_ANALYST","siliconflow","deepseek-ai/DeepSeek-V3","SILICONFLOW_API_KEY","https://api.siliconflow.cn/v1","China"),
("CROSS_ASSET_ANALYST","mistral","mistral-medium-3-5","MISTRAL_API_KEY","https://api.mistral.ai/v1","Europe"),
("SEASONAL_ANALYST","scaleway","llama-3.3-70b-instruct","SCW_SECRET_KEY","https://api.scaleway.ai/v1","France"),
("GEOPOLITICAL_ANALYST","volcengine","doubao-seed-2-1-pro-260915","ARK_API_KEY","https://ark.cn-beijing.volces.com/api/v3","China"),
)
assert len(NODES)==10 and len({n[0] for n in NODES})==10 and len({(n[1],n[2]) for n in NODES})==10
def control_auth(authorization):
    key=os.getenv("TITAN_CONTROL_API_KEY","")
    if len(key)<32:raise HTTPException(503,"OWNER_AUTH_NOT_CONFIGURED")
    if not authorization or not hmac.compare_digest(authorization,"Bearer "+key):raise HTTPException(401,"UNAUTHORIZED")
def candidates():
    return [{"role":role,"provider":p,"model_candidate":model,"hosting_region":region,
             "credentials_configured":bool(os.getenv(env)),
             "state":"NOT_LIVE_VERIFIED"} for role,p,model,env,base,region in NODES]
@router.get("/v1/nodes/candidates")
async def nodes(authorization:str|None=Header(default=None)):
    control_auth(authorization)
    return {"status":"CONFIGURATION_ONLY_NOT_A_HEALTH_CHECK","exactly_ten_candidates":len(NODES)==10,
            "verified_live_nodes":0,"consensus_valid":False,"trade_authorized":False,"nodes":candidates()}
async def probe_node(n,nonce,client,sem):
    role,p,model,env,base,region=n
    started=datetime.now(timezone.utc).isoformat()
    result={"role":role,"provider":p,"candidate_model":model,"hosting_region":region,
            "state":"BLOCKED","reason":"NOT_EXECUTED"}
    token=os.getenv(env,"")
    if not token:
        result["reason"]="CREDENTIAL_NOT_CONFIGURED";return result
    async with sem:
        try:
            prompt="Return exactly this token and nothing else: TITAN_HEALTH_"+nonce
            r=await client.post(base+"/chat/completions",headers={"Authorization":"Bearer "+token},
                json={"model":model,"messages":[{"role":"system","content":"You are participating ONLY in a diagnostic connectivity check. Never offer a financial recommendation."},{"role":"user","content":prompt}],"max_tokens":72})
            r.raise_for_status()
            d=r.json()
            content=d["choices"][0]["message"]["content"]
            rid=d.get("id")
            actual=d.get("model")
            if not isinstance(content,str) or ("TITAN_HEALTH_"+nonce) not in content or not isinstance(rid,str) or len(rid)<8 or not isinstance(actual,str) or not actual:
                raise ValueError("INFERENCE_RECEIPT_INCOMPLETE")
            if actual != model:raise ValueError("PROVIDER_RETURNED_DIFFERENT_MODEL")
            result.update({"state":"REMOTE_INFERENCE_OBSERVED","reason":None,
                         "returned_model_id":actual,"provider_request_id":rid,
                         "observed_at_utc":datetime.now(timezone.utc).isoformat(),
                         "started_at_utc":started})
        except httpx.HTTPStatusError as exc:
            result["reason"]="UPSTREAM_HTTP_"+str(exc.response.status_code)
        except (httpx.HTTPError,ValueError,KeyError,IndexError,TypeError) as exc:
            result["reason"]="PROBE_FAILED_"+type(exc).__name__
        return result
@router.post("/v1/nodes/probe-ten")
async def probe_ten(authorization:str|None=Header(default=None)):
    control_auth(authorization)
    if os.getenv("TITAN_DIAGNOSTIC_PROBES_ENABLED")!="1":
        raise HTTPException(503,"EXTERNAL_PROBING_NOT_ENABLED")
    # Fixed endpoints prevent arbitrary-URL credential exfiltration / SSRF.
    if any(urlparse(n[4]).scheme!="https" for n in NODES):
        raise HTTPException(503,"UNSAFE_PROVIDER_ENDPOINT")
    nonce=secrets.token_hex(16)
    sem=asyncio.Semaphore(4)
    async with httpx.AsyncClient(timeout=25,follow_redirects=False) as client:
        results=await asyncio.gather(*(probe_node(n,nonce,client,sem) for n in NODES))
    # Strict model-level uniqueness after inference, not merely ten API calls.
    seen=set()
    for x in results:
        if x["state"]=="REMOTE_INFERENCE_OBSERVED":
            pair=x["returned_model_id"].lower().split("/")[-1]
            if pair in seen:
                x.update({"state":"BLOCKED","reason":"DUPLICATE_ACTUAL_MODEL_ID"})
            seen.add(pair)
    good=sum(x["state"]=="REMOTE_INFERENCE_OBSERVED" for x in results)
    return {"status":"PROBE_COMPLETE_NOT_A_SIGNED_CONSENSUS" if good==10 else "BLOCKED",
        "candidate_nodes":10,"observed_remote_inference":good,"signed_titan_nodes_verified":0,
        "consensus_valid":False,"trade_authorized":False,
        "warning":"A successful provider probe is not a signed TITAN research execution.",
        "nodes":results}
