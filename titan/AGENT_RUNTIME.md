# TITAN: independent ten-model research runtime

This adds an **authenticated, research-only** execution endpoint. The older
`POST /v1/research` signed gateway stays unchanged and fail closed.

## What really works

`POST /v1/analysts/research` calls ten independently specified external model
APIs after configuration preflight. Roles run in exact fundamental, technical,
sentiment/macro order, with at most three concurrent model requests per phase.
A request must include a named instrument, asset class, timestamp, market data,
and named timestamped sources. Responses require a real provider request ID,
the exact pinned model ID, valid structured research and source references
that match the supplied snapshot. Each response has a SHA-256 digest and
a per-role Ed25519 TITAN **service attestation**, verified before research
quorum can be reported. Identical model identities and signer keys are refused.

Provider model IDs are candidates, not guaranteed to exist or to support this
API contract. Provider availability must be tested using actual inference.

## What this does not prove

TITAN's Ed25519 receipts attest what the service observed; they are **not**
cryptographic signatures supplied by the remote AI providers. A provider
request ID does not establish truth of a model's reasoning. Ten replies are
research quorum **only**, not the original ten independently signed TITAN
production consensus receipts. The additional numerical strategy, data
quality, signed-gateway, execution, macro, 2.5:1 net reward/risk and
one-active-trade constraints must still run before any trade. This endpoint
**never** authorises or sends orders.

## Environment configuration (private secret manager, not public GitHub)

- `TITAN_CONTROL_API_KEY`: owner-authentication bearer secret, 32+ characters.
- `TITAN_AGENT_RESEARCH_ENABLED=1`: explicit opt-in to billable live inference.
- External provider keys according to `diagnostics.NODES`:
  `MISTRAL_API_KEY`, `SCW_SECRET_KEY`, `DASHSCOPE_API_KEY`,
  `SILICONFLOW_API_KEY`, `ARK_API_KEY`.
- Each of the ten roles has its own distinct secret
  `TITAN_AGENT_SIGNING_KEY_<ROLE>`: base64-encoded raw 32-byte
  Ed25519 private key. Create with a trusted offline key generator;
  never place secrets in logs, Git commits, test fixtures or PR comments.
- Optionally `TITAN_MODEL_<ROLE>` pins a real provider model identifier to
  replace the unverified defaults listed in `diagnostics.NODES`.

The API reads these variables at request time, so missing credentials prevent
billing or fabricated research. It does not accept caller-specified endpoints
or risk overrides. Cross-border model endpoints require appropriate data
governance; never send broker account credentials or personal financial data.

### Endpoints

`GET /v1/analysts/readiness` returns protected *configuration only* status,
not live AI inference success. `POST /v1/analysts/research` accepts:

```json
{
  "snapshot": {
    "symbol": "GBP/AUD",
    "asset_class": "forex",
    "as_of_utc": "2026-10-28T17:00:00+00:00",
    "data": {"H4": {"close": 1.89}},
    "sources": [
      {"name": "illustrative-source", "as_of_utc": "2026-10-28T17:00:00+00:00"}
    ]
  }
}
```

The example is synthetic *request formatting*, not a real market record
or an authorised security analysis. Provide verified market data and the
full timeframes to the separate frozen trade-analysis system.

Run mock-network local regression tests with
`cd titan && python -m unittest discover -p 'test*.py' -v`.
These tests expressly do not make external model calls.

### Release process

1. Review feature PR without merging the live bridge branch.
2. Confirm GitHub Actions unit tests succeed; local mocked tests do not
   demonstrate production inference.
3. Pin ten currently available model IDs and provision secrets **outside Git**.
4. Review provider usage charges, protect the gateway and test a real
   authenticated request with a licensed, timestamped research snapshot.
5. Inspect ten distinct provider request IDs, signed service receipts and
   six ordered phase states. Confirm final outcome is still NO TRADE.
6. Only after this research path is verified should the separate original
   ten-agent production risk/CIO integration be designed and audited.

No autonomous trading, broker connectivity or public live-research
workflow is enabled by this change.
