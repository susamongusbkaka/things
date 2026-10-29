# TITAN V9 — Anticipation Research Pilot (29 October 2026)

**Status:** RESEARCH ONLY — NOT VALIDATED — NO TRADE. No frozen TITAN rule, live route, or risk control has been modified. The attached code is an isolated, locally implemented candidate research engine, not a deployed trading service.

## Question

Can a prospective price-compression warning improve the expectancy of a *subsequent confirmed* breakout, rather than placing orders immediately when compression is first detected?

## Methods and commercial software investigated

- **QuantConnect LEAN**: open-source event-driven backtesting, fill and corporate-action modelling, point-in-time data controls. https://www.lean.io/ and https://www.quantconnect.com/docs/v2/lean-engine/getting-started
- **Freqtrade/FreqAI**: reproducible historical testing, walk-forward retraining, look-ahead diagnostics. Primarily a crypto-trading platform; its research methods are transferable, not its claimed profitability. https://www.freqtrade.io/en/stable/ and https://www.freqtrade.io/en/stable/lookahead-analysis/
- **Lo, Mamaysky and Wang (2000)**: objective computational technical-pattern testing, Journal of Finance. https://www.nber.org/papers/w7613
- **Moskowitz, Ooi and Pedersen (2012)**: time-series momentum across liquid futures, Journal of Financial Economics. https://doi.org/10.1016/j.jfineco.2011.11.003
- **Bailey and Lopez de Prado (2014)**: deflated Sharpe / correction for selection and overfitting, Journal of Portfolio Management. https://doi.org/10.3905/jpm.2014.40.5.094
- **Evans and Lyons (2002)**: information conveyed by foreign-exchange order flow, Journal of Political Economy. https://www.journals.uchicago.edu/doi/10.1086/324391
- **Andersen, Bollerslev, Diebold and Vega (2003)**: macroeconomic announcement surprises and FX price discovery, American Economic Review. https://www.nber.org/papers/w8959
- **Cont, Kukanov and Stoikov (2014)**: order-flow imbalance and short-term stock price changes, Journal of Financial Econometrics. https://academic.oup.com/jfec/article-abstract/12/1/47/816163

Documented *public* methods and open-source research principles were used; no proprietary strategy source was copied. Academic support for an underlying mechanism is not evidence this particular implementation earns money.

## Data provenance

1. ejtraderLabs/historical-data, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF, USDCAD, EURJPY, GBPJPY, EURGBP, AUDJPY and XAUUSD D1 files; 2,400 bars per instrument, typically December 2012 to 4 March 2022. Repository: https://github.com/ejtraderLabs/historical-data
2. MithigaDM/FX-Data D1 CSVs, EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCHF and USDCAD; filtered to January 2011 through 11 July 2025. Repository: https://github.com/MithigaDM/FX-Data
3. On cross-checking overlapping rows for EURUSD, GBPUSD, USDJPY and XAUUSD, the two repositories contained **identical daily closing prices** after scale adjustment (100,000 for EURUSD/GBPUSD, 1,000 for USDJPY, 100 for XAUUSD). Thus the later period is a new date range, **not independent-feed corroboration**.

No broker-specific executable bid/ask quotations, actual spread, guaranteed fills, or rollover/financing charges were obtained. Assume round-trip cost of 0.08 ATR14 for the central experiment, stress-tested at 0.04 and 0.16 ATR. Real MT5 cost modelling remains mandatory.

## Candidate definitions (pre-specified for this pilot)

- **Baseline comparator (not frozen TITAN V9):** Daily close above the properly displayed Ichimoku cloud and above the *preceding 20 completed daily highs* for long (symmetrical short). Enter next daily open, stop beyond signal candle by 0.10 previous ATR14.
- **Early compression watch:** Within the previous seven completed trading days, ATR14 less than 0.90 of ATR50 and price no more than 0.65 ATR14 inside the relevant previous 20-day high/low.
- **Acceptance:** Following daily breakout candle total range exceeds 0.85 times preceding ATR14 and the close lies in the final quarter of the candle in the breakout direction.
- **Both:** Entry only after *both* historical compression watch and accepted breakout. This is a tested candidate, not an authorised TITAN entry rule.
- **Risk:** The TP is adjusted to achieve 2.5:1 **net** planned reward relative to stop risk including assumed round-trip cost. Stop-first if high and low cross opposing thresholds in the same candle; adverse opening gaps priced conservatively. Exit any remaining trade after 15 bars. Only one active trade across the scanned portfolio, no concurrent pending orders.

Every feature used for decision at the close of bar *t* is based on information available no later than that close; simulated execution begins at *t+1* open. Code includes automated tests for this restriction and conservative fill semantics.

## Exploratory results (11 instruments; ejtraderLabs, up to March 2022)

The earlier **immediate compression entry** lost money in the 2020–March 2022 holdout: 48 trades, win rate 20.8%, average −0.395 net R, versus simplified daily Ichimoku + 20-day breakout 57 trades, 35.1%, −0.049R. Both underperform in that period. The immediate entry was rejected for further integration.

## Later historical-period test (seven FX pairs; April 2022 to 11 July 2025)

One-active-trade portfolio with 0.08 ATR assumed costs:

| Experimental rule | Trades | Win % | Mean net R | Profit factor |
|---|---:|---:|---:|---:|
| Basic Ichimoku + range breakout comparator | 75 | 36.0 | −0.192 | 0.688 |
| Prior compression watch | 46 | 34.8 | +0.051 | 1.081 |
| Candle acceptance filter | 69 | 43.5 | −0.057 | 0.898 |
| **Prior watch + acceptance** | **36** | **41.7** | **+0.171** | **1.304** |

### Stress test for *watch + acceptance*, later period

| Assumed round-trip cost | Trades | Mean net R | Naive trade-bootstrap 95% interval |
|---|---:|---:|---|
| 0.04 ATR | 37 | +0.292 | [−0.162,+0.782] |
| 0.08 ATR | 36 | +0.171 | [−0.292,+0.651] |
| 0.16 ATR | 36 | +0.116 | [−0.323,+0.625] |

Trade-level bootstrap is a **rough diagnostic**, not an independent-trades guarantee; time clustering and alternative candidate selection can materially widen uncertainty. For the 0.08 ATR scenario, annual means were 2022 +0.750R (8 trades), 2023 −0.277R (11), 2024 +0.312R (12), 2025 −0.111R (5), indicating regime instability. The 36-trade result is not statistically conclusive. Additional testing of several hypotheses and inspection of outcomes creates selection bias. The 2022–25 date range is not now untouched for further parameter development.

## Implementation and testing

- `titan_v9_anticipation_research.py`: executable, standalone daily-CSV candidate generator and conservative research simulator. Outputs JSON; **cannot place orders**. Requires historical CSVs supplied locally. Does not perform full TITAN V9 six phases, ten-agent validation, MTF checks, or broker-specific execution checks.
- `test_titan_v9_anticipation.py`: 8 unit tests **passed** on 29 October 2026 covering stop priority, net 2.5:1 target calculation, adverse gap rejection, one-active portfolio restriction, malformed and duplicate OHLC, result arithmetic, time expiry and future-data invariance. Synthetic data are used for ENGINE unit tests only; reported strategy-performance results come from genuine historical CSVs processed during separate in-session research.

### Example reproducibility

Place seven vendor CSV files in a directory with names such as `EURUSD.csv`, `GBPUSD.csv`, etc. Then run:

```bash
python -m unittest -v test_titan_v9_anticipation.py
python titan_v9_anticipation_research.py EURUSD.csv GBPUSD.csv USDJPY.csv AUDUSD.csv NZDUSD.csv USDCHF.csv USDCAD.csv --cost-atr 0.08
```

The program starts calculations in 2011 and labels partitions as pre-2018 training, 2018–March 2022 validation, and April 2022–July 2025 later-period research. Historic vendor data may differ if repositories are updated.

## Conclusions and next experiments

**Do not merge this filter into frozen TITAN**. The current pilot finds a possible conditional improvement, not reproducible proof against the real V9 system. The code implements a distinct *precursor evidence* memory that can be compared to conventional entries, but it is not a permission to trade. Next research priorities:

1. Evaluate the actual D1/H4/H1/M15 four-cloud alignment plus mandatory TITAN six-phase decisions, rather than the simplified D1 comparator.
2. Acquire licensed bid-and-ask H4/M15 and broker cost/rollover history, including spread expansions around major announcements. Repeat as event-driven tests and apply strictly sequential validation.
3. Test independent forward data after 11 July 2025, on a prospective registration and holdout not inspected during signal design.
4. As additional genuinely *leading* information, investigate exchange/ECN order-flow imbalance, scheduled economic-surprise expectations versus realisations, futures positioning and reliable price-discovery data. These require authentic time-stamped datasets; proxy indicators cannot establish institutional activity.
5. Maintain all freeze gates, signed-agent receipts, actual data provenance and one-active-trade rule. A software module's unit tests do not imply its predictive validity.

**Final CIO research decision:** INCONCLUSIVE, RESEARCH ONLY — NO TRADE, NO PRODUCTION INTEGRATION.