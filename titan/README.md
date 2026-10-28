# TITAN approved Render–Scaleway–Mistral cloud bridge

Persistent source-code implementation of the **previously approved workaround**. Replit is not used. The bridge preserves the original, separate signed TITAN runner, and **does not** weaken the ten independently signed research agents, six-phase ordering, frozen strategy parameters or risk vetoes.

IMPORTANT: Cloud application availability does not establish live inference or research quorum. This bridge deliberately returns `BLOCKED` unless the upstream signed runner produces auditable and independently verifiable evidence. It NEVER sends a trade.

## Set up in Render (secrets, not in Git)

* `TITAN_CONTROL_API_KEY`: user-owned random secret of at least 32 characters for authorising requests to this bridge.
* `TITAN_SIGNED_GATEWAY_URL`: exact HTTPS base URL of the approved already deployed signed runner (e.g. `https://titan-signed-agent-runtime-staging.onrender.com`).
* `TITAN_GATEWAY_HOST_PIN`: exact signed runner hostname, default `titan-signed-agent-runtime-staging.onrender.com`.
* `TITAN_BRIDGE_API_KEY`: original gateway credential (not retrievable through this app).
* `SCW_SECRET_KEY`, `TITAN_SCW_MODEL`: Scaleway Paris API key and explicitly selected available model.
* `MISTRAL_API_KEY`, `TITAN_MISTRAL_MODEL`: Mistral API key and explicitly selected available model.

No real credentials are bundled or logged. Read-only `/health` makes **no** network or LLM request. Protected `/v1/provider-probe` performs a genuine, potentially billable single provider inference (never a security-analysis decision). Protected `/v1/research` asks the original signed gateway for a genuine ten-agent research run and **blocks** if the existing runner cannot expose signatures for independent verification. No simulated receipts, fallback claims, synthetic votes or live trading.

## Deploy

Runtime Python; build `pip install -r requirements.txt`; start `uvicorn app:app --host 0.0.0.0 --port $PORT`.

## Permanent operation criteria

1. Owner must provision secrets via Render environment or a secret manager; verify real provider requests using `/v1/provider-probe`.
2. Reconcile approved ten-node public keys, signer endpoints, immutable manifest hash and true external provider request IDs in the existing signed gateway.
3. Expose verified raw receipts (not counts only), and complete the numerical, adversarial, risk and CIO phases before approving any research conclusion.
4. To prevent free-plan cold starts and sustain real monitoring, a suitable always-on hosting plan and independent scheduled probes are necessary. This code alone cannot guarantee 100% uptime.
5. ChatGPT custom MCP onboarding/authorization remains an explicit separate connection step. A Render deployment by itself does not grant ChatGPT the right to call this protected endpoint.