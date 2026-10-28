# HCR-MTF 1.0 — TITAN Hierarchical Macro-Regime Conflict Resolution

**Status (28 October 2026): additive, research-only, NOT implemented in a live runner.** Complements [PMD-LTC 1.0](PMD_LTC_1_0.md) on this branch. This document is not an executed ChatGPT/Gemini/Grok committee, ten-agent quorum, working market feed, backtest, production strategy, live monitoring, or broker order.

## Purpose and precedence

At the **start of each trading week**, obtain *genuine independent* ChatGPT, Gemini, Grok and any other actually connected strategic LLM analyses of an identical, immutable, properly time-stamped public-market snapshot. Resolve the long-horizon bias using a **predeclared, audited** committee decision rule; subsequently receive all ten specialist external agents' **genuinely independent, authenticated** short-horizon outputs. Apply the proposed macro multiplier **only in a post-receipt aggregation layer**, never to change a specialist agent's input, reasoning, original signed vote or raw confidence. The lead AI/CIO still oversees the existing six phases in original order, with the pre-existing adversarial, market-event and risk vetoes intact.

This module is a **research overlay**. It cannot amend frozen strategy parameters or risk limits; it cannot reduce the mandatory ten signed external agent receipts; it cannot override CCEE's four deterministic internal-scoring requirements, net **>=2.5:1 to first opposing verified zone**, existing event restrictions, current **one active trade / no multiple pending orders**, or any metals-specific stronger rule. The cross-asset two-position exception remains a separate unratified proposal. No increase to size or orders without independent risk approval.

## 1. Exact independent weekly LLM input contract

A committee model must return valid JSON with a documented schema, not the illustrative placeholder string `"TRENDING | RANGING | TRANSITION"`. Model outputs must be **separate** and cannot see other members' conclusions until all requested responses have been sealed.

```json
{
  "as_of": "2026-10-26T00:00:00Z",
  "lookahead_used": false,
  "regime": "TRENDING",
  "regime_bias": "STRONG_BEARISH",
  "directional_bias": -1.0,
  "volatility_state": "EXPANDING",
  "macro_risk_events": [
    {"date": "2026-10-28T18:00:00Z", "type": "ILLUSTRATIVE_EVENT_ONLY"}
  ],
  "candidate_assets": [],
  "sentiment_score": null,
  "confidence": null,
  "evidence_ids": [],
  "provider": "EXAMPLE_ONLY_NOT_EXECUTED",
  "model_id": null,
  "provider_request_id": null,
  "dataset_manifest_hash": null
}
```

**All values above are a NON-MARKET illustrative schema**, not observations or executed LLM outputs. The sample `as_of` of 26 October 2026 is *historical* relative to 28 October 2026 and cannot be passed off as the freshest observation; illustration of an event timestamp is not proof of a scheduled release. Actual event entries require sourced date, precise timezone, impact class, applicable instruments, release duration, authoritative source ID and verification time. Do not substitute an arbitrary invented `sentiment_score` or `confidence` for missing model results.

Fields:
- `as_of`: exact immutable source cutoff UTC, plus separately stored `retrieved_at_utc`, model `started_at_utc`, `completed_at_utc`, and last **completed** year/month/week/day/hour bars (avoid 26-bar Ichimoku lookahead).
- `lookahead_used`: boolean claimed by model, **independently checked** with point-in-time provenance; a self-reported `false` is not validation.
- `regime`: one of `TRENDING`, `RANGING`, `TRANSITION`.
- `regime_bias`: one of `STRONG_BULLISH`, `WEAK_BULLISH`, `NEUTRAL`, `WEAK_BEARISH`, `STRONG_BEARISH`; must be **per instrument or explicitly defined instrument basket**, never global in a way that treats e.g. EUR/USD bearish as a bearish signal for gold or all equities.
- `directional_bias`, `sentiment_score`: declared finite scale in [-1,1], or `null`; never convert continuous score to discrete bias without a **preapproved fixed calibration and label mapping**.
- `volatility_state`: `CONTRACTING` / `EXPANDING`, with `UNKNOWN` or `null` when unavailable; independent ATR/regime evidence required.
- `confidence`: finite 0 to 1 **only when its method is defined, validated and evidenced**; else `null`.
- `candidate_assets`: true canonical instrument identifiers, not prose or `"..."`.
- `evidence_ids`: valid hashed references to actual source records, retrieved data snapshots, input manifest and dated event evidence, not ellipses.
- `provider`, `model_id`, `provider_request_id`, `dataset_manifest_hash`: genuine execution provenance, never synthetic receipt IDs.

The requested label `STRONG_*` is an **independent finding**; source measurements and committee policy must corroborate it before using a penalty. Report `INDETERMINATE` rather than asserting a "definitive" bias when models conflict or required providers were not actually invoked. The model quorum and tie/conflict resolution function must be defined, independently approved and versioned *before* the first production run. Until then, **no synthetic consensus or strong-regime penalty is calculated**.

## 2. Two-stage independent execution, then adjustment

**Stage A: Strategic LLM committee:** Run ChatGPT, Gemini, Grok and any permitted other provider independently on the same sealed input. Capture actual request IDs / model / time / as-of / dataset hashes. Independent sources can be considered individually, but a missing or disputed committee outcome is `MACRO_BIAS_UNVERIFIED`, not a fabricated `NEUTRAL`. Weekly bias is **refreshed for new factually verified shocks and source cutoffs** as needed; a Monday conclusion must not be treated as unchangeable until Friday.

**Stage B: Ten signed specialist agents:** Each specialist executes its original approved separate role with its own evidence, output, vote/confidence (where that role is approved to produce one), nonce-bound verified receipt and input manifest; no leakage of LLM decisions or other agent votes into these agents before their independent response is sealed. Signed **raw** outputs remain immutable. Missing role/receipt or unverifiable backend inference fails preexisting full quorum.

**Stage C: Deterministic resolution layer:** After sealing all raw votes, retrieve the *already validated* per-instrument committee bias. Apply the proposed multiplier only to the aggregation-facing **derived** confidence field. Raw votes and original confidence persist unchanged.

Given a signed directional specialist vote `v_i in {-1,0,+1}`, raw confidence `c_i in [0,1]`, and validated regime label `b`:

```python
def multiplier(bias, vote):
    if bias == "STRONG_BEARISH" and vote == +1:
        return 0.3
    if bias == "STRONG_BULLISH" and vote == -1:
        return 0.3
    if bias in ("NEUTRAL", "WEAK_BULLISH", "WEAK_BEARISH",
                "STRONG_BULLISH", "STRONG_BEARISH"):
        return 1.0
    raise ValueError("Unverified/unsupported regime bias")

adjusted_confidence_i = raw_confidence_i * multiplier(bias, raw_vote_i)
```

**Unspecified WEAK bias handling:** multiplier 1.0 is a *research-only provisional non-penalty* because the submitted policy did not specify a weak penalty; it is not permission to infer `NEUTRAL` from missing consensus. For `NEUTRAL`, all multipliers are 1.0, as explicitly requested.

Numeric demonstration (not observed market/model data): a LONG specialist vote with raw confidence `0.80` becomes effective `0.24` under `STRONG_BEARISH`, but stays `0.80` in the signed original. No boost is applied to same-direction votes. The direction vote is **never flipped** by a multiplier.

The ten agents are specialist roles and may not all produce comparable +/-1 votes. Compute a 10-agent aggregate **only if an approved existing role-vote map, denominator and confidence calibration are supplied**; otherwise expose the raw and derived vectors but no claimed weighted composite. Do **not** substitute these ten agent scores for the **separate** CCEE 4-scorer WCS or CATPR cross-asset 35/30/20/15 score. A stronger downstream technical consensus cannot override signed-agent objections that are independent existing risk or adversarial vetoes.

**Conflict policy:** The multiplier is not proof that the LLM macro classification is more accurate. It penalises opposing technical information on the premise of long-term alignment, which may suppress valuable early reversals. Retain the undiscounted rival scenario, track false dismissals, and permit the independent risk agent/CIO to veto even a heavily positive derived score.

## 3. High-impact macro event hard veto

Before **each short-term entry decision** (not just Monday), ingest current verified event times in UTC from authoritative calendars or central banks and tag impacted assets/currencies/sectors for research. The new two-hour veto applies **globally to all TITAN short-term new-trade decisions** whenever any qualifying high-impact event approaches, even when the candidate instrument is in a different asset class. Let `now_utc` be the timestamp of a real decision invocation, and `event_start_utc` the verified event start:

```python
pre_event_veto = any(
    event.high_impact
    and 0 <= (event.start_utc - now_utc).total_seconds() <= 7200
    for event in verified_events
)
trade_paused = pre_event_veto or event_in_progress_or_post_release_blackout or any_frozen_macro_veto
```

The requested window of **two hours is an ADDITIONAL hard veto**. The established restrictions on event aftermath, high-impact times, earnings and metals are **not shortened**. Where a required event calendar cannot be verified or refreshed, or timestamps/impact flags are missing, mark `EVENT_DATA_UNVERIFIED` and fail closed; do not infer the absence of events. The veto is unconditional even when all 10 agents or all 4 local scorers agree.

**Scope:** "ALL short-term trading is paused" means **new TITAN orders, position increases, fresh entries and pending-order authorisations across ALL instrument classes**, not merely instruments directly exposed to the event. Existing protective stop orders and prudent manual position management must **not** be disabled or cancelled by an analysis-layer veto; this module is not an order-management controller. Any preexisting stricter blackout also prevails.

## 4. Decision precedence and returned audit

Required exact ordering:
1. Validate public-source OHLC snapshot, close times, data rights, macro event calendar and existing positions.
2. Obtain independent authenticated long-term LLM committee responses and validated committee bias for each instrument or asset basket. If unresolved, mark as unavailable and withhold any regime multiplier or new execution authorisation.
3. Obtain all **ten** original independent specialist agent responses and Ed25519/real-backend evidence, without altering original votes.
4. Derive adjusted confidence and aggregated research scores **without modifying** the signed originals.
5. Apply unchanged TITAN six phases, strategy confirmations, adversarial and macro risk vetoes, broker last-mile executable quote/net RR >=2.5:1, one-active-trade rule and CIO final adjudication.
6. Any missing or invalid mandatory evidence, unresolved direction mismatch, uncalibrated confidence, failing hard event check or risk gate -> **NOT VALIDATED — NO TRADE**. No broker action.

Minimum reporting additions: `source_as_of_utc`, `weekly_bias_as_of_utc`, `bias_scope`, `llm_executions[]`, `committee_rule_version`, `committee_bias`, `event_calendar_as_of_utc`, `event_blackout{active,affected_assets,event_ids,reason}`, `agent_raw_votes[]`, `agent_adjusted_votes[]`, `multiplier_rules_version`, `four_scorer_wcs`, `cat_wcs`, `signed_agent_receipt_ids[]`, `six_phase_status[]`, `trade_status`. Null/unavailable is preferred to invented zeros.

## 5. Acceptance tests and research falsification

- Exact threshold timing: event at +7200 seconds vetoes, +7201 does not **from this new rule alone**; event in progress and post-release blackout still vetoes; timezone/DST and calendar delay fail closed.
- Mathematically check `STRONG_BEARISH` discounts only LONG 0.3, `STRONG_BULLISH` only SHORT 0.3, `NEUTRAL` preserves all, no fake zero or sign flipping, and weak policies do not invent a penalty.
- Verify raw 10-agent votes and signed request IDs byte-for-byte before/after adjustment, response/nonce and provider independence; 4-scorer WCS remains separately computed.
- Partial/disagreeing committee, stale weekly bias, missing Gemini/Grok execution, wrong-instrument global bias, absent event source, malformed schema, unverifiable sources/receipts -> no execution.
- Point-in-time chronological OOS on 3/5/10-session horizons; compare frozen baseline vs baseline+macro bias and its raw-vote counterfactual. Include early trend reversal misses, cost/slippage, cross-asset co-movement, event gaps, seasonal regimes, calibration, probability reliability, max drawdown and multiple-testing controls.
- Never claim improved win rate, actual independent model execution, no lookahead, live deployment or risk adjustment until the evidence proves it.

**Current implementation state:** GitHub specification/PR only; no running data collection, autonomous weekly schedule, actual Gemini/Grok inference, ten genuine signed agent executions or broker trades established.
