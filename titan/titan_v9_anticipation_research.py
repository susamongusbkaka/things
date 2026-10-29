"""TITAN V9 research-only anticipatory breakout experiment.

Independent experimental module. No live orders, no change to frozen TITAN gates.
Input: locally supplied authentic DAILY OHLC CSVs (one file per instrument).
Accepted vendor schemas: Date/open/high/low/close or time/open/high/low/close.

Experiment: when a cloud-aligned, volatility-compressed price approached a
completed 20-day extreme in the preceding seven daily sessions, investigate
subsequent accepted 20-day breakouts. This is NOT an executable TITAN signal.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path

COST_ATR = 0.08  # assumed round-trip cost, NOT observed broker bid/ask
TARGET_NET_RR = 2.5
MAX_HOLD_BARS = 15

@dataclass(frozen=True)
class Bar:
    date: str
    o: float
    h: float
    l: float
    c: float

@dataclass(frozen=True)
class Outcome:
    instrument: str
    method: str
    signal_date: str
    entry_date: str
    exit_date: str
    side: int
    entry: float
    stop: float
    target: float
    net_r: float
    rank: float
    reason: str

def load_csv(path: Path) -> list[Bar]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not {'open', 'high', 'low', 'close'}.issubset(reader.fieldnames or []):
            raise ValueError('OHLC columns missing')
        dt = 'Date' if 'Date' in reader.fieldnames else 'time'
        if dt not in reader.fieldnames:
            raise ValueError('Date/time column missing')
        out = []
        for row in reader:
            try:
                day = date.fromisoformat(row[dt][:10]).isoformat()
                o, h, l, c = [float(row[k]) for k in ('open','high','low','close')]
                if not all(map(math.isfinite,(o,h,l,c))) or l <= 0 or l > min(o,c) or h < max(o,c):
                    raise ValueError('invalid OHLC')
                out.append(Bar(day,o,h,l,c))
            except (ValueError, TypeError) as e:
                raise ValueError(f'Malformed market data on row {reader.line_num}: {e}') from e
    if any(out[i].date >= out[i+1].date for i in range(len(out)-1)):
        raise ValueError('Non-increasing or duplicate daily timestamps')
    return out

def true_range(b: list[Bar], i: int) -> float:
    t = b[i]
    return max(t.h-t.l, abs(t.h-b[i-1].c), abs(t.l-b[i-1].c)) if i else t.h-t.l

def mean(xs: list[float]) -> float:
    return sum(xs)/len(xs)

def simulate(b: list[Bar], index: int, side: int, stop: float,
             method: str, instrument: str, rank: float,
             cost_atr: float = COST_ATR) -> Outcome | None:
    """Signal is on bar index's close; entry is NEXT daily open.

    Conservative daily bar semantics: gap through stop fills at the opening
    price; ambiguous stop/target same day counts stop first. Exit at 15 bars.
    Cost is an explicit assumption, not broker pricing.
    """
    if index+MAX_HOLD_BARS >= len(b):
        return None
    a = mean([true_range(b,k) for k in range(index-14,index)])
    entry = b[index+1].o
    risk = side*(entry-stop)
    if not (.25*a <= risk <= 4*a):
        return None
    cost = cost_atr*a
    # True net RR: (gross take profit minus cost) / (gross risk plus cost) = 2.5.
    target = entry+side*(TARGET_NET_RR*(risk+cost)+cost)
    if abs((abs(target-entry)-cost)/(risk+cost)-TARGET_NET_RR) > 1e-9:
        raise AssertionError('Net RR violation')
    result = None
    for j in range(index+1,index+MAX_HOLD_BARS+1):
        x = b[j]
        stop_hit = x.l <= stop if side == 1 else x.h >= stop
        target_hit = x.h >= target if side == 1 else x.l <= target
        if stop_hit:
            fill = min(stop,x.o) if side == 1 else max(stop,x.o)
            result = (j,fill,'stop')
            break
        if target_hit:
            result = (j,target,'target')
            break
        if j == index+MAX_HOLD_BARS:
            result = (j,x.c,'expiry')
    assert result is not None
    j, fill, reason = result
    net_r = (side*(fill-entry)-cost)/(risk+cost)
    return Outcome(instrument,method,b[index].date,b[index+1].date,
                   b[j].date,side,entry,stop,target,net_r,rank,reason)

def signals(b: list[Bar], instrument: str, cost_atr: float = COST_ATR) -> list[Outcome]:
    if len(b)<140:
        return []
    n=len(b)
    # Complete, lagged bars only. Shifted Ichimoku cloud is evaluated
    # at visible chart position i; Senkou origins belong to i-26.
    highs=[z.h for z in b]
    lows=[z.l for z in b]
    tr=[true_range(b,i) for i in range(n)]
    a14=[float('nan') if i<13 else mean(tr[i-13:i+1]) for i in range(n)]
    a50=[float('nan') if i<49 else mean(tr[i-49:i+1]) for i in range(n)]
    def high(i: int,w: int) -> float:
        return max(highs[i-w+1:i+1])
    def low(i: int,w: int) -> float:
        return min(lows[i-w+1:i+1])
    def midpoint(i: int,w: int) -> float:
        return (high(i,w)+low(i,w))/2
    out=[]
    for i in range(110,n-MAX_HOLD_BARS-1):
        t=b[i]
        prior_atr=a14[i-1]
        h20=high(i-1,20)
        l20=low(i-1,20)
        span_a=(midpoint(i-26,9)+midpoint(i-26,26))/2
        span_b=midpoint(i-26,52)
        cloud_high=max(span_a,span_b)
        cloud_low=min(span_a,span_b)
        regime=1 if t.c>cloud_high else -1 if t.c<cloud_low else 0
        side=1 if regime==1 and t.c>h20 else -1 if regime==-1 and t.c<l20 else 0
        if side == 0:
            continue
        has_watch=False
        for k in range(i-1,max(110,i-7)-1,-1):
            if a14[k] < .9*a50[k]:
                boundary=high(k-1,20) if side==1 else low(k-1,20)
                distance=boundary-b[k].c if side==1 else b[k].c-boundary
                if 0 <= distance < .65*a14[k]:
                    has_watch=True
                    break
        width=t.h-t.l
        close_position=(t.c-t.l)/width if width>0 else .5
        accepted=(width>.85*prior_atr and
                  (close_position>.75 if side==1 else close_position<.25))
        score=((t.c-h20) if side==1 else (l20-t.c))/prior_atr
        stop=t.l-.1*prior_atr if side==1 else t.h+.1*prior_atr
        for method,condition in (('baseline',True),('precursor',has_watch),
                                 ('acceptance',accepted),
                                 ('both',has_watch and accepted)):
            if condition:
                v=simulate(b,i,side,stop,method,instrument,score,cost_atr)
                if v: out.append(v)
    return out

def portfolio(events: list[Outcome], method: str) -> list[Outcome]:
    """Exactly one active simulation position across ALL instruments."""
    eligible=sorted((v for v in events if v.method==method),
                    key=lambda x:(x.entry_date,-x.rank,x.instrument))
    chosen=[]
    booked_until=''
    for v in eligible:
        if v.entry_date>booked_until:
            chosen.append(v)
            booked_until=v.exit_date
    return chosen

def report(events: list[Outcome], start: str, end: str) -> dict:
    e=[x for x in events if start <= x.entry_date < end]
    n=len(e)
    profit=sum(max(0,x.net_r) for x in e)
    loss=-sum(min(0,x.net_r) for x in e)
    return {'trades':n,'mean_net_r':round(sum(x.net_r for x in e)/n,5) if n else None,
            'win_pct':round(100*sum(x.net_r>0 for x in e)/n,2) if n else None,
            'profit_factor':round(profit/loss,4) if loss else None}

def main() -> None:
    p=argparse.ArgumentParser(description='TITAN research-only; never sends orders')
    p.add_argument('files',nargs='+',type=Path,help='Daily OHLC CSVs, e.g. EURUSD.csv')
    p.add_argument('--cost-atr',type=float,default=COST_ATR)
    p.add_argument('--out',type=Path,default=Path('titan_v9_research_results.json'))
    a=p.parse_args()
    if not 0 <= a.cost_atr <= 1:
        p.error('cost-atr must be between 0 and 1')
    all_signals=[]
    meta={}
    for path in a.files:
        b=[x for x in load_csv(path) if x.date >= '2011-01-01']
        if len(b)<140:
            raise ValueError(f'Not enough authentic bars in {path}')
        all_signals.extend(signals(b,path.stem,a.cost_atr))
        meta[path.stem]={'bars':len(b),'from':b[0].date,'to':b[-1].date}
    result={'status':'RESEARCH ONLY - NOT VALIDATED FOR LIVE TRADING',
            'cost_atr_assumed':a.cost_atr,'net_rr_min':TARGET_NET_RR,
            'max_active_trades':1,'source_files':meta,'strategies':{}}
    for method in ('baseline','precursor','acceptance','both'):
        positions=portfolio(all_signals,method)
        result['strategies'][method]={
            'train_2011_2017':report(positions,'2011-01-01','2018-01-01'),
            'validation_2018_mar2022':report(positions,'2018-01-01','2022-04-01'),
            'later_2022_2025':report(positions,'2022-04-01','2026-01-01'),
            'positions':[asdict(t) for t in positions]}
    a.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'summary':{
        k:{p:v for p,v in val.items() if p!='positions'}
        for k,val in result['strategies'].items()}},indent=2))

if __name__=='__main__':
    main()