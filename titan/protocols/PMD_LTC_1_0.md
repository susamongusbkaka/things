# PMD-LTC 1.0 — TITAN Independent Public Market Data & Long-Term LLM Committee

**Issued:** 28 October 2026
**Status:** ADDITIVE RESEARCH-ONLY GOVERNANCE SPECIFICATION. No deployed feed ingestion, external LLM inference, signed agent quorum, verified realtime service, trading or persistent monitoring is claimed. This specification does NOT change frozen technical strategies, six phases, macro controls, 10 independently authenticated execution receipts, portfolio position limits, minimum net 2.5:1 reward/risk, or the separately proposed (not active) second-position exception.

## 1. User direction and scope

1. For **signal generation and market research**, prioritise verifiable, openly accessible, **non-broker-originated** exchange, public institution and appropriately licensed public market data. Do not treat the broker platform's chart/OHLC/tick-volume as the canonical independent market dataset. Public access is not proof of immediate, complete or licensed AI-usable data.
2. Use the **present trading year, month, week, day and hour**, preserving exact as-of and completed-bar timestamps, and also enough point-in-time historical candles to compute long-lookback indicators and test 3–10-session trends. Cover MN1/W1/D1/H4/H1 and M15 where required, plus all accessible original 21 MT5 timeframes / frozen trigger-specific M5/M3/M1.
3. **Long-term strategic scans** are executed as **separate, genuine** model analyses by the TITAN lead ChatGPT model, Gemini, Grok and other **specifically identified, actually connected** LLM services where available. This is an additional *strategic research committee*, not a replacement for or fictional execution of the pre-existing 10 external specialist agents.
4. The **10 specialist agents retain genuinely independent assigned work, analysis and signed receipts** on the same as-of market snapshot; individual agents may consult additional independent authorised data sources, but must disclose differences. Model conclusions or votes are not shared between agents before independent submissions are sealed. Long-term LLM conclusions are also generated separately and reconciled only AFTER submissions; no central model is allowed to overwrite the others' independent findings.
5. The lead AI coordinates data validation and post-submission arbitration. It must **never manufacture a Gemini/Grok execution, confidence metric, observation or provider receipt** when the model is unavailable; explicitly mark `NOT_EXECUTED`. A website containing a model's commentary is not a model-run receipt.

## 2. Data ingest: canonical independently sourced snapshots

Per run capture `run_id`, `symbol`, exact traded proxy/contract & quote units, `asset_class`, `provider`, `endpoint/feed`, `market_timezone`, `retrieved_at_utc`, `last_observed_at_utc`, `last_completed_bar_at_utc`, per-bar `open/high/low/close/volume?`, `native_interval`, `source_delay_seconds` or unknown, `license_status`, `transformation_hash`, `raw_dataset_hash`, `provider_authenticity`, `data_quality_flags` and interval completeness.

- Real/current research requires *latest source-available* data of the **current 2026 year/month/day/hour at the actual scan time**; no reusing stale daily technical summaries as fresh H4/M15 signals. Never replace OHLC candles with prose from financial commentary. Record exact ingestion cutoff (the source's as-of time), not the wall clock when an article was indexed.
- **Only closed bars** may enter execution gate computations. A live but incomplete hour/day is a separate `IN_PROGRESS` observation, useful for early warnings but not confirmation; don't accidentally use a forward-revised bar.
- Compute aggregation from genuine native trading data where time-zone, sessions, holidays, FX Sunday gaps, exchange settlement conventions, crypto 24/7 calendar, stock splits/dividends and futures roll/expiry are defined. Annual/monthly partial candles cannot be passed off as final.
- Require enough pre-2026 history for 52-period Ichimoku, 200-day MA, ATR regime comparisons, multi-year seasonality and out-of-sample tests; do not assume a single current-year sample provides 10+ completed seasonal years. Preserve vintage/revision data for macro series.
- For a mandatory signal, independently validate core OHLC spot/futures moves against a second eligible source when practical. Check price units, instrument/venue mapping, timestamps, outlier thresholds, duplicate bars, gaps and revisions. A source conflict results in `DATA_CONFLICT`/NO TRADE, not silent averaging. Venue disagreement in decentralised FX is normal; do not present any source as the single true spot-FX price.
- Require **rights-compatible** API/dataset access; an accessible webpage is not necessarily licensed for automated downloading, AI processing, redistribution or trained models. No scraping prohibited venue sites or ignoring exchange restrictions.
- Do not assume public feeds are "immediate". Classify `LIVE_VERIFIED`, `DELAYED_KNOWN`, `EOD`, `HISTORICAL`, `UNKNOWN_LATENCY`; do not label delayed/EOD as LIVE.
- Absolute signal staleness limits, allowable cross-provider divergence and percentile/outlier thresholds must be predeclared and instrument-specific. Unknown freshness or insufficient completed bars on any hard gate => fail closed; valid research/watch statuses can still be reported with clear qualifications.

## 3. Candidate authoritative/accessibly licensed sources (not an endorsed real-time universal feed)

| Sector | Candidate research source | Permitted functional role / limitation |
|---|---|---|
| EUR FX, official policy | ECB Data Portal euro reference rates, Bank of England public series | Daily reference/point-in-time macro corroboration; **not** H4/H1 live trade feed; ECB discourages transaction use |
| US macro | FRED/ALFRED API plus Fed/BLS/BEA official releases | Dated/vintaged rates, inflation, economic time series; not intraday FX price candles |
| Listed equity/index/futures | Primary public exchange publications or approved/licensed API distributors | Authenticate exchange timestamp, delay, rights and completeness; a CME webpage has **10+ minute delayed** quotes and restrictive automation/AI-use terms; do NOT scrape/programmatically mine it without applicable authorisation |
| Crypto | Kraken public OHLC/trades/WebSocket, Coinbase public candles | Real venue OHLC, useful cross-check; Kraken OHLC REST has 720-bar historical cap and includes a live unfinished candle; Kraken public historical files provide longer lookback |
| Spot FX | Multiple genuinely independent, license-compatible non-broker public aggregators / public-institution series | Spot FX lacks a single consolidated central exchange; H1/H4 immediate candles may be unavailable freely, so maintain `NO_TRADE` instead of fabricating or assuming CME futures = spot pair |
| Global non-Western coverage | Authoritative Japanese, Chinese, Arabic primary markets/policy institutions, local licensed exchange/public releases | Independent context and locally sourced original-language data; reconcile sessions, contracts, taxes and exchange controls |

Source policy references to check during integration:
- ECB reference methodology: https://data.ecb.europa.eu/methodology/exchange-rates
- FRED vintage and observations: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- CME public quote delay: https://www.cmegroup.com/trading/about-quotes.html
- CME content licences/AI restrictions: https://www.cmegroup.com/trading/market-data-explanation-disclaimer.html
- Kraken historical limits: https://support.kraken.com/in/articles/advanced-api-faq
- Kraken downloadable OHLCVT: https://support.kraken.com/in/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data
- Coinbase public candles: https://coinbase.github.io/coinbase-advanced-py/coinbase.rest.html

## 4. Two truly separate research layers, no vote inflation

**Tier A — Long-Term Strategic LLM Committee:**
- Distinct providers/models: `chatgpt-lead`, `gemini`, `grok`, and additional clearly named, actually connected providers.
- Each runs **independently** on the same immutable, timestamped source manifest, focusing on structural MN1/W1/D1 and historic-year/month regimes, causal macro drivers, long-term Ichimoku forward cloud shape and supply/demand, cross-asset dynamics, event regimes, scenario uncertainty.
- Each provider returns authenticated provider inference ID, immutable model identifier/version, start/end times, observed cutoff, dataset manifest hash, independent findings, disconfirming evidence, explicit assumptions, source links and analysis output digest. If unavailable: `NOT_EXECUTED` and no inferred agreement. ChatGPT's own output is the lead's analysis only, not an independent provider receipt.
- These LLM findings are **research** and may challenge strategy hypotheses; they do not vote on behalf of the ten agents or directly authorise trades. Historical analysis may use older years for genuinely backtestable context but must never substitute old market observations for current signals.
- Grok weekly-start long-trade-specific research, if invoked, preserves any separately approved narrower scope. No automatic change to Grok's previous schedule/mandate is implied. Missing ability to actually invoke Gemini/Grok => disclosed nonexecution, not simulated outputs.

**Tier B — Ten independently authenticated TITAN specialist agents:**
- Preserve exact formally approved ten role identifiers from the enforcement archive; do not reconstruct a plausible roster from memory or a demonstration adapter. Each agent receives *identical* signed snapshot manifest with current-year/month/day/hour candle cutoffs as appropriate to its actual specialty, plus its own permissible independently sourced extras.
- Execute and sign independently with external provider response IDs, nonce-bound request digest, response digest, Ed25519 attestation, UTC start/end, model/version, source lineage. A signature authenticates an attestation, not conclusively upstream model inference; cross-check real backend request IDs and telemetry.
- Ten specialists do not borrow ChatGPT/Gemini/Grok opinions. Prevent cross-agent prompts/results being leaked into other agents' independent analyses. Preserve distinct provider/signer identity and documented model/provider diversity to guard correlated reasoning.
- The mathematical CCEE four-scorer votes and cross-asset CAT_WCS remain separate **internal calculated scores**, not extra independently signed agents and not substitutes for ten receipts.

**Ordering and architecture:** 0. independently source and freeze timestamped public dataset -> 1. dispatch Tier A and Tier B on immutable inputs without pre-vote cross-contamination -> 2. finish the required TITAN six independent phase checks *in their preserved order*, consuming sealed research where appropriate -> 3. adversarial challenge and risk veto -> 4. accountable CIO reconcile (conflicts separately explained) -> 5. fail-closed candidate report. This outlines dependency orchestration, **not** permission to reorder the frozen six phases. Any LLM strategic input relevant to a specific phase becomes visible only at that phase and cannot prescript agent votes. A claimed "10/10" requires actual authentic individual outputs, not source visits or multiple role labels attached to one model.

## 5. Research vs executable fills

Market trend analysis must be driven by the independent public-source snapshot, not broker candles. **For actual execution-risk mathematics** a specific tradable venue/broker bid/ask, order size, symbol specification, spreads, slippage, stop rules and financing still have to be known and checked immediately before an order. This **last-mile execution check is not signal-source authority** and does not mean trusting broker charts as truth. Differences between independent reference data and broker quotes must be logged and can veto execution. If no reliable executable venue quote, trade status = `NO_TRADE`; never compute net 2.5:1 from an unexecutable reference quote.

The one-active-test-trade policy and one-live-pending-order limit stay effective. Existing proposed CATPR-MTF second-position exception remains unratified. The full risk/CIO review, including cross-class correlation, macro blackouts and hard stop constraints, remains mandatory. No automatic order placement is created by this protocol.

## 6. Report and verification gates

Each scan reports:
- exact `as_of_utc`, `retrieved_at_utc`, instrument/source and status of each MN1/W1/D1/H4/H1/M15 and other mandatory interval; label incomplete year/month/week/day/hour candles;
- independent feed origin, delay/licence status, price/volume and broker proxy type, dataset/manifest hashes and exact freshness checks;
- strategic LLM committee: ChatGPT lead, Gemini, Grok, other provider **ACTUALLY_EXECUTED / NOT_EXECUTED / INVALID_RECEIPT** individually, with real provider inference IDs and contradictions;
- full 10 approved specialists: each individually authenticated receipt status, role, exact time/data lineage; cannot invent missing roles or false votes;
- phase-by-phase existing risk gates, net R:R, portfolio open positions and stop/target provenance; recommendation status; no unsupported claimed accuracy, win rate or "highest mathematical probability".

Fail closed if mandatory current OHLC/validated zones, acceptable public-feed provenance, independent execution, current executable quote, signed 10-agent quorum, six phases, portfolio exposure or minimum net 2.5:1 TP1 fails. Produce `NOT VALIDATED — NO TRADE`, optionally with labelled early-watch research signals.

## 7. Tests prior to production approval

- Current-year/month/day/hour as-of time and age; stale signals, mislabelled latest partial candle, timezone DST, holidays and FX/crypto non-identical sessions, futures settlement and contract rolls.
- Feed independence: same syndicated upstream rebroadcast by two sites must **not** count as two independent confirmations; no broker-feed-tainted canonical data; unknown data license fails ingestion.
- Independent long-term LLM inference: absent Gemini/Grok credentials returns `NOT_EXECUTED`; cannot forward one model's conclusion to a competing model before sealed response; provider provenance verified.
- Ten-agent quorum: require ten true independently attested external executions; absent roster/signatures => fail; four local scorer outputs cannot satisfy quorum.
- Point-in-time/candle integrity, no lookahead in forward Ichimoku Kumo, trailing joins, revisions, volume semantics, ATR stability, nonrepainting and seasonal historic lookback.
- Public analytic source vs broker last-mile fill mismatch and cost/roll/slippage stress; no RR from reference-only prices. 
- Before deployment, validate baseline versus baseline + PMD-LTC with actual chronological out-of-sample multi-asset samples, data latency and cost sensitivity; do not assume analytical quality improves merely because sources are public.
- CI and integration tests must prove the new source/agent dispatch layer does not alter existing TITAN six-phase order or risk vetoes.

**Status declaration:** Documented only; Gemini, Grok and ten external agents are **not shown here to have executed**. No schedule/live feed was connected. No market decision was certified.
