# Provider Gateway Family — Mechanism Study R1

## 0. Method binding

Canonical method: Ordivon Recursive LEGO Calculus R2.1.

Current local skill digest:

`sha256:1985dc2765bda250b1f2f76e1b85425141e6aadbb7e39ef5bd5b92d063f08c09`

Problem admission is justified by high expected deletion of custom provider compatibility code, high verifiability through protocol differentials, and direct relevance to live Harness/provider/network dogfood.

No scalar project score is used.

## 1. Problem tuple

Goal: reuse mature external provider-gateway mechanisms while preserving Ordivon natural-owner boundaries, evidence lineage and effect safety.

Hard constraints:

1. Harness retains Run / Turn / Tool / WorkingSet / Provider-call continuity and candidate-completion semantics.
2. Runtime retains execution truth and credential authority.
3. Network v2 retains VPN/egress/destination policy.
4. Gateway does not become Host Work truth, semantic acceptance authority or an Ordivon mega-owner.
5. Effective upstream provider/model/account/attempt identity remains observable enough for lineage, recovery and attribution.
6. Protocol equivalence is qualified per capability, not inferred from an OpenAI-compatible surface.
7. Initial dogfood uses mock or ordinary API-key lanes. OAuth/subscription state is separate until credential lifecycle ownership is admissible.
8. No limit-evasion, account-sharing or provider-policy bypass mechanism is part of this qualification.

## 2. Re-representation

"AI gateway" is too coarse.

Use this task-conditioned generator family:

- G0 ingress protocol surface
- G1 protocol IR / translator
- G2 provider executor
- G3 credential/auth lifecycle
- G4 credential/account selector
- G5 retry/cooldown/circuit-breaker/session-affinity
- G6 network transport/egress binding
- G7 model/capability catalog
- G8 call observation/attempt receipt
- G9 management/control plane
- G10 plugin/extension surface

Immediate lower-Provider candidates are G0-G2 plus bounded parts of G4/G5/G7/G8.

G3 and G6 already have Ordivon natural owners and must not be silently transferred. G9/G10 are not Harness dependencies by default.

## 3. Two distinct gateway families

### 3.1 API-key / official provider gateway

Operational state:

`opaque credential -> provider request -> provider response`

This is the admitted first dogfood lane.

Credential material can remain Runtime-owned. Egress remains Network-owned. Gateway only consumes a bounded invocation-scoped presentation.

### 3.2 OAuth/subscription/CLI-account gateway

Operational state:

`login -> access token -> refresh/rotation -> entitlement/quota -> cooldown -> affinity -> rebind -> provider call`

This is not only protocol translation. It is a durable credential/session control system.

Therefore API-key and subscription/OAuth gateway modes are different system LEGOs and require different qualification.

The unresolved question is not "can an OAuth token be injected?" but "who owns rotating durable credential state and refresh/write-back semantics?"

## 4. CLIProxyAPI mechanism decomposition

Current source binding is recorded in `SOURCE_LOCK_R1.json`.

Useful core graph:

`Ingress -> Translator/IR -> Auth Manager -> Selector -> ProviderExecutor -> upstream`

Side mechanisms:

- credential refresh/state -> Auth Manager
- retry/cooldown/affinity -> selection/execution
- per-auth RoundTripper/proxy -> provider transport
- model registry -> model/capability surface

High-value mechanisms:

- explicit ProviderExecutor contract;
- separate translator registry;
- broad provider/protocol translator test corpus;
- RoundRobin / WeightedRoundRobin / FillFirst / SessionAffinity selectors;
- explicit cooldown/retry/error classification;
- dynamic model catalog;
- embeddable Go SDK and standalone loopback data plane.

Current dynamic qualification on exact current source:

- `go test ./sdk/cliproxy/auth` -> PASS.
- `go test ./sdk/translator/...` -> PASS.
- `go test ./internal/translator/...` -> PASS.

Important negative evidence:

- the first upstream test attempt without explicit VPN binding remained stuck in dependency download and was cancelled after approximately 200 seconds;
- the same source with `HTTPS_PROXY=http://127.0.0.1:19081` completed auth tests successfully;
- therefore test/runtime network binding is a material input and must not be treated as ambient deployment trivia.

Important architectural limits:

- an OpenAI-compatible wire shape is not proof of semantic equivalence;
- translator failure history includes reasoning continuity, tool-call reconstruction, Responses continuation identity and streaming terminal-state classes;
- account selection and affinity can become mutually inconsistent if priority/quota/cooldown semantics are composed incorrectly;
- gateway-local OAuth/auth files are not a substitute for Runtime CredentialAuthority;
- trusted in-process plugin executors are not a general Ordivon security boundary.

Disposition:

`QUALIFIED_FOR_ISOLATED_DOGFOOD` as a data-plane candidate.

Not production-qualified. Not admitted as credential or network authority.

## 5. OmniRoute mechanism decomposition

OmniRoute shares the same provider-routing ancestry but has expanded into a much broader local AI platform.

Useful graph:

`Ingress -> hub translation -> executor -> provider`

plus:

- connection/OAuth state
- quota/account selection
- combo routing/fallback
- circuit breakers
- proxy registry and assignment
- usage/persistence/dashboard
- MCP/A2A/skills
- memory/compression/other modules

High-information mechanisms:

- hub-and-spoke protocol normalization;
- rich provider/model catalog;
- quota-aware account selection;
- combo/fallback and affinity failure corpus;
- explicit roadmap toward core + SDK + modules + provider plugins.

Owner conflicts if adopted wholesale:

- proxy registry overlaps Network v2;
- connection/credential database overlaps Runtime credential authority;
- MCP/A2A/control-plane surfaces overlap existing Ordivon composition/authority surfaces;
- large mutable product surface increases independent failure/update domains;
- current modularization roadmap itself is evidence that the monolithic boundary is under pressure.

Disposition:

`HIGH_INFORMATION_REFERENCE` and adversarial corpus.

Whole-product adoption under the current Ordivon boundary is rejected.

Future modular core may be reconsidered under a fresh source binding and independent qualification.

## 6. Evidence independence

OmniRoute and CLIProxyAPI are not independent architecture observations: OmniRoute explicitly carries lineage/inspiration from CLIProxyAPI/related routing projects and LiteLLM-style normalization.

Therefore agreement between those two does not constitute independent convergence evidence.

Independent triangulation should use an ordinary API-gateway family such as LiteLLM/Bifrost/Envoy AI Gateway on the same frozen cases.

## 7. Falsified representation

Rejected claim:

`OpenAI-compatible wire shape => semantically interchangeable provider behavior`

Verdict:

`FALSIFIED`

A protocol bridge must be qualified per capability:

- basic chat
- streaming text
- tools
- streaming tools
- tool-result continuation
- reasoning/thinking state
- Responses continuation identity
- structured output
- multimodal
- cancellation
- timeout classification
- retry/fallback
- affinity/rebind
- quota classification
- effective upstream identity

One PASS does not imply another.

## 8. Candidate Ordivon seam

Do not create a new truth owner.

At most, add a non-authoritative Provider-boundary binding and evidence receipt.

### GatewayProviderBinding

Candidate fields:

- gateway implementation + exact release/source identity
- loopback endpoint identity
- ingress protocol
- capability-profile digest
- requested provider/model/route policy
- opaque Runtime credential authority/reference
- Network v2 authority/egress profile
- directFallback
- allowed effective-provider set

### GatewayProviderCallReceipt

Candidate fields:

- binding digest
- logical Harness Provider-call identity
- gateway request digest
- translator path
- ordered upstream attempts
- provider/model/non-secret account reference
- retry/fallback reason
- upstream request ID if exposed
- effective provider/model
- stream terminal standing
- bounded response/evidence digests

Unknown fields remain UNKNOWN.

This projection grants no retry, credential, network, tool, effect or semantic-completion authority.

## 9. Network lesson from dogfood

Current local evidence already showed a Harness DeepSeek call succeeds through the Surfshark-backed loopback path.

This study adds a second differential:

- external-source `go test` without explicit VPN binding -> dependency download stalled;
- same exact workspace with explicit `19081` -> dependency resolution + auth tests PASS.

Therefore NetworkBinding belongs in a provider/gateway execution commitment.

Long term, `19081` should not be semantically reused as a generic model-provider route merely because it works physically. A dedicated Network-v2 model-provider consumer should own provider destinations and `directFallback=false` policy where VPN is required.

## 10. Minimal broken frontier

BF-1 — capability-local protocol verifier bridge.

BF-2 — gateway binding/call-receipt provenance, especially exact effective provider/model/account/fallback lineage.

BF-3 — Runtime CredentialAuthority -> gateway API-key consumption without gateway-owned long-lived secret persistence.

BF-4 — Network-v2 model-provider VPN consumer with explicit destination policy and no unintended direct fallback.

BF-5 — separate rotating OAuth credential lifecycle owner/state machine.

Everything outside these frontiers remains preserved.

## 11. Qualified feasible region

Allowed next changes:

- research artifacts;
- mock/local protocol differential;
- non-authoritative binding/receipt prototype;
- isolated API-key canary;
- dedicated Network consumer;
- independent gateway differential.

Not yet allowed by evidence:

- replacing Harness Provider semantics with a gateway;
- moving CredentialAuthority into CLIProxyAPI/OmniRoute;
- moving VPN policy into gateway-local proxy configuration;
- treating gateway retry as safe after ambiguous external effects;
- using OAuth/subscription pooling as though it were ordinary API-key routing;
- adopting OmniRoute control plane wholesale.

## 12. Next operator program

1. Freeze the capability cases in `GATEWAY_QUALIFICATION_CASES_R1.json`.
2. Implement a local mock upstream and execute cases without real credentials.
3. Record semantic diffs, not only HTTP status.
4. Derive the smallest Harness adapter surface from observed requirements.
5. Add/qualify a Network-v2 model-provider egress consumer.
6. Bind one API-key credential through Runtime authority and execute a live canary.
7. Replay the same frozen differential through one independent ordinary API gateway.
8. Re-enter only the failing capability/frontier.
