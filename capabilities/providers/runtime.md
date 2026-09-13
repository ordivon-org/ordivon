# Provider: Ordivon Runtime

- Source: `/root/projects/ordivon-runtime`
- Observed revision: `e2c25e03dde1`
- Role: exact physical/local execution provider
- Migration mode: metadata only; Runtime remains external and replaceable

## Capabilities

- workspace-scoped execution;
- durable Job/Attempt/Artifact evidence;
- immutable/digest-bound inputs where configured;
- bounded Linux/Windows execution surfaces;
- exact execution/result projection and recovery-oriented inspection.

## Boundary

Runtime execution success is physical execution evidence only. It does not establish domain semantic completion or external-provider acceptance.

MCP is only an interoperability surface around such capabilities. If Runtime Jobs are exposed through MCP Tools or the official MCP Tasks extension, the MCP task/tool result is a protocol projection; Runtime remains authoritative for its Job/Attempt/Artifact execution evidence and recovery semantics. MCP transport retries or task handles do not themselves create exactly-once/idempotent external effects.

See `capabilities/providers/mcp.md` and `knowledge/lessons/mcp-interoperability-kernel.md`.

## Activation

Use only when a task requires this specific local execution/evidence boundary. Other mature execution providers may replace it without changing Ordivon Core.
