# Runtime Tool Necessity Audit R1

Source revision: `75dc93c56e367535cbff0d50921d188798c9de5e`

## Decision rule

Tool necessity is judged by **independent semantic contract**, not by repository reference count. A low-use Tool that protects a distinct authority/recovery boundary stays; a high-use Tool can still be a compatibility candidate if another primitive fully subsumes it.

## Result

- Public Tools audited: **23**
- Immediate deletions: **0**
- Explicit compatibility review: **`workspace.diff`**
- Narrow-boundary reviews: **`workspace.mutate`**, **`workspace.execPlan`**
- Safety-specialized execution Tools retained: **`workspace.execBound`**, **`workspace.execBoundTrusted`**, **`workspace.execCredentialBoundTrusted`**
- Operator-specialized Tools retained: **`input.ingest`**, **`release.apply`**, **`release.get`**

### Why not delete low-use Tools?

`job.list` and `workspace.list` are recovery/inventory surfaces; `release.*` is operator-only; `input.ingest` is opt-in ingress; credential-bound execution is a safety-separated secret-delivery contract. None should be deleted because normal source consumers are sparse.

### Real reduction opportunity

The main reduction is **internal**, not public: compile the execution-family Tools through one `AuthorityContract + OperationCircuitCompiler`. Public separation can remain as a safety affordance while duplicated implementation paths disappear.

### `workspace.diff`

The Tool describes itself as a legacy convenience surface. Keep it until every real consumer can obtain both bounded structured changes and required patch/rename semantics without loss. Then deprecation is plausible.

### `workspace.mutate`

Keep it narrow for atomic digest-fenced synchronous edits. It has no durable clientRequestId receipt, so durable Harness workflows should continue to prefer `workspace.exec` with a mature mutation tool. Do not widen it into a second patch/effect control plane.

### `workspace.execPlan`

Keep only as a bounded sequential Job-local plan. Adding branching, scheduling, compensation, cross-Job dependencies, or workflow semantics would violate Runtime ownership.
