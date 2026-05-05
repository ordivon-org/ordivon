# Agent Evidence Import Boundary (EGB-2)

Status: **CURRENT** | Date: 2026-05-05 | Phase: EGB-2
Tags: `egb-2`, `agent-evidence`, `trace`, `checkpoint`, `skill`, `mcp`
Authority: `source_of_truth` | AI Read Priority: 2

## Purpose

Agent ecosystems increasingly produce traces, checkpoints, skills, hooks, tool
manifests, and memory records. Ordivon should verify evidence around these
objects without becoming an agent runtime.

## Read-Only Import Targets

| External object | Ordivon interpretation |
|-----------------|------------------------|
| OpenAI trace | Event evidence |
| LangGraph checkpoint | State evidence |
| Claude skill | Capability boundary evidence |
| MCP manifest or auth config | Tool boundary evidence |
| Hook or tool-call record | Execution-claim evidence |
| Memory record | Source/freshness evidence |

## Non-Authorization Rules

```text
runtime guardrail != independent verification
tool available != action authorized
skill capability != permission
trace present != truth
checkpoint present != review
memory present != current truth
```

## Boundary

EGB-2 does not add an adapter, SDK, MCP server, agent runner, token refresh,
external tool invocation, or agent execution path. Import contracts are
verify-only and read-only.
