# TITAN PACE-MTF 1.0: Precursor, Acceptance, Context, Execution

**Status: integrated as a research-only candidate in the TITAN V9 codebase, disabled for order authorisation.** No amendment to the frozen six phases, ten independently executed and authenticated research-agent requirements, macro blackouts, risk sizing, minimum **2.5:1 net R:R to the first verified opposing zone**, one-active-trade rule, or no-overlapping-pending-orders restriction. No claims of profitable live trading or verified 2026 market feeds.

## Problem and novelty

Overlapping RSI/MACD/TSI/EMA signals often reuse the same closing-price information and can confirm too late. PACE-MTF instead **separates a historical anticipatory observation from a later execution-quality observation**. A closed daily compression warning may be informative even if immediate entry is negative expectancy. Requiring a subsequent accepted breakout reduces reflexive early entries. The D1/H4/H1/M15 Ichimoku cloud check is derived from the user's historical four-cloud method. It does **not** replace or relax different frozen TITAN strategies.

The previous exploratory early-compression-entry rule failed on holdout data. A combined daily precursor-plus-acceptance rule was positive only in a small 2022–2025 sample and had a bootstrap interval crossing zero. It is *not statistically validated*; selective testing creates multiple-comparison risk. Do not retrain or tune parameters on that already-inspected period.

## Custom state machine

1. **Cloud context:** Calculate the visible *completed* Ichimoku cloud at each timeframe. The Senkou origin at a chart bar `i` is `i-26`; use period 9/26/52. D1 determines the direction of the *research candidate*. If price is inside its cloud, the candidate is neutral. Require authentic, consecutive completed-timeframe histories; never manufacture missing H4, H1, M15 from D1.
2. **PRECURSOR / EARLY_WATCH:** ATR14 less than 0.90 ATR50 and the closed D1 price no more than 0.65 ATR14 **inside** a prior, 20-completed-day high/low. Record the warning's timestamp. If the last D1 bar has not broken out, display `EARLY_WATCH` or `ARMED_AWAITING_ACCEPTANCE` only, never a trade.
3. **ACCEPTANCE:** Within the seven *previous* closed D1 candles find at least one qualifying precursor. A later D1 breakout must close beyond the preceding 20 completed daily highs/lows in cloud direction, with candle range greater than 0.85 prior ATR14 and a closing position in the outer quarter of its range. Both signals are retrospectively observable as of the breakout close; entry at the compression watch is **not permitted** by this candidate.
4. **CONTEXT/CONFLUENCE:** Check all four named D1/H4/H1/M15 cloud regimes on genuinely supplied and chronologically completed OHLC. If missing, report `D1_ACCEPTED_MTF_UNVERIFIED`; if contradictory, `MTF_CONFLICT`; if aligned, `MTF_CONFLUENCE_RESEARCH_ONLY`. Additional market data (order-flow imbalance, macro-surprise magnitude, futures positioning) remain unscored until genuinely authenticated, as-of-aligned market-data adaptors exist.
5. **EXECUTION:** This is *NOT* PACE approval. Supply the candidate to the original six-phase, signed-agent, independent-data, CCEE/SDRC, macro/calendar, broker bid/ask, actual opposing-zone target, min **net** 2.5 R:R and account/pending-order enforcement layers. Failing any input produces **NOT VALIDATED — NO TRADE**. The PACE route always returns `trade_authorized=false`, `orders_submitted=0`.

The method preserves important time distinctions: an **early warning** is not a trade; a **D1 accepted breakout** is not four-timeframe alignment; four-timeframe alignment is not independent ten-agent execution; research consensus is not trading approval.

## API and security

An additive, owner-authenticated `POST /v1/anticipation/evaluate` route lives in the TITAN bridge. The historical original `POST /v1/research` signed-gateway route and `POST /v1/analysts/research` remain unchanged.

Request (structural example; numeric prices are illustrative, not historical):

```json
{
  "snapshot": {
    "symbol": "EURUSD",
    "asset_class": "forex",
    "as_of_utc": "2025-07-11T20:00:00Z",
    "source": "named broker/export and instrument feed",
    "source_observed_at_utc": "2025-07-11T20:00:00Z",
    "bars": {
      "D1": [
        {"closed_at_utc": "2025-07-10T21:00:00Z", "closed": true, "open": 1.17, "high": 1.18, "low": 1.16, "close": 1.175}
      ],
      "H4": [], "H1": [], "M15": []
    }
  }
}
```

The schema is illustrative only; a valid call requires at least 112 D1 bars and at least 78 bars per supplied intraday timeframe (and a last bar within five days of `as_of_utc`). The requester must independently confirm the reported candle-completion state; the service cannot authenticate a self-declared source. Provided external-claim objects are explicitly unverified and unscored. Requests require the existing `TITAN_CONTROL_API_KEY`; there are no live credentials or trade endpoints in the module.

Output contains the stage, direction, timestamped precursor observations, D1 acceptance flag, individual cloud regimes, missing/conflicting timeframe lists, mandatory unfulfilled validation controls, and permanent no-trade status. No score is represented as a calibrated win probability.

## Historical evidence and limitations

The exploratory D1 pilot (MithigaDM/FX-Data, seven FX pairs) found 36 simulated 2022–2025 portfolio trades for precursor+acceptance at assumed 0.08 ATR round-trip cost, win rate 41.7%, mean +0.171R, profit factor 1.304. Naive trade-bootstrap 95% interval approximately −0.292R to +0.651R. These data were reviewed during method selection and no longer count as an untouched holdout. Broker fill, rollover and stop-gap assumptions were not validated. This is not a complete V9 backtest. Test engine source is included separately for reproducibility and must be run on the same archived vendor CSVs to establish byte-identical results.

## Research standards and independent precedents

- Lo, Mamaysky & Wang (2000), *Foundations of Technical Analysis*, Journal of Finance / NBER w7613: objective pattern-testing framework, not a claim that this pattern works.
- Bailey & López de Prado (2014), *The Deflated Sharpe Ratio*, Journal of Portfolio Management: multiple hypothesis/selection bias.
- Evans & Lyons (2002), *Order Flow and Exchange Rate Dynamics*, Journal of Political Economy: genuine order flow is a distinct possible data source, not equivalent to a candle proxy.
- Andersen, Bollerslev, Diebold & Vega (2003), *Micro Effects of Macro Announcements*, American Economic Review: announcement surprises matter; no substitute with unverified headlines.
- QuantConnect LEAN and Freqtrade: reproducible event-oriented backtest and look-ahead diagnostics, neither guarantees profitable forecasts.

## Tests and next integration gates

Run from `titan`:

```
python -m unittest discover -p 'test*.py' -v
```

The PACE-specific tests cover signature-free no-order response, auth, invalid/future/incomplete OHLC, provenance, no-look-ahead, precursor-only watch, accepted breakout, MTF conflicts and MTF absent. The prior daily research-only backtest and its independent unit tests are kept separate.

**Remaining:** full historical D1/H4/H1/M15 aligned backtest; real bid/ask historical cost and gap forensics; instrument-by-instrument chronological holdout after 2025-07-11; genuine external-agent proofs and six-phase consensus; event embargo and first opposing zone; 21 timeframe availability; separate production release approval. Until complete, DO NOT USE PACE as an executable trade trigger.