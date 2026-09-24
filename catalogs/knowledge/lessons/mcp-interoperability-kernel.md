# MCP Interoperability Kernel — extracted design lessons

Status: **REGISTERED / PROTOCOL-READY**
Registered: 2026-09-14
Studied against stable MCP specification: **2026-07-28**

## One-sentence model

**MCP standardizes how an AI host discovers context/capabilities and invokes them across process/network boundaries; it deliberately does not standardize the internal execution, workflow, trust or domain semantics behind those capabilities.**

## Mechanism 1: protocol should expose capability, not absorb provider semantics

A tool may expose `deploy`, `query`, `render`, `execute` or `create_invoice`, but the MCP layer should not redefine what those operations mean internally.

General pattern:

```text
Agent / Host
    ↓
MCP schema + transport
    ↓
Provider-native adapter
    ↓
Provider/domain system
```

The server adapter translates protocol calls into provider-native actions and translates results back. Provider semantics stay provider-native.

## Mechanism 2: keep context, templates and actions as distinct primitives

MCP's server primitives encode an important separation:

```text
Resources = contextual data
Prompts   = reusable user-facing interaction templates
Tools     = executable capabilities
```

Do not collapse all three into a generic `tool` abstraction when the distinction improves control, caching and UX.

This also prevents accidental authority escalation: reading context is not the same operation class as executing a side effect.

## Mechanism 3: control should live at the natural actor

The protocol's control model is intentionally asymmetric:

- Prompt selection is user-controlled;
- Resource attachment/management is application-controlled;
- Tool invocation is model-controlled within host policy.

The host still owns trust/approval policy around all three.

This supports a broader Ordivon rule:

**Capability description and actor intent are inputs to authorization, not authorization itself.**

## Mechanism 4: stateless transport is better than hidden session authority

The 2026-07-28 protocol removed transport-level sessions and the initialization handshake. Requests carry their version/capabilities explicitly.

When cross-call state is actually necessary, use an explicit provider/server-minted handle passed in ordinary parameters.

This is a strong design lesson:

```text
hidden transport session state
    <
explicit domain/provider state handle
```

because the state becomes inspectable, routable, cacheable and easier to recover across server instances.

Do not create global Ordivon chat/session truth merely because a connector needs continuity.

## Mechanism 5: multi-step interaction does not require bidirectional session RPC

MCP's Multi Round-Trip Requests demonstrate a stateless pattern for missing information:

```text
request
  ↓
input_required(requests, opaque requestState)
  ↓
client obtains input
  ↓
retry original operation + inputResponses
  ↓
complete
```

This is useful beyond MCP: long/open server callbacks are not the only way to model interactive operations.

The server can encode continuation state in a bounded opaque handle instead of requiring an always-open stateful connection.

## Mechanism 6: execution handles are projections, not execution engines

The official Tasks extension can expose a durable/long-running operation as:

```text
taskId
status
poll interval
TTL
input-required state
result/error
```

But the protocol explicitly relies on the server to durably create/manage that task before returning it.

Therefore:

```text
MCP Task
= interoperable job handle / observation surface
!= durable execution substrate
```

This is the correct boundary for Ordivon Runtime, Temporal, n8n, ComfyUI and other engines: each may project execution state through MCP without surrendering its internal authority model.

## Mechanism 7: protocol-level durability must not be inferred from transport retry

A failed network stream, retried `tools/call`, or successful JSON-RPC response does not establish external-effect idempotency.

MCP provides request/response semantics, not exactly-once side effects.

Consequential providers still need provider/domain mechanisms such as:

- idempotency keys;
- transaction identifiers;
- durable Job/Attempt records;
- provider-native operation IDs;
- reconciliation/read-back.

Do not solve effect semantics in the connector transport.

## Mechanism 8: extension framework is preferable to core inflation

The 2026 core moves optional functionality such as Tasks into explicit extensions and provides capability negotiation for independent features.

Retain the lesson:

**Keep the interoperable core small; move specialized semantics into independently negotiable extensions or provider APIs.**

This aligns with Ordivon's own principle that the common core should be capability-neutral.

## Mechanism 9: deprecation is architectural guidance

MCP now formally deprecates features such as Sampling, Roots and Logging rather than making them permanent core obligations.

Their suggested replacements are revealing:

- Sampling -> direct model-provider API;
- Roots -> tool/resource/configuration parameters;
- Logging -> stderr/OpenTelemetry.

This is mature substitution behavior: if a more natural authority exists, remove the protocol abstraction rather than keep layering compatibility forever.

Ordivon should follow the same discipline.

## Mechanism 10: authorization should bind tokens to the actual resource

MCP's HTTP authorization requires OAuth-style audience/resource binding so tokens for one server are not blindly accepted by another.

General lesson:

`credential valid somewhere != credential authorized here`

Token audience, issuer, target resource and scopes/claims must be validated at the receiving boundary.

This matters especially when many MCP servers sit behind gateways/proxies.

## Mechanism 11: protocol auth is not business authorization

OAuth can establish that a caller has access to an MCP server. It cannot alone decide that a particular user/model should:

- transfer money;
- delete production data;
- publish media;
- sign a contract;
- execute privileged local commands.

Keep business/host approval and provider authorization independent.

## Mechanism 12: observability should ride standards, not protocol-specific logs

The current spec explicitly points tracing toward OpenTelemetry trace-context propagation and deprecates the old MCP Logging feature.

Correct architecture:

```text
MCP request
 + traceparent/tracestate/baggage
      ↓
provider/executor spans
      ↓
OpenTelemetry pipeline
```

MCP should transport correlation context; OpenTelemetry should own telemetry semantics/storage/export.

## Mechanism 13: reference implementation status is not production maturity

The official reference-server repository states that its servers demonstrate protocol/SDK patterns and are not production-ready solutions.

This is an important project-selection lesson:

**Official reference implementation proves intended protocol usage, not production security, scalability or product fitness.**

Evaluate production servers/providers separately.

## Relationship to Agent Skills

```text
Agent Skill
= procedural knowledge: how/when to perform a task

MCP
= interoperability: how a host/client accesses external context/capability
```

A Skill may tell an Agent when/how to call MCP tools. MCP may transport prompt templates, but neither replaces the other.

## Relationship to Codex

Codex has its own tool registry/agent loop. MCP is one way for tools/capabilities to enter that registry.

```text
Codex agent loop
     ↓
Tool Registry
     ├─ native tools
     ├─ shell/apply_patch
     └─ MCP-derived tools/resources
```

Do not wrap native Codex tools in MCP merely for visual symmetry unless interoperability requires it.

## Relationship to n8n

MCP exposes capabilities/context to AI hosts. n8n executes deterministic/event-driven integration workflows.

An MCP tool can invoke n8n; n8n can call MCP-capable services; neither replaces the other.

## Relationship to Ordivon Runtime

Runtime owns exact local physical execution evidence and durability semantics where required.

MCP can expose Runtime tools/jobs to Agents, but:

```text
MCP successful tool call
!= Runtime physical execution semantics
!= domain completion
```

The Runtime provider card should retain this separation.

## What Ordivon should retain

1. Adopt MCP protocol semantics directly rather than private connector RPC schemas.
2. Keep Tools, Resources and Prompts semantically distinct when useful.
3. Prefer explicit provider state handles over hidden transport sessions.
4. Use stateless multi-round-trip interaction for additional input when appropriate.
5. Treat MCP Tasks as an interoperable job projection, not a scheduler/runtime.
6. Keep exactly-once/idempotency/recovery semantics in the natural execution/provider layer.
7. Use extensions instead of inflating the core.
8. Follow deprecations toward more natural authorities rather than preserving obsolete abstractions.
9. Bind remote credentials to their intended MCP resource/server.
10. Keep protocol authorization separate from business/host approval.
11. Propagate OpenTelemetry context rather than invent MCP-specific observability.
12. Treat reference servers as learning artifacts, not automatically trusted production dependencies.

## What Ordivon should not copy

- a private MCP-like protocol;
- hidden session state above the provider/domain state;
- deprecated Sampling/Roots/Logging semantics in new code;
- MCP reference servers as production systems without threat-model review;
- a universal MCP task database;
- tool descriptions as authorization policy;
- transport retries as side-effect idempotency;
- MCP metadata as domain truth;
- custom telemetry semantics that duplicate OpenTelemetry.

## Minimal prototype

A minimal server/client pair can be built as:

```text
Client
  │ JSON-RPC request + per-request version/capabilities
  ▼
Server
  ├─ server/discover (optional)
  ├─ tools/list
  ├─ tools/call
  ├─ resources/list/read
  └─ prompts/list/get
```

One tool can deliberately require missing input:

```text
tools/call
  ↓
input_required
  ↓
client gathers form value
  ↓
retry with inputResponses
  ↓
complete
```

The same server can then project an existing durable background Job through the Tasks extension to demonstrate the difference between protocol job observation and execution ownership.

## Project-study acceptance

### One-sentence test

PASS: MCP is a stateless Agent-capability/context interoperability protocol, not an execution or business-state engine.

### Prototype test

PASS: a conforming subset requires only JSON-RPC, per-request capabilities, the three server primitives, one MRTR elicitation exchange and a transport; durable tasks/auth/extensions can be added independently.

## Verdict

**PASS — ADOPT STANDARD / DELETE PRIVATE CONNECTOR SEMANTICS WHERE MCP IS SUFFICIENT.**

Further study should be workload-driven around a concrete extension, conformance requirement, enterprise auth deployment or MCP security problem.
