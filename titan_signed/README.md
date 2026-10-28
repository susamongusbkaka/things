# TITAN signed runner: audit-ready candidate (NOT DEPLOYED)

Source recovered from the existing deployed Render signed runner on 28 October 2026.
The live original Render service has NOT been modified.

Improvements in this candidate:
- Return the actual Ed25519-signed envelopes (receipt, output, signature) after original
  signature verification, not self-asserted integer counts alone. Envelopes are
  returned only from the authenticated signed-runner endpoint after all gates.
- Include the independently pinned manifest hash in the successful response.
- Refuse ten different roles mapped to fewer than ten distinct provider/model IDs.
- Reject floating `latest` research-model aliases.
- Require ten explicit signed research-direction votes, at least six matching,
  and an independent CIO output agreeing with the majority direction.
- Preserve the original macro/technical/sentiment/advocate/numerical/risk/CIO
  flow, original risk vetoes, net 2.5:1 R:R and no broker orders.

**Not sufficient for production**:
- Exact original 27-Oct-2026 enforcement archive and certified ten-agent roster
  are still unavailable; candidate role labels must not be treated as approved.
- No ten independently signed real inference receipts have been received.
- Ed25519 signing can attest the remote signing service, not independently prove
  the external model actually performed inference. Cross-check upstream model
  provider telemetry and backend request IDs, including model identity and data age.
- The existing gateway's JSON hash canonicalisation is not RFC8785; all
  adapters must agree before signing.
- A separate receipt certifier must verify envelopes and frozen risk gates
  before TITAN's bridge can emit any consensus decision. The bridge remains BLOCKED.
- Real-time risk remains dependent on authenticated market data, order book,
  broker spread, macro events and portfolio state.

This file is committed in an isolated branch for review and syntax/contract
testing; do not deploy it to the original signed runner automatically.
