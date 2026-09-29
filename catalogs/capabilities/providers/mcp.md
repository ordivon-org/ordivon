# Provider / Standard: Model Context Protocol (MCP)

Status: **ADOPT STANDARD / PROTOCOL-READY**
Studied against stable specification: **2026-07-28**
Role: interoperability protocol between AI hosts/clients and external capability/context servers.

## One-sentence understanding

**MCP is a stateless JSON-RPC interoperability protocol that standardizes how AI hosts discover and invoke server-provided tools, read resources and retrieve prompts while leaving execution semantics, business state, security policy and domain truth to the participating systems.**

## Current protocol model — 2026-07-28

The stable `2026-07-28` specification materially simplifies the protocol core:

- JSON-RPC 2.0 message model;
- stateless, self-contained requests;
- protocol version + client capabilities carried per request in `_meta`;
- optional `server/discover` for up-front server capability discovery;
- no protocol-level `Mcp-Session-Id`;
- no mandatory `initialize` / `notifications/initialized` handshake;
- Streamable HTTP and stdio remain the important transport families;
- server-side list/read responses can carry cache hints;
- optional extensions are negotiated explicitly through `extensions` capabilities.

This is a transport/interoperability contract, not a workflow/runtime architecture.

## Host / Client / Server boundary

### Host

The AI application/orchestrator owns high-level composition, model/user interaction, trust policy and the set of MCP client connections.

### Client

A client is the protocol connector between one host and one particular server. The architecture describes a 1:1 client-to-server relationship while a host may manage many clients/servers.

### Server

A server owns a focused external capability/context surface and exposes selected MCP primitives. It can be a local process or remote service.

A server should not become an Ordivon-wide task authority merely because it is connected through MCP.

## Core server primitives

### Tools — model-controlled capability

Tools expose executable functions/actions to the model/host.

Typical protocol surface:

```text
tools/list
     ↓
Tool{name, description, inputSchema, ...}
     ↓
tools/call(name, arguments)
     ↓
result / error / input_required / optional task extension
```

The tool schema describes how to call a capability. It does **not** establish that:

- the server is trusted;
- the operation is safe;
- the caller is authorized;
- an external effect is idempotent;
- execution success means domain success.

Tool descriptions/annotations from an untrusted server are themselves untrusted data.

### Resources — application-controlled context

Resources expose readable contextual data/content through URIs and templates.

Typical surface:

```text
resources/list
resources/templates/list
resources/read(uri)
```

Resources are suited to data/context such as file contents, records, repository history or other server-owned readable material.

A Resource is not automatically a canonical knowledge object. The underlying source system remains authoritative unless the domain explicitly says otherwise.

### Prompts — user-controlled reusable interaction templates

Prompts expose parameterized message/workflow templates:

```text
prompts/list
prompts/get(name, arguments)
```

They are intended to be explicitly selected/invoked by a user-facing host rather than silently treated as executable authority.

Agent Skills and MCP Prompts overlap superficially in carrying instructions but differ structurally:

- Agent Skill = reusable procedural package activated by an Agent/client;
- MCP Prompt = server-provided parameterized interaction template exposed through protocol.

Do not create automatic one-to-one conversion rules between them.

## Core client primitive

### Elicitation

The current core client feature allows a server operation to request additional user/client input.

In `2026-07-28`, this uses **Multi Round-Trip Requests (MRTR)** rather than server-initiated JSON-RPC calls:

```text
client -> tools/call
server -> resultType=input_required + inputRequests
client gathers/authorizes input
client -> new tools/call request + inputResponses + requestState
server -> complete result
```

The retry uses a new JSON-RPC request ID. Server progress can be encoded in opaque `requestState` echoed by the client.

This keeps the transport stateless while supporting multi-step interaction.

## Deprecated client/server features

As of `2026-07-28`, new implementations should not adopt these protocol features:

- **Sampling** — deprecated; integrate directly with model-provider APIs instead;
- **Roots** — deprecated; pass directories/files through tool parameters, resource URIs or server configuration instead;
- **MCP Logging feature** — deprecated; use stderr for stdio or OpenTelemetry for structured telemetry.

Do not design new Ordivon architecture around deprecated MCP Sampling/Roots/Logging semantics.

## Extensions

The core protocol now provides an explicit extension negotiation mechanism. Extensions are opt-in and require both sides to declare support.

Examples include:

- Tasks;
- MCP Apps/UI;
- OAuth Client Credentials;
- Enterprise-Managed Authorization.

Extensions should remain independently versioned/provider-owned features rather than being copied into Ordivon Core.

## Tasks extension boundary

`io.modelcontextprotocol/tasks` is now an official extension rather than core protocol.

A long-running supported operation may return:

```text
resultType = task
Task{taskId, status, ttlMs, pollIntervalMs, ...}
```

The client can use:

```text
tasks/get
tasks/update
```

and continue polling until a terminal state. Task state can also become `input_required`.

Critical boundary:

**MCP Tasks standardizes client/server observation and interaction with long-running operations; it does not define the server's internal durable-execution implementation.**

A server still has to durably create/manage the task before advertising it. MCP Tasks therefore does not replace Temporal, Ordivon Runtime, a job queue or another execution substrate; it can expose such a substrate through a common protocol.

For Ordivon Runtime:

```text
Runtime Job/Attempt/Artifact semantics
        ↓ optional projection
MCP Tasks / Tools surface
        ↓
MCP client / Agent
```

Do not invert this and make MCP Tasks the physical execution authority.

## Transport boundary

### stdio

Useful for local child-process servers. Protocol messages travel over stdin/stdout; diagnostic logs should not corrupt protocol stdout.

### Streamable HTTP

Useful for remote MCP services. Current protocol behavior is stateless at request level; change notifications can use a dedicated subscription/listen stream.

`HTTP+SSE` from older MCP revisions is deprecated; new implementations should prefer Streamable HTTP.

Transport choice should not change domain semantics.

## Cache / discovery behavior

Current list/read responses such as `tools/list`, `prompts/list`, `resources/list` and `resources/read` carry cache metadata (`ttlMs`, `cacheScope`). Servers should return tool lists deterministically to support stable client/prompt caching.

Cache hints concern discovery/read performance. They do not create a domain freshness guarantee beyond the server's declared hint; consequential work must still verify current target state when required.

## Authorization boundary

For HTTP authorization, current MCP builds on OAuth 2.1-related standards and requires audience/resource binding, including RFC 8707 Resource Indicators.

Important rules include:

- bearer access tokens go in `Authorization` headers, not query strings;
- clients request tokens for the intended MCP server resource;
- servers validate token audience and accept only tokens intended for themselves;
- authorization-server issuer/resource metadata must be validated according to the specification/security guidance;
- optional enterprise and machine-to-machine authorization mechanisms live in extensions.

MCP authorization establishes access to an MCP server. It does not automatically establish per-tool business authorization, safe execution, human consent or downstream-provider authority. Servers/hosts must retain those checks at the natural system boundary.

## Observability boundary

The current protocol documents W3C/OpenTelemetry trace-context propagation through `_meta` (`traceparent`, `tracestate`, `baggage`).

This is the correct direction:

`MCP transports trace context; OpenTelemetry owns telemetry semantics.`

Do not invent a private Ordivon MCP logging/tracing schema.

## Reference-server rule

The official `modelcontextprotocol/servers` repository contains a small set of **reference implementations** (Everything, Fetch, Filesystem, Git, Memory, Sequential Thinking, Time).

The project explicitly warns that these are educational examples demonstrating MCP features/SDKs, **not production-ready solutions**.

Therefore:

- learn protocol usage from them;
- use production/provider-owned servers when available;
- evaluate threat model/permissions separately;
- do not infer maturity/security from being in the reference repository.

## Ordivon routing rule

MCP is appropriate when a capability needs a standard Agent-facing discovery/invocation/context interface.

Use:

```text
existing native connector/API
    ↓ if an Agent-standard surface is valuable
MCP server/client adapter
```

MCP does not justify wrapping every local command/API merely for uniformity. A direct API/SDK/CLI may remain thinner when no MCP interoperability is required.

## Ordivon ownership boundary

MCP should own only interoperable protocol semantics.

MCP should **not** own:

- business/domain truth;
- Job/Attempt execution truth;
- workflow orchestration;
- global Agent memory;
- provider credentials beyond protocol authorization exchange/storage mechanics;
- idempotency/exactly-once effects;
- sandbox policy;
- filesystem/process isolation;
- model routing;
- observability semantics;
- domain V&V.

Those remain with the natural provider, host, execution engine, identity system, OpenTelemetry stack or domain validator.

## Prototype recipe

A minimal current MCP implementation can prove the architecture with:

1. JSON-RPC 2.0 request/response codec;
2. per-request `_meta` carrying protocol version + client capabilities;
3. optional `server/discover`;
4. `tools/list` and `tools/call` with JSON Schema arguments;
5. `resources/list` and `resources/read`;
6. `prompts/list` and `prompts/get`;
7. one `input_required` MRTR elicitation round;
8. stdio transport;
9. optional Streamable HTTP POST surface;
10. OAuth/resource validation only if remote protected access is required.

Optional extension prototype:

11. return a durable external job as an MCP Tasks handle and expose `tasks/get` polling.

No database, workflow engine, model client, vector store or task scheduler is required by the MCP core itself.

## Prototype readiness gate

**PASS.** Host/client/server roles, stateless request semantics, core primitives, MRTR, transport, authorization, extension and execution-authority boundaries are explicit enough to implement a minimal conforming server/client pair without deeper source study.
