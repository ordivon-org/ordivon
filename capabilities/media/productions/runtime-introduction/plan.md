# Runtime introduction production plan

This plan is derived from the Runtime implementation bound in `production.json`, not from a generic product-video template.

## The one proof

The first film should prove one complete property:

> After delivery becomes uncertain, one admitted operation still has a stable identity, can be recovered as the same Job, exposes bounded evidence, and can close only the exact Workspace state that was reviewed.

The film is not a catalog of every Runtime feature. Cancellation, restart reconciliation, backup, restore, administrative repair, deployment rollback, authority profiles, and protocol compatibility belong in later focused material.

## Existing code that makes the proof real

| Production fact | Current Runtime implementation |
| --- | --- |
| exact source binding | `workspace.open`, `workspace.get`, `sourceRevision`, `sourceStateDigest` |
| guarded change | `workspace.read`, durable `workspace.patch`, expected file digest and exact text range |
| durable execution identity | `clientRequestId`, Runtime Job, Attempt, source-state binding |
| observable progress | `task.observe` with status, elapsed time, progress revision, current/completed/failed step fields and bounded output |
| recovery after uncertain delivery | exact operation replay and `task.list(clientRequestId=...)` return the original recorded Job |
| durable evidence | stdout, stderr, result and terminal-evidence Artifacts exposed through `artifact.read` |
| reviewable source effect | `workspace.diff` with structured changed-path sets |
| exact cleanup boundary | `workspace.get.sourceStateDigest` plus `workspace.close.expectedSourceStateDigest` compare-and-close |

The implementation references are primarily:

- `scripts/mcp_probe.py` — reusable MCP client;
- `scripts/mcp_e2e.py` — complete real-system proof and request shapes;
- `crates/ordivon-runtime-core/src/runtime/types.rs` — Job, observation and Artifact results;
- `crates/ordivon-runtime-core/src/runtime/patch.rs` — durable Patch receipt and replay identity;
- `crates/ordivon-runtime-core/src/universal/types.rs` — Workspace, diff and close results;
- `docs/agent-ux.md` and `docs/runtime.md` — recovery and compare-and-close semantics.

## The executable demonstration

The clean recording path should be owned by `ordivon-runtime` as a new bounded demonstration client, tentatively:

```text
scripts/demo_runtime_flow.py
examples/runtime-demo/
```

It should reuse `scripts/mcp_probe.py::McpClient` and target the already installed loopback service. It should not rebuild Runtime, launch a temporary server, run the whole acceptance suite, or print credentials.

### Demonstration fixture

Use a tiny Python repository created from `examples/runtime-demo/` in a temporary directory. The fixture should contain:

- one readable source file with a small, explicit defect or configuration value;
- one test that fails before the guarded Patch and passes after it;
- one report command that emits a compact deterministic summary;
- no network dependency, secret, package installation or external service.

The fixture exists to make Runtime state visible. It is not presented as an AI benchmark or a meaningful software product.

### Demonstration trajectory

1. Create the temporary source repository and record its commit.
2. Call `workspace.open` and show the returned `workspaceId` and exact `sourceRevision`.
3. Call `workspace.read`; use its digest in one durable `workspace.patch` request.
4. Submit one `workspace.execPlan` with a stable human-readable `clientRequestId` and three steps: inspect, verify, report.
5. Recreate the MCP client and replay the exact operation request. Verify that the returned `jobId` and `attemptId` are unchanged.
6. Use `task.list(clientRequestId=...)` and `task.observe` to recover and observe the Job.
7. Read the terminal-evidence Artifact with `artifact.read` and show its Job, Attempt, Workspace and source-revision binding.
8. Show `workspace.diff` and its structured changed paths.
9. Read `workspace.get.sourceStateDigest` after review.
10. Call `workspace.close` with `force=true` and that exact `expectedSourceStateDigest`.
11. Write one redacted JSON receipt for Studio. It may contain identifiers, durations, statuses, digests and selected evidence fields, but never the bearer token, environment values, full local state roots or unrelated jobs.

The operation should last long enough for at least one non-terminal `task.observe` result, but it must not add artificial production delays to Runtime itself. A small deterministic fixture workload may take approximately three seconds.

## Presentation output of the demo client

The normal Runtime API remains structured JSON. The demonstration client should additionally support a presentation mode that prints one compact event at a time:

```text
SOURCE     5ce2…
WORKSPACE  ws-…  detached
PATCH      committed  sha256:…
JOB        job-…  attempt-…
STEP       inspect  1/3
STEP       verify   2/3
RECOVER    same job-…
EVIDENCE   terminal-evidence  sha256:…
DIFF       1 modified path
CLOSE      exact state matched
```

This is a projection of real responses, not a second state model. The JSON receipt remains the machine-readable capture source.

## Film structure

Target master: English, 16:9, approximately 78 seconds. Real product capture remains the majority of screen time.

| Time | Image | Proof |
| --- | --- | --- |
| 0–6 s | Programmatic hook: “The command ran. Did it commit? Can you reconnect?” | execution uncertainty is the problem |
| 6–13 s | Current `RuntimeFlow` composition | Workspace → Job → Attempt → Evidence → Recovery |
| 13–24 s | Real terminal: source commit, `workspace.open`, guarded Patch | exact source and protected mutation |
| 24–37 s | Real terminal: `workspace.execPlan` and one live `task.observe` | durable Job and observable progress |
| 37–48 s | New client / exact replay, then `task.list` by request identity | recovery returns the same Job, not new work |
| 48–59 s | Artifact descriptor and bounded terminal-evidence read | evidence survives the client interaction |
| 59–68 s | `workspace.diff`, `workspace.get`, compare-and-close | reviewed exact source state is the close fence |
| 68–75 s | Boundary card | owner-trusted Linux; not semantic completion; not a hostile-code sandbox |
| 75–78 s | End card | durable local execution for Agent and automation workflows |

## Media boundary

### Must be real capture

- the source repository commit;
- every MCP Tool call and compact response projection;
- the same recovered Job and Attempt identifiers;
- real Artifact digest and bounded content;
- real diff and source-state digest;
- successful compare-and-close result.

### May be programmatic motion

- the opening uncertainty question;
- the conceptual Runtime flow;
- a request-identity line reconnecting to the same Job;
- the source-state digest acting as a close fence;
- boundary and end cards.

Programmatic motion must explain real Runtime facts. It must not fabricate terminal sessions or substitute animated JSON for the core demonstration.

## What the first film should not show

- Cargo build output or temporary server startup;
- the complete `scripts/mcp_e2e.py` acceptance run;
- bearer tokens, environment values, source roots or unrelated Runtime history;
- giant raw JSON responses that cannot be read at viewing speed;
- cancellation, backup, restore, repair and rollback as a feature montage;
- claims of hostile-code isolation, semantic Task success or universal external-effect idempotency.

## Studio changes after the Runtime demo exists

Only three additions are justified for the first film:

1. a receipt-driven request-replay visual showing the same `clientRequestId` resolving to the same `jobId`;
2. a receipt-driven compare-and-close visual showing the reviewed `sourceStateDigest` matching the close request;
3. capture registration in `assets.json`, followed by narration timing and an editorial cut.

A generic dashboard, media database, visual editor, Runtime clone or cross-project Console is not required.

## Acceptance before recording

The demonstration is ready to capture only when:

- it runs twice against the installed service without manual cleanup;
- exact replay returns the same Job and Attempt;
- at least one non-terminal observation is available;
- the terminal-evidence Artifact can be read and verified;
- the diff contains only the intended fixture change;
- compare-and-close succeeds only for the reviewed source-state digest;
- the receipt contains no secret or unstable unrelated machine data;
- a failed run leaves a documented cleanup command and no active Job.
