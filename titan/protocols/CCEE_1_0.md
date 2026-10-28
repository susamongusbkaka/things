# CCEE 1.0 — TITAN Central Confluence & Execution Eligibility Engine

**Adopted specification:** 28 October 2026.  
**Status:** ADDITIVE, RESEARCH-ONLY PROTOCOL. This document is **not** a deployed algorithm, live feed, remote-agent execution, trade authorisation, execution service, or demonstrated profitable model.

## Precedence and invariants

CCEE adds **deterministic, auditable technical scoring and a four-scorer vote** to TITAN. It does not replace the established six ordered phases (fundamental, technical, macro/sentiment, adversarial, risk, lead AI/CIO), the immutable/frozen trading strategies, independent **ten-agent signed-execution quorum**, the 21-MT5-timeframe review where authentic data permit, the minimum **net 2.5:1** risk/reward to a verified opposing zone, cross-market/event restrictions, metal-specific caution, or the limit of **one active TITAN test trade with no concurrent active pending orders**. An internal deterministic score cannot impersonate a genuinely independent external agent's execution receipt. External model output and market narratives are not inputs to CCEE's mathematical technical vote; the existing macro/event and independent research phases retain **hard veto** outside this module. The additive architecture is `CCEE_technical_pass AND all_preexisting_TITAN_gates_pass`.

"EXECUTE_LONG" and "EXECUTE_SHORT" are **eligibility labels in a research output**, never permission to place a broker order. This repository bridge does not place trades. Without independent signed evidence, venue quote/spread, valid candle data, existing-position and macro checks, output **NO_TRADE** regardless of vote. No promise of continuous monitoring: that requires a connected, running data feed, scheduler and appropriately authorised infrastructure.

The score measures **signal agreement, not the mathematical probability of a winning trade**. Only separately calibrated, leakage-free, out-of-sample results could support a probability statement; currently none is established.

## 1. Input, freshness and computable evidence

For each instrument and each required timeframe, ingest authentic timestamped **completed** OHLC candles (source, timezone, broker venue, price precision, timestamp of last completed bar, gaps and adjustments). Use reported exchange volume or explicitly labelled FX tick volume only if supplied; decentralised spot FX tick volume is **not** consolidated institutional order flow. Require market bid/ask, normal and current spread, commissions, slippage assumptions, contract size, overnight financing for hold-to-target, stop minimum, current portfolio/position status, event blackout flags and verifiable zone history. Mark absent, stale or inconsistent fields as **UNAVAILABLE**, not zero, neutral or guessed.

Timeframe analysis is top down: W1/D1 strategic, H4 primary swing setup, H1 context and M15 entry, plus 21 MT5 timeframes wherever authentic data are provided and any more granular timeframe mandated by an existing strategy. CCEE is an additive confirmation layer, not permission to bypass the user's frozen D1/H4/H1/M15 cloud agreement rules for that strategy.

### Ichimoku (9,26,52), evaluated at completed candle `t`

- `Tenkan[t] = (highest(high[t-8:t]) + lowest(low[t-8:t])) / 2`.
- `Kijun[t] = (highest(high[t-25:t]) + lowest(low[t-25:t])) / 2`.
- `spanA_raw[t] = (Tenkan[t] + Kijun[t]) / 2`; `spanB_raw[t] = (highest(high[t-51:t]) + lowest(low[t-51:t])) / 2`.
- The **cloud visually located at time t** is `spanA_raw[t-26]` and `spanB_raw[t-26]` (where available). The *forward cloud* shown at `t+26` is calculated from **known values at t**, not from any future prices.
- The Chikou line is `close[t]` drawn at `t-26`; for a strict unambiguous filter require `close[t] > high[t-26]` for LONG, `close[t] < low[t-26]` for SHORT. This is stricter than a Chikou versus historical close comparison; calibrate variants before changing this declared research setting.
- **LONG:** `close[t] > max(cloudA_at_t, cloudB_at_t)`, `Tenkan[t] > Kijun[t]`, and Chikou clearance; SHORT uses `< min(...)`, `Tenkan[t] < Kijun[t]` and the opposite Chikou clearance. Price inside the cloud, crossed/flat equality or missing lookback => no directional signal.
- Record cloud slope, span ordering/twist, thickness in ATR units, prospective support/resistance and forward shift for **early watch**. Forward display is *not a forecast*. Avoid any 26-bar lookahead/repainting when backtesting.

### Supply/demand and structural levels

Detect completed rally-base-drop supply (RBD), drop-base-rally demand (DBR), and rule-defined order-block candidates with *origin timestamps*, distal/proximal bounds, untouched/mitigated flag, number of later touches, break-of-structure, overlap resolution, departure distance divided by ATR14 and departure velocity (distance / completed bars). Count touches and rejections of a pivot with a predeclared ATR/tick tolerance; group nearly identical levels rather than double-counting them. An "institutional order block" is **a chart-pattern proxy**, not proof of an identified institution or order flow. Rank zone quality by freshness, ATR-normalised departure, valid volume **if available**, alignment with W1/D1/H4 structure, and space to nearest opposing level. If volume is unavailable, explicitly mark the volume evidence **NOT MEASURED**; do not substitute an invented confidence score. Follow existing SDRC-MTF 1.0 for zone definitions, freshness and target vetoes.

### Bollinger Bands (20, 2)

On completed prices, `mid[t] = SMA20(close)`, `sigma[t] = population_stdev20(close)`, `upper=mid+2*sigma`, `lower=mid-2*sigma`, and `bandwidth=(upper-lower)/abs(mid)` when `mid != 0`. Predeclare a lookback and quantile threshold for squeeze classification (a possible **research candidate** is lowest 20% of 120 completed widths); require demonstrably increasing bandwidth plus directional close/break for release. Classify upper/lower **band walks** using a stated consecutive-bar rule, not a single wick. A close above or below the middle band *alone* is insufficient for the user's "ride the band" requirement. For overextension/mean reversion, use a declared statistical test (e.g. z-score relative to SMA20 plus prior completed-bar reversal), not subjective judgement. The candidate thresholds are **provisional/unbacktested** and cannot silently alter existing strategies.

## 2. Four deterministic sub-scorers and exact WCS

The four roles are **internal calculators**, not the independent signed ten-agent network:

| Scorer | Evidence | Vote |
| --- | --- | --- |
| A / trend | Ichimoku cloud, Tenkan/Kijun, multi-timeframe trend | LONG +1 / SHORT -1 / NEUTRAL 0 |
| B / structure | Current validated S&D/S&R bounce, break/retest, structural quality | +1 / -1 / 0 |
| C / volatility | BB squeeze/release, expansion, band-walk and overextension | +1 / -1 / 0 |
| D / momentum | Tenkan/Kijun cross state and Chikou clearance/momentum | +1 / -1 / 0 |

Each returns `{vote: -1|0|1, confidence: c}` with **finite** `c in [0,1]`; attach data timestamps, signal version, component measurements and a reproducible documented normalisation/calibration for `c`. **Never invent confidence values**: if inputs or confidence-calibration method are absent, return `null` and a failed gate, not a vote or a fabricated zero. Exactly four valid roles must be present.

```
WCS = (vA*cA + vB*cB + vC*cC + vD*cD) / 4
LONG  eligible only if WCS >= +0.75
SHORT eligible only if WCS <= -0.75
```

Hence `WCS in [-1,1]`. The equal agent denominator is always **4**, not the number of non-neutral or responding scorers. Numerical example **for mathematical explanation only, not a market reading**: four LONG votes with confidences `(0.8, 0.9, 0.7, 0.8)` yield `WCS=0.80`. A NEUTRAL with confidence 0 and three perfect LONG votes produces `0.75`. **Important implication:** at threshold 0.75, ANY opposite vote with positive confidence necessarily prevents a LONG/SHORT from passing, even if the other three report confidence 1. This follows mathematically from the stated rule, notwithstanding the wording "no single agent veto". A null/failed scorer must fail closed, not be treated as neutral.

The four roles overlap (trend and momentum both use Ichimoku): votes are **correlated**, not independent statistical evidence. WCS 0.75 is **not a 75% win probability**. A 4/4 consensus must **not** increase position size unless a separately approved, frozen risk schedule explicitly permits it; no experimental module may increase overall risk or bypass portfolio caps.

## 3. Combined entry eligibility (logical AND, fail closed)

1. Ichimoku LONG/SHORT directional filter satisfied on all required execution-strategy timeframes; forward cloud reviewed without future leakage.
2. Observed price is rejecting or accepting a specific **verified** appropriately aligned S&D zone or major structural S&R level. Record exact touched/broken levels, timestamp and required confirmed close.
3. Completed-candle BB band-walk or objectively defined squeeze release in the proposed direction; no disqualifying overextension/mean-reversion or conflict.
4. Four authentic internally **computed** scorer records present and threshold attained for the same instrument, direction, as-of timestamp and data versions.
5. Full pre-existing TITAN six-phase and signed external ten-agent requirements, adversarial vetoes, macro/event calendar and high-impact blackout, minimum net **2.5:1 to verified FIRST opposing TP**, spread/fees/slippage/financing, authentic broker levels and one-active-trade/no-multiple-pending limit must ALL pass.

A structural stop is **beyond** the distal zone edge or actual Kijun structural invalidation with tick/spread buffer; it cannot be an arbitrary pip distance. TP1 is nearest verified opposing supply/demand/S&R, TP2 only if sourced. For longs: SL < executable entry < TP; for shorts: SL > executable entry > TP. Label target-specific **net** RR after costs, using correct side of executable bid/ask. If the nearest TP fails 2.5:1 **net**, do not rescue the trade using an unverified distant TP2.

State transitions: `EARLY_WATCH` (forward cloud and structural proximity) -> `ARMED` (observed zone interaction and preliminary valid structure) -> `CONFIRMED_TRIGGER` (closed bars and all requirements), else `INVALID` / `NO_TRADE`. These labels are decision-support only; this specification does not send orders.

## 4. Canonical machine-readable output

For a market evaluation, return **valid JSON** (no comments, no JSON5 syntax, no NaN or Infinity). Retain the user's requested fields and use `null` for measurements not calculable; do not emit numeric 0.00 as a fake market price. Additional fields make the evidence auditable:

```json
{
  "timestamp": null,
  "instrument": null,
  "market_regime": null,
  "indicator_states": {
    "ichimoku_signal": null,
    "sd_sr_confluence": null,
    "bollinger_state": null
  },
  "agent_votes": {
    "trend_agent": {"vote": null, "confidence": null},
    "structure_agent": {"vote": null, "confidence": null},
    "volatility_agent": {"vote": null, "confidence": null},
    "momentum_agent": {"vote": null, "confidence": null}
  },
  "weighted_consensus_score": null,
  "final_decision": "NO_TRADE",
  "execution_parameters": {
    "entry_price": null,
    "stop_loss_price": null,
    "take_profit_price": null,
    "risk_reward_ratio": null
  },
  "state": "AWAITING_MARKET_DATA",
  "receipt_status": "NOT_VERIFIED",
  "data_provenance": null,
  "logic_validation": "Missing timestamped closed-candle data and/or verified independent evidence; NO TRADE."
}
```

Permitted regimes: `TRENDING`, `RANGING`, `VOLATILE`; indicator states: `BULLISH`, `BEARISH`, `NEUTRAL`; zone confluence boolean; BB state `SQUEEZE`, `EXPANSION`, `MEAN_REVERSION`; decisions `EXECUTE_LONG`, `EXECUTE_SHORT`, `NO_TRADE` — **EXECUTE** labels are hypothetical research approvals only. Regime/indicator null means uncomputable, not a market classification. Attach per-timeframe observations, source hashes, candle ranges, scorer diagnostics, frozen gate results, dated events, exact receipt IDs and invalidation measurements in the underlying full run audit.

## 5. Validation and acceptance tests (required before integration)

- WCS exact boundary (+0.75/-0.75), four roles, negative votes, neutral votes, missing confidence, NaN and out-of-range values. An opposite vote proves automatic threshold failure as described above.
- Ichimoku lookback and the 26-bar visual shift: verify no future leakage or rewriting historical cloud readings; cloud inside/outside and equality behavior.
- BB denominator, population standard deviation, edge cases, no squeeze label without history, expansion versus mean-reversion rejection.
- S&D zone freshness, mitigations, volume-source provenance, distinct pivots, lower-timeframe premature signals and false breakout traps.
- Point-in-time chronological unseen holdout and walk-forward on original broker-priced data; compare frozen baseline vs baseline+CCEE on FX, shares and indices, 3–10-session horizons and event regimes; report net expectancy, win rate, MAE/MFE, max drawdown, risk-adjusted performance, signal delay and rejected-opportunity counterfactuals. Account for spread variations, rolls, commission, financing and multiple testing.
- Validate all six phases, ten actually independent signed agent receipts, macro/event stops, net TP1 RR, and open-position/order vetoes; no override by positive WCS.

**Until live data and all independent controls are established, the required result is `NO_TRADE`.** Specification/PR creation does not mean production rollout, broker execution, measured predictive accuracy or continuous background monitoring.
