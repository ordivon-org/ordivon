# Provider: n8n

Status: **AVAILABLE / PROTOTYPE-READY**  
Role: deterministic integration automation provider for APIs, SaaS applications, events and recurring business workflows.

## One-sentence understanding

**n8n turns external events and API/app operations into a credential-aware node graph that a workflow engine can execute, observe and retry without Ordivon owning the integrations.**

## When Ordivon should route work here

Prefer n8n when the workload is mainly:

- webhook/event driven;
- scheduled or recurring;
- SaaS-to-SaaS or API-to-API integration;
- deterministic transformation/routing;
- notification, approval or lightweight business automation;
- a repeated multi-service workflow whose control flow is known in advance.

Do not use n8n as the default substrate for:

- open-ended engineering/repository work;
- scientific reasoning;
- dynamic investigation;
- generic computer use;
- heavyweight scientific/data pipelines better served by domain workflow systems;
- Ordivon-wide task/state truth;
- local workstation execution already owned by Runtime/Codex or another natural provider.

## Core primitives

### Node

A node is a normalized external capability surface:

`capability descriptor + configuration schema + execution adapter`

Typical node execution modes include action/execute, poll trigger, webhook trigger and streaming/subscription trigger.

Use declarative HTTP/API routing where sufficient. Use provider-maintained programmatic nodes when the external API requires pagination, batching, binary handling, version quirks, custom retries or other service-specific behavior.

### Credential

Credential state is separate from capability/node description.

Conceptually:

`credential fields + authentication transform + credential test + usage boundary`

Credentials remain authoritative in n8n when n8n is the provider. Ordivon must not mirror secrets into a global credential database merely to compose the workflow.

### Trigger

Classify external event acquisition using mature terms:

- **Push/Webhook** — provider pushes an event;
- **Poll** — workflow periodically queries for changes;
- **Stream/Subscription** — long-lived event connection or subscription.

External webhook/subscription effects require lifecycle handling, not just creation:

`check/reconcile -> create if missing -> run -> delete/cleanup when retired`

### Workflow

A workflow is primarily:

`nodes + connections + parameters/expressions`

The workflow definition and execution history remain authoritative in n8n. Ordivon may reference or project them, but should not create a duplicate workflow state model.

### Workflow-as-code

Where practical, prefer agent-authored workflow source/SDK definitions over manual canvas authoring:

`intent -> agent -> workflow source -> validation/build -> n8n execution`

The visual editor remains useful for inspection/debugging, but is not required as Ordivon's primary authoring interface.

## Ordivon routing rule

For an external integration need, prefer in order:

1. an already-connected native ChatGPT connector/MCP provider when it directly satisfies the task;
2. an existing mature n8n node/workflow when the task is recurring/event-driven/multi-service;
3. generic HTTP/OpenAPI for a simple standard API;
4. a thin custom adapter only when the mature options are insufficient on a real workload.

## Authority boundary

- workflow truth -> n8n;
- n8n credential truth -> n8n;
- execution history for n8n workflows -> n8n;
- external service truth -> external provider;
- domain-semantic completion -> domain-specific verification, not n8n green status alone.

Do not copy n8n's workflow DB, credential DB, queue/worker model or execution engine into Ordivon.

## Prototype recipe

A minimal Ordivon-routed n8n prototype can be implemented with these pieces:

1. choose one Trigger: manual, schedule, webhook, poll or subscription;
2. bind credentials in n8n rather than in Ordivon;
3. compose one or more action/transform/control nodes;
4. define explicit success evidence at the target service;
5. create/import/build the workflow, preferably from code when automation authoring is useful;
6. execute it through n8n;
7. inspect the actual external target state, not only workflow execution success;
8. for external subscriptions, verify create/reconcile/cleanup lifecycle.

No Ordivon workflow engine, task database or credential store is required to implement this prototype.

## Prototype readiness gate

**PASS.** The core abstractions, authority boundaries, routing conditions and minimum implementation path are understood well enough to build a working prototype without further architectural study.
