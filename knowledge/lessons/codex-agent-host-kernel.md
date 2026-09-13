# Codex Agent Host Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Codex is a coding-agent host: it keeps thread context, repeatedly lets a model choose between tool calls and a final answer, dispatches calls through policy-governed tool/execution boundaries, and exposes that lifecycle through replaceable client APIs.**

## Core loop

The essential mechanism is small:

`input -> model -> tool call -> policy -> execute -> result -> model -> ... -> final response`

A thread persists context across user turns; a turn contains the repeated sampling/tool cycle for one unit of user interaction.

## Extracted mechanisms

### 1. Keep the reasoning loop generic

The core agent loop should not contain service-specific execution logic. It needs only to distinguish model output that is:

- a tool request; or
- an assistant/final message.

Tool requests are handed to a registry/dispatcher, and their outputs become the next model input.

### 2. Separate tool specification, dispatch and runtime

A capability should have:

`tool schema/spec -> handler/dispatcher -> runtime/environment`

This lets shell, patching, MCP and future capabilities coexist without rewriting the agent loop.

### 3. Separate intent from authority

A model requesting an action is not authorization to perform it.

Evaluate requested actions against explicit approval, filesystem, network, execution and environment policies before performing side effects.

Prefer scoped additional permissions over broad unsandboxed execution.

### 4. Scope project instructions hierarchically

Repository guidance such as `AGENTS.md` can be inherited from project root toward the current path, with more-specific local instructions taking precedence.

This is a simple reusable pattern for large repositories: context follows the object being changed rather than loading one universal instruction block.

### 5. Keep execution environments replaceable

The agent loop should target an abstract/current environment rather than assuming all tools execute in the coordinator process.

A process/filesystem executor may be local or remote. Environment selection and execution transport are separate from reasoning.

### 6. Do not confuse execution transport with durable effects

Codex exec-server is an execution/session transport. Its forwarding path does not itself replay requests or persist a durable external-effect ledger.

Use a durable execution/effect provider only when the workload actually requires stronger recovery, receipt or exactly-once/reconciliation properties.

### 7. Expose the agent through structured APIs

A TUI is only one client. The same agent/thread lifecycle can be exposed via SDK or RPC surfaces.

For machine composition, prefer structured SDK/app-server protocols over GUI automation.

### 8. Persistent thread state is useful; global Task truth is not required

Codex persists enough conversation/thread information for resume/fork/inspection, but this does not make the thread a universal business/domain task record.

Keep domain truth in its natural owner.

### 9. Context is an active working set

Project instructions, Skills, MCP servers/tools, plugins and other context can be discovered or activated for the current work. They need not all be permanently injected into every model request.

This supports the Ordivon principle of a task-local capability working set.

### 10. Verification remains outside the agent's claim

A successful turn or final assistant message is not proof that the engineering goal was achieved.

Use tests, builds, integration behavior and target-system observation according to the Engineering method kernel.

## Minimal prototype architecture

```text
Client / Ordivon
      |
      v
Thread store / context
      |
      v
Model sampling loop
      |
      +------ final assistant message ------> done
      |
      v
tool call
      |
      v
Tool Registry
      |
      v
Approval / Sandbox Policy
      |
      v
Execution Environment
      |
      v
structured tool result
      |
      +------------------------------> model loop
```

A small prototype therefore needs only:

- thread history;
- model client;
- tool schema registry;
- one or two tools (`shell`, `apply_patch` is sufficient for a coding proof);
- approval/sandbox decision point;
- process/filesystem executor;
- structured events/results;
- final independent verification.

Everything else—TUI, plugins, cloud tasks, memories, apps, marketplace, multiple model providers, advanced multi-agent features—is product capability layered around this kernel.

## What Ordivon should use rather than rebuild

- Codex's coding-agent loop;
- Codex project instruction handling;
- Codex tool registry and shell/patch mechanics;
- Codex sandbox/approval machinery;
- Codex Skills/MCP support where useful;
- Codex SDK/app-server for embedding;
- Codex execution environment support for ordinary engineering work.

## What Ordivon should not delegate blindly

- cross-domain semantic acceptance;
- durable effect/reconciliation requirements that exceed Codex execution semantics;
- deterministic SaaS/business automation better owned by n8n;
- durable business/scientific workflow semantics better owned by domain workflow engines;
- global provider/credential/task authority.

## Project-study acceptance

### One-sentence test

PASS: Codex can be accurately described as a policy-governed coding-agent host built around persistent thread context plus a model/tool execution loop.

### Prototype test

PASS: the minimum primitives and execution path are explicit enough to implement a small functional clone, while Ordivon should normally embed the mature implementation instead.

## Verdict

**PASS.** Further Codex source study should be demand-driven: inspect specific subsystems only when Ordivon needs to integrate or replace a concrete boundary.
