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

## International ten-node connection diagnostics (Chinese-language sources included)

The **read-only diagnostics** extension registers ten immutable role-to-model candidates across
Scaleway (France), Mistral (France), Alibaba Bailian (Singapore), SiliconFlow (China)
and Volcano Engine Ark (China). These are ONLY model candidates; the registry does
not say that the nodes are healthy, independent signers or participants in a
research consensus.

Protected routes:
- `GET /v1/nodes/candidates`: show ten candidates and only whether credentials
  are configured; `verified_live_nodes=0` because this is NOT a health check.
- `POST /v1/nodes/probe-ten`: real, potentially billable health inferences,
  available only if `TITAN_DIAGNOSTIC_PROBES_ENABLED=1` and authenticated
  with `TITAN_CONTROL_API_KEY`. All providers get an unpredictable challenge;
  require actual response content, real provider request ID, and exact pinned
  model ID. Concurrency is limited to 4. Zero simulated passes.
- No diagnostic endpoint can approve a security, forecast or trade.
- No unsigned diagnostic counts can enter the signed TITAN consensus votes.

Optional keys (not required to run the gateway in BLOCKED mode):
`DASHSCOPE_API_KEY` (Alibaba Qwen international region),
`SILICONFLOW_API_KEY` (SiliconFlow China),
`ARK_API_KEY` (Volcano Engine Ark).
`SCW_SECRET_KEY` and `MISTRAL_API_KEY` remain the original two providers.
Keep keys only in Render secrets; never commit them. Chinese endpoints may involve
cross-border data transfer; do not submit personal/account information or broker
credentials. Regional Alibaba keys must match the API region.

**Verified cloud check on 2026-10-28**:
GitHub Actions CI succeeded and reached both Render `/health` endpoints.
The bridge reported owner authentication unconfigured; both services reported
model provider credentials unconfigured. It DID NOT demonstrate ten active agents
or any signed financial research outcome.

Provider references:
- Alibaba (Chinese): https://www.alibabacloud.com/help/zh/model-studio/what-is-model-studio
- Volcano Engine (Chinese): https://console.volcengine.com/ark/region%3Acn-beijing/docs/integrate-third-party-tools
- SiliconFlow (Chinese): https://docs.siliconflow.cn/docs/usercases/use-siliconcloud-in-KiloCode
- Scaleway catalog: https://www.scaleway.com/en/docs/generative-apis/reference-content/supported-models/
- Mistral model lifecycle and pinning: https://docs.mistral.ai/inference/model-lifecycle
- Render Free lifecycle: https://render.com/docs/free

Do not use GitHub Models for inference; GitHub retired the service on
2026-07-30 (https://github.blog/changelog/2026-07-30-github-models-is-now-retired/).
GitHub Actions remains useful ONLY as an independent network/CI runner.

**Current blocker:** Two public gateways are reachable, but none of the required
owner/provider credentials has been verified as configured. The original signed
gateway still requires an approved pinned manifest with ten distinct authenticated
Ed25519 agent signers, independent numerical validators and the original risk/CIO
phases. Do not confuse ten model API probes with compliance with that protocol.

## Research-only protocol specifications

- [SDRC-MTF 1.0: supply/demand candidate ranking and annotated candlestick report](protocols/SDRC_MTF_1_0.md). Documentation only; not deployed in the signed runner and does not modify the frozen trading rules or fail-closed gates.
- [CCEE 1.0: Central Confluence & Execution Eligibility Engine (Ichimoku, S&D/S&R, Bollinger, 4-scorer WCS)](protocols/CCEE_1_0.md). Additive deterministic research protocol; not deployed, backtested, continuously monitoring or connected to an order broker. Existing six-phase, signed ten-agent and frozen risk vetoes still apply.
