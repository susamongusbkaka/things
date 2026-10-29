"""Synthetic inputs validate software invariants, not market profitability."""
import os
import unittest
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pace_mtf import evaluate, cloud_direction, precursor, router


T = datetime(2025,7,11,20,tzinfo=timezone.utc)

def bars(n=125,period=timedelta(days=1),start=None,trend=0.0):
    start = start or T-period*n
    out=[]
    for i in range(n):
        p=100+i*trend
        out.append({"closed_at_utc":(start+period*i).isoformat(),
                    "closed":True,"open":p,"high":p+1,"low":p-1,"close":p})
    return out

def snapshot(with_mtf=False):
    d={"D1":bars()}
    if with_mtf:
        for f,period in [("H4",timedelta(hours=4)),("H1",timedelta(hours=1)),("M15",timedelta(minutes=15))]:
            d[f]=bars(125,period,start=T-period*125)
    return {"symbol":"EURUSD","asset_class":"forex","source":"unit-test synthetic",
            "as_of_utc":T.isoformat(),"source_observed_at_utc":T.isoformat(),"bars":d}

class PaceInvariants(unittest.TestCase):
    def test_no_trade_even_with_four_timeframes(self):
        x=evaluate(snapshot(True),now=T)
        self.assertEqual(x["status"],"RESEARCH_ONLY_NOT_VALIDATED")
        self.assertFalse(x["trade_authorized"])
        self.assertEqual(x["orders_submitted"],0)
        self.assertEqual(x["stage"],"CLOUD_NEUTRAL")
    def test_missing_mtf_exposed(self):
        x=evaluate(snapshot(),now=T)
        self.assertEqual(x["missing_timeframes"],["H4","H1","M15"])
        self.assertFalse(x["research_confluence_observed"])
    def test_future_candle_fails_closed(self):
        d=snapshot();d["bars"]["D1"][-1]["closed_at_utc"]=(T+timedelta(minutes=1)).isoformat()
        self.assertEqual(evaluate(d,now=T)["status"],"BLOCKED")
    def test_unclosed_bar_fails_closed(self):
        d=snapshot();d["bars"]["D1"][-1]["closed"]=False
        self.assertEqual(evaluate(d,now=T)["reason"],"UNCONFIRMED_CANDLE")
    def test_price_integrity(self):
        d=snapshot();d["bars"]["D1"][-1]["high"]=90
        self.assertEqual(evaluate(d,now=T)["reason"],"INCONSISTENT_OHLC")
    def test_nonfinite_not_accepted(self):
        d=snapshot();d["bars"]["D1"][-1]["close"]=float("nan")
        self.assertEqual(evaluate(d,now=T)["status"],"BLOCKED")
    def test_missing_provenance_rejected(self):
        d=snapshot();d["source"]=""
        self.assertEqual(evaluate(d,now=T)["reason"],"SOURCE_PROVENANCE_REQUIRED")
    def test_independent_claims_not_scored(self):
        d=snapshot();d["independent_context"]=[{"kind":"ECN_order_flow","value":"buy"}]
        x=evaluate(d,now=T)
        self.assertEqual(x["independent_context_status"],"UNAUTHENTICATED_AND_NOT_SCORED")
        self.assertFalse(x["independent_data_verified"])
    def test_cloud_no_lookahead(self):
        d=snapshot(True);b=[]
        for x in d["bars"]["D1"]:
            b.append({"t":datetime.fromisoformat(x["closed_at_utc"]),"o":x["open"],"h":x["high"],"l":x["low"],"c":x["close"]})
        self.assertEqual(cloud_direction(b,110),cloud_direction(b[:111],110))
        self.assertEqual(precursor(b,110,1),precursor(b[:111],110,1))
    def test_unauthenticated_endpoint_fails(self):
        a=FastAPI();a.include_router(router);client=TestClient(a)
        old=os.environ.pop("TITAN_CONTROL_API_KEY",None)
        try:
            self.assertEqual(client.post("/v1/anticipation/evaluate",json={"snapshot":snapshot()}).status_code,503)
            os.environ["TITAN_CONTROL_API_KEY"]="x"*32
            self.assertEqual(client.post("/v1/anticipation/evaluate",json={"snapshot":snapshot()}).status_code,401)
            y=client.post("/v1/anticipation/evaluate",json={"snapshot":snapshot()},headers={"Authorization":"Bearer "+"x"*32})
            self.assertEqual(y.status_code,200)
            self.assertFalse(y.json()["trade_authorized"])
        finally:
            if old is None:os.environ.pop("TITAN_CONTROL_API_KEY",None)
            else:os.environ["TITAN_CONTROL_API_KEY"]=old
    def test_instant_outcome_invariant(self):
        self.assertEqual(evaluate(snapshot(),now=T)["decision"],"NOT VALIDATED — NO TRADE")



# A hand-constructed price path is used ONLY to verify state transitions.
# It is not offered as historical evidence of trading profitability.
def constructed_signal(final_breakout=True, include_mtf=True, conflict=False):
    start=T-timedelta(days=131)
    d=[]
    for i in range(131):
        if i<65:
            c=100+(.2 if i%2 else -.2); high=c+2; low=c-2
        elif i<104:
            c=105+(.1 if i%2 else -.1); high=c+1.2; low=c-1.2
        else:
            c=110.1; high=110.5; low=109.7
        if i==130 and final_breakout:
            c=112.0;high=112.2;low=109.7
        d.append({"closed_at_utc":(start+timedelta(days=i)).isoformat(),
                  "closed":True,"open":c-.1 if i==130 and final_breakout else c,
                  "high":high,"low":low,"close":c})
    snap=snapshot(include_mtf)
    snap["bars"]["D1"]=d
    if include_mtf:
        for f in ("H4","H1","M15"):
            z=snap["bars"][f]; n=len(z)
            for i,bar in enumerate(z):
                # Trend delta after 26-bar displacement forces a cloud regime.
                p=100+(n-i if conflict and f=="H4" else i)*.04
                bar.update({"open":p,"high":p+.4,"low":p-.4,"close":p})
    return snap

class StateTransitions(unittest.TestCase):
    def test_compression_before_acceptance(self):
        d=constructed_signal(False,False)
        x=evaluate(d,now=T)
        self.assertEqual(x["stage"],"EARLY_WATCH",x)
        self.assertTrue(x["near_boundary_compression"])
    def test_precursor_plus_acceptance_with_all_clouds(self):
        d=constructed_signal(True,True)
        x=evaluate(d,now=T)
        self.assertEqual(x["stage"],"MTF_CONFLUENCE_RESEARCH_ONLY",x)
        self.assertGreater(x["precursor_count_last_7_d1"],0)
        self.assertTrue(x["accepted_daily_breakout"])
        self.assertFalse(x["trade_authorized"])
    def test_precursor_plus_acceptance_missing_mtf(self):
        d=constructed_signal(True,False)
        x=evaluate(d,now=T)
        self.assertEqual(x["stage"],"D1_ACCEPTED_MTF_UNVERIFIED",x)
    def test_adverse_mtf_blocks_research_confluence(self):
        d=constructed_signal(True,True,True)
        x=evaluate(d,now=T)
        self.assertEqual(x["stage"],"MTF_CONFLICT",x)
        self.assertIn("H4",x["conflicting_timeframes"])
    def test_breakout_without_precursor_is_not_accepted(self):
        d=constructed_signal(True,False)
        for row in d["bars"]["D1"][-12:-1]:
            row["high"]+=1.5
            row["low"]-=1.5
        x=evaluate(d,now=T)
        self.assertFalse(x["research_confluence_observed"])

if __name__=='__main__': unittest.main()