# SDRC-MTF 1.0 — TITAN Supply/Demand Ranking and Annotated Chart Protocol

**Status:** Additive research/reporting protocol; not integrated into the signed TITAN runner, not backtested, not production-approved. **Trading permission:** None. Nothing here changes frozen strategies, execution rules, six-phase sequencing, ten independently authenticated agent requirements, net minimum 2.5:1 R:R, or the single active test trade / single pending-order limit.

## Purpose and precedence

Scan an explicit instrument universe in **both** LONG and SHORT directions, measure actual supply/demand zones, rank qualified candidates, and display **one** highest-ranked, defensible setup with an evidence-grounded candlestick chart, a concise 4–6 sentence explanation, and a one-row trade summary. The module is a **presentation, discovery and ranking overlay**, not a substitute for TITAN's full strategy selection, independent external-agent checks, macro/event review, adversarial testing, or CIO decision. No candidate that fails a frozen gate may be upgraded by a high score. If evidence is unavailable: **NOT VALIDATED — NO TRADE**.

## Required run inputs

- Instrument universe, tickers and exact broker/exchange symbols, including tick size, quote currency, trading session and timezone.
- Data provider, retrieval time and **last completed bar** timestamp; unmodified authentic OHLC for all required timeframes, and volume only when sourced/defined. For the plot, default to the last **120 completed entry-timeframe candles**, unless user specifies N. No invented or reconstructed candles.
- Context/setup/entry timeframes: inspect all 21 standard MT5 timeframes **when genuine data are available**; MN1/W1/D1 regime and structural context; H4 primary setup; H1 refinement and M15 execution, with M5/M3/M1 for an applicable pre-existing ICT trigger. Respect a user's expressly specified timeframes only within mandatory higher-timeframe gates.
- Spread/bid-ask, symbol-specific minimum stop distance, commission, slippage, financing/borrow where applicable, event calendar, equity/margin exposure, existing positions and pending orders. Distinguish observed, calculated, assumed and unavailable values.
- Frozen risk amount or risk percentage **only if actually supplied or already approved**; never assume an account balance, 1% risk or that a demonstration is authorisation.
- Predeclared ranking rules and as-of cutoff; data lineage, missing-data notes and agent receipt identifiers.

## 1. Scan, identify, rank, and reject

1. Examine bullish and bearish cases without direction bias, including market regime, economic/earnings/geopolitical catalysts, liquidity, cross-asset effects, SMC, LMTD and all relevant frozen TITAN strategies.
2. Define a **demand zone** using an observed completed basing range followed by statistically substantial upward departure; define **supply** analogously for downward departure. Record the origin candle timestamp, proximal/distal price limits, departure candles, ATR-normalised departure, later revisits, tests, structural breaks and any sweep. Do not equate a chart formation with proof of institutional transactions or manipulation.
3. Mark zone freshness: untouched since validated origin > first retest > multiply tested. Resolve overlapping zones and prior-move ambiguity deterministically; reject zones without adequate history or clear boundaries.
4. Quantify entry-to-invalidation risk and price-room to genuine **nearest opposing structure/zone**. Verify whether the first usable target alone meets the frozen net **at least 2.5:1** minimum with current bid/ask and realistic estimated total costs; do not rely on TP2 to rescue an invalid TP1, or silently allow a partial exit below the mandatory threshold.
5. Provisional, **not calibrated and not a probability**, composite score out of 100 for eligible research candidates: higher-timeframe trend alignment (25); zone freshness (20); departure strength (20); net R:R and space to opposing structure (20); independent confluence from break/retest, liquidity sweep, key levels and confirmed momentum/volatility (15). Each factor receives a documented 0–1 evidence-supported subscore, with `score = 25a + 20f + 20d + 20r + 15c`. If any essential factor is unmeasurable, mark **UNSCORED** instead of estimating. Weights are a provisional rubric only and require separate point-in-time validation before any claim of predictive benefit.
6. Rank all candidates, including rejected candidates and both directions. Select exactly one top **eligible** setup only after the required TITAN strategy/risk filters and evidence checks; report its score, the closest competitor, and the factual ranking differences. No eligible setup means **NO TRADE**.

## 2. Levels, net math, and state machine

- **Direction:** LONG or SHORT, with named strategy, supplied symbol and last-completed-bar time.
- **Entry:** exact executable-side entry price, choosing either limit at an **observed** zone edge or market entry **only following all mandated closed-bar confirmations**. Do not suggest a blind pending order, and never place an order.
- **SL:** beyond the **distal/far** zone boundary in the losing direction, allowing justified symbol tick size, realistic spread, ATR / volatility and market structure buffer. For LONG require SL < entry; for SHORT require SL > entry. Recalculate risk when the stop changes; never widen an already placed stop.
- **TP1:** closest qualifying opposing structure or supply/demand zone; **TP2:** next evidence-backed major opposing zone if available. LONG requires each target > entry; SHORT requires each target < entry. Do not invent TP2 to complete a template.
- Calculate gross reward/risk from signed distances, then calculate **net** R:R using instrument-correct buy/ask and sell/bid, commission, plausible slippage, and contract size when required. Label each value as **net**, **gross** or **unverified**. Report target-specific R:R; never substitute seasonal profit/loss ratios or projected win rate. If executable prices, opposing levels, or costs cannot be established, withhold numeric net R:R and the execution endorsement.
- Respect frozen eligibility, position/correlation checks, current/forthcoming high-impact news blackout, stop constraints, one active trade **and no concurrent pending orders**, and any metals-specific stricter presentation rule.
- Status: EARLY WATCH, AT-ZONE WATCH, ARMED, CONFIRMED TRIGGER, INVALID or **NO TRADE**. Only `CONFIRMED TRIGGER` with all authentic signed external agents / complete six-phase evidence could advance to CIO research approval. A research approval is **not** a broker order or real-money authorisation.

## 3. Mandatory annotated single-candidate chart

Where authentic candles and price levels exist, render a **single** readable candlestick chart (Python/matplotlib, Plotly or equivalent) based **exclusively on the genuine entry-timeframe OHLC**. Show N completed candles with axis timestamps/timezone and price units/tick precision.

- **Demand** zones: semitransparent **green** rectangles from observed origin to plot right edge, labels `Demand: low–high`.
- **Supply** zones: semitransparent **red** rectangles from observed origin to plot right edge, labels `Supply: low–high`.
- **Entry:** blue solid horizontal line and exact price; **Stop Loss:** red dashed horizontal line and exact price; **TP1 / TP2:** green dashed lines and prices. Use available TP2 only.
- **Orange projected path** with arrowheads from a *hypothetical* entry through an anticipated retest/pullback (only if pertinent) to TP1 and TP2. It must be clearly labeled **SCENARIO / NOT OBSERVED / NOT A FORECAST**, with a visually different style from historical candles; no implying a guaranteed price path.
- Include title `[INSTRUMENT] [ENTRY TIMEFRAME] — [LONG/SHORT] from [DEMAND/SUPPLY] | Net RR 1:[X]` if net figure verified; otherwise `RR NOT VERIFIED`; clear axes, price/time labels, light grid and non-obscuring legend.
- Show meaningful indicators only if included in ranking/mandatory strategy confirmation. The chart is not a substitute for underlying indicator evidence on required timeframes.
- No invented levels, dates, candles, volumes, support zones, indicator values or agent outcomes. Do **not** draw an apparently real chart from synthetic demonstration prices when it is being presented as a market scan.

## 4. User-facing compact report

For any *fully evidenced* selected setup, in this order:

1. One annotated chart for the single highest ranked setup.
2. Directly below: **4–6 plain-language sentences** describing (a) why it outranked the strongest alternative and the score/confluence, (b) zone/entry/SL logic, (c) TP1/TP2 and opposing levels, (d) invalidation, and (e) evidence/confirmation status.
3. One-row table: `Direction | Entry (type) | SL | TP1 | TP2 | Net RR TP1 / TP2`.
4. One-line disclosure: **Educational technical analysis only; not financial advice or authorisation to trade.**

Retain the full signed phase-by-phase audit, agent receipts, timestamps, rejected alternatives and risk-veto rationale in the underlying auditable TITAN record; the compact visual **must not suppress** mandatory evidence. If data are insufficient, do not force a ranked trade or chart of fabricated prices; instead show clearly **NOT VALIDATED — NO TRADE**, the specific missing inputs, a one-row N/A table where appropriate, and the disclaimer.

## 5. Governance, verification and validation

- Run mandatory TITAN stages in existing order: (1) fundamental, (2) technical, (3) sentiment/macro, (4) adversarial Devil's Advocate, (5) risk, (6) accountable lead-AI/CIO consensus; preserve the genuine external ten-agent signed evidence requirements and failure states throughout. Written names of roles or simulated votes are never real execution.
- Strictly separate **data availability**, **candidate scoring**, **chart drawing**, **phase completion** and **actual independent research/model execution**. An attractive diagram cannot overrule an unverified phase.
- Before any change from research candidate to accepted module, compare frozen baseline against baseline+SDRC-MTF using clean original timestamped OHLC, chronological walk-forward/OOS, variable bid-ask/fees and realistic fills, region/event subgroups and equity-index/FX/metal regimes. Audit zone-label look-ahead, stale candles, non-repainting, ties, adversarial alternative selection and false breakouts. No performance improvement, calibration or live deployment is claimed here.
- No automated trading, API order placement, financial-advice claim, altered risk budget, changes to frozen parameters, or implicit merging/deployment are authorised by this Markdown specification.
