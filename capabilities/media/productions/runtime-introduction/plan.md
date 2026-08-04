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

- `scripts/demo_runtime_flow.py` — bounded presentation-ready proof against the installed service;
- `examples/runtime-demo/` — deterministic no-network fixture;
- `scripts/mcp_probe.py` — reusable MCP client;
- `scripts/mcp_e2e.py` — complete real-system acceptance and request shapes;
- `crates/ordivon-runtime-core/src/runtime/types.rs` — Job, observation and Artifact results;
- `crates/ordivon-runtime-core/src/runtime/patch.rs` — durable Patch receipt and replay identity;
- `crates/ordivon-runtime-core/src/universal/types.rs` — Workspace, diff and close results;
- `docs/agent-ux.md` and `docs/runtime.md` — recovery and compare-and-close semantics.

## Executable demonstration

The recording path is owned by `ordivon-runtime`:

```text
scripts/demo_runtime_flow.py
examples/runtime-demo/
```

It reuses `scripts/mcp_probe.py::McpClient`, targets the installed loopback service, does not rebuild Runtime or launch a second server, and does not print credentials.

The fixture contains one explicit recovery-policy defect, one test that fails before the guarded Patch and passes after it, one deterministic report, and no network or package-install dependency.

### Demonstration trajectory

1. Create the temporary source repository and record its commit.
2. Call `workspace.open` and show the returned `workspaceId` and exact `sourceRevision`.
3. Call `workspace.read`; use its digest in one durable `workspace.patch` request.
4. Submit one `workspace.execPlan` with a unique request identity and three steps: inspect, verify, report.
5. Recreate the MCP client and replay the exact operation request; require unchanged `jobId` and `attemptId`.
6. Use `task.list(clientRequestId=...)` and `task.observe` to recover and observe the Job.
7. Read the terminal-evidence Artifact and verify its Job, Attempt, Workspace and source-revision binding.
8. Require `workspace.diff` to contain only `policy.py`.
9. Read `workspace.get.sourceStateDigest` after review.
10. Call `workspace.close` with `force=true` and that exact `expectedSourceStateDigest`.
11. Write a redacted JSON Receipt containing selected identities, timings, statuses and digests, but no bearer token, source path, Runtime state root or unrelated Job.

The fixture takes approximately three seconds and yields non-terminal observations without adding delays to Runtime itself.

## Verified demonstration result

The Demo has completed independent live runs against the installed service. Each run produced:

```text
SOURCE     <revision>
WORKSPACE  <workspace>  detached
PATCH      committed  <request digest>
JOB        <job>  <attempt>
RECOVER    same <job>
STEP       inspect  1/3
STEP       verify   2/3
STEP       report   3/3
EVIDENCE   terminal-evidence  <digest>
DIFF       1 modified path  policy.py
CLOSE      exact state matched  <source-state digest>
```

Within each run, replay returned the same Job and Attempt. Across runs, identities remained independent. Receipt audits verified identity binding, non-terminal observations, evidence consistency, one-file source effect, exact close, secret exclusion and cleanup with no residual demo Workspace.

The selected Studio Receipt is stored at `evidence/runtime-demo.receipt.json` and validated by `schemas/runtime-demo-receipt.schema.json` plus semantic checks.

## Film structure

Target master: English, 16:9, approximately 78 seconds. Real product capture remains the majority of screen time.

| Time | Image | Proof |
| --- | --- | --- |
| 0–6 s | Programmatic hook: “The command ran. Did it commit? Can you reconnect?” | execution uncertainty is the problem |
| 6–13 s | `RuntimeFlow` composition | Workspace → Job → Attempt → Evidence → Recovery |
| 13–24 s | Real terminal: source commit, `workspace.open`, guarded Patch | exact source and protected mutation |
| 24–37 s | Real terminal: `workspace.execPlan` and live `task.observe` | durable Job and observable progress |
| 37–48 s | Receipt-driven exact replay composition and selected real terminal output | recovery returns the same Job, not new work |
| 48–59 s | Artifact descriptor and bounded terminal-evidence read | evidence survives the client interaction |
| 59–68 s | Receipt-driven exact-close composition and selected real diff | reviewed source state is the close fence |
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
- the Receipt-driven request replay to the same Job and Attempt;
- the Receipt-driven source-state digest match;
- boundary and end cards.

Programmatic motion must explain real Runtime facts. It must not fabricate terminal sessions or substitute animated JSON for the core demonstration.

## What the first film should not show

- Cargo build output or temporary server startup;
- the complete `scripts/mcp_e2e.py` acceptance run;
- bearer tokens, environment values, source roots or unrelated Runtime history;
- giant raw JSON responses that cannot be read at viewing speed;
- cancellation, backup, restore, repair and rollback as a feature montage;
- claims of hostile-code isolation, semantic Task success or universal external-effect idempotency.

## Current Studio implementation

The first film now has:

1. a validated live Runtime Receipt;
2. a Receipt-driven request-replay composition;
3. a Receipt-driven compare-and-close composition;
4. a Preview evidence summary;
5. deterministic H.264/BT.709 rendering and QC.

A generic dashboard, media database, visual editor, Runtime clone or cross-project Console remains unnecessary.

## Acceptance before recording

The Runtime demonstration is ready for recording. The remaining capture acceptance is:

- no private terminal history or notifications enter the frame;
- the presentation projection remains readable at final viewing size;
- the selected capture file is hashed and registered before editing;
- visual playback review confirms no clipped text, unreadable identifiers or misleading timing;
- the captured run produces a Receipt that passes the same validation as the current selected evidence.
