# Ordivon Game source audit — Core A series

## Status

This report records the source-level audit and hardening pass completed on 2026-08-01.

The audit did not redesign Station Zero, promote a generic Game platform, activate `ANC-GAME-002`, or add a governance layer. It traced the executable authority path, reproduced concrete failures, fixed owner-local defects, measured constraint cost, and retained only changes whose verified benefit exceeded their permanent cost.

## Audited baselines

| Source | Revision / digest |
|---|---|
| Ordivon Game baseline | `389ab20f0b4ebad61481b6db78e8d8c878fd40e7` |
| Ordivon Computing baseline | `9b970833d57c31ee5aabc0f4a7498e484fcbb9df` |
| `core/foundations.md` SHA-256 | `7ac5eb7a158d169277a53f59c6655a4201bacc58e9a00d1fef86ab874560698f` |
| `ANC-GAME-002` SHA-256 | `efa4cbe45cee81dca94da870f662fa0064fa165d2402221c8c00cf6dc0ab029f` |

The Computing repository was read only. No Core, Protocol, Host, Harness, Runtime, Security, or World repository was modified.

## Scope and execution route

```text
HTTP / browser / direct API
→ MissionControlService
→ TeamHost
→ TeamStore + TeamExecutionStore
→ EmbeddedHostAuthority
→ GameWorldExecutor
→ GameStore
→ authoritative World reducer
→ Command receipt + World Event
→ Observation + Verification
→ Team Round + Host Outcome
→ Replay / Diagnosis / Comparison
```

The frozen single-Agent compatibility path was also inspected because it remains callable and can affect retained evidence.

At closeout the source tree contains 71 TypeScript source files, 16,297 lines, and zero static import cycles. No architectural layer was added.

## Core A application

- **A1:** retained SQLite transactions, WAL, parameterized SQL, Node HTTP, Playwright, and the existing World reducer; no database, router, lock service, scheduler, or workflow engine was rebuilt.
- **A2:** removed cross-owner Team and Host SQL; each owner now admits and verifies its own truth.
- **A5:** tested identity and continuity under concurrent callers, process replacement, and independent-process contention.
- **A7/A8:** stale cognition can no longer overwrite durable Team consequence; retained heads precede downstream completion.
- **A9/A10:** World receipts, Observations, accepted Verification, terminal Proposal evidence, and completed Round evidence remain explicit.
- **A11:** measured complete semantic verification on and off the hot path; rejected the per-Step form after an 81.7% runtime increase.
- **A13:** kept every fix inside an existing owner; no generic monitor, policy, transaction, approval, or Event layer was introduced.
- **A14:** every reproduced defect received a deterministic, corruption, concurrency, or multi-process regression test.
- **A15/A16:** audited permanent substrate only; the broader Game experience and `ANC-GAME-002` remain separate product questions.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| G-AUDIT-01 | high | uninitialized Mission Control reads created Host and Team schema | fixed |
| G-AUDIT-02 | medium | DeploymentStore read Team execution SQL directly | fixed |
| G-AUDIT-03 | medium | TeamStore read Host Journal SQL directly | fixed |
| G-AUDIT-04 | critical | concurrent commits could overwrite a completed Round head with `blocked` | fixed |
| G-AUDIT-05 | high | Authority completion occurred before durable Round CAS | fixed |
| G-AUDIT-06 | high | check-then-insert windows failed under independent processes | fixed |
| G-AUDIT-07 | high | `busy_timeout` was applied after a lock-taking WAL pragma | fixed |
| G-AUDIT-08 | medium | `TeamStore.projection()` could deliver or expire Messages | fixed |
| G-AUDIT-09 | medium | Goal reads silently recreated missing Objective Graph evidence | fixed |
| G-AUDIT-10 | medium | Message refresh lacked exact previous-head CAS | fixed |
| G-AUDIT-11 | medium | concurrent proposal review could race Context creation | fixed |
| G-AUDIT-12 | medium | Host Journal point reads did not verify record digest | fixed |
| G-AUDIT-13 | medium | frozen AgentSession initialization/save had concurrency windows | fixed without expansion |
| G-AUDIT-14 | low | oversized JSON and malformed percent paths were inconsistently classified | fixed |
| G-AUDIT-15 | rejected constraint | full Team semantic verification on every Step nearly doubled runtime | rejected from hot path |

## Source-level corrections

### Read paths remain reads

`createMissionControlView()` and timeline now perform a pure initialization query before constructing schema-owning stores. Tests compare `sqlite_master` before and after setup-state reads and prove no tables are created.

`TeamStore.projection()` now defaults to `refreshMessages = false`. Delivery and expiry remain explicit execution actions through `refreshMessages()`.

Goal reads no longer heal a deleted Objective Graph Artifact. The expected content-addressed Artifact must already exist and match; absence is `team_corrupt`.

### SQL ownership is local

`DeploymentStore` calls the Team execution owner’s pure `teamCognitionStarted()` query instead of knowing `team_rounds`.

`TeamStore` calls `HostStore.getJournalEvent()` instead of selecting from `host_journal`. Point reads verify the retained record digest before returning data.

The final source scan found no Team table SQL outside `TeamStore` / `TeamExecutionStore`, and no Host table SQL outside `HostStore` and the frozen AgentSession owner that explicitly composes it.

### Round and Proposal heads use exact CAS

Updates now bind both expected and next objects:

```text
saveRound(expected, next, eventType)
saveProposal(expected, next, eventType)
```

The durable update requires the exact previous canonical JSON. Stale writers receive `team_conflict`; they cannot rewrite a newer head. Transition matrices reject invalid backward transitions. Completed Rounds are immutable. Rejected or verified Proposals are semantically immutable; timestamp-only duplicate retries return the retained head without emitting another event.

The original six-way reproduction committed valid World work but left one completed Round overwritten as blocked. After the fix, stale callers fail explicitly, every completion event has a completed retained head, and no duplicate World Effect is produced.

### Durable Round head precedes Authority completion

The previous order could write Host Verification and Outcome before the Round CAS. The corrected sequence is:

```text
CAS Round to completed
+ append completed event in one transaction
→ reload retained completed head
→ idempotently reconcile Host Verification and Outcome
```

If a process stops between these stages, the next Team Step checks only the immediately previous World revision and reconciles missing Authority completion. This is bounded recovery, not a full-history scan.

Tests prove that a stale completed writer cannot complete Authority after another head wins, and that a retained completed Round with missing Authority completion recovers on the next Step.

### Independent processes converge

A new workload launches six independent Node processes against one SQLite file. They concurrently initialize the same Team, initialize the frozen AgentSession, store the same Artifact, and retain the same Team Round.

The final database contains one Team configuration, one Goal, four Team Tasks, three Profiles, one AgentSession, one shared Artifact, one Team Round, and one creation event per authoritative object.

The retained mechanisms are transaction-local rechecks, `INSERT OR IGNORE` only for deterministic/content-bound identities, exact reload validation, event emission only by the inserting process, and affected-row checks for CAS writes.

### SQLite startup waits before lock-taking work

`busy_timeout` is now applied immediately after opening the connection, before `journal_mode = WAL` and schema migration. Independent constructors no longer fail before the configured waiting policy exists.

### Explicit semantic verification

`TeamExecutionStore.verify()` checks Authority transcript integrity, status-dependent Round bindings, retained Observation identity, accepted Verification for completed Rounds, completed-event equality with retained heads, and terminal-Proposal event equality with retained heads.

It runs at explicit `syncContract()`, final `TeamHost.run()` closeout, and dedicated audits. It does not replace Replay’s graph-specific diagnostics or run on every Step.

## A11 cost audit

| Configuration | Median 18-Round runtime | Change |
|---|---:|---:|
| baseline | 5.16 s | — |
| full semantic verify on every Step | 9.37 s | +81.7% |
| CAS hot path + bounded closeout verify | 5.31 s | +2.9% |

A complete 18-Round semantic verification costs approximately 94.9 ms median and 110.4 ms p95. This is acceptable at explicit audit and closeout boundaries, not at every cognition or World step.

### HTTP boundary

The current server now returns:

- `413 request_too_large` for JSON bodies above 64 KiB;
- `400 invalid_request` for malformed percent-encoded paths;
- existing domain mappings for World, Team, Host, Deployment, and storage errors.

The correction is local to the existing router and does not introduce a framework.

## Full validation

### Unit, property, integration, corruption, and fault tests

```text
tests:      277
passed:     277
failed:     0
skipped:    0
```

Coverage:

```text
line:       98.02%
branch:     90.04%
functions:  98.32%
```

The increase from 265 to 277 tests comes from source-audit regressions, including independent-process contention.

### Browser product path

The complete browser workflow passed with Chromium `151.0.7922.34`:

- first Deployment reaches verified victory;
- Replay reaches revision 5;
- Diagnosis is verified-direct;
- second Deployment fails with `power_exhausted`;
- exact comparison shows Victory versus Failure;
- reload restores comparison state;
- no browser page errors were observed.

### Frozen receipt

The canonical successful trajectory remains unchanged:

```text
status: victory
reason: rescue_signal_verified
turn: 25
digest: 41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2
```

The canonical failure remains:

```text
status: failure
reason: reactor_meltdown
turn: 10
digest: 4db74d8a1d2f4583031d5ba7f2fbe9310ef89ef3f57847d803eb70edab737ac1
```

Persisted recovery matches the pure successful policy and verifies all 25 commands.

### Measurement

- 1,000 random policies retained the expected terminal distribution and score range;
- recovery perturbation retained 64 recoverable alternatives out of 103;
- Replay projection median: `1075.097 ms`;
- Replay product target: `1500 ms`;
- target passed;
- release-input generation completed and binds the audited source, tests, workflow, Scenario, and Ruleset contracts.

## Constraint ledger after the audit

### Keep

- one authoritative deterministic World reducer;
- expected World revision and digest admission;
- exact Command identity and retained receipt;
- atomic Team Tick;
- exact Round and Proposal CAS;
- exact Authority Decision / Grant binding;
- accepted Verification before completed Outcome;
- append-only World and Host journals;
- snapshots as cache only;
- owner-local idempotent initialization and content-addressed Artifacts;
- explicit closeout semantic verification;
- bounded previous-Round Authority reconciliation.

### Shrink or localize

- keep Station Zero coordination local to three specialists;
- keep Team transition semantics inside `TeamExecutionStore`, not Protocol;
- keep HTTP classification local to the current server;
- keep complete semantic verification out of the hot path;
- keep Message refresh explicit rather than projection-driven;
- keep multi-process coordination inside SQLite transactions rather than adding a lock service.

### Freeze

- single-Agent M1/M2 Host and `/api/agent/*` compatibility path;
- Game-private Provider adapters and session persistence;
- old debug/raw product surfaces;
- Game-local Host Contract projections pending Harness migration.

### Delete only after evidence

Physical deletion remains gated on:

1. Harness-backed cognition reproducing the same single- and multi-Agent workload;
2. equal-budget comparison showing no required capability loss;
3. no remaining release, Replay, or migration consumer;
4. retained compatibility evidence and rollback path.

## Residual risks and non-claims

### SQLite remains a single-node authority

The audit proves independent local processes can converge on one SQLite file. It does not claim distributed consensus, network partition tolerance, or multi-host active-active authority.

### Cross-owner recovery is bounded, not magically atomic

Round commitment and Host authority completion are separate owner-local durable actions. The audit proves idempotent next-Step reconciliation for the immediately previous Round. It does not claim a distributed transaction.

### The compatibility path remains debt

The frozen single-Agent Host still duplicates responsibilities expected to move to Ordivon Harness and Ordivon Host. This audit made it concurrency-safe enough to remain callable; it did not make it a future architecture.

### Large modules remain large

`storage.ts`, `server.ts`, and the Host/Team engines remain substantial. Static size alone did not justify extraction: there is no import cycle, no newly unowned responsibility, and no second materially different Game world proving a reusable layer.

### Product quality is not proved by infrastructure tests

The audit proves execution, evidence, recovery, concurrency, and HTTP properties. It does not prove long-term player enjoyment, Agent-native relationship value, or the broader `ANC-GAME-002` thesis.

## Final judgment

The authoritative World kernel was already strong. The principal weakness was the surrounding retained semantic state under concurrent callers and independent processes.

The audit therefore did not add more governance. It made existing commitments exact:

```text
reads remain reads
owners admit their own truth
stale writers lose explicitly
durable heads precede downstream completion
identical retries converge
conflicting identities fail closed
complete verification runs where its cost is justified
```

The resulting architecture remains thin: one World authority, one Team execution owner, one Host evidence owner, SQLite transactions, explicit receipts, and no speculative platform layer.
