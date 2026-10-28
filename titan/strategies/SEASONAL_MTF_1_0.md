# SEASONAL-MTF 1.0 — TITAN Calendar-Based Seasonal Research Strategy

**Status:** Research-only candidate specification, not yet integrated into the signed TITAN runner, deployed as a strategy, calibrated, or validated on real historical data. **Trading permission:** Never. This file is additive to frozen TITAN strategy parameters, independent-agent receipts, six sequential phases, 2.5:1 net reward/risk gate, and the one-active-trade discipline.

## Purpose

Search stocks, forex, indices, ETFs, futures and commodities for recurring fixed-calendar entry/exit tendencies. Use price-history evidence to **propose** a directional research hypothesis; the calendar cannot constitute an execution signal by itself.

Reference inspiration: Gecko Software TradeMiner (https://www.trademiner.com/). Its proprietary 0–5 ranking formula is **not** available to TITAN. Do not label any TITAN score a reproduced TradeMiner score.

## Required inputs

- Asset class, ticker/universe, historical as-of cutoff, raw/licensed adjusted OHLC data with source and timestamp
- Entry month/day or bounded entry-calendar search range; exit month/day or bounded holding-length search range
- LONG or SHORT; year sample minimum 10 completed observations (20+ preferred)
- Asset-specific trading sessions and holiday conventions, timezone, broker or exchange, contract history and currency conversion
- Verified spread, commission, rollover/financing, dividends, borrow costs, futures roll treatment, slippage; mark any substituted values as **assumed**
- Predeclared window search grid, costs, minimum sample size, scoring criteria and holdout protocol

## Deterministic candidate logic

1. Validate monotonically increasing point-in-time OHLC bars, corporate-action adjustments, delisted constituents, futures roll rules, source and as-of cutoff. Invalid or incomplete datasets fail closed.
2. For each historical year, map the same entry date to the first available actual session **on or after** it; map the exit to the last session **on or before** its specified date. Bound calendar shifts, skip gaps, respect leap years, and support windows crossing year-end.
3. Enter at opening price and exit at closing price for this **hypothetical fixed-window statistical experiment only**. Explicitly distinguish assumed fill prices from broker-executable bid/ask.
4. Calculate per-year signed long/short net return, outcome, holding sessions, close-based drawdown, OHLC maximum adverse excursion, and all-years/earlier-years/held-out-years statistics.
5. Report wins as successes/valid completed years, Wilson binomial uncertainty, average/median net return, best/worst year, mean return per session, worst historical drawdown, holding sessions, and per-year journal. **Do not** call mean window return a tradable P&L unless quantity, costs and contract specifications are known.
6. Historical profit/loss ratio is NOT the TITAN risk:reward metric. Only a proposed stop, target, executable bid/ask and realistic net costs can establish the separate mandatory minimum 2.5:1 R:R.
7. Screen different candidate windows on training years only; keep the most recent years untouched until all choices are frozen. Rank all discoveries, including failed searches, with multiple-testing / data-snooping controls. Do not re-optimise after inspecting holdout.
8. Validate against buy-and-hold/directional-drift and randomized calendar-window baselines; apply a second unseen future period or forward paper test when possible. Stress ±calendar days, cost inflation, high/low volatility regimes, structural breaks, corporate events, and missing data.
9. Rank only qualifying candidates with transparent **TITAN provisional** 0–5 subtests: (i) 95% Wilson lower win-rate bound exceeds 50%, (ii) mean and median net window returns are positive, (iii) mean net return/session clears predeclared economic hurdle (experimental 1 basis point/session), (iv) positive mean net return divided by average max adverse excursion is at least 0.25, (v) latest holdout has positive mean return and ≥60% positive windows. Each test gives one point. This rubric is a research heuristic, uncalibrated and not predictive probability; a high score cannot authorise any trade.
10. Rank qualified windows separately from those rejected for missing data, inadequate sample, data snooping, inconsistent held-out performance, assumed cost gaps, or failing technical/risk gates.

## TITAN coordination

- **Phase 1 Fundamental:** Check central banks, monetary policy, seasonal business drivers, earnings, dividend calendars, inventory cycles, geopolitical catalysts; inspect original-language Japanese, Chinese and Arabic research as appropriate.
- **Phase 2 Technical:** Compare D1/W1/MN1 and H4 structure; inspect remaining available MT5 timeframes; require frozen strategy confirmations rather than modify them. Prioritise equities as candidates for the historical four-aligned-cloud method only when independently supported.
- **Phase 3 Sentiment/Macro:** Independently executed seasonal analyst and other mandated ten signed specialist roles, subject to real receipt/data verification; do not confuse an agent's narrative with a backtest.
- **Phase 4 Devil's Advocate:** Challenge cherry-picking, look-ahead, multiple testing, instrument survivorship, regime shifts, and mistaken economic narratives.
- **Phase 5 Risk:** Macro calendar, variable spreads, entry/exit execution, correlation, open positions, net ≥2.5:1 reward/risk, and one-trade-at-a-time.
- **Phase 6 CIO:** Status only EARLY WATCH / ARMED / CONFIRMED / INVALID / NO TRADE, with exact provenance and receipt completeness; seasonal score is **not** an override.

## Reporting schema

Asset | LONG/SHORT | Calendar entry/exit | Years | Wins/years | Average net window % | Worst historical close-based DD % | Worst MAE % | Holdout mean net % | Provisional score /5 | Status, evidence cutoff, invalidation.

For insufficient years, incomplete bars, missing verified agent receipts or unperformed technical/risk checks, display **NOT VALIDATED — NO TRADE**, not invented values or execution approval.

## Evaluation / validation criteria

Compare frozen TITAN baseline against baseline+SEASONAL-MTF on point-in-time data, clean untouched walk-forward splits and historical spread/fees. Evaluate incremental expectancy, signal coverage, drawdown, tail losses, robustness, multiple-comparison-adjusted uncertainty, and evidence of marginal value after technical/macro filters. Promote this module only through separate review of those findings.

**Disclosure:** Historical seasonality describes observed tendencies, not guarantees or predictions. Backtests can overfit; the method is not a verified profitable strategy. No real-money automation or orders are permitted by this specification.
