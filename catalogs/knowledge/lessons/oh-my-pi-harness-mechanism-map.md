# Oh My Pi Harness Mechanism Map — extracted donor architecture

Status: **REGISTERED / PROTOTYPE-READY MAP**  
Registered: 2026-09-14  
Upstream: `can1357/oh-my-pi`

## One-sentence model

**Oh My Pi (OMP) is a high-density coding-harness donor whose reusable value is not one monolithic architecture but a set of replaceable Agent Computer Interface mechanisms that move fragile mechanical work out of the model while keeping semantic choice in the agent.**

## Why this matters to Ordivon

Ordivon now treats **Host, Harness, Runtime** as its three semantic cores. Everything else is replaceable implementation or domain/capability material.

OMP therefore MUST NOT become a fourth core and MUST NOT be copied wholesale. Its mechanisms are decomposed into independently selectable kernels that fit behind existing Ordivon truth boundaries.

```text
Host
  objective / Task / acceptance
        |
        v
Harness
  Agent Run / cognition / Tool authority / effect continuity
        |
        +-- OMP-derived replaceable mechanisms
        |     edit ABI
        |     session/context graph
        |     persistent eval
        |     child runs / hub
        |     live capability discovery
        |     LSP/DAP adapters
        |     stream intervention/advisor
        |
        v
Runtime
  Workspace / Job / Attempt / Patch / Artifact / physical recovery
```

The integration rule is:

> **Adopt mature mechanism; retain Ordivon semantic authority.**

## Extracted mechanism inventory

| Kernel | Problem solved | Ordivon owner | Standing |
|---|---|---|---|
| Adaptive Edit ABI | models know what to change but fail mechanical edit encodings | Harness -> Runtime Patch | HIGH / FIRST |
| Branchable Session + Context Projection | durable history is larger than current cognition | Harness | HIGH |
| Persistent Eval + Tool Re-entry | repeated shell/model turns waste context on deterministic computation | Harness capability | HIGH |
| Child Run + Agent Hub | parallel specialization and resumable delegated work | Harness + Runtime Workspace | HIGH |
| Live Capability/MCP Binding | installed/discovered capabilities change during a session | Harness | HIGH |
| LSP/DAP Code Intelligence | grep/print are weak substitutes for IDE/debugger protocols | Harness capabilities | HIGH / mature standards |
| Stream Intervention + Advisor | corrective knowledge need not permanently tax every prompt | Harness cognition experiment | EXPERIMENTAL |
| Resource/Tool Algebra | large capability ecosystems need a smaller model-facing vocabulary | Harness/interface design | CROSS-CUTTING |

## Cross-cutting design law: semantic choice vs mechanical encoding

OMP repeatedly applies one pattern:

```text
agent chooses semantic intent
        |
        v
small model-facing protocol
        |
        v
deterministic mechanism
        |
        v
real provider / Runtime / protocol
```

Examples:

- source change intent -> edit codec -> exact file mutation;
- symbol navigation -> LSP action -> language server;
- debugger intent -> DAP action -> debugger adapter;
- computation intent -> persistent cell -> language runtime;
- delegation intent -> child-run contract -> isolated child session/workspace;
- resource request -> compact internal URI/tool surface -> underlying store/provider.

This is the reusable architectural principle.

## Cross-cutting design law: small model-facing vocabulary

Do not expose every backend operation as unrelated Tool names when a smaller algebra can represent them safely.

Preferred form:

```text
many provider/backend capabilities
          |
          v
bounded semantic interface family
          |
          v
model
```

Examples include one `lsp` Tool with action variants, one `debug` Tool over DAP actions, one `task` Tool over child-run creation, and resource schemes such as `agent://` / `history://` for large outputs.

This does **not** mean collapsing authority. A small vocabulary is an interface property, not permission inheritance.

## Cross-cutting Ordivon authority law

OMP mechanisms must obey the existing three-stage capability relation:

```text
installed/discovered capability
        !=
Run-admitted capability
        !=
turn-admitted action
```

Dynamic discovery may update what exists. It does not silently update what a Run or turn is authorized to use.

Likewise:

```text
Tool request != Tool authorization
Tool execution success != semantic success
Agent Run completion != Host Task completion
session transcript != Runtime physical truth
```

## Prototype dependency order

The kernels are intentionally independent, but a sensible build order is:

1. Adaptive Edit ABI
2. Branchable Session + Context Projection
3. Persistent Eval + Tool Re-entry
4. Child Run + Agent Hub
5. Live Capability/MCP Binding
6. LSP/DAP Code Intelligence
7. Stream Intervention + Advisor

LSP can be introduced before step 6 specifically as an Edit-Gateway helper; the ordering above is for standalone kernel graduation.

## What must remain external/replaceable

Do not canonize OMP-specific:

- prompts;
- TUI behavior;
- provider list;
- exact session JSONL format;
- exact hashline syntax;
- exact worktree/isolation implementation;
- Bun as the only JavaScript runtime;
- exact agent names/roles;
- memory backend;
- browser/search implementations;
- advisor model selection;
- plugin marketplace/discovery UX.

Those are replaceable donor implementation choices.

## Prototype-readiness contract

A mechanism is considered extracted only if the corresponding kernel document specifies:

1. problem statement;
2. architectural laws;
3. minimum data structures;
4. model-facing or caller-facing API;
5. deterministic control flow;
6. authority/truth owner;
7. failure and cancellation behavior;
8. persistence/recovery boundary where relevant;
9. minimum implementation stack;
10. falsifiable acceptance tests.

## Upstream evidence anchors

Primary upstream references used for this extraction:

- `README.md`
- `docs/tools/edit.md`
- `docs/session.md`
- `docs/tools/eval.md`
- `docs/tools/task.md`
- `docs/agent-hub.md`
- `docs/tools/hub.md`
- `docs/tools/lsp.md`
- `docs/tools/debug.md`
- `docs/mcp-server-tool-authoring.md`
- `docs/extensions.md`
- `packages/coding-agent/DEVELOPMENT.md`

## Project-study acceptance

### One-sentence test

PASS: OMP can be decomposed into independently useful Agent Computer Interface mechanisms without making OMP itself an Ordivon semantic owner.

### Prototype test

PASS: every high-value mechanism is assigned a separate prototype-ready kernel with explicit Host/Harness/Runtime ownership.

## Verdict

**PASS — TREAT OMP AS A HIGH-DENSITY DONOR, NOT A NEW CORE.**
