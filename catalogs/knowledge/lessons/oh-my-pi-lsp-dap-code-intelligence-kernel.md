# Oh My Pi LSP + DAP Code Intelligence Kernel — extracted design and prototype specification

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Expose mature IDE and debugger protocols as compact Agent Tools so the model can ask semantic questions and issue semantic refactors/debug actions instead of simulating an IDE with grep or a debugger with print statements.**

## Problem

Coding agents commonly overuse generic primitives:

```text
grep -> read -> guess definition
edit many imports manually
insert print -> rerun -> guess runtime state
```

Mature standards already expose the missing machine semantics:

- **LSP**: definitions, references, symbols, diagnostics, rename, code actions, capabilities;
- **DAP**: launch/attach, breakpoints, stepping, stack, scopes, variables, evaluate, memory and modules where adapters support them.

OMP integrates both directly into the coding harness.

## Ordivon rule

**Adopt protocols, not proprietary ontologies.**

Do not invent an `OrdivonSymbolGraph` or `OrdivonDebuggerProtocol` unless standards fail a measured workload.

Harness owns the Agent-facing adapter and action authority. Language servers/debug adapters own protocol semantics. Runtime owns physical process/source truth where applicable.

# Part A — LSP kernel

## Minimum Agent-facing API

Use one `lsp` Tool with action variants rather than dozens of unrelated Tools:

```ts
type LspAction =
  | "diagnostics"
  | "definition"
  | "references"
  | "hover"
  | "symbols"
  | "rename"
  | "rename_file"
  | "code_actions"
  | "type_definition"
  | "implementation"
  | "capabilities";
```

Minimum request:

```ts
{
  action: LspAction,
  file?: string,
  line?: number,
  symbol?: string,
  query?: string,
  newName?: string,
  apply?: boolean
}
```

## LSP client lifecycle

```text
workspace/cwd
  -> detect language/server
  -> spawn or attach reusable server client
  -> initialize
  -> track server capabilities
  -> open/refresh target file
  -> request
  -> normalize result
```

Cache one client per meaningful `(server config, workspace)` identity.

Do not share one mutable LSP server across unrelated Workspaces unless the server/broker mechanism proves correct namespace separation.

## Read-only vs mutating LSP actions

Classify at the Harness Tool layer:

Read-oriented:

- diagnostics;
- definition;
- references;
- hover;
- symbols;
- type definition;
- implementation;
- capabilities.

Mutation-generating:

- rename;
- rename_file;
- code action with edits;
- raw request if allowed.

Even a mutation-generating LSP response should not directly become canonical source truth.

## WorkspaceEdit lowering

Safe Ordivon flow:

```text
LSP request
   -> WorkspaceEdit
   -> preview/normalize against current Workspace
   -> exact CanonicalEdit[]
   -> Runtime workspace.patch
   -> re-run diagnostics/tests
```

This lets LSP supply semantic refactor intelligence while Runtime retains exact mutation/recovery semantics.

## File rename

Implement the mature LSP lifecycle:

```text
workspace/willRenameFiles
  -> collect edits to imports/re-exports/etc.
  -> exact file move + edits through Runtime-safe mutation plan
  -> workspace/didRenameFiles notification
```

If current Runtime Patch cannot atomically represent move + edit, prototype the sequence in an isolated Workspace and explicitly document the weaker physical boundary rather than claiming atomicity.

## Diagnostics

Diagnostics are valuable post-edit verification evidence but are not sufficient semantic acceptance.

Retain a clean `OK`/zero-diagnostic result as evidence; empty definition/hover responses may be treated as low-value model context.

# Part B — DAP kernel

## Minimum Agent-facing API

Start smaller than OMP's full surface:

```ts
type DebugAction =
  | "launch"
  | "attach"
  | "set_breakpoint"
  | "continue"
  | "step_over"
  | "step_in"
  | "step_out"
  | "pause"
  | "threads"
  | "stack_trace"
  | "scopes"
  | "variables"
  | "evaluate"
  | "output"
  | "terminate";
```

Later add instruction/data breakpoints, disassembly, memory and modules based on adapter capability evidence.

## DAP state model

```ts
type DebugSession = {
  debugSessionId: string;
  adapter: string;
  targetRef: string;
  state: "starting" | "running" | "stopped" | "terminated";
  activeThreadId?: number;
  activeFrameId?: number;
  breakpoints: object[];
  capabilities: object;
};
```

The Agent Tool should hide protocol sequence noise while keeping capability failures explicit.

## DAP lifecycle

```text
resolve adapter
  -> launch adapter process/connect socket
  -> initialize DAP
  -> launch/attach target
  -> configure breakpoints
  -> configurationDone
  -> wait for stopped/terminated events
  -> inspect frames/scopes/variables
  -> continue/step/evaluate
  -> terminate/disconnect
```

## Runtime integration

There are two cases:

### Runtime owns target process

Preferred where possible:

- Runtime Job/Attempt remains physical process authority;
- DAP adapter attaches to that process or a debug launch provider binds back to the Runtime Job;
- debugger observations reference Runtime target identity.

### DAP launches target independently

Acceptable prototype/exception, but then DAP provider owns that target process truth. Do not fabricate a Runtime Job for a process Runtime did not supervise.

Long term, prefer a Runtime execution provider capable of debug launch/attach commitments if workloads justify it.

## Capability negotiation

DAP actions such as memory/disassembly must be gated on adapter-advertised capabilities. Unsupported action is a typed capability failure, not an invitation to guess.

## Cancellation

Cancelling an Agent debug Tool call is not necessarily terminating the debuggee. Keep these separate:

- abort one request;
- pause target;
- terminate target;
- close adapter session.

Explicit action semantics prevent accidental process loss.

## Minimum prototype stack

### LSP

- one TypeScript/Python/Rust language server already installed;
- JSON-RPC stdio client library;
- diagnostics/definition/references/rename;
- WorkspaceEdit -> Adaptive Edit Gateway lowering.

### DAP

- one debugger adapter such as debugpy or lldb/dlv;
- DAP client library or small protocol client;
- launch/attach, breakpoint, continue, stack, variables, evaluate;
- explicit session registry.

Do not implement protocol parsers from scratch if mature libraries are available.

## Acceptance tests

### LSP

1. Definition resolves correctly without grep heuristics.
2. References enumerate multiple files.
3. Rename preview produces a WorkspaceEdit.
4. Applied rename lowers through exact Runtime Patch rather than direct uncontrolled write.
5. File rename updates at least one import via `willRenameFiles` semantics where server supports it.
6. Diagnostics before/after edit are captured.
7. Server crash is isolated and restartable.

### DAP

1. Launch/attach one sample program.
2. Breakpoint stops at expected line.
3. Stack/scopes/variables return structured state.
4. Evaluate reads one local expression.
5. Continue reaches next breakpoint/termination.
6. Unsupported adapter capability fails explicitly.
7. Tool request cancellation does not silently terminate target unless `terminate` is requested.

## Project-study acceptance

### One-sentence test

PASS: OMP demonstrates that IDE/debugger protocols should be first-class Agent capabilities rather than reconstructed indirectly through text tools.

### Prototype test

PASS: the action subsets, lifecycle and Runtime/Edit lowering boundaries above are sufficient to build one LSP and one DAP prototype using standard protocol clients.

## Verdict

**PASS — DIRECTLY ADOPT MATURE LSP/DAP PROTOCOLS; KEEP HARNESS AUTHORITY AND RUNTIME PHYSICAL TRUTH.**
