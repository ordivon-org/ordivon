# Provider: Ordivon Runtime

- Source: `/root/projects/ordivon/services/runtime`
- Observed owner revision: `7741c2e9e53fc4954ce16b692cfe19b27703caee`
- Role: exact physical/local execution and effect-commit evidence provider
- Source standing: canonical modular-monorepo owner; Runtime remains independently replaceable at the execution-provider boundary

## Capabilities

- workspace-scoped execution;
- durable Job/Attempt/Artifact evidence;
- immutable/digest-bound inputs where configured;
- bounded Linux/Windows execution surfaces;
- exact execution/result projection and recovery-oriented inspection.

## Boundary

Runtime execution success is physical execution evidence only. It does not establish domain semantic completion or external-provider acceptance.

MCP is only an interoperability surface around such capabilities. If Runtime Jobs are exposed through MCP Tools or the official MCP Tasks extension, the MCP task/tool result is a protocol projection; Runtime remains authoritative for its Job/Attempt/Artifact execution evidence and recovery semantics. MCP transport retries or task handles do not themselves create exactly-once/idempotent external effects.

Temporal owns generic durable-workflow semantics such as Event History/replay, durable timers, Activity retries/heartbeats, Task Queues/Workers, Signals/Updates/Queries and workflow Visibility. Runtime must not grow competing workflow/orchestration machinery. Its retained value is narrower: bind one Agent-proposed local physical operation to exact source/executable/input/authority facts, cross one physical dispatch boundary at most once per Attempt, own the concrete process tree, preserve identity-bound terminal evidence, and fail closed on ambiguous opaque effects rather than speculatively redispatching them.

The preferred composition for long-lived orchestration is `Temporal Workflow -> Activity -> Runtime` only when that Activity requires Runtime's exact local effect/evidence boundary; ordinary idempotent provider Activities should call their provider directly.

See `capabilities/providers/mcp.md`, `knowledge/lessons/mcp-interoperability-kernel.md`, `capabilities/providers/temporal.md`, and `knowledge/lessons/temporal-durable-execution-kernel.md`.

## Activation

Use only when a task requires this specific local execution/evidence boundary. Other mature execution providers may replace it without changing Ordivon Core.
