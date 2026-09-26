# n8n Integration Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**n8n is an integration execution substrate: external event sources and API/app capabilities are normalized as credential-aware nodes, connected into deterministic workflows, and executed while n8n retains authority over its own workflow, credentials and execution state.**

## Why Ordivon cares

The valuable part for Ordivon is not owning another workflow platform. It is avoiding the recurring cost of writing and maintaining adapters for APIs, SaaS systems, event subscriptions, authentication flows and deterministic multi-service automation.

Use n8n as a provider; keep Ordivon responsible for problem classification, provider selection, composition decisions and domain-level verification.

## Extracted mechanisms

### 1. Prefer declarative integration before custom adapters

A large class of REST capabilities can be described as:

`credential + endpoint + method + parameters + response mapping`

Do not write a custom Ordivon adapter when an existing mature node, OpenAPI surface or generic HTTP integration is sufficient.

### 2. Separate capability from credential

A node describes what can be done. A credential provides authority to do it.

Do not embed secrets into capability definitions and do not centralize provider credentials into Ordivon without a proven cross-provider requirement.

### 3. Keep credentials with their natural provider

Examples:

- n8n node -> n8n credential;
- native connector -> connector/provider auth;
- Cloudflare capability -> Cloudflare authority;
- GitHub CLI -> GitHub CLI credential context.

Ordivon should usually know only that a capability is available and usable.

### 4. Use the standard event acquisition taxonomy

External events normally reduce to:

- Push/Webhook;
- Poll;
- Stream/Subscription.

Avoid inventing a private Ordivon event vocabulary unless a real residual gap exists.

### 5. Treat external subscriptions as lifecycle-managed effects

Creating a webhook/subscription is insufficient.

The minimal lifecycle is:

`observe/check -> reconcile -> create if absent -> operate -> remove/cleanup when no longer desired`

This prevents duplicate registrations and orphan external effects.

### 6. Route deterministic integrations to deterministic workflow providers

If the task can be represented as a known graph of triggers, transforms, conditions and effects, prefer n8n over repeatedly asking an agent to improvise the same sequence.

Agents remain useful for designing/modifying the workflow and handling uncertainty boundaries.

### 7. Prefer workflow-as-code for agent authoring

For Agent-first operation, the desirable path is:

`human intent -> agent-generated workflow definition/source -> validate/build -> n8n -> external systems`

The canvas is a useful human inspection/debugging surface, not a required authoring primitive.

### 8. Do not duplicate n8n state

When n8n owns a workflow:

- n8n owns its workflow definition;
- n8n owns its credential references/secrets;
- n8n owns its workflow execution history;
- external systems own their target state.

Any Ordivon cross-system view should be a disposable reference/projection rather than a new source of truth.

### 9. Provider execution success is not domain success

A green n8n execution proves that the workflow engine completed its mechanics. It does not automatically prove the intended external/business outcome.

Verify the actual target state when the outcome matters.

## Practical routing heuristic

Use this decision order for external-service work:

`native connector/MCP -> mature n8n integration -> generic HTTP/OpenAPI -> thin custom adapter`

Move downward only when the earlier option fails the actual requirement.

Use n8n preferentially when multiple systems, recurring triggers or event lifecycle management are involved. For one simple synchronous API call, direct connector/HTTP access may be thinner.

## Minimum prototype knowledge

A developer/agent who understands the following can implement a useful prototype:

1. choose trigger type: webhook, poll, stream/subscription, schedule or manual;
2. select existing node or generic HTTP operation;
3. bind provider-owned credentials;
4. connect nodes and basic control flow;
5. define the desired external effect and verification evidence;
6. create/import/build the workflow;
7. run it and inspect execution;
8. verify external reality;
9. clean up external subscriptions where applicable.

That is sufficient prototype knowledge. Deeper knowledge of n8n's frontend, worker queue internals, database schema, enterprise collaboration, LangChain subsystem or task runner is not required unless a real workload exposes a need.

## Deliberately not adopted into Ordivon

- a custom n8n-compatible workflow IR;
- a duplicate workflow engine;
- n8n execution database semantics;
- n8n credential database semantics;
- queue/Redis/worker internals as Ordivon infrastructure;
- n8n visual editor internals;
- n8n AI-agent/LangChain stack as Ordivon's agent layer;
- a global Ordivon trigger framework.

## Project-study acceptance rule

A GitHub project is considered sufficiently understood for this learning track when both are true:

1. **one-sentence test** — its essential mechanism and role can be stated accurately in one sentence;
2. **prototype test** — we understand the minimum primitives, boundaries and execution path well enough to implement a small working prototype or compose the mature project directly.

If either test fails, continue source-level study before moving to the next project.

## n8n verdict

**PASS.** One-sentence understanding is stable and the prototype path is explicit. Further source study should now be demand-driven rather than exploratory.
