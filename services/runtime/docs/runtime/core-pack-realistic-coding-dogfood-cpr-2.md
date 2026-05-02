# CPR-2 Realistic Coding Governance Dogfood — Runtime Evidence

Status: **CLOSED** | Date: 2026-05-02 | Phase: CPR-2
Tags: `cpr-2`, `realistic`, `coding-dogfood`, `core-pack-loop`, `governance`
Authority: `supporting_evidence` | AI Read Priority: 2

## Summary

CPR-2 proved that Ordivon's Core/Pack governance loop can govern a real
low-risk coding task. The task — adding a test scenario to the Coding Pack
dogfood script — was selected, gated through all 5 Coding Pack gates,
implemented as a bounded patch, receipted, reviewed, and documented.

## Selected Task

Add Run 11 to `scripts/h9f_coding_dogfood.py`: a medium-impact single-file
change with a test plan, expected to pass all 5 gates and receive `execute`.

This task was chosen because:
- 1 file changed, no logic alteration
- No forbidden paths touched
- Clear expected outcome (execute)
- Fills a test coverage gap (medium-impact path wasn't explicitly tested)
- Reversible in one commit

## 10-Node Loop Execution

### Node 1 — Intent
**What was proposed?** Add a medium-impact test scenario to the Coding Pack
dogfood script to prove the execute pathway for medium-impact changes.

**Why is it safe?** Test data only. No logic changes. No forbidden paths.
No live action surface. 1 file, reversible.

### Node 2 — Context
**What supported the decision?**
- Existing 10-run dogfood script (`scripts/h9f_coding_dogfood.py`)
- Coding Pack policy with 5 gates (`packs/coding/policy.py`)
- OSS-1 architecture audit confirmed Coding Pack is the primary dogfood target
- CPR-1 proved the loop works with simulated intakes

### Node 3 — Governance
**Coding Pack 5-gate results:**

| Gate | Check | Result |
|------|-------|--------|
| Gate 1 | task_description present | PASS |
| Gate 2 | file_paths non-empty | PASS |
| Gate 3 | No forbidden paths | PASS |
| Gate 4 | Impact not high | PASS (medium) |
| Gate 5 | test_plan present | PASS |

**Decision**: EXECUTE. All 5 gates passed. No rejection or escalation.

### Node 4 — TaskPlan
```
Allowed files: scripts/h9f_coding_dogfood.py
Forbidden files: packs/coding/policy.py, governance/risk_engine/,
                  finance/*, pyproject.toml, .env, uv.lock, package.json
Planned operations: Add 1 test run (R11) to existing 10-run suite
Rollback: git revert 1 commit
Evidence plan: Run dogfood script, verify 11/11 pass
Authorization: This TaskPlan does not authorize live execution, broker
               access, credential access, or policy activation.
```

### Node 5 — Receipt
**Files changed**: `scripts/h9f_coding_dogfood.py` (+19 lines)
**Files intentionally not touched**: `packs/coding/policy.py`, all finance paths
**Tests run**: `uv run python scripts/h9f_coding_dogfood.py` → 11/11 PASS
**Verification**: pr-fast 12/12 PASS, gov tests 302/302 PASS
**Skipped**: Frontend (no files touched), Finance (no files touched)

### Node 6 — Outcome
**What changed**: Coding Pack dogfood now has 11 test runs (was 10)
**New coverage**: Medium-impact + test_plan → execute pathway explicitly tested
**Results**: 4 execute, 5 reject, 2 escalate (was 3/5/2)
**What did not change**: Policy logic, RiskEngine behavior, forbidden paths
**No degraded status, no new debt**

### Node 7 — Review
**Review status**: APPROVED_FOR_CLOSURE
**Evidence sufficiency**: Dogfood script passes; pr-fast 12/12; gov tests 302/302
**Detector findings**: ADP-3 run against changed files — no blocking findings
**Boundary findings**: No forbidden paths, no live surface, no credential surface
**Gate response**: All 5 Coding Pack gates passed
**Closure recommendation**: CLOSE — bounded, safe, governance-proven

ReviewRecord does not authorize live execution, broker access, or policy activation.

### Node 8 — Lesson
**What was learned?**
- The Coding Pack 5-gate policy correctly classifies medium-impact single-file
  changes as EXECUTE when a test plan is present.
- The CPR-1→CPR-2 progression proves the loop can govern both simulated and
  real low-risk tasks.
- The dogfood script architecture (pre-existing from pre-DG era) remains a
  valid governance artifact even after extensive meta-governance phases.

**Lesson status**: Advisory only. Non-binding.

### Node 9 — CandidateRule
**No new CandidateRule proposed.** Existing CR-7P-001/002/003 remain reference-only.
The Coding Pack gate behavior did not produce evidence warranting a new rule.

CandidateRule status: NON-BINDING. Promotion criteria not met.

### Node 10 — Policy Path
**Policy activation**: NO-GO. Correctly gated.
CodingDisciplinePolicy operates in advisory/validation mode.
No binding policy was activated.
Phase 8 remains DEFERRED.

## Pack Used

Coding / AI Work Governance Pack (`packs/coding/`).
5 gates: description, files, forbidden paths, impact, test_plan.

## Supporting Infrastructure

| Infrastructure | Usage in CPR-2 |
|----------------|----------------|
| DG truth substrate | CPR-2 docs registered; current_truth reflects loop status |
| ADP-3 detector | Run against changed files — no blocking findings |
| GOV-X gate matrix | Task classified C0 (docs/test only), READY_WITHOUT_AUTHORIZATION |
| HAP-3 | TaskPlan/ReviewRecord structure documented |
| PV | No public surface touched |

## Boundary Confirmation

- No live finance ✓
- No broker/API access ✓
- No credential access ✓
- No external system invocation ✓
- No public release ✓
- No package publication ✓
- No public repo ✓
- No license activation ✓
- No runtime enforcement ✓
- No CI enforcement ✓
- No Policy activation ✓
- No Phase 8 entry ✓
- CandidateRule non-binding ✓
- Detector PASS is not authorization ✓

## Verification

| Check | Result |
|-------|--------|
| Coding dogfood | 11/11 PASS (4 exec / 5 rej / 2 esc) |
| pr-fast baseline | 12/12 PASS |
| Gov tests | 302/302 PASS |
| Registry | 92 entries, all invariants pass |
| Receipt integrity | 0 hard failures |
| Architecture | Clean |
| Runtime evidence | Verified |
| ADP-3 detector | No blocking findings on changed files |
| Ruff format/check | PASS |
| Frontend | Not in scope |
| Finance | Not in scope |

## Next Recommended

CPR-2 proved the loop governs a real task. The Core/Pack governance loop
is now the main product pathway. DG/ADP/PV remain supporting infrastructure.
Next: Seal CPR-2, then CPR-3 if more dogfood depth is desired, or return
to DG-2/ADP-4 if supporting infrastructure needs hardening.
