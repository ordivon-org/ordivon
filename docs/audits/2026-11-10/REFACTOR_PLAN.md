# Ordivon — REFACTOR_PLAN (native stock-only execution)

**Review source:** `docs/audits/2026-11-10/AUDIT_REPORT.md` and `MODERN_CRITERIA.md` (SourceCut `ef17d6879d12faa61fff3bb762b0d500d73c9113`).
**Goal:** one actual, independently verifiable source-code repair and accurate read-only repository baseline without colliding with other Agent Owner PRs. No features, no new test code, no new consumer interfaces, no new enforcement/hook runtime.
**Architecture:** preserve the current 21 Owner roots and existing boundary checker; one bounded Web configuration parser correction under its natural Owner; remaining high-risk refactors defer to real Owner with paths and evidence. Python/Rust/TS tools remain per Owner.

## Global constraints and rejection rules

Work only in isolated Git Workspace from pinned main; review all existing PR overlaps. No modifications to `tools/repo/exhaustive_coverage.py` (#2012), `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md` (#2006/#2010/#2013), Host/Harness/Skills/Workstation/Artifact owners' concurrent branches. No full-scale source reorganization based solely on directory aesthetics. No new tests. Existing owner verification required for every changed module. Recovery is Git revert with exact commit and re-run owner checks.

## Phase 0–1 — already observed, not action approval

- [x] Baseline 21 owners, 5002 tracked files, 123199041 bytes, exact input provenance.
- [x] Source identity and overlapping PRs checked via GitHub `gh pr list/view`, local clean isolated Workspace.
- [x] Existing `check_owner_boundaries.py` ran exit0 with 2320 active files, 31 declared seams, 38 references.
- [x] Frozen 12 modern criteria and full mechanically labeled `INVENTORY.md`; no claim of exhaustive semantic proof.

## Task A / F01 — Web exact positive-integer config parse (small, owner-local code repair)

**File:** `apps/web/src/config.ts:15-22`. **Actual interface:** `integerEnv(name: string, fallback: number): number`; consumed by `loadConfig()` for `ORDIVON_WEB_PORT`, `ORDIVON_WEB_SESSION_IDLE_SECONDS`, `ORDIVON_WEB_SESSION_ABSOLUTE_SECONDS` (`:25-54`).

**Before invariant violated:** `Number.parseInt(raw,10)` accepts a valid numeric prefix then ignores junk suffix. Existing native Node reproduction returned 42 for `42garbage`. The error text itself promises a positive integer.

**Change:** require raw input to be a complete nonempty base-10 digit string (no sign, whitespace, exponent or trailing characters), then `Number(raw)` and preserve `Number.isSafeInteger(value) && value > 0`. Permit leading zeroes to avoid gratuitous compatibility break; all inputs remain ordinary decimal strings. No new exported symbols/DB schema or library. No new test file.

**Existing verification:** `mise run web:verify` (native Owner task from `tools/repo/owners.toml`, or inspect `apps/web/mise.toml` for delegated command); additionally direct Node code evaluation for valid and invalid env input, using actual source module only if runtime supports TS source. Confirm current Web test/e2e surface not modified. **Expected:** invalid suffix rejected; normal `8789`, `1800`, `43200` unchanged; native verification exit0. If toolchain unavailable, report ENV_BLOCKED and do not claim PASS.

**Rollback:** `git revert <scoped-source-commit>` and original Web native verify. Risk low–medium: configurations with silently tolerated junk suffix now fail closed; this is intentional contract tightening.

## Task B — No competing remediation under other Owners

**Files (read-only):** `services/harness/src/ordivon_harness/ordivon/loop.py`, `run_continuity.py`; `services/runtime/crates/ordivon-runtime-core/src/pg_admission.rs`; `capabilities/artifact/artifact_verification/stage.py`; `tools/repo/exhaustive_coverage.py`; `docs/architecture/OWNER_MODULARITY_STRUCTURE_LIFECYCLE_PROGRAM_R1.md`.

**Process:** give path, potential problem, natural Owner, pending PR and unanswered actual-consumer/failure property to existing Space. Record Handoff. Do not create a replacement framework or another test, no aggregate Owner refactor before actual consumer closure. Stop any candidate whose deletion moves complexity into callers or destroys historical source evidence.

## Task C — Existing verification and two-axis review

- [x] Check no new source/test/API files (`git diff --stat`), and read affected code diff plus all current external import callers.
- [x] Run actual Web Owner verification. `git diff --check`; existing `tools/repo/check_owner_boundaries.py`; existing owner-boundary tests as necessary to prove the same contract. The root aggregate CI has unrelated time/environment costs and cannot be assumed PASS if not run.
- [ ] Matt Standards: check documented source style and smells; Matt Spec: exact positive decimal config, no extra scope. A PASS on one axis never masks a FAIL on the other.
- [ ] Update `BASELINE_AFTER_AUDIT.md` with exact attempts/exits/source or UNKNOWN and delta; write an evidence-bearing Space handoff, commit isolated branch and open GitHub PR. No merge/deploy claim before native readback.

## Tasks D/E — Cross-owner planning (not implemented by this branch)

- [ ] Runtime Owner: check stale opt-in/PG text against installed exact source, then qualify or correct (no speculative behavior change).
- [ ] Harness Owner: isolate actual distinct change reasons for 3186-line continuity module and 2366-line loop, protecting open PR #2015/#2009; do not split by line count alone.
- [ ] Artifact Owner: decide whether stage hook abstraction hides real complexity or only duplicates verification routes. Check existing #1974/#1994 before changes.
- [ ] Repo/Architecture Owner: reconcile open #2006/#2010/#2013 and use existing #2012 source inventory, not an additional checker.
- [ ] Web Owner later: evaluate `WebStore.db` public test-only usage only if it causes a concrete maintenance or correctness failure. Not needed to fix F01.

## Acceptance states

`OBSERVED` = actual files and current negative example; `SOURCE_REPAIRED` = Git diff; `NATIVE_VERIFIED` = observed Web and Repo commands exit0; `PR_OPEN` = remote GitHub ref; `MERGED`, `INSTALLED`, `EXECUTED`, `CONSUMED` require their own producer facts. Do not infer them from a Spec or from a tool write.

## Space handoff contract

`SourceCut | Actor/Owner | Phase | Current state | Completed effects | Native evidence pointers and exit codes | Pending precise counterexample | Next file and action | PR/merged/installed status`. Post to existing Space; no new Ordivon Host Work or second Task registry.

## Actual native task-C receipt

Web verify 18/18 pass, zero skip; TypeScript typecheck exit0. Eight Node actual-source parser cases matched. Existing owner boundary checker exit0, 17 owner-boundary unit tests pass, architecture documentation checker exit0. Entire repo aggregate CI not run. No new test files.
