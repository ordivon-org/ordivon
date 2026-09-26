# LiteLLM Model Gateway Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**
Registered: 2026-09-14

## One-sentence model

**LiteLLM separates model-provider variability from applications by normalizing request/response/error contracts, then optionally promotes that adapter layer into a shared gateway that owns deployment routing, model-access credentials, quotas/budgets and model-call telemetry.**

## Mechanism 1: adapter library and shared gateway are different deployment decisions

A frequent architecture mistake is turning every useful library into a service.

LiteLLM provides two distinct surfaces for good reason:

```text
SDK
= local application dependency

Proxy
= shared model-access control plane
```

Use SDK when one program merely needs provider portability.

Use Proxy only when multiple clients need shared concerns such as:

- centralized upstream credentials;
- virtual keys;
- model access policy;
- shared routing/fallback;
- cost/budget accounting;
- rate limits;
- common observability/guardrails.

General rule:

**Promote an adapter into infrastructure only when a shared policy/authority actually exists.**

## Mechanism 2: normalize provider transport, not model capability

OpenAI-compatible request/response shapes are useful anti-corruption layers, but models remain semantically different.

Do not infer that two providers are interchangeable merely because they both accept `/chat/completions`.

Differences may include:

- tool calling;
- reasoning controls;
- structured output;
- context window;
- modalities;
- prompt caching;
- tokenizer behavior;
- safety filters;
- latency/cost;
- data-region/privacy constraints.

Provider normalization should remove API boilerplate while leaving real capability selection visible to the caller/decision layer.

## Mechanism 3: separate logical model groups from physical deployments

The caller should often request a stable **model group/capability name**, not a concrete endpoint.

```text
logical model group
      ↓
router
      ↓
physical deployments/providers
```

This allows provider/region/key rotation and redundancy without rewriting application code.

But avoid semantic lies: group only deployments that satisfy the group's declared capability/quality contract.

## Mechanism 4: retry must have one owner

LiteLLM contains an especially useful reliability lesson: when its Router owns retry, provider SDK retries are disabled to avoid nested multiplication.

Generalize this:

```text
one logical operation
    ↓
one retry owner per layer of semantics
```

Model-request retry can belong to LiteLLM.

Durable workflow retry can belong to Temporal.

Opaque physical-effect ambiguity can belong to Runtime/provider reconciliation.

Do not let all three independently retry the same external semantic action.

## Mechanism 5: fallback is a capability decision, not only an availability decision

Failing from provider A to provider B can change:

- model behavior;
- quality;
- data residency;
- pricing;
- tool/structured-output support;
- safety policy.

Therefore cross-model/provider fallback should occur only within a caller-approved capability set.

Availability machinery should not silently downgrade requirements.

## Mechanism 6: start routing simple

LiteLLM exposes weighted, rate-aware, latency, cost, least-busy and custom routing, but its own production recommendation favors a simple shuffle/weighted strategy because usage-aware routing introduces Redis operations and latency.

General rule:

**Routing intelligence has coordination cost. Add it only when measured traffic/capacity/cost data justifies it.**

This directly argues against resurrecting a generic Ordivon Resource Allocation layer just because models have quotas.

## Mechanism 7: virtual keys are capability delegation

A gateway virtual key is a delegated authority boundary:

```text
upstream provider credentials
        ↓ held centrally
gateway policy
        ↓
virtual key
        ↓
application / Agent
```

The downstream client receives only the authority it needs: allowed model groups, quotas, expiry and related gateway permissions.

This is superior to copying provider master keys into every application.

## Mechanism 8: budget guarantees require durable accounting state

A configured number is not a budget guarantee by itself.

LiteLLM documentation explicitly notes DB-less deployments cannot enforce spend budgets reliably and can continue serving requests.

General rule:

**A limit is real only if its measurement, persistence and enforcement path are real.**

Keep model-gateway spend accounting separate from financial ledger/accounting truth; reconcile provider invoices when money-level accuracy matters.

## Mechanism 9: quotas belong near the constrained resource

TPM/RPM/concurrent-call limits are model-provider/gateway concerns.

Let the model gateway measure/enforce them close to the provider calls instead of centralizing all resource constraints in Ordivon.

A higher-level planner may observe capacity, but it should not duplicate the provider's quota truth.

## Mechanism 10: cache only when response reuse is semantically safe

Exact response caching can reduce model cost/latency.

Semantic caching is much more dangerous: a nearby embedding does not imply the prior answer/tool choice is valid for the new request.

Especially for agentic workflows:

```text
semantic similarity
!=
same state
!=
same required action
```

Do not enable semantic cache globally for interactive Agents. Caching should be workload-local and testable.

## Mechanism 11: observability belongs on standards

LiteLLM's OpenTelemetry direction is useful because the gateway does not need to invent another trace database/ontology.

Correct layering:

```text
model gateway emits spans/metrics/events
        ↓
OpenTelemetry / AI semantic conventions
        ↓
chosen backend
```

This prepares the next Ordivon study: OpenTelemetry + OpenInference should define the semantic substrate; Langfuse/Phoenix should later be evaluated as products on top.

## Mechanism 12: the gateway is not the Agent

Model routing is infrastructure selection:

> Which allowed deployment should serve this model request?

Agent reasoning is application/domain behavior:

> What should I do next, what tool should I call, which evidence is enough?

Do not put Agent policy, workflow state or domain completion into the model gateway simply because every model request passes through it.

## Mechanism 13: gateway success is not model correctness

A successful 200 response only establishes that an upstream model request completed.

It does not prove:

- factual correctness;
- safe tool choice;
- task completion;
- research validity;
- legal/business acceptability.

Domain V&V remains independent.

## Mechanism 14: centralized gateways increase blast radius

A Proxy simplifies clients but concentrates:

- provider credentials;
- prompts/responses;
- identities;
- spending authority;
- routing policy;
- telemetry.

Therefore moving from SDK to Proxy requires stronger secrets, access-control, logging/privacy, HA and supply-chain discipline.

Do not centralize unless the shared-policy benefit exceeds the new blast radius.

## Relationship to Ordivon

Ordivon should not own a generic model gateway.

Preferred routing:

```text
simple single-provider workload
  -> native provider SDK

provider-portable Python workload
  -> LiteLLM SDK

many Agents/apps needing common governance
  -> LiteLLM Proxy or another mature AI Gateway
```

Ordivon should retain only task/domain model-selection requirements and capability constraints, not provider API normalization or quota plumbing.

## Relationship to Codex

Codex/other Agents may consume a LiteLLM-compatible endpoint if that deployment is supported and useful. LiteLLM remains below the agent loop.

Do not route Codex through an extra gateway when direct provider access is simpler and no shared gateway requirement exists.

## Relationship to Temporal

Place model calls in Activities/side-effect boundaries when durable workflows require them. Record the returned model output as Activity result/history so replay does not silently call the model again.

Assign request-level retries to LiteLLM and workflow-level retries to Temporal deliberately.

## Relationship to OpenTelemetry / OpenInference

LiteLLM should emit/propagate standard telemetry. It should not become the semantic authority for all Agent spans.

The upcoming OpenTelemetry/OpenInference study should define the shared telemetry vocabulary and propagation boundary.

## What Ordivon should retain

1. Separate local provider-adapter use from shared gateway deployment.
2. Normalize API transport while preserving real model capability differences.
3. Address stable model groups rather than concrete deployments when redundancy is useful.
4. Give retry ownership to one layer at a time.
5. Restrict fallback to capability-compatible/approved models/providers.
6. Prefer simple routing until measured need justifies smarter coordination.
7. Delegate model authority through scoped virtual keys rather than distributing provider master credentials.
8. Treat budgets as real only when durable accounting/enforcement state exists.
9. Keep quotas near the model gateway/provider.
10. Enable response caching only where reuse semantics are explicitly safe.
11. Use OpenTelemetry/OpenInference-compatible observability rather than private model logs/traces.
12. Keep model gateway, Agent reasoning and domain verification as separate authorities.
13. Account for increased privacy/security blast radius when centralizing model traffic.

## What Ordivon should not copy

- provider-by-provider request/response adapters;
- another OpenAI-compatible model proxy;
- custom round-robin/fallback/cooldown machinery;
- virtual-key and model-budget databases;
- generic TPM/RPM quota coordination;
- private model cost tables unless required as a thin temporary fallback;
- semantic cache as a universal Agent memory layer;
- custom LLM tracing/observability ontology;
- Agent planning/workflow state inside the gateway.

## Minimal prototype

```text
Client
  ↓ normalized request
ProviderAdapterRegistry
  ↓
ModelGroup
  ↓
Router
  ↓
Deployment A / B
  ↓
normalized response
```

Add:

```text
virtual key -> allowed model groups
retry owner -> bounded retry/fallback
usage record -> durable DB -> budget check
standard telemetry callback
```

Two adapters and two deployments are enough to prove the architecture.

## Project-study acceptance

### One-sentence test

PASS: LiteLLM is a provider-normalization layer that can be promoted into a shared AI gateway owning model deployment routing, delegated access, quotas/budgets and telemetry.

### Prototype test

PASS: adapter normalization, logical model groups, routing/fallback, virtual-key delegation and durable budget enforcement are explicit enough to implement a small clone or use LiteLLM directly.

## Verdict

**PASS — USE A MATURE MODEL GATEWAY WHEN SHARED MODEL POLICY EXISTS; DO NOT BUILD ORDIVON-NATIVE MODEL PROXY/ROUTER.**

Further study should be workload-driven around a real gateway deployment, enterprise-only features, security hardening, exact provider/model compatibility or migration from an existing shared model proxy.
