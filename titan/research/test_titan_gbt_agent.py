import csv
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from titan_gbt_agent_v1_1 import (
    Candle, Config, Zone, validate_candles, load_csv, atr_wilder,
    define_candidates, cost_adjusted_rr, scan_manifest,
)

class TitanResearchTests(unittest.TestCase):
    def test_incomplete_strict_csv_flag(self):
        with tempfile.TemporaryDirectory() as folder:
            csv_path = Path(folder)/'candles.csv'
            csv_path.write_text('close_time_utc,open,high,low,close,is_complete,source\n2026-01-01T00:00:00Z,1.1,1.2,1.0,1.15,false,CSV\n')
            rows=load_csv(str(csv_path))
            self.assertFalse(rows[0].is_complete)
            self.assertTrue(validate_candles(rows))
            csv_path.write_text('close_time_utc,open,high,low,close,is_complete,source\n2026-01-01T00:00:00Z,1.1,1.2,1.0,1.15,maybe,CSV\n')
            with self.assertRaises(ValueError): load_csv(str(csv_path))

    def test_malformed_data_fails(self):
        t=datetime(2026,1,1,tzinfo=timezone.utc)
        rows=[Candle(t,1.1,float('nan'),1.0,1.1,True,'feed')]*30
        self.assertTrue(validate_candles(rows))

    def test_costs_reduce_rr(self):
        a=cost_adjusted_rr('LONG',1.10,1.09,1.13,0,0,0)
        b=cost_adjusted_rr('LONG',1.10,1.09,1.13,.0002,.0001,.0001)
        self.assertAlmostEqual(a,3)
        self.assertLess(b,a)
        self.assertLess(cost_adjusted_rr('SHORT',1.10,1.11,1.07,.0002,.0001,.0001),3)

    def test_tp1_cannot_be_rescued_by_tp2(self):
        t=datetime(2026,1,1,tzinfo=timezone.utc)
        rows=[Candle(t+timedelta(hours=4*i),1.102,1.103,1.101,1.102,True,'unit') for i in range(40)]
        demand=Zone('demand',1.098,1.1,10,12,2.1,.7)
        supply1=Zone('supply',1.102,1.103,18,20,2.2,.8)
        supply2=Zone('supply',1.12,1.121,25,26,2.4,.8)
        candidates=define_candidates(rows,[demand,supply1,supply2],atr_wilder(rows,14),
                         Config(max_entry_distance_atr=50),.00001,(0,0,0),'bullish')
        ds=[x for x in candidates if x.direction=='LONG']
        self.assertTrue(ds)
        x=ds[0]
        self.assertLess(x.net_rr_tp1_est,2.5)
        self.assertGreater(x.net_rr_tp2_est,2.5)
        self.assertFalse(x.net_rr_tp1_est>=2.5)

    def test_requires_explicit_data_mode(self):
        run=subprocess.run([sys.executable,str(Path(__file__).parent/'titan_gbt_agent_v1_1.py')],
                           capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('required',run.stderr)

    def test_min_rr_cannot_be_lowered(self):
        run=subprocess.run([sys.executable,str(Path(__file__).parent/'titan_gbt_agent_v1_1.py'),
                           '--demo','--min-rr','2.0'],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('frozen 2.5',run.stderr)

    def test_manifest_without_costs_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            with (folder/'data.csv').open('w',newline='') as f:
                writer=csv.writer(f)
                writer.writerow(['close_time_utc','open','high','low','close','is_complete','source'])
                t=datetime(2026,1,1,tzinfo=timezone.utc)
                for i in range(40):
                    writer.writerow([(t+timedelta(hours=4*i)).isoformat(),1.1,1.101,1.099,1.1,'true','unit_fixture'])
            (folder/'manifest.json').write_text(json.dumps({'instruments':[{'symbol':'EURUSD','timeframe':'H4',
                'csv':'data.csv','tick_size':.00001,'pip_size':.0001}]}))
            result=scan_manifest(str(folder/'manifest.json'),Config(),str(folder/'out.png'))
            self.assertEqual(result['status'],'NOT_VALIDATED_NO_TRADE')
            self.assertIsNone(result['chart'])

if __name__=='__main__': unittest.main()