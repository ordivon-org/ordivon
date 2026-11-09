# Artifact Standing Convergence — R2.1 Implementation Plan

> Agent execution: use the checked-in Ordivon LEGO skill, Matt to-spec/to-tickets/implement/TDD/code-review, and Superpowers writing-plans/executing-plans/verification-before-completion as reference methods. These do not grant effect or completion authority.

**Goal:** Converge existing v1/v2 verification to one bounded Standing semantics, retain consumer compatibility until migration, delete duplicate decisions after verification.
**Architecture:** one pure evaluator; raw evidence remains native; both existing interfaces call it. No extra registry, server or mandatory pipeline.
**Tech:** Python 3.15, uv, mise, pytest, Ruff, existing finite model check.
**Spec:** `capabilities/artifact/docs/ARTIFACT_STANDING_CONVERGENCE_SPEC_R21.md`.
**SourceCut:** `3b43977e682d8c7668f6371ffd998c7821e4312a`.

## Global constraints

R2.1 `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`; UNKNOWN cannot become PASS; don't infer consumer success; compatibility expand–migrate–contract; don't touch running Temporal/Zot service configuration; native Owner `mise run verify`; no weak-model trials.

### T1. Shared requirement-coverage projection (first implementation slice)
**Files:** modify `artifact_verification/claim_coverage.py`, `artifact_verification/stage.py`, `scripts/artifact_verify.py`; add `tests/test_artifact_standing_common.py`.
**Interface:** `assess_required_statuses(required, observed, issues=()) -> dict`, pure. Exposes required/failed/missing/unknown/complete/status. Required semantics are independent of raw native PASS; native pointer check remains authoritative for v2.
- [x] Write a v1/v2 caller-level failing test that requires a common Standing projection and exercises missing required gates/claims.
- [x] Run new focused test, observe RED (missing field/function).
- [x] Implement minimal pure shared evaluator; reuse in both existing entrypoints, preserving existing compatibility fields.
- [x] Run focused owner tests and native negative checks GREEN.
- [x] Run full owner verify and compare public response compatibility; review diff on spec and code-quality axes.
- [x] Commit self-contained slice; no invented deployment claim.

### T2. Falsification and finite refinement
**Files:** existing `artifact_verification/formal/`, `tests/test_artifact_verify.py`, `tests/test_artifact_stage_missing_validator.py`.
- [x] Add failing assertions for NOT_EVALUATED/FAIL/pointer-mismatch and no vacuous success; use exact source-bound theorem/model where feasible.
- [x] Implement minimal corrected predicate or reuse claim coverage model.
- [x] Run model, focused negative tests, owner verification; record scope, non-claims, commit.

### T3. Prototype retirement / duplicate authority cleanup
**Files:** retired prototype, migrated `tests/test_artifact_standing_entrypoints.py`, existing production v1/v2 entrypoints and formal Spec.
- [x] Map actual tracked & runtime consumers of prototype.
- [x] Move useful behavior-only tests to public Standing seam.
- [x] Remove no-longer-used prototype, stale claims, obsolete documentation, retain Git history.
- [x] Check with `rg`, owner tests and Git diff; commit.

### T4. Sidecar/dependency closure
**Files:** `artifact_core/input_snapshot.py`, selected native family adapter and exact binding.
- [ ] Pick a real consumer whose format requires sidecars; capture one reproducible pre-fix mismatch.
- [ ] Bind complete declared graph through existing Runtime/Artifact native semantics.
- [ ] Test substitution/replacement failures and actual native readback; expand qualification only to proved bindings; commit.

### T5. Consumer readback integration
**Files:** selected Game/Publication/Data consumer tests and Artifact contract only.
- [ ] Execute one exact source material → native output → verify → independent consumer readback flow.
- [ ] Bind input/output digest, current provider and consumer evidence.
- [ ] Assert verified technical scope vs separate domain acceptance; run each natural owner's tests; commit.

### T6. Contract & retire
**Files:** `artifact_operations/providers/direct_python.py`, `artifact_verification/stage.py`, `scripts/artifact_verify.py`, tests, docs.
- [ ] Census exact decision branches/callers; remove duplicate once migrated.
- [ ] Re-run negative suite and consumer readback; reduce lines and decision authorities without introducing third branch; commit.

### T7–T8. Cross-Owner adoption and release
**Owner:** Host/Harness/Runtime + natural consumer. Make a separate SourceCut-specific cross-Owner spec and only implement what proven consumer requires. Keep existing Host Work and Runtime Job distinctions; don't invent a global work registry. Merge via CI with reviewer independent of implementation; live deployed currentness is verified separately.

## Execution evidence

Record each ticket's RED output, GREEN output, source commit and actual consumer consequence. Check off only the ticket proved; do not claim broader implementation finished because the plan exists.


## Evidence snapshot — 2026-11-09

- T1/T2 implementation tests: new RED before code, GREEN after code, including contradicted FAIL remaining UNKNOWN.
- Owner verify via mise: 569 passed, 3 skipped, 42 deselected, 115 subtests; Ruff, source-bound finite checks green.
- Old model 289008 states plus the new shared-standing finite 50-case abstraction; zero counterexamples for those explicit models.
- Existing Office integration test test_legacy_stage_can_emit_exact_profile_claim_key_set remains red on an unmodified baseline as well as candidate; this is not evidence of a source regression. It is not included in the non-integration gate. Needs real native-toolchain investigation before integration qualification.
- No remote deployment or domain consumer acceptance claimed. T3–T8 remain not implemented.


## T3 closure and T1/T2 clarification — 2026-11-09

- The prototype standing_decision_r1.py had no visible production consumers; only one pressure test imported it. That test has been migrated into the production entrypoint suite, retaining actual WAVE and integration-marked Office scenarios. Git retains its history; source file is retired.
- The native v2 adapter now treats a matched and valid required claim FAIL as a supported scoped FAIL, rather than treating every ordinary failure diagnostic as evidence corruption. A native PASS contradicting such a failure remains UNKNOWN. This behavior has a test-first RED→GREEN record.
- T4 input closure, T5 actual final consumer and T6 duplicate production-policy removal remain OPEN. T3 prototype deletion alone does NOT establish a fully unified production qualification engine.


## T3 final owner verification receipt — 2026-11-09

- From capabilities/artifact: UV_OFFLINE=1 MISE_OFFLINE=1 mise run verify.
- Actual result: 569 passed, 3 skipped, 42 integration deselected, 115 subtests, Ruff and finite abstraction checks PASS.
- Full toolchain Office integration remained outside the owner non-integration gate; earlier independent unmodified-source control reproduced that test failure.
- Exact HEAD and GitHub CI must still be checked after this T3 commit; SOURCE success does not establish MERGED, INSTALLED, CONSUMED or DOMAIN_ACCEPTED.
