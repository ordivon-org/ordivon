# Provider Gateway Family — Recursive LEGO R2.1

Status: research-qualified / isolated dogfood in progress  
Date: 2026-10-02  
Method: Recursive LEGO Calculus R2.1  
Method digest: `sha256:1985dc2765bda250b1f2f76e1b85425141e6aadbb7e39ef5bd5b92d063f08c09`

## Purpose

This package records the local Ordivon study of mature multi-provider gateway mechanisms, centered on CLIProxyAPI and OmniRoute and intended to be triangulated against independent ordinary API gateways such as LiteLLM/Bifrost.

The goal is not to add another Ordivon control plane. The goal is to determine which external gateway mechanisms can replace custom provider protocol/routing code below Harness while preserving natural-owner boundaries.

## Current owner boundary

- Harness owns Run / Turn / Tool / WorkingSet / Provider-call continuity and semantic candidate completion.
- Runtime owns physical execution and configured CredentialAuthority.
- Network v2 owns VPN / egress / destination policy and direct-fallback semantics.
- External gateway may own bounded protocol translation, provider execution, catalog projection, and bounded account selection only when qualified.
- Host remains semantic continuity, not provider execution truth.

## Current external source lock

See `SOURCE_LOCK_R1.json`.

Current observations:

- CLIProxyAPI main: `6fecc6e5567912661654a4eaf9b8f5436facd1c2`.
- OmniRoute default remote HEAD: `52823517533cfceec7abef2ff3e6285a19fe4121`.
- OmniRoute `refs/heads/main`: `fc5e2bccd4f70fecf5aab94dfb8136c74ab5a21b`.

Earlier observed source identities are retained as superseded provenance, not current truth.

## Current verdict

- CLIProxyAPI auth/selection core: upstream focused test PASS on exact current source.
- CLIProxyAPI public translator registry: PASS.
- CLIProxyAPI internal translator family: PASS.
- CLIProxyAPI as a lower gateway data-plane candidate: qualified for isolated dogfood, not production-qualified.
- CLIProxyAPI as Ordivon credential authority: rejected.
- CLIProxyAPI OAuth/subscription mode: separate unresolved rotating-credential owner frontier.
- OmniRoute: high-information mechanism and adversarial corpus; whole-product adoption rejected for the current Ordivon boundary.
- "OpenAI-compatible == semantic equivalence": falsified. Qualification is capability-local.

## Key files

- `MECHANISM_STUDY_R1.md` — R2.1 decomposition, owner boundaries, findings and broken frontier.
- `SOURCE_LOCK_R1.json` — exact external source bindings and superseded identities.
- `GATEWAY_QUALIFICATION_CASES_R1.json` — frozen capability-local verifier cases.
- `GATEWAY_BINDING_RECEIPT_R1.schema.json` — non-authoritative Harness-side binding/call-receipt candidate.
- `EVIDENCE_R1.json` — Runtime jobs and current qualification receipts.
- `QUALIFICATION_MAP_R1.json` — upstream test coverage mapped to frozen GQ cases without overstating the independent verifier bridge.
- `MOCK_DIFFERENTIAL_R1.json` — first independent local mock differential, including the bounded GQ07 counterexample.
- `MOCK_DIFFERENTIAL_R2.json` — streaming Tool reconstruction plus bounded 429 recovery / same-provider credential failover.

## Next execution frontier

1. Local mock differential with no real credential: Chat, Responses, Tools, streaming, reasoning, continuation.
2. Define one minimal Harness gateway adapter only after the frozen differential shows the exact required surface.
3. Create a Network-v2-owned model-provider VPN consumer; do not permanently reuse another consumer's semantic route.
4. API-key live canary through Runtime-owned credential delivery + Network-owned egress.
5. Triangulate the same frozen cases through an independent ordinary API gateway.
6. Treat rotating OAuth/subscription credentials as a separate owner/state-machine problem.

## Current convergence R3

- Canonical implementation owner seams are now on Ordivon main: Harness gateway evidence projection and Network v2 model-provider egress.
- Exact current CLIProxyAPI carrier is 6fecc6e5567912661654a4eaf9b8f5436facd1c2 (v8.0.10); SDK auth/translator and internal translator/executor focused suites passed locally.
- The live Network consumer at 127.0.0.1:19881 is source-byte verified, reaches all six admitted Provider surfaces, rejects unknown destinations, and has directFallback=false.
- Generic OpenAI compatibility is not treated as universal semantic equivalence; GQ07 remains the explicit Responses-continuation counterexample.
- Whole OmniRoute is not adopted. It remains a source-locked mechanism/adversarial corpus; only bounded mechanisms may be adapted.
- See CURRENT_CONVERGENCE_R3.json for exact jobs, commits, source identities, verdicts, and remaining frontiers.
- Live API-key dogfood reached OpenRouter through CLIProxyAPI and the Network v2 model-provider egress. The Runtime openrouter-provider/api_key currently fails OpenRouter auth with 401, while the legacy local OpenRouter secret returned 200 at the same probe time; automated rotation was blocked by platform safety policy and no authority mutation occurred.

## Current convergence R4

- Added an internal qualified GatewayBackedDeepSeekTurnAdapter that reuses the existing DeepSeek Harness codec and rewrites only the physical transport to one evidence-bound loopback gateway.
- The same exact AgentTurnRequest yields byte-identical provider request bodies and identical normalized AgentTurnResult on direct versus gateway-backed fixture paths.
- The adapter has no Provider API-key input, retry/fallback surface, credential selection, or Network selection authority; it composes with the existing durable ProviderCallLifecycle.
- Latest focused gate: 30 tests plus 9 subtests PASS, Ruff PASS, and the supported public API remains unchanged.
- Wider Harness regression passed 60 tests plus 23 subtests. The canonical queue is currently blocked before this delta by unrelated Browser/Agent-Automation Ruff violations; those paths remain with their natural owners.
- Runtime openrouter-provider/api_key rotation remains blocked because no authorized CredentialAuthority write Tool is currently exposed; no mutation was attempted through a bypass.
- See CURRENT_CONVERGENCE_R4.json for exact method fences, file digests, Runtime Jobs, qualified properties, non-claims, and next frontier.

## Current convergence R5

- Canonical Harness now owns the qualified capacity/admission and single-provider OpenAI-chat seams; CC Switch remains inventory/capacity/provider-projection tooling rather than Harness execution authority.
- The local model-provider census has 15 existing carriers: DeepSeek x6, Google x5, and one each for OpenRouter, Cerebras, NVIDIA, and BigModel/GLM. PROVIDER_API_CARRIERS_R5.json is research/evidence mapping only, not a live provider registry.
- provider_api_readonly_probe.py consumes exactly one Runtime CredentialAuthority binding and emits sanitized auth/rate/spend evidence without secret bytes. Its live OpenRouter probe correctly returns AUTH_HOLD on the current stale/invalid 401 authority.
- sync_cc_provider_from_runtime_credential.py creates an idempotent CC provider projection from a Runtime-delivered credential using a mode-0600 temporary settings_config; the secret is absent from process argv and the temporary file is removed before Job completion. Existing IDs are not mutated headlessly because CC 5.11.1 deletion requires TTY confirmation; rotations use a new versioned projection ID instead.
- provision_model_provider_credentials.sh is a one-shot operator wizard built on the installed wizard template. It validates the existing 0600 legacy carriers, encrypts them with systemd-creds, preserves and atomically extends ORDIVON_CREDENTIAL_AUTHORITIES_JSON, inherits the existing openrouter-provider principal ACL instead of inventing one, and restarts only ordivon-runtime.service. The wizard is statically qualified but intentionally not executed by the Agent because CredentialAuthority provisioning is operator-owned.
- After that single operator cutover, the remaining pipeline is Agent-automatable: runtime.describe currentness -> provider-native read-only auth/capacity probes -> AUTH-PASS CC projection -> Harness capacity snapshot/admission -> bounded/free route canary.
- Codex subscription OAuth remains a separate external-policy HOLD after provider 403 unsupported_country_region_territory; no region bypass is part of this lane.
- Repository-wide CI reaches the pre-existing next-monorepo-archive retirement drift: canonical main and this candidate both have meta/next tree 1d8582c6 while the policy pins 320474d4; the R5 delta changes zero meta/next paths. R5 records this bounded baseline instead of altering the retirement owner.

See CURRENT_CONVERGENCE_R5.json for exact standings and evidence Jobs.
