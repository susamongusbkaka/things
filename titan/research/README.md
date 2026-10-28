# TITAN SDRC-MTF 1.1 research runner (NOT a trading engine)

This is a provisional, uncalibrated implementation of TITAN's supply/demand ranking and annotated chart module. It **does not** alter frozen TITAN strategies, risk controls, the ordered six-phase orchestration, signed ten-agent quorum, or the one-position/one-pending-order discipline. It cannot place trades. Its statuses never constitute broker execution approval.

## Run

Python 3 with `numpy` and `matplotlib`.

```bash
pip install numpy matplotlib
python titan_gbt_agent_v1_1.py --demo --output demo.png
python titan_gbt_agent_v1_1.py --csv EURUSD_H4.csv --htf-csv EURUSD_D1.csv --symbol EURUSD --timeframe H4 --tick-size 0.00001 --pip-size 0.0001 --spread-pips 1.2 --slippage-pips 0.4 --commission-pips 0.6 --output research.png
python -m unittest -v test_titan_gbt_agent
```

Synthetic demo is exclusively illustrative, requires `--demo` and is conspicuously watermarked. Default execution with neither `--demo`, `--csv` nor `--manifest` is an error.

CSV columns: `close_time_utc,open,high,low,close,is_complete,source`. Timestamps must be explicit UTC and strictly increasing; `is_complete` must be exactly `true` or `false`. Uploaded CSV source metadata is **not** independently authenticated. Higher-timeframe data must be supplied separately, not inferred from entry-timeframe data. At least 35 HTF bars are required for the provisional EMA20 slope. Input OHLC is not backfilled or synthesised.

### Batch scan

Create a JSON manifest, using real filenames and broker-specific values:

```json
{
  "instruments": [
    {
      "symbol": "EURUSD",
      "timeframe": "H4",
      "csv": "EURUSD_H4.csv",
      "htf_csv": "EURUSD_D1.csv",
      "tick_size": 0.00001,
      "pip_size": 0.0001,
      "spread_pips": 1.2,
      "slippage_pips": 0.4,
      "commission_pips": 0.6
    }
  ]
}
```

Run `python titan_gbt_agent_v1_1.py --manifest markets.json --output winner.png`. The batch scanner ranks *research candidates* on a provisional 25/20/20/20/15 rubric, selects one eligible research candidate and plots exactly one chart. Lack of sufficiently complete evidence returns `NOT_VALIDATED_NO_TRADE` rather than inventing a setup.

## Corrections from submitted draft

- Frozen TP1 cost-adjusted RR >= 2.5 is mandatory; TP2 cannot rescue TP1 and the CLI cannot lower the floor.
- Trading costs are explicitly user-supplied **estimates** (spread, slippage, commission expressed in pip-equivalent quote-price units); the estimated cost-adjusted R:R is **not** broker-verified net R:R. Financing, variable spread, volume-dependent fills, broker stop constraints and actual bid/ask quotes are not covered.
- A separate higher timeframe is necessary; no spurious “HTF” derived from the same timeframe.
- Zones are known only from the departure's completed confirmation candle; close breaches of the distal zone invalidate a zone. Future data cannot be used to discover pre-confirmation zones at the present scan cutoff.
- Candle-completion booleans are parsed strictly, prices must be finite, positive and internally consistent, and timestamps must be increasing and UTC.
- Entry is hypothetical; there is no blind broker pending-order placement. Candlestick plot contains completed-bar UTC times and explicitly labels the forward trajectory as illustrative, not observed or forecast.
- Synthetic data cannot silently run on a normal scan. Multi-instrument ranking supported through a manifest.

## Non-compliance / incomplete integration disclosure

The code **does not** implement all 21 MT5 timeframes, all frozen TITAN strategy modules, price-side broker execution rules across instrument contracts, true cross-asset fundamentals, current event calendar, account exposure/margin, live data retrieval, independent ten-node signed agent receipts, six-phase independent validation, or forward/walk-forward profitability tests. The zone-detection thresholds, trend slope, scoring rubric, and cost-adjusted calculation are provisional research hypotheses. **No trade is validated or authorised by this module.** Do not deploy as a live strategy or connect to broker order endpoints.