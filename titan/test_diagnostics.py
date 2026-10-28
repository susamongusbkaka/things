"""No live model calls: deterministic fail-closed smoke tests."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app
class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        self.clean=patch.dict(os.environ,{
            "TITAN_CONTROL_API_KEY":"x"*32,
            "TITAN_DIAGNOSTIC_PROBES_ENABLED":"0",
            "MISTRAL_API_KEY":"","SCW_SECRET_KEY":"",
            "DASHSCOPE_API_KEY":"","SILICONFLOW_API_KEY":"","ARK_API_KEY":""
        })
        self.clean.start()
    def tearDown(self):self.clean.stop()
    def test_no_anonymous_access(self):
        self.assertEqual(self.client.get("/v1/nodes/candidates").status_code,401)
        self.assertEqual(self.client.post("/v1/nodes/probe-ten").status_code,401)
    def test_no_authorized_probe_by_default(self):
        r=self.client.post("/v1/nodes/probe-ten",headers={"Authorization":"Bearer "+"x"*32})
        self.assertEqual(r.status_code,503)
    def test_candidate_roster_is_not_health_proof(self):
        r=self.client.get("/v1/nodes/candidates",headers={"Authorization":"Bearer "+"x"*32})
        self.assertEqual(r.status_code,200)
        d=r.json()
        self.assertEqual(len(d["nodes"]),10)
        self.assertEqual(d["verified_live_nodes"],0)
        self.assertFalse(d["consensus_valid"])
        self.assertEqual(len({n["role"] for n in d["nodes"]}),10)
        self.assertTrue(all(n["state"]=="NOT_LIVE_VERIFIED" for n in d["nodes"]))
        self.assertEqual(len({(n["provider"],n["model_candidate"]) for n in d["nodes"]}),10)
    def test_enabled_probe_without_keys_remains_blocked(self):
        os.environ["TITAN_DIAGNOSTIC_PROBES_ENABLED"]="1"
        d=self.client.post("/v1/nodes/probe-ten",headers={"Authorization":"Bearer "+"x"*32}).json()
        self.assertEqual(d["status"],"BLOCKED")
        self.assertEqual(d["observed_remote_inference"],0)
        self.assertEqual(d["signed_titan_nodes_verified"],0)
        self.assertFalse(d["consensus_valid"])
        self.assertTrue(all(n["reason"]=="CREDENTIAL_NOT_CONFIGURED" for n in d["nodes"]))
    def test_public_health_rejects_consensus(self):
        d=self.client.get("/health").json()
        self.assertEqual(d["verified_agents"],0)
        self.assertFalse(d["consensus_verified"])
if __name__=="__main__":unittest.main()
