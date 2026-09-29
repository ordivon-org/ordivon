# Provider: LiteLLM

Status: **PROTOTYPE-READY / MODEL-GATEWAY PROVIDER / NOT LOCALLY INSTALLED**
Role: model-provider normalization, routing and multi-tenant AI gateway for applications and Agents.

## One-sentence understanding

**LiteLLM normalizes many model providers behind OpenAI-compatible/native interfaces and, when used as a Proxy, centralizes model routing, credentials, virtual keys, budgets, rate limits, caching and telemetry so applications do not each reimplement provider integration and gateway policy.**

## Current upstream observation — 2026-09-14

- repository: `BerriAI/litellm`;
- observed GitHub scale: about 58.5k stars;
- latest stable release observed: `v1.100.1` (2026-09-10);
- current development package metadata observed around `1.102.0`;
- Python support declared as `>=3.10,<3.15` in current project metadata;
- source outside `enterprise/` is MIT-licensed; `enterprise/` has separate BerriAI Enterprise licensing terms.

## Current local observation

No `litellm` executable or `uv tool` installation was observed on this workstation during this study.

No generic custom LLM/model gateway was found in `/root/projects` by a shallow gateway/chat2api/litellm census. The matches observed were domain-specific proxies (Finance/Network/Harness), not a shared model gateway.

Do not install LiteLLM solely to complete the catalog. Use the SDK when one application needs provider normalization/routing; activate the Proxy when multiple applications/Agents/teams need a shared model-access control plane.

## Two distinct operating modes

### Python SDK

Use the SDK when model access belongs inside one Python application and no shared gateway is required.

Core responsibilities:

- translate OpenAI-style/native requests to 100+ provider APIs;
- normalize responses;
- normalize common error classes;
- optional Router for multiple deployments/providers;
- application-local retries/fallbacks/load balancing;
- cost calculation and observability callbacks.

Do not deploy a network gateway just to avoid writing provider-specific SDK calls in one application.

### Proxy / AI Gateway

Use the Proxy when model access must become a shared platform boundary.

Core responsibilities include:

- OpenAI-compatible network endpoint;
- centralized provider credentials/model aliases;
- authentication/authorization hooks;
- virtual keys;
- model access control;
- per-key/user/team/project spend tracking and budgets;
- TPM/RPM/concurrency limits;
- routing/load balancing/fallback/cooldown;
- response caching;
- guardrail/policy hooks;
- observability/export hooks;
- central admin/configuration surface.

This is a real control plane and normally introduces persistent dependencies such as PostgreSQL for virtual-key/budget state and Redis/Valkey for distributed routing/cache/rate-limit state when those capabilities are enabled.

## Provider normalization

LiteLLM's core adapter layer maps provider differences into stable calling surfaces such as:

- chat completions;
- Responses API-style calls;
- embeddings;
- image generation;
- audio;
- batches and other supported endpoints.

Conceptually:

```text
Application request
       ↓
normalized LiteLLM call
       ↓
provider adapter
       ↓
OpenAI / Anthropic / Bedrock / Vertex / Azure / Ollama / ...
       ↓
normalized response / error
```

The normalization layer should remove transport/provider boilerplate, not erase meaningful model capability differences. Callers still need to know whether a model actually supports the required endpoint, tool semantics, structured output, context size, modality or reasoning behavior.

## Model groups and deployments

LiteLLM separates a caller-facing model/group name from concrete deployments.

Example concept:

```text
model group: "reasoning-primary"
      ├─ OpenAI deployment A
      ├─ Azure deployment B
      └─ provider deployment C
```

The application requests the stable model group. The Router selects a concrete deployment according to routing/health/policy configuration.

This is the correct place for deployment redundancy. Do not encode provider endpoint selection throughout Agent or Ordivon domain code.

## Routing / load balancing

The Router supports strategies such as weighted/simple shuffle, rate-limit-aware routing, latency-based routing, least-busy, cost-aware/custom strategies and provider/model fallbacks.

The production default/recommended path is deliberately simple (`simple-shuffle` / weighted selection); more stateful usage-aware strategies can impose Redis/latency overhead.

General rule:

**Start with the simplest routing strategy that satisfies availability/capacity requirements; add adaptive/cost/usage routing only after measured need.**

## Retry / fallback / cooldown boundary

LiteLLM owns **model-request-level** reliability:

- retry a failed provider request;
- temporarily cool down unhealthy/rate-limited deployments;
- retry another deployment in the same model group;
- fall back to another configured model group/provider;
- enforce request timeouts and concurrency limits.

The Router deliberately prevents double retry loops by disabling provider-SDK internal retries when LiteLLM owns the routing retry loop.

This is not business/workflow retry.

```text
LiteLLM retry
= try to obtain one model response

Temporal retry/workflow
= durable application control flow

Runtime reconciliation
= physical effect/execution ambiguity handling
```

Do not allow these layers to retry the same semantic operation independently without an explicit retry ownership rule.

## Virtual keys and access control

LiteLLM Proxy virtual keys are a gateway-level indirection between applications/users/teams and upstream provider credentials.

They can carry/control:

- permitted model groups;
- ownership/team relationship;
- TPM/RPM/concurrency limits;
- budget/spend limits;
- expiration;
- route/model/MCP permissions depending on enabled features.

The Proxy can therefore keep raw OpenAI/Anthropic/Azure/etc. credentials away from downstream applications.

A LiteLLM virtual key is authority for **gateway model access**, not general Ordivon authorization and not provider/domain authority for non-model tools.

## Budget / spend boundary

LiteLLM can meter model usage and enforce budgets at proxy, key, user, team/member and related scopes.

Important operational fact: budget enforcement requires persistent database-backed spend state. Current documentation explicitly warns that DB-less deployments do not actually enforce configured spend budgets and can fail open.

Therefore:

- do not advertise budget guarantees without a working durable database;
- independently verify spend/accounting when budget enforcement is consequential;
- treat model-pricing metadata/cost calculation as operational accounting estimates unless reconciled against provider billing when financial accuracy matters.

LiteLLM budget state should not become Ordivon's general capital/accounting ledger.

## Rate-limit boundary

LiteLLM may enforce/request-route using:

- TPM;
- RPM;
- concurrent request limits;
- deployment cooldown state;
- provider health/failure information.

These are model-gateway capacity controls. They should not become a universal Resource Allocation subsystem.

## Caching boundary

LiteLLM supports exact-response caches and semantic caches across backends such as Redis/Valkey, S3/GCS, local/disk and Qdrant-backed semantic caching.

Use caching only when the application semantics permit replaying a previous model response.

### Exact cache

Useful for identical deterministic-ish requests where reusing the same prior response is acceptable.

### Semantic cache

Potentially useful for single-shot FAQ-like prompts, but dangerous for agentic/conversational traffic because a semantically similar request may require a different fresh response or tool decision. LiteLLM's own documentation warns semantic caching can go badly wrong on agentic traffic.

Do not enable semantic caching globally for Ordivon Agents.

## Observability boundary

LiteLLM exposes callbacks/integrations and OpenTelemetry support for model requests, costs, latency, identity and related gateway events.

Its newer OpenTelemetry v2 path intentionally delegates the HTTP root span to standard FastAPI instrumentation and uses canonical `gen_ai.*` attributes/mappers.

Correct ownership:

```text
LiteLLM
= instrument/export model-gateway events

OpenTelemetry / OpenInference
= telemetry semantic substrate

Langfuse / Phoenix / other backend
= analysis/evaluation/product UI if selected
```

Do not create Ordivon-native model trace/span semantics.

## Security / privacy boundary

A model gateway sits on a high-value path: prompts, responses, provider credentials, user/team identity and cost data can all pass through it.

Therefore:

- minimize logging of prompt/response content by default;
- use supported scrubbing/redaction controls when telemetry leaves the gateway;
- keep upstream credentials in secret managers/environment/provider-native auth rather than in workflow files;
- use virtual keys/OIDC/service accounts instead of distributing provider master keys;
- isolate Proxy admin/master-key authority from ordinary inference callers;
- pin/review deployments and supply-chain updates;
- verify licensing before relying on features under the `enterprise/` tree.

Gateway success does not establish model-output correctness or safety.

## Ordivon routing rule

Use the thinnest model-access layer that satisfies the workload:

```text
one provider + one application
    -> provider SDK directly

multiple providers in one Python application
    -> LiteLLM SDK

shared multi-app/Agent access, routing, credentials, budgets or governance
    -> LiteLLM Proxy / mature AI Gateway
```

Do not deploy a shared gateway merely for architectural symmetry.

## Boundary with Codex / Agent frameworks

LiteLLM supplies model access. Codex/Agent frameworks own the model-tool reasoning loop.

```text
Agent loop
   ↓ model call
LiteLLM
   ↓ provider selection/normalization
model provider
```

LiteLLM routing must not become Agent planning. Choosing which provider deployment serves a request is different from deciding which reasoning model/task strategy is best for the domain outcome.

A higher-level decision system may select a model group; LiteLLM then selects a concrete deployment inside that allowed group.

## Boundary with Temporal

A Temporal Activity may call LiteLLM to perform one model inference. The model result becomes Activity output/Event History state.

LiteLLM retries are request-level availability mechanics. Temporal controls durable application retry/orchestration. Avoid nested uncontrolled retries by assigning retry ownership deliberately.

## Boundary with MCP

MCP can expose tools/context to Agents and can itself be gateway-managed by some LiteLLM product features, but model-provider access and MCP capability access are separate authorities.

Do not make LiteLLM the universal authority for every Ordivon capability merely because it can manage model/MCP access in one product surface.

## Licensing boundary

Current main repository licensing is mixed by directory:

- source outside `enterprise/`: MIT;
- `enterprise/`: separate BerriAI Enterprise license/terms.

Before commercial embedding/modification, confirm that required features are in the MIT portion or obtain the appropriate commercial terms. Calling/operating the open-source gateway does not imply enterprise features are MIT.

## Prototype recipe

A minimal LiteLLM-like prototype needs only:

1. define a provider adapter interface for `completion(request) -> normalized response`;
2. implement two provider adapters;
3. normalize errors to a shared error taxonomy;
4. define model groups containing multiple deployments;
5. implement weighted/random deployment selection;
6. implement one bounded retry + fallback policy with one owner of retries;
7. attach cost/latency metadata;
8. optionally expose an OpenAI-compatible HTTP endpoint;
9. for gateway mode, issue one virtual key mapping to allowed models + limits;
10. persist key/spend state before claiming budget enforcement.

No Agent loop, workflow engine, vector database or custom observability backend is required to reproduce the architectural core.

## Prototype readiness gate

**PASS.** Provider normalization, SDK/Proxy split, deployment routing, retry/fallback ownership, virtual-key/budget/caching and observability boundaries are explicit enough to implement a minimal provider router/gateway or consume LiteLLM directly.
