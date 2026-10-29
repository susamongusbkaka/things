"""Offline, synthetic fixtures: NEVER present these as market observations."""
import asyncio
import math
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import httpx

from proactive import scan, tsi, rsi, net_rr
from cloud_market_data import cloud_scan
from proactive_journal import record_alert, evaluate_outcome, metrics

def candles(tf_hours: float, count: int=120, drift: float=0.1, offset_hours: float=2000.0):
    end = datetime.now(timezone.utc) - timedelta(hours=offset_hours)
    start = end - timedelta(hours=tf_hours*count)
    out = []
    for i in range(count):
        c = 100 + i*drift + 0.01 * math.sin(i/5)
        out.append({"time": (start + timedelta(hours=i*tf_hours)).isoformat(),
                    "open": c-0.02, "high": c+0.1,
                    "low": c-0.1, "close": c})
    return out

def snapshot(drift=0.08):
    return {"instrument": {"name":"SYNTHETIC TEST ONLY", "symbol":"TESTONLY",
             "asset_class":"TEST", "market":"SYNTHETIC"},
            "source":"SYNTHETIC UNIT TEST — NOT MARKET DATA",
            "as_of": datetime.now(timezone.utc).isoformat(),
            "frames": {k:candles(h,drift=drift) for k,h in
                       (("D1",24),("H4",4),("H1",1),("M15",0.25))}}

class ScannerTests(unittest.TestCase):
    def test_long_short_and_fail_closed(self):
        x=scan(snapshot())
        self.assertEqual({c["direction"] for c in x["candidates"]},{"LONG","SHORT"})
        self.assertEqual(x["candidates"][0]["direction"],"LONG")
        self.assertEqual(x["candidates"][0]["baseline_ichimoku_D1_H4_H1_M15"],"ALIGNED")
        self.assertFalse(x["trade_authorized"])
        self.assertEqual(x["signed_agents_verified"],0)
        self.assertFalse(any(c["execution_eligible"] for c in x["candidates"]))

    def test_short_alignment(self):
        self.assertEqual(scan(snapshot(-0.08))["candidates"][0]["direction"],"SHORT")

    def test_incomplete_frames_remain_watch_only(self):
        x=snapshot()
        del x["frames"]["M15"]
        result=scan(x)
        self.assertIn("MISSING_M15",result["missing_core_frames"])
        self.assertFalse(result["trade_authorized"])

    def test_no_open_candle(self):
        x=snapshot()
        x["frames"]["M15"][-1]["time"]=x["as_of"]
        with self.assertRaisesRegex(ValueError,"open or future"):
            scan(x)

    def test_reject_naive_timestamps_and_bad_ohlc(self):
        x=snapshot()
        x["frames"]["H4"][-1]["time"]="2025-01-01T00:00:00"
        with self.assertRaisesRegex(ValueError,"UTC offset"):
            scan(x)
        x=snapshot()
        x["frames"]["H4"][-1]["high"]=1
        with self.assertRaisesRegex(ValueError,"invalid OHLC"):
            scan(x)

    def test_tsi_and_rsi_signs(self):
        self.assertGreater(tsi([20+i*.04 for i in range(140)]),0)
        self.assertLess(tsi([20-i*.04 for i in range(140)]),0)
        self.assertEqual(rsi([10.0]*140),50)

    def test_net_rr_exploratory_not_an_order(self):
        good=net_rr("LONG",{"entry":100,"stop":98,"tp1":106},
             {"round_trip_commission_price":.1,"round_trip_slippage_price":.1,"financing_price":0})
        self.assertTrue(good["passes_numerical_rr_only"])
        self.assertEqual(good["state"],"CALCULATED_FROM_UNVERIFIED_INPUT")
        self.assertEqual(net_rr("SHORT",{"entry":100,"stop":98,"tp1":106},{} )["state"],"UNVERIFIED")

    def test_journal_research_outcome(self):
        with tempfile.TemporaryDirectory() as folder:
            path=folder+"/journal.sqlite"
            alert={"alert_id":"test1","symbol":"TESTONLY","direction":"LONG",
                   "as_of":"2024-01-01T00:00:00+00:00","source":"SYNTHETIC ONLY",
                   "state":"EARLY WATCH","signal_close":100}
            record_alert(path,alert)
            self.assertEqual(metrics(path)["alerts_total"],1)
            future=candles(.25,count=120)
            result=evaluate_outcome(path,"test1",future,"M15",
                     datetime.now(timezone.utc).isoformat(),stop=98,tp1=106)
            self.assertEqual(result["state"],"RESEARCH_OBSERVATION_ONLY")
            self.assertIn(result["barrier_event"],{"TP1_FIRST_BAR","STOP_FIRST_BAR","AMBIGUOUS_SAME_BAR","NEITHER"})
            self.assertFalse(result["fill_verified"])
            self.assertEqual(metrics(path)["evaluated"],1)

class CloudVendorTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_key_does_not_call_internet(self):
        with patch.dict(os.environ,{"TITAN_TWELVEDATA_API_KEY":""}):
            x=await cloud_scan(["EUR/USD"])
        self.assertEqual(x["reason"],"EXTERNAL_FEED_KEY_NOT_CONFIGURED")
        self.assertFalse(x["trade_authorized"])

    async def test_reject_invalid_and_duplicate_symbols(self):
        with self.assertRaises(ValueError):
            await cloud_scan(["EUR/USD","eur/usd"])
        with self.assertRaises(ValueError):
            await cloud_scan(["https://bad.host/"])
        with self.assertRaises(ValueError):
            await cloud_scan(["A","B","C"])

    async def test_mock_vendor_populates_all_four_frames(self):
        # MockTransport returns SYNTHETIC fixtures without external requests.
        import urllib.parse
        intervals={"1day":24,"4h":4,"1h":1,"15min":0.25}
        def respond(req):
            qs=urllib.parse.parse_qs(req.url.query.decode())
            interval=qs["interval"][0]
            h=intervals[interval]
            source=candles(h,count=130,offset_hours=48 if h==24 else 8)
            values=[{"datetime":datetime.fromisoformat(b["time"]).strftime("%Y-%m-%d" if h==24 else "%Y-%m-%d %H:%M:%S"),
                     **{k:str(b[k]) for k in ("open","high","low","close")}} for b in source]
            return httpx.Response(200,json={"status":"ok","meta":{"symbol":"EUR/USD",
                    "interval":interval,"exchange_timezone":"UTC",
                    "exchange":"FOREX","type":"Physical Currency"},
                    "values":list(reversed(values))})
        transport=httpx.MockTransport(respond)
        with patch.dict(os.environ,{"TITAN_TWELVEDATA_API_KEY":"SYNTHETIC_TEST_KEY"}):
            async with httpx.AsyncClient(transport=transport) as client:
                res=await cloud_scan(["EUR/USD"],client=client)
        instrument=res["instruments"][0]
        self.assertEqual(instrument["instrument"]["symbol"],"EUR/USD")
        self.assertEqual(len(instrument["frame_features"]),4)
        self.assertFalse(instrument["trade_authorized"])
        self.assertFalse(res["trade_authorized"])

    async def test_mismatch_blocks_without_assumed_symbol(self):
        def respond(req):
            return httpx.Response(200,json={"status":"ok","meta":{"symbol":"GBP/USD",
               "interval":"4h"},"values":[]})
        with patch.dict(os.environ,{"TITAN_TWELVEDATA_API_KEY":"TEST_KEY"}):
            async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
                res=await cloud_scan(["EUR/USD"],client=client)
        self.assertEqual(res["instruments"][0]["status"],"NOT_VALIDATED_NO_TRADE")

if __name__=="__main__":
    unittest.main()
