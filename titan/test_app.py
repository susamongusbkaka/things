import os,unittest
from fastapi.testclient import TestClient
from app import app,PROVIDERS
class FailClosedTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        for k in ("TITAN_CONTROL_API_KEY","TITAN_BRIDGE_API_KEY","TITAN_SIGNED_GATEWAY_URL","MISTRAL_API_KEY","SCW_SECRET_KEY","QWEN_SINGAPORE_API_KEY","DEEPSEEK_API_KEY","TITAN_QWEN_MODEL","TITAN_DEEPSEEK_MODEL"):os.environ.pop(k,None)
    def test_health_is_blocked(self):
        d=self.client.get("/health").json();self.assertEqual(d["status"],"BLOCKED");self.assertFalse(d["consensus_verified"])
    def test_unauthorized(self):self.assertEqual(self.client.post("/v1/research",json={"snapshot":{"x":1}}).status_code,503)
    def test_auth_reject(self):
        os.environ["TITAN_CONTROL_API_KEY"]="x"*32
        self.assertEqual(self.client.post("/v1/research",json={"snapshot":{"x":1}},headers={"Authorization":"Bearer fake"}).status_code,401)
    def test_missing_gateway(self):
        os.environ["TITAN_CONTROL_API_KEY"]="x"*32
        self.assertEqual(self.client.post("/v1/research",json={"snapshot":{"x":1}},headers={"Authorization":"Bearer "+"x"*32}).status_code,503)
    def test_probe_missing_keys(self):
        os.environ["TITAN_CONTROL_API_KEY"]="x"*32
        d=self.client.post("/v1/provider-probe",json={"provider":"mistral"},headers={"Authorization":"Bearer "+"x"*32}).json()
        self.assertEqual(d["status"],"BLOCKED")
    def test_chinese_registry_pinned(self):
        self.assertEqual(PROVIDERS["qwen_singapore"][0],"https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
        self.assertEqual(PROVIDERS["deepseek"][0],"https://api.deepseek.com/v1")
    def test_qwen_without_credentials_blocked(self):
        os.environ["TITAN_CONTROL_API_KEY"]="x"*32
        result=self.client.post("/v1/provider-probe",json={"provider":"qwen_singapore"},headers={"Authorization":"Bearer "+"x"*32}).json()
        self.assertEqual(result["status"],"BLOCKED")
        self.assertEqual(result["verified_runs"],0)
    def test_deepseek_without_credentials_blocked(self):
        os.environ["TITAN_CONTROL_API_KEY"]="x"*32
        result=self.client.post("/v1/provider-probe",json={"provider":"deepseek"},headers={"Authorization":"Bearer "+"x"*32}).json()
        self.assertEqual(result["status"],"BLOCKED")
        self.assertEqual(result["verified_runs"],0)
    def test_no_unknown_providers(self):
        os.environ["TITAN_CONTROL_API_KEY"]="x"*32
        self.assertEqual(self.client.post("/v1/provider-probe",json={"provider":"unknown"},headers={"Authorization":"Bearer "+"x"*32}).status_code,422)
if __name__=="__main__":unittest.main()
