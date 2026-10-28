# CATPR-MTF 1.0 — TITAN Cross-Asset Trend Scanner and Portfolio Risk Engine

**28 October 2026 — ADDITIVE DRAFT PROTOCOL, NOT DEPLOYED OR BACKTESTED.**
This is an explicitly requested **proposed amendment** to the existing one-active-trade policy: retain single-position default; permit a tightly gated two-position exception only once separately reviewed, integrated and formally authorised. A GitHub specification does **not** change running TITAN code or create trading permissions. No broker order, external signed-agent quorum, actual historical backtest or live correlation study occurred in documenting this module.

## 1. Strict disjoint asset taxonomy

Assign each **broker-specific tradable instrument** one and only one category before analysis:
- `FOREX`: liquid spot/forward FX pairs, including EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD, NZDUSD, USDCHF and specified crosses.
- `EQUITIES`: listed individual shares, equity-sector ETFs/proxies and equity index benchmarks/proxies (S&P500, Nasdaq100, FTSE100, DAX40), per the user's provided examples.
- `COMMODITIES`: spot/futures/CFD commodities including XAUUSD, XAGUSD, WTI, Brent, copper; record exact futures contract, expiry, multiplier, roll and quotation units.
- `INDICES`: non-equity macro/volatility/regional baskets such as DXY and VIX. Cash benchmarks are not automatically tradable; require a precise approved futures/ETF/CFD symbol and derivatives basis/roll mechanics.
- `CRYPTO`: high-liquidity BTCUSD, ETHUSD and other approved pairs; retain venue and 24/7-session calendar.
Do not assign the same instrument to two classes to satisfy a diversity rule; different classes do **not** prove statistical independence or low correlation.

## 2. Scan horizon and evidence

Target **3–10 regular trading sessions**; for crypto, state separately if this means 3–10 UTC daily bars, since 24/7 markets differ from weekday exchanges. Screen LONG **and SHORT** within each universe. Require authentic completed, timestamped, vendor-provenance OHLCV where available for W1/D1/H4, plus H1/M15 and all existing required 21 MT5 timeframes when reliable. Confirm the exact tradable symbol, bid/ask, contract size, spread distribution, slippage, overnight carry/financing, earnings, dividend/borrow and event exposure as applicable. For seasonality and volatility regimes retain genuine dated history; no made-up candles, score features or expectancy.

Reject binary event risk using frozen macro blackout parameters, scheduled Tier-1 releases, unscheduled policy/geopolitical shocks and earnings. Macro context is a separately auditable factual risk stage, not a licence to fabricate technical probabilities. Pre-existing frozen TITAN six phases, independent ten signed agent receipts, final risk veto and lead-AI/CIO adjudication still apply.

## 3. Two distinct scores — no namespace collision

**Cross-asset trend ranking score**, provisional `CAT_WCS in [0,1]`:

```
CAT_WCS = 0.35 * T + 0.30 * S + 0.20 * M + 0.15 * V
```

Each component is a finite, explicitly defined and auditable normalised input from **0 to 1**:
- `T`: documented W1/D1/H4 direction/Ichimoku and MA alignment, including the user's strict multi-timeframe Ichimoku requirements when applicable.
- `S`: verified structure breakout/retest, clear invalidation, confirmed supply/demand and opposing zones; actual **net TP1 RR >= 2.5** is a hard gate rather than something that a strong score can conceal.
- `M`: objective macro regime and future-event alignment, e.g. verifiable policy-rate differentials, policy surprise and event flags, not subjective news narrative.
- `V`: measured ATR14 regime, Bollinger Band 20/2 compression/expansion, ADX and realised volatility against a historical baseline.

The user's formula provides **weights but not a reproducible 0-to-1 calibration for inputs**; consequently **do not invent CAT_WCS** before predeclaring normalisation, sourcing closed-bar inputs and validating its behaviour on chronological out-of-sample data. If any component missing, `CAT_WCS: null`, status `UNSCORED`, not 0.00/0.85. An observed WCS of 0.85, once measurable, is **NOT** 85% estimated probability of success.

**Existing CCEE 1.0 score** uses **four trend/structure/volatility/momentum votes** and `CCEE_WCS = sum(vote*confidence)/4` in **[-1,1]**, with +/-0.75 directional thresholds. CAT_WCS and CCEE_WCS are mathematically different; NEVER conflate, relabel or use one as evidence for the other's threshold. Each must pass its own gate when required.

## 4. Portfolio status, correlation, same-class veto and proposed exception

Maintain exact open positions, pending orders, entry date/side/size, stop, venue, portfolio equity, current float, realised exposure, FX delta, margin, correlations, leverage, sector/factor overlap and volatility; unverified user-reported status remains unverified. Neither account information nor exact trade positions may be invented. The normal rule remains **one active trade and no multiple pending orders**.

**Requested second-position exception (proposal; not deployed):** All must hold simultaneously:
1. Precisely **one** existing active TITAN trade; the user's reported EURUSD demo position counts as active until verified closed.
2. The **pre-exclusion #1 ranked** candidate has measured `CAT_WCS >= 0.85`, not a qualitative rank or `CCEE_WCS` substitute.
3. Its single strict asset class differs from **every** currently open position's class. Any same-class proposed candidate gets `REJECTED: CORRELATION RISK` regardless of WCS.
4. The candidate independently satisfies existing full Ichimoku, S&D/S&R, market structure, momentum, BB volatility, sentiment/macro and all frozen strategy gates, including authentic W1/D1/H4/H1/M15 confirmation as appropriate.
5. Complete six ordered TITAN phases; **all ten genuine independently authenticated external execution receipts**; adversarial review; current bid/ask and spread; **net >= 2.5:1 to verified TP1**; no disqualifying news/event; strict total portfolio loss, margin and concentration caps.
6. Separately **calculate actual observed rolling/conditional correlations** and joint risk under stress with source-provenance aligned historical returns (currency/units adjusted). Different-asset-class classification does not waive factor correlation. If risk limits or correlation policy thresholds are undefined, block rather than guess. The proposed rule changes the earlier frozen one-trade policy and therefore requires an approved risk-policy revision before any exception becomes executable.
7. No two open pending orders. Do not increase position size based on score or unanimous voting without a separately ratified risk budget, and do not widen existing stops.

Use a state `TWO_POSITION_EXCEPTION_PROPOSED` vs `TWO_POSITION_EXCEPTION_RATIFIED`. **Before ratification, block a second trade** even if all other requirements appear to pass. If #1 is same-class, WCS<0.85, not computable, or fails any hard gate, default `NO_TRADE` and do not advance rank #2 automatically as a means of bypassing #1 conditions. For new portfolios with no active position, apply original normal single-position gates.

## 5. Required output and ranking

### Section 1: Portfolio status
Report factual active asset, class, long/short, exact entry date **only if verified**, data source, reported/unverified P&L, and slot status.

### Section 2: Ranked evidence table
`Rank | Tradable instrument | Strict class | Direction | CAT_WCS or UNVERIFIED | Class/risk state`. Display user-requested top candidates and rejections, distinguish **research-priority ranking** from calculated quantitative score. Missing data, mixed timeframe signals or unverified executable futures contract => keep status not-qualified.

### Section 3: Primary qualifying setup
Provide ONLY the highest fully eligible candidate; include realistic 3–10 session conditional horizon, exact dated W1/D1/H4 evidence, true breakout/pullback entry, **structural** stop beyond S&D distal/Kijun with bid/ask buffer, verified **nearest** opposing TP1 and extended TP2, and *net* R:R per target. No invented levels, imagined projections or hypothetical trades presented as authorised. If absent, write **NOT VALIDATED — NO TRADE**, with conditional reference levels clearly labelled not as an order.

### Section 4: Risk and governance
Explain event/vulnerability, exposure, correlations/currency-factor overlap, execution controls, signed agent outputs, score calibration and explicit veto reasons. Any **EXECUTE** word means research decision eligibility, not an exchange/broker order.

## 6. Test and release criteria

Unit tests: all five asset classes mutually exclusive; duplicate index assignments blocked; same-class rejection even WCS=1; CAT_WCS exactly 0.85 threshold; missing component => null; #1 same-class does not fall back to #2; opposite currency exposures across assets; cash VIX not executable; missing active-trade info; stop/TP1 bid-ask net RR; failure of any of ten verified agent receipts; no multiple pending orders; event blackout. Additional rolling 60/90/180-session return-correlation and tail-stress research with explicit allowed thresholds selected and signed by risk owner **before** simulation. Chronological OOS, walk-forward, realistic costs and event stress tests compare baseline vs CATPR-only vs baseline+CATPR+CCEE and test 3/5/10-session expectancy, net returns, drawdown and delays, with leakage/multiple-testing controls.

**Implementation status:** Markdown-only research protocol pending approval. No automatic data ingest, market monitoring, remote agent running or broker execution is provided by the document.
