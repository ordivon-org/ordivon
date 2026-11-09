# Runtime R2.1 Formal Refinement — Implementation Plan

Companion: services/runtime/docs/runtime-contract-refinement-spec-r1.md. Source branch: feat/runtime-pg-workspace-contract-20261109, PR #1983. Execute under existing AGENTS.md and Runtime AGENTS.md; use Matt tracer bullets, Superpowers RED→GREEN and verification-before-completion, ECC scoped verification-loop. No weak-model experiment.

## Evidence on entry

PR #1983 head 15ac1ee0a6fc1c1891984627558e805d0367ecbd; mandatory CI fails because native Runtime release produces 14 canonical artifacts while .github/workflows/runtime-release.yml asserts exactly 13. GitHub repo-mechanics checks test this intentional invariant and failed. CodeQL succeeded. Source/installed/consumer truth remains distinct. Fetch current main before merge; do not force-push.

## Full dependency graph (vertical deliverables, not layer tasks)

### T0 — Formal adoption and fixed acceptance
Blockers: none.
Files: services/runtime/docs/runtime-contract-refinement-spec-r1.md and this plan.
Acceptance: goal, R2.1 tuple, Owner/source/consumer, invariants, fairness assumptions, negative controls and exact proof states are explicit. No new Agent or Registry.
- [x] Read upstream Matt/ECC/Superpowers methods and native R2.1 thought LEGOs.
- [x] Recheck #1983 GitHub CI against actual deployed source and repository release workflow.
- [ ] Commit spec and plan before implementation.

### T1 — Restore tagged-release consumer correctness
Blockers: T0.
Files: .github/workflows/runtime-release.yml and tools/repo/test_github_governance.py.
Seam: native deploy manifest -> tagged release staging -> attestation verification.
Acceptance: independent test fails on current fixed count, then passes after replacing count with exact manifest subject-set comparison; all missing/duplicate/extra artifacts fail. Version/additive changes reuse one canonical set.
- [ ] Write RED test checking full manifest name-set correspondence, not hardcoded numeric count.
- [ ] Run actual failing repo governance test.
- [ ] Modify existing tag release pipeline using current native candidate manifest; no separate manifest generator.
- [ ] Run source-native governance test and negative missing/extra/duplicate cases GREEN.
- [ ] Commit.

### T2 — Prove conditional Workspace progress in the current formal Owner
Blockers: T0. Independent of T1.
Files: services/runtime/formal/WorkspaceConsumerCloseR1.tla; optional progress cfg; scripts/tla-formal; formal/README.md.
Seam: official pinned TLC with existing Close safety model.
Acceptance: safety unchanged; reachable Close; under no new Jobs/Git dependents and WF(Close), continuously enabled eligible Workspace eventually closes. Without fairness, TLC finds a named counterexample, not a syntax failure.
- [ ] Extend named TLA+ actions and configuration minimally; do not encode a new scheduler or pretend consumerReleased is independently verified.
- [ ] RED run without fairness -> TLC liveness counterexample with trace.
- [ ] GREEN run with WF(Close) -> model checker PASS.
- [ ] Bind prior unsafe-close and reachability falsifiers; update native formal check.
- [ ] Commit.

### T3 — Make concrete/abstract correspondence auditable
Blockers: T2.
Files: existing Runtime PG reclaim implementation, tests/test_pg_native_reclaim.py, formal/README.md (only if needed).
Seam: public operator IO, PG snapshot, MCP get/close and exact Git source digest.
Acceptance: every abstract pre/post has a native witness or UNKNOWN; test one real behavior violating an assumed race/safety, RED->GREEN; avoid unrelated gate accumulation.
- [ ] Pin concrete fields for age, current activity, active lease, git ref and close.
- [ ] Add correct negative test at existing public seam (PG changes between selection and close, Runtime close uncertain).
- [ ] GREEN fix with qualified native mechanism, not filesystem rm.
- [ ] Keep strong linearizability UNKNOWN if Runtime/PG coupling is not proven.
- [ ] Commit.

### T4 — Full source and CI validation
Blockers: T1,T2,T3.
Existing verification: Python governance tests, Runtime formal tool, service native tests, repo:ci, Runtime:verify, GitHub Merge Queue.
Acceptance: all relevant checks with observed exit codes and non-trivial results; inspect conflicts against new main; two-axis standards/spec review.
- [ ] Focused RED/GREEN evidence recorded.
- [ ] TLC check + falsify with pinned toolchain; do not call missing TLC PASS.
- [ ] Real repo governance tests and Runtime native tests, Ruff, docs, diff.
- [ ] Push to #1983, read actual GitHub status; fix genuine failures.
- [ ] Merge through existing queue only after required checks pass.

### T5 — Installed system and final consumer
Blockers: T4 + real installed Runtime authority.
Acceptance: byte-identical qualified release, loaded unit, real PG dry-run and eligible physical closure witnessed; Git/Artifact retention checked, no bypass.
- [ ] Native release candidate and exact digest readback.
- [ ] Observe actual systemd/PG/Runtime under installed identity; dry-run.
- [ ] Close only a known eligible Workspace via Runtime native Close.
- [ ] Report SOURCE/MERGED/INSTALLED/CONSUMED individually.

### T6 — Systemwide method adoption via existing thought LEGO
Blockers: T5, or independently qualified comparable Owner consumer.
Files: only the existing .agents/skills/recursive-lego-calculus and compositional-contracts if a real missing reusable law is demonstrated.
Acceptance: no repeated instructions, no parallel registries, external mature techniques applied only where their proof obligation matches an actual consumer.
- [ ] Extract valid reusable rule with proof assumptions and counterexample links.
- [ ] Prefer delete/compose/provider over custom implementation; preserve unrelated Owner native contracts.
- [ ] Retire superseded tests/text only after proven implementation and consumer equivalence.

## Evidence ledger

For each task record: property | formal model+config | assumptions/fairness | falsifier | concrete source+test | release/installed digest | actual consumer standing | remaining UNKNOWN. This is a report format, not a new database.

Stopping conditions: a failing required GitHub check cannot become PASS by narrative, mock-only success cannot become installed truth, and real value-delivering work is not blocked by unrelated UNKNOWN.
