# Oh My Pi Persistent Eval + Tool Re-entry Kernel — extracted design and prototype specification

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Keep a session-scoped language runtime alive across Agent turns and let code inside it call the same admitted Agent Tools, so deterministic data processing and tool composition happen in code rather than through repeated model round-trips.**

## Problem

Without persistent eval, an Agent often performs:

```text
model -> shell/python -> huge output -> model -> another shell/python -> ...
```

This wastes tokens, repeatedly reconstructs program state and turns deterministic computation into language-model cognition.

OMP exposes persistent Python and JavaScript/Bun cells, retained state, structured `display()`, artifact-backed output, cancellation, backgrounding and a bridge back into session Tools/subagents.

## Ordivon ownership

Harness owns:

- eval-kernel identity within an Agent Run;
- which languages are available;
- Tool bridge admission;
- model-visible output projection;
- kernel lifecycle.

Runtime/provider owns:

- physical worker process if executed through Runtime;
- process resources/cancellation/evidence where Runtime is chosen as supervisor.

A kernel never gains authority merely because it exists.

## Core law

```text
kernel availability != Tool authority
```

Every `tool.<name>(args)` invoked from code MUST pass through the same Harness turn/Run Tool-admission path as a direct model Tool call.

The bridge is transport, not privilege escalation.

## Minimum API

Model-facing Tool:

```json
{
  "language": "py",
  "code": "data = ...",
  "title": "optional",
  "timeout": 30,
  "reset": false
}
```

Minimum result:

```ts
type EvalResult = {
  language: "py" | "js";
  status: "ok" | "error" | "cancelled" | "backgrounded";
  stdoutTail: string;
  structuredDisplays: unknown[];
  artifactRefs: string[];
  durationMs: number;
  jobId?: string;
};
```

## Kernel identity

Key retained workers by at least:

```text
HarnessRunId + language + workspace/cwd identity + interpreter/runtime identity
```

This prevents accidental state sharing across unrelated Runs or Workspaces.

Prototype keys:

```ts
python:${runId}:${workspaceDigest}:${pythonExecutableDigest}
js:${runId}:${workspaceDigest}:${jsRuntimeDigest}
```

## Worker protocol

A minimal worker transport can be newline-delimited JSON over stdin/stdout:

```ts
type KernelRequest =
  | {type:"execute"; cellId:string; code:string}
  | {type:"reset"}
  | {type:"shutdown"};

type KernelEvent =
  | {type:"stdout"; text:string}
  | {type:"stderr"; text:string}
  | {type:"display"; value:unknown}
  | {type:"tool_call"; callId:string; name:string; args:unknown}
  | {type:"done"; cellId:string; ok:boolean};
```

The host answers `tool_call` with a correlated Tool result after normal Harness authorization/execution.

## Tool re-entry flow

```text
model -> eval(code)
        |
        v
persistent kernel
        |
   await tool.read(...)
        |
        v
Kernel Bridge
        |
        v
Harness Tool admission
        |
        v
actual provider / Runtime
        |
        v
structured Tool result
        |
        v
kernel continues computation
        |
        v
display(compact_result)
        |
        v
model
```

The key performance gain is that raw intermediate Tool data can be transformed/filter/aggregated inside code before returning to the model.

## Structured display

Support at minimum:

- string/text;
- JSON-compatible object/array;
- table-like arrays;
- image/artifact reference.

Large output must spill to Artifact/CAS storage and return only a bounded tail + reference.

`display()` is preferable to forcing the model to parse arbitrary stdout.

## Persistent state

State survives cells in the same language/runtime:

```text
cell 1: import + load data
cell 2: transform existing variable
cell 3: compare with Tool result
```

`reset=true` kills/recreates only that language runtime for the Run.

Do not share mutable globals between Python and JS unless an explicit bridge/data object exists.

## Cancellation and timeout

Two clocks should be distinguished:

1. **runtime work clock** — actual computation/output/tool execution budget;
2. **host wait clock** — time waiting for child Agent/model handles if such bridges exist.

For the first prototype, one wall-clock timeout is acceptable, but cancellation MUST propagate:

```text
Harness cancel
  -> kernel execute cancellation
  -> pending Tool calls cancelled/observed according to their own semantics
  -> worker remains reusable only if its state is known-consistent
```

If cancellation may leave interpreter state ambiguous, destroy and recreate the worker rather than pretending it is clean.

## Backgrounding

Optional second-stage feature:

- if a cell exceeds a threshold, return a managed async handle;
- keep streaming to Artifact/output sink;
- inject/offer result later;
- foreground model remains available for new caller input.

This is useful but not required to prove persistent eval.

## Subagent bridge

OMP also permits `agent(...)` from Eval. Ordivon should implement this only as syntactic sugar over the Child Run kernel:

```python
h = await agent(prompt, schema=..., tools=[...])
result = await h.wait()
```

The Eval kernel MUST NOT maintain an independent subagent authority or scheduler.

## Security boundary

The initial prototype should default to owner-trusted code, matching current Runtime/Harness assumptions.

Still enforce:

- Tool names from the current admitted Tool set only;
- no secret injection merely because the kernel has filesystem/process access;
- clear workspace/cwd identity;
- output bounds;
- explicit reset/shutdown;
- resource quotas where possible.

For hostile code, use an external sandbox/VM boundary instead of claiming the persistent interpreter is a security sandbox.

## Minimum implementation stack

### Python first

- Python subprocess;
- persistent event loop or simple exec namespace;
- JSONL bridge;
- retained globals dict;
- `display()` helper;
- async `tool()` RPC helper;
- bounded stdout/stderr capture;
- Runtime-supervised process or explicit Harness child process.

### JavaScript later

Add Bun/Node only after Python proves workload value. Language plurality is not itself a kernel requirement.

## Acceptance tests

1. Variable created in cell 1 is available in cell 2.
2. `reset` removes prior state.
3. Code calls an admitted read-only Tool and uses returned value without model round-trip.
4. Attempt to call a non-admitted Tool is rejected by Harness.
5. Large output spills and leaves a bounded model-visible result.
6. Cancellation terminates the active cell and leaves kernel state explicitly reusable or destroyed.
7. Tool failure is returned to code as a structured exception/result, not silently swallowed.
8. Two Harness Runs do not share interpreter state.
9. Workspace identity change does not reuse the wrong retained kernel.
10. A compact computation benchmark uses fewer model tokens/turns than shell-loop baseline while producing the same verified result.

## Project-study acceptance

### One-sentence test

PASS: persistent eval is a stateful programmatic Tool-composition surface, not merely a convenience wrapper around `python -c`.

### Prototype test

PASS: the worker identity, JSONL transport, Tool re-entry contract and cancellation rules are enough to implement a Python prototype without inventing new authority semantics.

## Verdict

**PASS — HIGH-VALUE HARNESS CAPABILITY; PROTOTYPE PYTHON FIRST, REUSE NORMAL TOOL AUTHORITY.**
