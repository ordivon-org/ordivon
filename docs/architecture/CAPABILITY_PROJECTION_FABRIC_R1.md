# Ordivon Capability Projection Fabric R1

Date: 2026-09-28
Status: **EXECUTABLE SPEC / WAVE 1 SOURCE QUALIFIED — LIVE RELEASE PENDING**

Machine-readable execution plan: `docs/architecture/capability-projection-fabric-lego-r1.json`.

## 1. Objective

Evolve the current static Gateway Capability Router into a scalable capability-discovery and projection seam without creating a universal capability registry, global Profile/Bundle owner, credential vault, workflow engine, provider-status database, or Mega Gateway.

The target is not "load every MCP into Gateway". The target is:

```text
source/provider-owned capability definitions
        -> rebuildable discovery projection
        -> caller/run-scoped candidate view
        -> independent authorization/admission
        -> small visible capability window
        -> Gateway route/protocol adaptation
        -> natural owner/provider
        -> owner/provider-native result/effect evidence
```

Gateway remains a thin, rebuildable, non-authoritative northbound adapter.

## 2. Baseline truth

Baseline source revision for this spec: `e9c9d54212161e0fda78a6ef5c994e01924d38b8`.

Fresh live census immediately before this spec established:

- Gateway `0.5.0` is live and still reports `truth_role=non-authoritative-routing-projection`;
- live owners are `runtime.linux`, `runtime.windows`, and `host`;
- live coarse capabilities are `execution.linux`, `execution.windows`, `continuity.external`, and `artifact.runtime`;
- direct Linux Runtime reports `local_linux available=true`;
- Host schema 9 integrity is healthy;
- Gateway owner observation still has the known Runtime `ExceptionGroup/TaskGroup` projection seam and therefore must not use a false `available=false` as provider truth;
- source contains the optional `external.pull` transport, but the live Gateway does not advertise an `external.pull` owner, so source presence is not deployment truth.

All present-tense claims must continue to be re-established from their natural owners.

## 3. External architecture pressure

R1 absorbs only the stable ideas that have converged across mature systems:

- AWS AgentCore Gateway: MCP target aggregation, capability synchronization, target-level credential providers, dynamic/default listing modes, and semantic tool search;
- Microsoft API Center + API Management: design-time inventory/discovery separated from runtime gateway enforcement; Products group MCP servers for consumers without making the gateway the source of downstream truth;
- Docker MCP Toolkit: Catalog -> Profile -> Gateway, plus experimental Dynamic MCP where a small primordial tool set discovers and adds session-scoped MCP servers;
- n8n: Node/Credential/Trigger/Execution separation and a large integration ecosystem, useful as an external integration/workflow provider rather than a new Ordivon kernel owner.

References:

- <https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-MCPservers.html>
- <https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-targets-mcp.html>
- <https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview>
- <https://learn.microsoft.com/en-us/azure/api-management/govern-mcp-server-products>
- <https://docs.docker.com/ai/mcp-catalog-and-toolkit/>
- <https://docs.docker.com/ai/mcp-catalog-and-toolkit/dynamic-mcp/>

These examples justify discovery/projection seams. They do **not** justify a new universal Ordivon Registry owner.

## 4. Constitutional constraints

`ARCHITECTURE_REANCHOR_R1.md` remains binding.

R1 therefore enforces:

1. no universal Registry, Profile, Bundle, Session, Task, Evidence, or ProviderStatus owner;
2. Gateway does not own provider truth, credentials, policy semantics, workflow state, Job/Attempt state, Harness Run state, or domain completion;
3. capability, provider, authority, credential, availability, visibility, and callability remain separate concepts;
4. discovery never grants authority;
5. availability observation never grants authority;
6. caller/run projection never grants authority;
7. unknown external effects are reconciled by frozen identity and are never blindly replayed;
8. direct third-party MCP remains direct when Gateway adds no irreducible routing, policy, normalization, recovery, verification, or composition value;
9. provider-native catalogs/profiles may be referenced as provider-owned objects; Ordivon does not copy their authority into a new global database;
10. semantic ranking is not reimplemented merely for architectural symmetry; a mature external search/index provider is preferred once scale justifies semantic retrieval.

## 5. Vocabulary

### 5.1 CapabilityDefinition

A source- or provider-declared description of a capability. It may include stable identity, category, description, tags, owner/provider reference, input/output schema reference, and truth boundary.

A definition does not prove deployment, current availability, authorization, or successful execution.

### 5.2 CapabilityObservation

A bounded current observation from the natural owner/provider: configured state, availability, node/provider identity, supported contexts, or an observation error.

Observation is not definition authority, authorization, or effect truth.

### 5.3 CapabilityCandidate

A rebuildable projection joining a definition with zero or more current observations. It is suitable for discovery and selection only.

### 5.4 CapabilityView

A caller-owned or Run-owned selection of candidate capability references for one context. A view may be task-scoped, HarnessRun-scoped, client-scoped, or provider-native.

Gateway does not persist a universal Profile/Bundle store. If a Harness Run needs durable exact Tool visibility, Harness remains the owner through its existing Tool catalog/grant digests and exact turn projection.

### 5.5 CapabilityAdmission

An authorization/admission decision owned by the existing Security/provider policy boundary. Discovery results never imply admission.

### 5.6 CapabilityProjection

The small northbound view visible to a consumer after source selection, current observation, caller/run context, and where required independent admission. Projection is rebuildable and non-authoritative.

## 6. Capability dimensions, not a global lifecycle

R1 rejects a mutable global state machine such as `DISCOVERED -> INSTALLED -> AUTHORIZED -> RUNNING`.

Instead, independent owners provide orthogonal facts:

```text
definitionPresent   <- source/provider catalog
configured          <- deployment/provider adapter
available           <- natural owner/provider observation
authorized          <- Security/provider IAM
visible             <- caller/Harness/context projection
callable            <- conjunction evaluated at the execution boundary
```

Therefore:

```text
installed/discoverable != configured
configured != available
available != authorized
authorized != visible
visible != callable
callable != effect committed
```

No single Gateway boolean may collapse these facts.

## 7. Target architecture

```text
                 source/provider definitions
                   /        |        \
          Gateway routes  MCP server  n8n/Docker/provider catalog
                \          |          /
                 \         |         /
                  rebuildable candidate projection
                              |
                    caller/run-scoped view
                              |
                   Security/provider admission
                              |
                       Context Projector
                              |
                    small northbound window
                              |
                      Ordivon Gateway
                    routing / adaptation
                              |
             +----------------+----------------+
             |                |                |
          Runtime            Host       external provider/MCP
             |                |                |
       physical truth   semantic Work     provider truth
```

No box named `Global Capability Registry` is introduced.

## 8. Kernel vs projected surface

Gateway keeps a small release-controlled kernel surface. Dynamic scale belongs in discovery/projection, not in thousands of static MCP tool schemas.

R1 kernel candidates:

```text
system.describe
capability.describe
capability.search
execution.submit
execution.resolve
execution.get
execution.cancel
artifact.read
```

Existing Host Social Work tools remain stable northbound projections during R1. R1 does **not** dynamically rewrite MCP `tools/list` yet.

Future dynamic projected `tools/list` is admitted only after real client interoperability evidence proves that it is better than meta-tool execution for the target consumers.

## 9. R1 `capability.search` contract

R1 implements one deliberately small discovery primitive over the current rebuildable projection.

Input:

- `query`: trimmed text, 1..512 characters;
- optional `category`: exact category filter;
- optional `ownerId`: exact owner filter;
- `limit`: 1..50, default 10;
- `includeUnavailable`: default true.

Search corpus is derived from current `CapabilityDescriptor` fields only. It does not crawl source trees, inspect credentials, invoke effects, or persist an index.

R1 ranking is deterministic lexical matching, not a custom semantic-search engine:

1. exact capability name;
2. capability prefix;
3. exact token match across capability/category/owner/description/tags;
4. substring match across the same metadata;
5. lexical capability name as the stable tie-break.

The result exposes `matchKind`, never a fake semantic confidence score.

If/when the candidate universe is large enough that lexical retrieval is insufficient, semantic retrieval should be delegated to a mature search/index provider or provider-native capability search and compared empirically before custom indexing is admitted.

### Search non-claims

`capability.search` does not claim:

- authorization;
- credential availability;
- effect authority;
- provider success;
- domain completion;
- semantic optimality;
- that an unavailable observation means the owner itself is down.

## 10. Source-derived metadata

The current static route table remains the natural source for Gateway-owned route declarations. R1 extends route declarations with discovery metadata rather than creating a database.

Minimum route metadata:

- stable capability name;
- category;
- owner id;
- short description;
- stable discovery tags;
- truth boundary;
- owner operation family / existing route semantics.

Dynamic provider capabilities may contribute analogous provider-owned metadata through future adapters, but Gateway must preserve their source/provider identity and observation timestamp/digest rather than pretending to author the definition.

## 11. Provider discovery and synchronization — later R1/R2 seam

For a real remote MCP provider, use the official MCP client discovery path. Do not hand-code a second MCP negotiation stack.

A provider capability snapshot must be explicitly identified by:

- provider reference;
- endpoint/target reference without credential bytes;
- protocol/discovery mode;
- observed capability definition digest;
- observed-at/currentness metadata;
- source/provider truth boundary;
- discovery failure if current observation failed.

Two allowed patterns:

1. **on-demand/dynamic listing** — query the provider when the consumer asks;
2. **synchronized snapshot** — retain a rebuildable index/snapshot only when scale/latency requires it.

Any synchronized snapshot is cache/index truth only. Provider definitions and provider effects remain provider-owned.

## 12. Caller/run-scoped profiles without a Profile owner

External systems prove that profiles/products are useful selection units, but Ordivon must not introduce a universal durable Profile owner.

Allowed forms:

- caller configuration containing exact capability/provider refs;
- standard project configuration owned by that project/app;
- HarnessRun-bound exact Tool surface/digest owned by Harness;
- provider-native profile/product reference owned by Docker/Azure/n8n/etc.;
- transient session/run view derived by a Context Projector.

Gateway may consume an explicit view. Gateway must not silently invent, rank, or persist a user's long-term Profile.

## 13. Authorization and credentials

Discovery and authorization are separate.

The existing `gateway-capability-authz-v1` Security seam remains the intended capability authorization owner. R1 search is safe to implement before full mutation/effect admission because search is read-only discovery and explicitly makes no authorization claim.

Before dynamic external-effect capabilities are exposed as callable through Gateway:

```text
verified ingress Principal
  + requested capability
  + trusted Agent/Grant/Effect evidence
  -> Security/provider policy decision
  -> Gateway enforcement point
  -> provider/owner call
```

Credential bytes never enter capability search results or Gateway durable state. Provider adapters receive opaque credential references or provider-native credential bindings from their natural credential owner.

## 14. Execution and effect recovery

Capability discovery does not replace the existing Runtime/Harness recovery law.

For Runtime execution:

```text
requestId -> existing Runtime Job identity -> resolve/observe/reconcile
```

For external providers, an adapter must declare its response-loss strategy before effectful promotion:

- provider idempotency key;
- provider effect lookup/read-back;
- immutable request identity + reconciliation;
- or `UNKNOWN/reconciliation_required` when effect truth cannot be established.

`timeout -> retry` is not an accepted generic policy.

## 15. `external.pull` disposition

The current source-level `external.pull` implementation is a provider-neutral execution-delivery transport with durable queue/attempt/lease mechanics. It is not currently live in the public Gateway deployment.

R1 rules:

- do not use `external.pull` as a universal Provider Registry;
- do not let worker capability advertisement become authorization;
- retain the correct `claimed-but-unstarted` vs `started-and-unknown` recovery distinction;
- keep it feature-gated while there is no production consumer;
- after two real provider/worker consumers exist, re-evaluate whether the transport should remain co-located with Gateway or be extracted behind a narrow provider/execution transport port.

## 16. Observation/error fidelity

ARD-003 remains a prerequisite before availability can drive aggressive capability filtering.

Current known seam:

```text
Runtime direct available=true
Gateway owner observation -> ExceptionGroup/TaskGroup -> projected available=false
```

Until fixed, discovery must preserve `observationError` and must not treat an observation failure as proof that the natural owner is unavailable.

A future search/view may filter `available=false` only when the observation is itself authoritative enough for that decision; `observationError != ownerUnavailable`.

## 17. Executable LEGO plan

### Wave 0 — freeze contract

- **CPF-00** fresh truth + duplicate-abstraction census;
- **CPF-01** this spec + machine-readable plan;
- **CPF-02** architecture guards: explicitly reject universal Registry/Profile owner and Gateway credential/workflow state.

### Wave 1 — searchable rebuildable projection

- **CPF-10** extend static route definitions with discovery description/tags;
- **CPF-11** add pure deterministic search over `CapabilityProjection`;
- **CPF-12** expose `capability.search` northbound, advance Gateway public-surface epoch/version, and add exact contract tests;
- **CPF-13** prove search cannot dispatch owner work and does not claim authorization/callability.

### Wave 1A — observation correctness

- **CPF-14 / ARD-003** normalize owner transport/TaskGroup failures so projection can distinguish observation error from natural-owner unavailable state;
- **CPF-15** requalify direct Runtime vs Gateway projection on Linux and Windows.

### Wave 2 — admission and task/run-scoped views

- **CPF-20** define a caller-owned `CapabilityView` lowering seam only when a real consumer exists;
- **CPF-21** enforce the existing Security capability AuthZ contract on one narrow effect/read path, then generalize by evidence;
- **CPF-22** prove Harness exact Tool catalog/grant digests can consume a projected candidate set without Gateway owning Run visibility.

### Wave 3 — real external provider canaries

- **CPF-30** integrate one external integration provider (prefer n8n or one direct remote MCP) through read-only discovery first;
- **CPF-31** integrate a second independently owned provider path;
- **CPF-32** only after CPF-30/31, decide whether a shared Provider Discovery adapter is justified by real duplication;
- **CPF-33** qualify credential reference and response-loss reconciliation for the first effectful provider action.

### Wave 4 — context scaling

- **CPF-40** measure tool-schema/context pressure with real provider catalogs;
- **CPF-41** compare static projection, lexical meta-search, provider-native semantic search, and mature external semantic retrieval;
- **CPF-42** admit dynamic MCP tool-surface projection only if client interoperability and measured context/latency quality justify it.

### Wave 5 — transport extraction decision

- **CPF-50** two-consumer census for `external.pull`;
- **CPF-51** retain in Gateway if it remains narrow transport mechanics, otherwise extract it behind a provider-neutral port without changing northbound effect identities.

## 18. R1 acceptance gates

R1 Wave 1 is accepted only when:

1. Gateway still has no capability database or credential store;
2. existing static route semantics remain source-derived;
3. `capability.search` returns deterministic, bounded results;
4. search results retain owner/category/truth-boundary/observation-error context;
5. search performs no owner mutation or execution dispatch;
6. discovery makes no AuthZ/callability claim;
7. existing `capability.describe` and execution response-loss contracts remain unchanged;
8. exact MCP surface manifest, package version, and surface epoch move together;
9. Gateway owner tests and repository architecture guards pass;
10. the candidate remains a source implementation only until normal release/deployment acceptance separately promotes it.

## 19. Explicit non-goals

R1 does not build:

- a universal capability registry service;
- a vector database for tools;
- a new semantic ranking model;
- a Gateway workflow engine;
- a Gateway scheduler;
- a Gateway OAuth server or credential vault;
- a provider-status truth database;
- a global Profile/Bundle service;
- a generic `action.execute` that erases owner-specific effect/recovery semantics;
- automatic dynamic MCP installation;
- automatic authorization from discovery metadata;
- a replacement for n8n, Docker MCP Toolkit, Azure API Management, AWS AgentCore Gateway, Temporal, Runtime, Host, Harness, or provider-native truth.

## 20. Promotion rule

Every later abstraction must satisfy the Architecture Re-Anchor admission rule: at least two independent real consumers, no mature external natural owner already covering the semantic, one explicit owner/state boundary, independently testable failure/recovery, and measurable reduction in repeated irreducible duplication.

R1 deliberately starts with a small searchable projection because it is the smallest executable step that moves Ordivon toward large capability universes while preserving current authority laws.

## 21. Wave 1 source qualification receipt

CPF-01/02/10/11/12/13 are source-qualified on the isolated candidate. This is not a live-deployment claim.

- focused Gateway Ruff + capability/Gateway/surface tests: `job-01a0e64f-fb2a-7c23-a31d-d9d018d8e770` — PASS;
- complete Gateway owner verify: `job-01a0e650-907a-7312-96ed-09d851b95223` — PASS;
- architecture constitution/docs guard + 27 repo tests: `job-01a0e653-8226-7b61-b509-0c8e1097b830` — PASS;
- full repository CI: `job-01a0e653-d3cf-7ce0-858a-65adca212eb6` — PASS.

The candidate adds one read-only public discovery primitive, `capability.search`, and advances the source Gateway package identity to `0.6.0` / MCP surface epoch `3`. Live Gateway remains `0.5.0` until the normal release path independently promotes and verifies the candidate.
