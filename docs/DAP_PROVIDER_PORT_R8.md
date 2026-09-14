# DAP Provider Port R8

Status: provider-neutral authority model prototype

## Objective

Compose mature Debug Adapter Protocol implementations without pretending that debugging
is globally read-only and without making a debugger provider a second Runtime.

DAP differs materially from LSP. One protocol carries observations, target execution
control, debugger configuration, process lifecycle, and direct target mutation. Harness
therefore classifies each admitted action before any provider dispatch.

## Stable consequence classes

```text
observation
    threads, stackTrace, scopes, variables, source, modules,
    loadedSources, readMemory, disassemble, breakpointLocations,
    dataBreakpointInfo, exceptionInfo, completions

execution-control
    continue, next, stepIn, stepOut, stepBack, reverseContinue,
    pause, goto, restartFrame

debugger-configuration
    setBreakpoints, setFunctionBreakpoints, setExceptionBreakpoints,
    setInstructionBreakpoints, setDataBreakpoints

target-mutation
    setVariable, setExpression, writeMemory

process-lifecycle
    launch, attach, restart, terminate, disconnect

effect-capable
    evaluate
```

`evaluate` is intentionally never treated as observation-only. Debuggers may execute
inferior function calls or debugger commands as part of evaluation. A client-selected
`watch`/`hover`/`repl` context is not sufficient proof that evaluation is side-effect
free.

Raw/custom DAP requests are not in the Harness R8 action surface.

## Stop-epoch law

DAP thread/frame/variables references are transient provider handles. They are not durable
Harness identities.

```text
stopped event
    -> DapStopEpoch(session, epoch, thread)
    -> frame / variables / memory handles bind stopDigest

continue / step / resume
    -> old stop epoch is over
    -> old frameId / variablesReference MUST NOT be reused
```

A handle from one stop epoch fails closed against another stop epoch even if the debugger
happens to recycle the same integer id.

## Process and effect ownership

Every target binding declares both:

```text
processOwner    = runtime | dap-provider | external
effectExecutor  = runtime | dap-provider | external
```

These are distinct from semantic authority. A provider may control a process without
owning Harness Run truth. An observation-only action must claim `effectExecutor=none`;
an effectful action must identify the concrete physical executor.

The initial local GDB launch experiment is provider-owned: GDB launches and controls the
inferior. It must not be represented as a Runtime-owned target. A later attach experiment
may bind a Runtime-owned target explicitly if the operating system and debugger permit
that ownership split.

## Provider port

`HarnessDapProviderPort` exposes only:

```text
initialize() -> provider descriptors
execute(DapActionIntent) -> DapActionObservation
shutdown()
```

The action intent carries the stable Harness consequence class and, for stop-scoped
operations, the exact stop digest. Provider-advertised capabilities are descriptors only;
they do not modify immutable Run/Tool authority.

## Local GDB donor probe

The local machine provides GDB 17.2 with native DAP support (`gdb -i dap`). A temporary
Microsoft `@vscode/debugadapter-testsupport` client exercised a compiled C fixture through:

```text
initialize
setBreakpoints
launch
stopped
threads
stackTrace
scopes
variables
evaluate
continue
terminated
```

At the breakpoint in `add(int a, int b)`, GDB reported `a=2`, `b=3`, and local `sum=5`.
The evaluate request for `a + b` returned `5`.

GDB also advertised write-memory, set-variable, set-expression, cancel, and
single-thread execution capabilities. This is concrete evidence that a DAP provider
cannot be admitted as one read-only Tool merely because many common debugger queries are
observational.

## Next evidence gate

1. commit/regress this provider-neutral consequence/stop-epoch model;
2. rerun GDB from that exact implementation revision and retain a verified receipt;
3. separate provider-owned `launch` evidence from a Runtime-owned-target `attach` test;
4. expose only a compact Agent-facing debug action surface after Run/Tool authority
   distinguishes observation from execution-control and mutation consequences;
5. do not add a permanent DAP client dependency until provider lifecycle/fault behavior
   earns it.

## Revision-bound GDB launch evidence

After the consequence-aware provider port landed at:

```text
bd8aeec harness: add consequence-aware DAP provider port
```

a fresh local occurrence used GDB 17.2 native DAP and temporary Microsoft
`@vscode/debugadapter-testsupport 1.68.0` as the client donor. No DAP client dependency
was added to Harness.

The C fixture stopped in `add(int a, int b)` and produced:

```text
stack: add -> main
arguments: a=2, b=3
locals: sum=5
evaluate("a + b") = 5
continue -> exited -> terminated
```

GDB advertised `supportsWriteMemoryRequest`, `supportsSetVariable`,
`supportsSetExpression`, and `supportsCancelRequest`. The occurrence therefore
reinforces the consequence law: debugger capability presence is not read-only Run
authority, and even a successful watch-context evaluate remains classified
`effect-capable`.

This specific path is explicitly provider-owned:

```text
processOwner   = dap-provider
effectExecutor = dap-provider
Runtime-owned target = NOT CLAIMED
```

Verified receipt:

```text
evidence/dap-r8-gdb-launch-20260914.json
payload digest:
sha256:e889b292cb021f3a4655f5f0d31c8b1f2abb7d7889b4e0b45bfb4a94dfcd6860
```

The next ownership experiment is attach to a target whose process lifecycle originates
from Runtime rather than from GDB.
