import unittest
import tempfile
import math
from pathlib import Path
from titan_v9_anticipation_research import Bar, Outcome, load_csv, simulate, portfolio, report, signals

def data(n=70,constant=100):
    # Synthetic candles for ENGINE TESTS ONLY; never presented as market performance.
    from datetime import date,timedelta
    start=date(2024,1,1)
    return [Bar((start+timedelta(days=i)).isoformat(),constant,constant+1,constant-1,constant)
            for i in range(n)]

class EngineInvariants(unittest.TestCase):
    def test_stop_wins_ambiguous_bar(self):
        b=data()
        b[20]=Bar(b[20].date,100,110,90,100)
        r=simulate(b,19,1,98,'test','PAIR',1.0)
        self.assertEqual(r.reason,'stop')
        self.assertAlmostEqual(r.net_r,-1)
    def test_target_adjusted_for_net_2_5(self):
        b=data()
        b[20]=Bar(b[20].date,100,105.8,99,104)
        r=simulate(b,19,1,98,'test','PAIR',1.0)
        cost=.08*2
        self.assertAlmostEqual((r.target-r.entry-cost)/(r.entry-r.stop+cost),2.5)
        self.assertEqual(r.reason,'target')
        self.assertAlmostEqual(r.net_r,2.5)
    def test_adverse_gap_is_not_capped_at_stop(self):
        b=data()
        b[20]=Bar(b[20].date,95,96,94,95)
        r=simulate(b,19,1,98,'test','PAIR',1.0)
        # Entry has gapped beneath the planned stop; reject the trade.
        self.assertIsNone(r)
    def test_one_position_across_pairs(self):
        a=Outcome('AAA','both','2024-01-01','2024-01-02','2024-01-05',1,100,98,106,2.5,1.0,'target')
        b=Outcome('BBB','both','2024-01-01','2024-01-02','2024-01-06',1,100,98,106,2.5,.5,'target')
        c=Outcome('CCC','both','2024-01-08','2024-01-09','2024-01-10',1,100,98,106,-1,.5,'stop')
        q=portfolio([b,a,c],'both')
        self.assertEqual([v.instrument for v in q],['AAA','CCC'])
    def test_csv_rejects_corrupt_and_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.csv'
            p.write_text('time,open,high,low,close\n2024-01-01,2,1,3,2\n')
            with self.assertRaises(ValueError):load_csv(p)
            p.write_text('time,open,high,low,close\n2024-01-01,2,3,1,2\n2024-01-01,2,3,1,2\n')
            with self.assertRaises(ValueError):load_csv(p)
    def test_time_expiry_at_exact_horizon(self):
        b=data()
        v=simulate(b,19,1,98,'test','PAIR',1.0)
        self.assertEqual(v.reason,'expiry')
        self.assertEqual(v.exit_date,b[34].date)
        self.assertLess(v.net_r,0)  # assumed cost charged even on flat trade

    def test_future_data_does_not_rewrite_historical_signals(self):
        from datetime import date,timedelta
        start=date(2020,1,1)
        bs=[]
        for i in range(250):
            close=100+.02*i+5*math.sin(i/8)
            bs.append(Bar((start+timedelta(days=i)).isoformat(),close-.2,close+1,close-1,close))
        old=signals(bs,'TEST')
        for i in range(250,280):
            close=100+.02*i+30*math.sin(i)
            bs.append(Bar((start+timedelta(days=i)).isoformat(),close-.2,close+1,close-1,close))
        new=signals(bs,'TEST')
        old_cutoff=old[-1].signal_date if old else '2020-07-01'
        earlier=[r for r in new if r.signal_date<=old_cutoff]
        self.assertEqual(earlier,old)

    def test_report_on_mixed(self):
        a=Outcome('A','both','2024-01-01','2024-01-02','2024-01-05',1,100,98,106,2.5,1,'target')
        b=Outcome('B','both','2024-01-07','2024-01-08','2024-01-10',1,100,98,106,-1,1,'stop')
        x=report([a,b],'2024','2025')
        self.assertEqual(x['trades'],2)
        self.assertAlmostEqual(x['mean_net_r'],.75)

if __name__=='__main__':unittest.main()