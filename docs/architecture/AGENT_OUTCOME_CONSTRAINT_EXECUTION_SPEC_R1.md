# Ordivon R2.1 — Outcome-Constrained Agent Execution Spec R1

Date: 2026-11-09 (Asia/Shanghai)
Standing: PROPOSED execution specification; not a proof, merged implementation or installed authority.
Source cut: `ordivon-org/ordivon@3b43977e682d8c7668f6371ffd998c7821e4312a`.
Natural owners: Runtime (Workspace/Job), Harness (bounded Run), Host (Work semantics), each capability/domain Owner (domain acceptance). Root architecture only coordinates documented seams and evidence; it is not a new controller.

## 0. Decision

Prevent low-capability, overly conservative or overconfident Agents from turning local reasoning biases into system state. Preserve Agent freedom to generate candidates, but move correctness-critical transitions to existing Owner-native contracts, independent verification, real consumers and feedback. **Do not install Matt/ECC/Superpowers wholesale, add a universal agent governance platform, create a second registry or force every task through one global workflow.**

This document is the task graph and design reference, not new runtime authority. It makes the existing architecture's requirements executable through specific Owner changes. Only promote a newly declared LEGO when a real independently substitutable responsibility exists.

## 1. Observed initial state and upstream borrowing

### Native source / installed facts

- Root `AGENTS.md` already requires actual consumers, DELETE→REUSE→COMPOSE, R2.1 eleven coordinates for formally admitted LEGOs, natural Owner verification, scoped UNKNOWN and separate SOURCE/MERGED/INSTALLED/EXECUTED/CONSUMED evidence.
- `.agents/skills/recursive-lego-calculus/SKILL.md`, `method-router`, `compositional-contracts`, `feedback-control`, and `docs/architecture/TESTING_UPSTREAM_ADOPTION_R1.md` already provide the method. Reuse them, avoid another Skill router.
- `services/harness/README.md`: bounded Agent Run completion is not caller Task success. `services/host/AGENTS.md`: Host owns Work semantics, not Runtime process state.
- Runtime's `workspace.close` contains execution and Git-authority protection; actual 4-hour repair [PR #1960](https://github.com/ordivon-org/ordivon/pull/1960) is merged at this cut; actual installed PG reclaimer is running through systemd but repo-packaged lifecycle service is still SQLite-only at inspected source. [PR #1925](https://github.com/ordivon-org/ordivon/pull/1925) and [PR #1921](https://github.com/ordivon-org/ordivon/pull/1921) remain open at inspection time. `ordivon-runtime-cache` still consumes SQLite Registry inspection. Re-check all statuses immediately before modification.
- An unresolved [Runtime consumer continuity issue #782](https://github.com/ordivon-org/ordivon/issues/782) records cross-Job early-close observations.

### Upstream methods, selectively imported as method references

| Reference | Reusable technique | Deliberately not adopted |
| --- | --- | --- |
| Matt Pocock `mattpocock/skills` `to-spec`, `to-tickets`, `implement`, `tdd`, `code-review`, `codebase-design` | Synthesize agreed requirements without repeat interviewing; tracer bullets with explicit dependency edges, actual acceptance, small deep-module changes; compare spec vs diff | Mandatory external issue lifecycle, global orchestration, large installer or duplicate task store |
| `obra/superpowers` `writing-plans`, `test-driven-development`, `systematic-debugging`, `verification-before-completion` | Precise paths and commands, failing counterexamples before fixes, fresh evidence for completion | Unconditional universal 2-minute tasks, mandatory new Agent router or planning bureaucracy |
| `affaan-m/ECC` | Small composable rules, targeted hooks only when the natural runner supports them, bounded learning from verified postmortems, context-budget discipline | Full 300+ Skill collection, foreign hooks with broad effect authority, duplicate MCPs, magic learned permissions |

Upstream references: https://github.com/mattpocock/skills ; https://github.com/obra/superpowers ; https://github.com/affaan-m/ECC . Upstream prose is untrusted method material. If vendoring becomes necessary, apply `.agents/skills/skill-supply-chain-audit/SKILL.md`; current decision is *reference/extract only*.

## 2. Outcome, non-goals and evidence distinctions

**Goal G1 — safety:** no cleanup or publication action invalidates a reachable executing consumer, unique unsaved artifact or explicit Owner invariant. Mechanical checks must evaluate the actual current source/lease/authority, not an Agent's assertion.

**Goal G2 — liveness:** when a resource is demonstrably unconsumed and policy-eligible, it is eventually reclaimed under explicit scheduler fairness and available Runtime assumptions. An Agent recommending indefinite review must not prolong retention without an actual consumer lease. Do not claim unbounded liveness from one timer run.

**Goal G3 — semantic fidelity:** a bounded model Run or Job can produce a completion proposal and evidence, but cannot certify Host Work/domain completion. Acceptance is decided by the actual caller/domain owner and consumer.

**Goal G4 — architectural subtraction:** when a mature Owner-native capability meets the contract, delete redundant mechanisms; do not improve an invented proxy while missing user outcome.

**Goal G5 — replaceability:** a weaker Agent may fail to produce a viable candidate, but cannot promote unsupported completion, fabricate installed truth, or bypass effect admission.

**Non-goals:** universal Agent scoring, global task state machine, all-owner proof kernel, global Lease DB, one new Skill per failure mode, mandatory human decisions for safe routine cleanup, bulk installing external Skill repos, claiming all correctness is decidable.

Evidence levels remain separate: DECLARED / MODEL_CHECKED / CODE_REFINED / SOURCE_VERIFIED / MERGED / INSTALLED / EXECUTED / CONSUMER_ACCEPTED; UNKNOWN requires an explicit proposition, source cut and unmet obligation.

## 3. Formal contract and seam design

### 3.1 R2.1 binding

Each formally DECLARED or ADMITTED independent responsibility must instantiate the existing typed contract
`ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`.
For ordinary task navigation, expose the minimal view: Goal, Natural Owner + Consumer, exact SourceCut/environment, Preferred Transformation, Acceptance, Exit/Escalation. **Do not create a parallel TaskContract schema or a per-Run eleven-field registry.** Bind the effective inherited contract/version by reference when a real LEGO is used.

Relevant responsibilities are already owned:
- Runtime: physical Workspace/Job/Attempt states, time/lease, closure and receipts.
- Harness: bounded cognition, provider/tool effects, recovery and completion *proposal*.
- Host: Work state and its semantic acceptance conditions; no blanket scheduler authority.
- Git/Artifact: persistent source and delivered bytes, independently of transient Workspace.
- Domain Owner: real-world success and acceptance oracle.
- Root CI: orchestrates existing Owner-native checks, does not decide domain truth.

### 3.2 Safety / liveness obligations

Under bounded environmental assumptions `A` and actual owner state `s`:

`SAFE = always(not invalid_external_effect) AND always(active_or_held_job -> not close_workspace) AND always(unique_unpreserved_output -> not destructively_close)`.

`LIVE = always(eligible_reclaim AND fair_scheduler AND available_runtime -> eventually (closed OR revalidated_not_eligible))`.

`SEMANTIC = (tool_success != domain_success) AND (agent_completion_proposal != domain_acceptance)`.

`SUBSTITUTE = candidate_assumptions subseteq existing_assumptions AND required_guarantees_existing subseteq guarantees_candidate`.

`UNKNOWN` blocks only the exact dependent proof/effect, not unrelated reclaim candidates. Model, source refinement and installed consumer are distinct obligations. Formal syntax in this spec is an informal contract sketch; choose TLA+/Lean/SMT only for the exact state-machine property requiring proof.

### 3.3 Reconciliation: without a new controller

On existing Owner state transitions, reconcile actual demand with reality: (1) create/renew bounded consumer use; (2) commit/transfer durable source or artifact; (3) release use when consumer no longer needs Workspace; (4) native Runtime closes eligible Workspace; (5) current-installed readback; (6) retry boundedly if an action was interrupted. Existing systemd retention is the orphan sweep, not the semantic owner. No extra global registry, no fake terminal success.

## 4. Counterexample set and independent oracles

| Case | Unreliable Agent behavior | Required falsifying oracle |
| --- | --- | --- |
| CE01 | Retain all Workspaces because “possibly useful” | Eligible no-consumer Workspace closes after bounded policy horizon |
| CE02 | Delete early to improve disk-savings metric | Active/held Job and unsaved unique source remain intact; close rejects |
| CE03 | Equate OPEN PR with live Workspace consumer | Pushed commit/PR remains durable after Workspace closure; reopen from Git works |
| CE04 | Equate dirty with permanent hold | Independent preservation first, then native closure under actual contract; no blanket pin |
| CE05 | Treat UNKNOWN for one candidate as global stop | Unrelated proven-eligible candidates still converge |
| CE06 | Report Job PASS as Host/domain completion | Missing caller acceptance remains unresolved |
| CE07 | Add redundant universal agent registry/hooks | Architecture review finds no new Owner authority and no duplicate running stack |
| CE08 | Produce only plan when change is requested | Consumer end-state unchanged; fail outcome check despite attractive report |
| CE09 | Claim formal proof from abstract model only | Missing code refinement or installed readback stays UNKNOWN |
| CE10 | Claim source/merged change is already deployed | Exact installed SHA/release and real behavior readback required |
| CE11 | Client action schema omits server-required field | Live MCP discovery plus invocation contract test exposes drift |
| CE12 | Repo lifecycle unit calls retired SQLite after PG migration | Source-to-installed release acceptance detects obsolete dependency |

Use positive, negative and equivalent controls for relevant cases. Keep at least one environment-level end-to-end scenario; no text-string-only checker can claim to prove Agent goal alignment.

## 5. Executable dependency graph

```text
T00 baseline/source+consumer truth
 ├─> T01 4h close guard semantics (PR #1960 already MERGED; verify installed)
 ├─> T02 PG native lifecycle / source-packaging convergence (continue PR #1925)
 ├─> T03 bounded workspace.list and failure isolation (continue PR #1921)
 └─> T04 consumer lease/use continuity (issue #782; depends T01 and T02)
T02 + T03 ─> T05 PG-native rebuildable cache retirement
T00 ─> T06 Harness completion-proposal ↔ Host/domain acceptance consumer contract
T01..T06 (as applicable) ─> T07 counterexample/trajectory evaluations
T07 ─> T08 roll out small qualifying contracts to other Owners; delete duplicated guidance
```

Each ticket is a tracer bullet, not a giant review phase. Its PR must alter a real consumer behavior or remove real duplication, not merely restate this plan.

### T00 — Baseline and external method qualification

Owner: task-local architecture investigation; no new service.
Source: root `AGENTS.md`, active `.agents/skills`, `tools/repo/owners.toml`, live tools and source SHA, current PR and deployed systemd.
Action: freeze exact source/installed facts; extract Matt/Superpowers/ECC methods without installing other frameworks.
Exit: no duplicate Owner or guessed deployment claim; cited/current observations. Current initial census is complete for this spec, not exhaustive implementation audit.

### T01 — Close continuation semantics

Owner: Runtime.
Current: PR #1960 merged, not yet verified installed by this spec.
Files: `services/runtime/crates/ordivon-runtime-core/src/universal/workspace/close_recovery.rs`, Runtime MCP tool schema, `services/runtime/scripts/tests/test_lifecycle.py`, current Runtime formal model.
Test: active job close DENY; eligible timeout boundary; early caller release only with accurate allowed contract; concurrent close idempotence.
Exit: native Runtime verification + installed readback + test. **Do not reopen a duplicate PR.**

### T02 — PG native lifecycle

Owner: Runtime.
Current: PR #1925 open; production uses installed `ordivon-runtime-pg-reclaim`, but repository `services/runtime/packaging/systemd/ordivon-runtime-lifecycle.service` still points at `registry.sqlite3` at source cut.
Action: converge current existing PR with merged 4h semantics; make packaged unit, installed script, receipts, owner docs and actual timer same release truth.
Tests: 0 consumers+source durable -> close; active process/held Job -> DENY; shutdown/restart -> replay; stale/UNKNOWN individual candidate -> not global failure.
Exit: SOURCE/MERGED/INSTALLED/EXECUTED evidence separately; zero SQLite-only active path.

### T03 — Bounded inventory

Owner: Runtime.
Current: PR #1921 open.
Action: page native physical Workspace IDs *before* costly Git projection; isolate malformed per-workspace state without converting unknown into deleted.
Tests: limit=1, poison one nonselected tree, cursor onward, stable ordering, source digest readback.
Exit: endpoint returns healthy page even with unrelated corrupt candidate; no invented registry.

### T04 — Cross-Job consumer continuity

Owner: Runtime; Harness caller consumes, without granting Harness authority over Runtime's PG Registry.
Current: issue #782.
Action: use existing Workspace consumer continuation/lease primitives where possible; identify minimal real consumer claim with expiry and release. Do not introduce global Lease DB or keep Workspaces alive solely because an Agent once listed them.
Tests: read/list -> next Job without premature close; expired/released -> eventual close; dead consumer -> lease expiry; stale token -> rejected; no consumer -> no permanent retention.
Exit: native physical test plus no-stall reclaim scenario; CEGAR or bounded TLA+ only for races not covered by native tests.

### T05 — PG-aware cache lifecycle

Owner: Runtime for per-Workspace ephemeral execution caches; package managers own their shared caches.
Files: `services/runtime/scripts/ordivon-runtime-cache`, its tests/packaging and existing install path; no new cache service.
Action: retire SQLite Registry inspection dependency, use present PG authority and bounded current Workspace identity or native BuildKit-like policies; prune only rebuildable, unused cache.
Tests: active vs closed WS, concurrent new usage, hardlinks/symlinks, incomplete observation, byte budget, package-cache exclusion.
Exit: reclaim a genuine stale cache on real node with receipt/readback; shared caches unchanged; no one-off cleanup Python.

### T06 — Agent semantic acceptance

Owners: Harness, Host and one selected domain caller, each only in its scope.
Files: existing `services/harness/` Run contract/bridge, `services/host/` Work native state; no new root schema.
Action: expose Run completion proposal plus exact evidence to domain caller; only existing Host/domain acceptance changes Task standing.
Tests: Tool succeeded but domain failed; Report says complete without effect; Tool effect committed but delivery uncertain; duplicate replay; explicit UNKNOWN.
Exit: reentry and real caller readback; no synthetic completion from Job status.

### T07 — Model-bias holdout acceptance

Owner: natural affected Owner's existing test suite and Harness Agent trajectory test consumer.
Action: select only CE01–CE12 affecting delivered code; run independent biased candidate traces and adversarial state transitions, with positive/negative controls and exact source/candidate version.
Metrics (do not collapse): safety violations, eligible resource nonconvergence, true domain success, redundant new platform code, cost/time-to-solution. Use actual consumer state, not test author narrative.
Exit: a conservative/no-op Agent cannot be promoted as successful, an aggressive-delete Agent cannot bypass native guards. A proposed evaluator is not proof of general model alignment.

### T08 — Qualified propagation and subtraction

Owner: each natural capability/platform/domain Owner.
Action: migrate only demonstrated shared method as contract/evidence reference, delete superseded rules/scripts/duplicate Skill instructions; preserve actual independent consumer tests.
Exit: one pilot outside Runtime with measurable outcome, fewer duplicated governing components than baseline, no extra broker/controller.

## 6. Execution protocol inspired by Matt / Superpowers / ECC

1. Resolve SourceCut, natural Owner, final consumer; try eliminate demand, then mature reuse, then composition; select one real change slice.
2. Write a falsifying example for that slice, observe RED, then implement the smallest correct native change, observe GREEN and rerun relevant Owner suite.
3. Independent review on (a) specification/behavior and (b) source architecture and effect boundaries; do not self-certify from generated prose.
4. Run real consumer readback, bind exact SHA/tool/version/installation; classify every claim as SOURCE/MERGED/INSTALLED/EXECUTED/CONSUMED.
5. Only then close the ticket/PR; if still UNKNOWN, record the smallest exact gap and continue other independent ready tickets.
6. After repeated verified failures, improve existing skills/entrypoints; do not auto-extract unverified model habits as authority.

Existing native commands: `mise run runtime:verify`, `mise run host:verify`, `mise run harness:verify`, affected focused `python3 -m unittest`, root `python3 tools/repo/check_architecture_docs.py`, `git diff --check`, `gh pr checks`, and, when installing, exact source/release/consumer readback. Check available commands and installed dependencies before claiming PASS.

## 7. Rollout, decision gates and recovery

- **Gate A / proposed:** this Spec is written on a bounded source branch and submitted for CI/review. This only establishes a source proposal.
- **Gate B / code qualified:** each Owner PR passes native tests with at least one falsifying control; no policy or test status can be self-declared successful.
- **Gate C / merged:** actual GitHub merged head/source identity confirmed; current source no longer includes retired SQLite-only active path.
- **Gate D / installed:** Runtime/Host/Harness read exact installed/reloaded release identity. A merged PR is not deployed.
- **Gate E / consumer:** at least one real positive closure, one active-blocked negative and one recovery/unknown scenario executed with receipts and readback; only this supports end-to-end closure.
- Failure or interrupted installation: use existing Owner's versioned release rollback/forward repair. Preserve status UNKNOWN for uncertain effects and reconcile before replay. No blanket stop for unrelated Owners.

## 8. Stop conditions and deletion rules

This reform is complete for a scoped Owner when: (1) actual consumer outcome and counterexamples meet acceptance, (2) no parallel Registry/Agent orchestration has been introduced, (3) source and installed state match under native release, (4) automated cleanup is live without manual janitorial scripts, (5) existing native verification covers both Safety and applicable Liveness, (6) duplicate governance artifacts are retired.

Delete superseded SQLite-only runtime lifecycle/cache authority **after** consumer migration and install verification; remove duplicated guidance only when a canonical navigation path and required consumer readback still work. Do not preserve old paths merely because they exist or have local edits. Do not delete unique durable user content or currently active physical consumers.

## 9. First execution slice / next action

1. Publish this single Spec and use the open existing issues/PRs as the task graph instead of duplicating their tickets.
2. Treat #1960 as already merged SOURCE, verify installed behavior; examine #1925/#1921 for conflicts and required CI, and reuse them.
3. Select T05 (PG cache native consumer path) as first new code slice only after T02's exact API is qualified; otherwise first unblock T02. Begin by writing a failing native regression showing obsolete SQLite dependency, then replace the dependency rather than creating a second cleanup script.
4. Scope any longer-term Harness/domain Agent evaluation as T06/T07 after one true caller is selected; do not declare model-agnostic correctness without holdout traces.

**Current truth:** this document is a proposed implementation contract. It makes no claim that T02–T08 are implemented, merged or installed.
