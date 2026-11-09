# Ordivon repository source-modernization — stock-only refactor plan

**Spec:** `AUDIT_SCOPE.md` + `MODERN_CRITERIA.md` + `INVENTORY.md` + `AUDIT_REPORT.md`; base `ef17d6879d12faa61fff3bb762b0d500d73c9113`. This is *not* the existing broad multi-Owner program or a new management framework. Tasks are an explicit DAG, separated by real Owner; do not grow tests or consumers.

## Dependencies and decisions

| Task | Preconditions | Exact existing-source operation | Native verification | Rollback / risk |
|---|---|---|---|---|
| P0 (Phase0) | — | Freeze exact main, 21 owners, open PR collision map and 12 checkable criteria | `git rev-parse HEAD`, `git status --porcelain`, `tools/repo/owners.toml` inspect | No effect; repeat from source |
| P1 (Phase1) | P0 | Enumerate 5,002 paths with original `exhaustive_coverage.py` and `git ls-files`, group owner code/types/tree, observe initial module graph | Original source digest and tracked count | No effect |
| P2 (Phase2) | P1 | Evaluate M01–M12; distinguish witnessed doc drift from unproven module-depth hypotheses; check SourceCut overlaps | Original `check_owner_boundaries.py`, `check_structure_r2.py`, `check_architecture_docs.py` | No effect |
| P3 (Phase3) | P2 | Freeze this plan and dependency constraints: **only current non-colliding Repo owner document fix in this branch** | `git diff --check`; current PR paths | Revert plan commit if not useful |
| P4A (Phase4) | P3 | Edit only `docs/architecture/OWNER_DEPENDENCY_BOUNDARY_R1.md` to reflect the current proven 2,320/31/38 checker result. Add genuinely existing new seam groupings, mark SourceCut and scope. **No checker or tests changed.** | Original `python3 tools/repo/check_owner_boundaries.py` and `python3 tools/repo/check_architecture_docs.py`, root `mise run repo:ci` | `git revert <commit>`; lowest effect risk; markdown only |
| P4B (Phase4) | P4A | Confirm no unplanned changes and record actual check result/return code; amend any false doc claims | `git diff --check`, exact changed file diff | If a check fails, repair source / report blocked, never pretend PASS |
| P5 (Phase5) | P4B | Record exact changed paths + six output docs, baseline delta, Source vs MERGED/INSTALLED/CONSUMED truth; Host handoff | PR SHA, Git clean, native verify output and Host topic sequence | Retain branch if PR blocked; no deploy |

**No second Phase4 batch is admitted without new unique evidence and collision check.** Other proposed Owner refactors remain in existing Owner PRs; specifically #2012 owns `exhaustive_coverage.py` and tests, #2015 Harness, #2016 Host, #2008 Workstation, #2017 Chaoxing. No additional cold telemetry startup, root port, universal schema, test harness, eslint plugin, CI hook or global control Agent is needed.

## Change contract for P4A

**Before:** `OWNER_DEPENDENCY_BOUNDARY_R1.md` records 2026-11-06 snapshot (~2,136 active / 19 seams / 21 refs) and a partial 8-family summary.

**After:** explicitly source-qualified at 2026-11-10 main: 2,320 active / 10 packages / 31 seams / 38 refs, and new existing Catalog ELE / Data/Composition Capital seam categories. State that this is **bounded source-literal and AST observation**, not installed deployment, complete dynamic graph or formal proof.

**Expected negative:** docs still displaying 2,136 or 19/21 as current would mislead the Owner/Agent; changing test scripts to accept a fixed count is not an acceptable fix. **Expected positive:** original checker reproduces the new numbers and root docs checker remains green.

## Skill and theoretical challenge to every work unit

- Matt deletion test: does removal improve locality? A pure info-report edit is accepted only when it corrects a false source-of-truth representation; no cosmetic refactor.
- ECC search-first/impact: existing owner source checks and exact path references before editing; no new hooks/automations required.
- Superpowers writing-plans/executing-plans/verification: this concrete file/command/expected-output task and original `mise` checks, not a second execution platform.
- R2.1 / Parnas / Hexagonal: repo-level docs are navigation, not a new authority; owner semantics unchanged. Replacing the old numbers improves evidence binding without altering consumer contracts.
- Anti-conservatism: source-only markdown change should not wait for speculative production tests or manual approvals. Anti-overreach: no invented domain proof from green lint.

## Handoff

State = source planned / source applied / verified / PR open / merged / installed / consumed **separate**. Completed = actual file diff and original native exit codes. Pending = PR CI, peer concrete falsifiers and only material source/installed delta. Evidence = exact SHA, GitHub URL, full command and path. The Host Space message is coordination, not a gate.
