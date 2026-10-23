# Harness U4 — Spec → SOP → existing Skill + Tool → Acceptance

**Process decision (2026-10-15):** Use mature existing Skills to support planning/execution. A task-specific SOP is the execution plan; **do not create or require a new Skill per stage**. This SOP supersedes the earlier four-stage Skill-distillation proposal.

## 1. Spec — what must hold?

Scoped verified evidence must become stale when either Harness `pyproject.toml` `[project].requires-python` or top-level `uv.lock` `requires-python` changes. Unchanged semantics, including reordered constraints and formatting-only changes, stay current. Missing required Python declarations fail closed. Existing historical runtime dependency evidence digests must preserve their exact bytes.

Source scope: `services/harness/scripts/check_evidence.py` and targeted tests. No protected/main merge, provider, installation or live service operation is implied.

## 2. Short SOP — forecast actions and bound capabilities

1. **Locate** exact current source/Work and the acceptance predicate. Skill: existing TDD practice. Tools: Host `work.get`, Runtime `workspace.get/read`, Git.
2. **Reproduce** the smallest counterexample on the original logic, including a legal unchanged/equivalent control. Skills: existing `user-agents/diagnosing-bugs` and `user-agents/tdd`. Tools: Runtime `workspace.exec`, Python `unittest`.
3. **Repair** the minimal code path, preserving historical digest identity; no change to unrelated interfaces. Skill: `user-agents/tdd`. Tools: Runtime `workspace.mutate/exec`, Git diff.
4. **Check** using the owner's Python and focused regressions; compare any lint warning against the source baseline. Skill: `obra-superpowers/verification-before-completion`. Tools: `mise exec -- python3`, `unittest`, `ruff`, `git diff --check`, `check_evidence.py`.
5. **Accept or hold** strictly against the Spec: record expected vs actual outcome, exact commit, run receipts and untested scope. Skill: existing verification practice; optional self-review via mature `user-agents/code-review` as helpful, not mandatory independent review.

This SOP is a **revisable forecast**, not a second Spec or a new permission system. Skill selection informs the procedure; Tools actually execute it. If observed evidence changes, adapt the SOP and record why.

## 3. Actual execution — factual receipts

Historical first repair candidate `cb2f39df11286d91d46de43398ca258fa3aa8b4d` and initial RED/GREEN preceded this written SOP; no retroactive pre-action claim. Earlier RED `job-01a13fb0-9d0f-7451-a38c-f1eda5b184bc` caught three false-green variants (project-only, lock-only, both). GREEN `job-01a13fb2-2aa6-7fd0-9cc1-b88673df0786` fixed them.

SOP-guided continuation added reordered-equivalent and missing-declaration controls. Native run `job-01a14012-d9a5-74c0-9b38-c40cbe00ff17`: targeted **7/7 PASS**, existing Evidence Index **12/12 PASS**, evidence **95 historical / 1 verified**, focused Ruff E4/E7/E9/F and formatting checks PASS. Three unrelated historical full-Ruff warnings remained unchanged.

An intervening experiment generated four stage Skills and catalog-tested them. The **user subsequently rejected per-stage Skill creation**; these experimental candidate files were removed from the current branch. Their historical Git commits remain traceable, but they are not part of the current proposed system. One useful finding was a broad substring Skill search matching an unrelated word such as `a`; it warrants a separate scoped search-quality task, not new Skills.

## 4. Acceptance — claim exactly the verified scope

Required: original three false-green cases rejected; unchanged/reordered constraints accepted; absent requirement rejected; existing Evidence Index regression and historical evidence contract green; project Python **3.14.7**; clean exact Git commit; source scope limited.

Acceptance of this local code candidate **does not imply** protected repository publication, provider or installed effect, or whole-Harness system acceptance. No independent audit step is automatically required for this ordinary scoped source candidate.

**Next operating convention:** Spec → compact SOP (including *existing* Skill + Tool bindings) → act → acceptance. Improve the next SOP from real execution observations; create no new Skill unless a distinct later need is explicitly established.

## Remote-main re-representation (2026-10-16)

The historical 95/1 Evidence receipt above belongs to the earlier *local* source cut. On the latest observed GitHub main `3818e74543a79225d429e27e2acffcf88a40792a`, native Python 3.14.7 test replay `job-01a1406d-1b19-7660-96fe-928bf3d7bf66` passed 7/7 Python currentness cases, 12/12 existing Evidence tests and the actual **93 historical / 1 verified** evidence inventory. Preserve the remote inventory and never substitute local evidence counts as remote truth.
