# TITAN PROACTIVE 1.0 — cloud-first opportunity discovery and learning

Status: additive **research-only Python implementation**, not incorporated into
the signed TITAN runner and not independently backtested or authorised for trading.

## No personal computer required
External market data is fetched **server-side** from Twelve Data using a
server-held \`TITAN_TWELVEDATA_API_KEY\`. Users can view a cloud API from mobile.
There is **no local MT5 dependency**, file-upload obligation, broker login
or workstation installation. External observations are NOT the broker's live
bid/ask executable quotes. Data provider subscription/coverage is distinct
from a valid agent consensus and a broker-usable market price.

The protected endpoint \`POST /v1/opportunities/cloud-scan\` accepts:
\`{"symbols":["EUR/USD"]}\`
with \`Authorization: Bearer <TITAN_CONTROL_API_KEY>\`. Two symbols
maximum, 4 external time series per symbol. This design limits the commonly
documented Eight Credits Per Minute free tier but quotas/prices/coverage vary.
Excess or unavailable data must fail closed, not quietly fabricate values.

## Research functions
- Read and validate timestamped **completed** D1/H4/H1/M15 OHLC;
  clear source, instrument, fetch timestamp and missing-frame errors.
- Compute Ichimoku cloud comparison with correct 26-bar forward-cloud
  displacement, EMA21/55, ATR14, RSI14, signed momentum TSI 25/13,
  price sweeps, accepted breakouts, and a research-only squeeze flag.
- Independently rank LONG and SHORT using explicitly **uncalibrated**
  0–100 research heuristic; distinguish EARLY WATCH, ARMED, INVALID.
  No signal is promoted to CONFIRMED or authorised for trading by this
  scanner, irrespective of score or numerical R:R.
- Calculate hypothetical net R:R *only* with explicit side-specific
  levels and currency-unit-normalized fees; show its input uncertainty.
  Enforce frozen 2.5:1 only in the pre-existing signed runner.
- Independently journal early alerts and observed forward MFE/MAE.
  Same-candle stop/target collision is marked AMBIGUOUS_SAME_BAR.
  Never describe those outcomes as actual filled trades or P&L.
- Provide read-only external-agent handoff: results explicitly identify
  zero externally executed TITAN signed agents; use existing independently
  authenticated upstream six-phase runner for full approval.
  Never treat unexecuted model names or provider probes as research receipts.

## Limitations
The tool does **not** cover all 21 timeframes, all frozen strategies, news,
earnings, spread/commission, independent signed agent runs, full execution
risk, or broker orders. Those requirements still apply unchanged to any
full TITAN scan/approval. The exploratory signal score is NOT a probability
of profit and is not to be used as a trade trigger.

For sustained journal storage set \`TITAN_JOURNAL_DB_PATH\` on an actually
persistent mounted volume (not a free ephemeral filesystem). The metrics
endpoint is blocked until configured. Do not log account identifiers,
credentials, position size or other sensitive account information.

The cloud feed accepts only a fixed HTTPS vendor endpoint and a validated
symbol; no remote URL from the caller, no code execution or trade placement.
Vendor OHLC is checked, not cryptographically signed by TITAN. Neither a
provider name nor the presence of a credential authenticates its data.
Treat historical testing and provider availability as unfinished until
actually run with original external data and recorded results.

## Research baseline and test targets
Use the original user's fully aligned D1/H4/H1/M15 Ichimoku rule as the
pre-registered baseline, then compare baseline against baseline plus filters
in equities and FX separately. Stratify chronology, instrument, regime,
cost schedule, instrument survival, event restrictions and out-of-sample
results. Evaluate signal recall, false positives, drawdown, expectancy,
time-to-detection, opportunity cost and execution fidelity. High filter
counts alone are not evidence of improvement.

## Reference
Twelve Data API docs: https://twelvedata.com/docs
API costs/entitlements: https://twelvedata.com/pricing

**Governance:** existing frozen six-phase ordering, signed independent
ten-agent receipts, numerical, adverse, macro and risk checks, min net
2.5:1 and single active trade/pending-order discipline take precedence.
Do not deploy this as an execution engine or merge into production without
separate review, genuine historical tests, independent receipt verification,
and explicit approval.
