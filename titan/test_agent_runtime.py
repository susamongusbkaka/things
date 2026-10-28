"""Deterministic mock-provider tests. Passing tests does NOT mean models ran live."""
import asyncio, base64, json, os, unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from agent_runtime import NODE_BY_ROLE, REQUIRED_ROLES, PHASE_ORDER, run_research, verify_receipt
from app import app

SNAPSHOT = {"symbol":"GBP/AUD", "asset_class":"forex",
            "as_of_utc":"2026-10-28T17:00:00+00:00",
            "data":{"H4":{"close":1.89}},
            "sources":[{"name":"fixture-OHLC","as_of_utc":"2026-10-28T17:00:00+00:00"}]}

def secrets():
    env = {"TITAN_CONTROL_API_KEY":"t"*32, "TITAN_AGENT_RESEARCH_ENABLED":"1"}
    for role, provider, model, provider_env, base, region in NODE_BY_ROLE.values():
        env[provider_env] = "mock-only-not-a-provider-key"
        key = Ed25519PrivateKey.generate()
        raw = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                serialization.NoEncryption())
        env["TITAN_AGENT_SIGNING_KEY_" + role] = base64.b64encode(raw).decode()
    return env

def provider(request):
    args = json.loads(request.content)
    role = json.loads(args["messages"][-1]["content"])["role"]
    analysis = {"stance":"NEUTRAL", "confidence":0.4,
                "evidence":[{"claim":"Fixture observation only","source":"fixture-OHLC",
                             "as_of_utc":"2026-10-28T17:00:00+00:00"}],
                "risks":["Incomplete historical candles"],"invalidations":["Different live data"]}
    return httpx.Response(200, json={"id":"request-"+role.lower(),
             "model":args["model"],"choices":[{"message":{"content":json.dumps(analysis)},
                                              "finish_reason":"stop"}]})

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.p = patch.dict(os.environ, secrets(), clear=True)
        self.p.start()
        self.http = TestClient(app)
    def tearDown(self):
        self.p.stop()
    def run_mock(self, handler=provider):
        async def go():
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                return await run_research(dict(SNAPSHOT), client)
        return asyncio.run(go())

    def test_authentication_is_required(self):
        self.assertEqual(self.http.get("/v1/analysts/readiness").status_code, 401)
        self.assertEqual(self.http.post("/v1/analysts/research",json={"snapshot":SNAPSHOT}).status_code,401)
    def test_disabled_never_calls_provider(self):
        os.environ["TITAN_AGENT_RESEARCH_ENABLED"]="0"
        self.assertEqual(self.run_mock()["reason"],"RESEARCH_DISABLED")
    def test_missing_credentials_blocks_before_billing(self):
        del os.environ["MISTRAL_API_KEY"]
        self.assertEqual(self.run_mock()["reason"],"AGENT_PREFLIGHT_FAILED")
    def test_duplicate_provider_model_blocks(self):
        os.environ["TITAN_MODEL_QUANT_ANALYST"]=NODE_BY_ROLE["STRUCTURAL_ANALYST"][2]
        self.assertEqual(self.run_mock()["reason"],"AGENT_PREFLIGHT_FAILED")
    def test_signer_reuse_blocks(self):
        a,b=REQUIRED_ROLES[:2]
        os.environ["TITAN_AGENT_SIGNING_KEY_"+b]=os.environ["TITAN_AGENT_SIGNING_KEY_"+a]
        self.assertEqual(self.run_mock()["reason"],"AGENT_PREFLIGHT_FAILED")
    def test_ten_distinct_mock_transport_calls_no_trade(self):
        seen=[]
        def counted(request):
            seen.append(request)
            return provider(request)
        result=self.run_mock(counted)
        self.assertEqual(len(seen),10)
        self.assertEqual(len(result["receipts"]),10)
        self.assertTrue(result["research_quorum_verified"])
        self.assertEqual(tuple(p["phase"] for p in result["phases"]),PHASE_ORDER)
        self.assertFalse(result["trade_authorized"])
        self.assertEqual(result["orders_submitted"],0)
        self.assertEqual(result["provider_native_signatures"],0)
    def test_model_mismatch_blocks(self):
        def wrong(request):
            d=json.loads(provider(request).content)
            d["model"]="different-model"
            return httpx.Response(200,json=d)
        result=self.run_mock(wrong)
        self.assertEqual(result["reason"],"INDEPENDENT_AGENT_EXECUTION_FAILED")
        self.assertEqual(len(result["receipts"]),0)
        self.assertFalse(result["research_quorum_verified"])
    def test_signatures_reject_tampering(self):
        result=self.run_mock()
        receipt=result["receipts"][0]
        trusted=receipt["service_public_key_b64"]
        self.assertTrue(verify_receipt(receipt,trusted))
        receipt["body"]["analysis"]["stance"]="BEARISH"
        self.assertFalse(verify_receipt(receipt,trusted))
    def test_unreferenced_evidence_blocks(self):
        def invalid(request):
            d=json.loads(provider(request).content)
            content=json.loads(d["choices"][0]["message"]["content"])
            content["evidence"][0]["source"]="imaginary"
            d["choices"][0]["message"]["content"]=json.dumps(content)
            return httpx.Response(200,json=d)
        self.assertEqual(self.run_mock(invalid)["reason"],"INDEPENDENT_AGENT_EXECUTION_FAILED")

if __name__=="__main__":
    unittest.main()
