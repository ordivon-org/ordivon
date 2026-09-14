# Provider: OpenAI Codex

Status: **AVAILABLE / PROTOTYPE-READY**  
Role: policy-governed coding-agent host and engineering execution provider.

## One-sentence understanding

**Codex turns a persistent engineering conversation into policy-governed tool actions over a workspace by looping model decisions through a tool registry, approval/sandbox controls, execution environments and structured thread/turn state.**

## When Ordivon should route work here

Prefer Codex when the workload is mainly:

- repository understanding and modification;
- shell/build/test/debug work;
- code review and engineering investigation;
- multi-turn software changes that benefit from persistent context;
- project-local instructions, Skills, MCP tools or repository-native tools;
- agentic engineering where the next action depends on observed code/tool results.

Do not treat Codex as:

- Ordivon's universal workflow engine;
- a durable cross-domain Job/Effect ledger;
- the source of domain-semantic completion;
- a replacement for n8n/Temporal/domain workflow systems when the work is deterministic or durability-oriented;
- a reason to duplicate its model/tool loop, sandbox, tool registry or session protocol inside Ordivon.

## Core primitives

### Thread / Turn

A thread preserves conversation/project context across multiple turns. A turn runs an agent loop until the model returns an assistant result with no further tool work, is interrupted, or encounters a terminal condition.

Conceptually:

`thread state + turn input -> model -> tool call? -> execute -> tool result -> model ... -> final response`

### Context / instructions

Codex assembles task context from the active conversation plus project-local guidance such as hierarchical `AGENTS.md`, configuration, Skills and available tool/provider metadata.

The useful design principle is scoped context inheritance: broad project instructions apply first; more-specific directory instructions override them for files in their subtree.

### Tool registry

Tools are registered capabilities with a specification and handler/runtime. Shell execution, patch application, MCP/tools and other capabilities are exposed through this registry rather than hard-coded into the reasoning loop.

Keep the model/tool loop generic; add capability through tool registration/providers.

### Approval and sandbox boundary

Execution authority is separate from model intent.

A tool request is evaluated against:

- approval policy;
- filesystem/network sandbox policy;
- command/exec policy and reusable scoped rules;
- any requested additional permissions;
- the selected execution environment.

Prefer least additional permission inside the sandbox; escalate beyond the sandbox only when the task actually requires it.

### Execution environment / exec-server

Codex can execute against a local or selected execution environment. `codex exec-server` is a small process/filesystem execution server and transport boundary, including remote transports.

Its transport layer is not a durable external-effect ledger: remote forwarding does not replay requests or persist execution state. Session/process resumption is limited to what the destination retains.

### Host/control surfaces

Codex can be driven through multiple replaceable surfaces:

- CLI/TUI;
- Python SDK;
- TypeScript SDK;
- app-server JSON-RPC protocol;
- MCP-facing surfaces.

Ordivon should prefer a structured supported surface rather than UI automation when embedding Codex.

## Ordivon boundary

For ordinary engineering work:

`Ordivon FRAME/PLAN -> Codex thread/turn -> tools/workspace -> Ordivon/domain VERIFY`

Codex owns the engineering agent loop and its thread/tool execution semantics. The repository/Git/build/test systems own their natural state. Ordivon owns only the problem-to-capability composition and domain-level acceptance framing.

Runtime remains useful where Ordivon specifically needs durable Job/Attempt/Artifact evidence, exact execution receipts, cross-domain physical execution authority or recovery semantics beyond Codex's execution transport. Do not route ordinary Codex shell work through a second executor merely for symmetry.

LangGraph is a different category: use it only when Ordivon is engineering a bespoke Agent application's explicit state machine, cyclic routing, checkpoint inspection/forking or dynamic human-interrupt behavior. Do not rebuild ordinary Codex engineering sessions as LangGraph graphs.

## Prototype recipe

A minimal Codex-like prototype needs only:

1. create/resume a thread containing conversation and project instructions;
2. assemble the tool specifications available for the current turn;
3. send context + tools to the model;
4. if the model returns a tool call, dispatch it through a registry;
5. evaluate approval and sandbox/permission policy before the side effect;
6. execute in the selected environment and capture structured output;
7. append the tool result to thread history and sample the model again;
8. stop when the model returns only the final assistant response;
9. persist enough thread/turn events to resume and inspect the conversation;
10. verify the requested engineering outcome independently of Codex's final claim.

For Ordivon there is normally no reason to build this clone: use Codex itself through its CLI/SDK/app-server and retain the prototype model only as architectural understanding.

## Prototype readiness gate

**PASS.** The agent loop, context model, tool registration, permission boundary, execution environment and host API boundaries are understood well enough to implement a minimal functional prototype or embed Codex directly.
