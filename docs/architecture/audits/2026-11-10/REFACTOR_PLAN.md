# REFACTOR_PLAN — evidence-led small-batch retirement, no capability expansion

Source SHA: ef17d6879d12faa61fff3bb762b0d500d73c9113. Read AUDIT_SCOPE, INVENTORY and AUDIT_REPORT first. Sequence is F0 -> F1 -> F2 -> F3 -> F4 -> F5. Execute only source-bound changes with real owners; no new feature, test, public consumer, registry, execution controller or policy framework. Plans are not product delivery.

## F0 — establish current baseline (complete)

- [x] Root 5002 Git-tracked paths, 21 Owners and registered source regions, 5003-row inventory ledger including header.
- [x] 12 modern criteria with falsifiable diagnostics and canonical Nx/Turborepo, Fowler, Google SRE, Microsoft clean architecture references.
- [x] Native root checkers pass: `python3 tools/repo/check_owner_boundaries.py`, `check_architecture_docs.py`, `check_composition_architecture.py`. Keep their bounded scope explicit.
- [x] Real source-code sample across Host, Runtime, Harness, Gateway, Security, Network, Workstation, Web, Capital, Artifact and Composition; remaining file-level verdicts UNKNOWN.
- [x] Host Space handoffs seq 25965 and 25966 to seek other Owner rebuttal, not fabricated approval.

## F1 — remove retired Runtime planning files, repair their consumers (low risk)

Natural owner: services/runtime.

- [x] Delete `services/runtime/planning/EXECUTION_FABRIC_R1_ROADMAP.md`, an expressly retired plan. Remove only the now-dangling sourceEvidence entry in `services/runtime/planning/lego-plan-r1.json:14`.
- [x] Delete `services/runtime/planning/WINDOWS_AUTHORITY_FACTORIZATION_EXECUTION_PLAN_R1.md` and `WINDOWS_AUTHORITY_FACTORIZATION_LEGO_R1.json`; do not delete Windows C#/Rust/PowerShell source or its ability.
- [x] Delete the two obsolete `WORKSPACE_CONSUMER_LIFECYCLE_R21` Spec/Plan files containing requested-but-now-frozen API/consumer/test expansions. The existing merged TLA model remains unchanged.
- [x] Update `services/runtime/formal/README.md:384-386` and `services/runtime/docs/guides/runtime-legos.md:35-44` to describe current stock audit rather than a new consumer-feature roadmap.
- [ ] Verify with existing Runtime `python3 scripts/check_docs.py`, root `python3 tools/repo/check_architecture_docs.py`, `git diff --check`, and all observed direct source references. Rollback: Git revert this exact cleanup commit; Git retains deleted plans as historic objects.
- Risk: external users of raw historical path not statically observed; an old draft PR #1998 still links to these files. Close own outdated draft after its contents are preserved in history and superseded by new audit, rather than merging both.

## F2 — fix PG reclaim Git subprocess return-code defect (low diff, high contract relevance)

Natural owner: services/runtime.

- [x] Prechange existing `python3 -m unittest discover -s scripts/tests -p test_pg_workspace_reclaim.py -v`.
- [x] Prechange existing deployment suite with `ORDIVON_RUNTIME_INSPECT=/usr/local/libexec/ordivon/ordivon-runtime-inspect` as the known native tool prerequisite. The first attempt on a different isolated workspace without the executable yielded failures; rerunning after providing this *existing* binary produced 75/75 success in the prior stock-audit workspace.
- [x] Modify `services/runtime/scripts/ordivon-runtime-pg-reclaim:190-192` only. Take the existing Git `status` result, check both nonzero `returncode` and dirty `stdout` before proceeding; keep existing `git_changed_at_close` skip field. No other eligibility, minimum age, scheduled timing, or consumer interpretation changes.
- [x] Run exact same existing tests, compile-only syntax check, document checker and Git diff. No new tests, no new API.
- Risk: changing from allowing a failed Git command with empty stdout to skipping its close attempt is intentional fail-closed repair; Core still independently fences close.
- Rollback: revert this single source hunk.

## F3 — verify and review bounded effects

- [x] Root native boundary/architecture/composition checks and Git diff --check.
- [ ] Runtime existing 7 PG eligibility tests + 75 deploy/reclaim tests (test prerequisites explicit); docs checker; confirm no Rust/TypeScript/Test file mutation.
- [ ] Matt Standards axis: verify native authority, deep-module boundary, no second GC, no dangling references. Matt Spec axis: strictly no new feature/test/consumer. ECC: confirm what is genuinely retired and what is still consumed. Superpowers: cite fresh command outputs and exact Git SHA.
- [ ] Compare latest GitHub main/PRs for overlapping paths. Avoid racing other Owner branches; if this is already merged, REUSE and drop redundant diff.

## F4 — source commit and native handoff

- [ ] Commit with source SHA and small refactor message. No Git reset, stash or force close of any other Workspace.
- [ ] Publish scoped PR using existing GitHub credentials after verifying current main and Git checks; do not auto-merge pending external CI failures.
- [ ] Host Space handoff: STATUS, SOURCE_SHA, DONE, OPEN/UNKNOWN, exact file:line, reviewer objections and NEXT. Peer message commit != peer approval.

## F5 — further existing-code simplification, separately qualifiable and not falsely called complete

- [ ] Runtime A02: map active deploy/status/pressure/Windows callers and production installation digest before consolidating legacy lifecycle/reclaim/cache implementations. Use current native PG operator; do not create another GC or change semantic retention policy under guise of refactor.
- [ ] Harness A06, Web A07, Artifact A08: source-level diff and existing Owner verify prerequisites before any internal relocation; only move code if it reduces measured blast radius. No framework rewrite, no new tests.
- [ ] R2 root restructuring: documented as partially deployed; do not move all 21 Owners to packages as a cosmetic sweep. Keep natural authority and independent lockfiles.
- [ ] Full 5002-path ledger is a navigation index; no claim every file has a complete human semantic audit. The rest remain explicit follow-through with identified Owner.

## Rollback and completion standards

| Task | Existing mechanical proof | Rollback | Production claims |
| --- | --- | --- | --- |
| F1 | Existing doc/architecture root checks; no dangling tracked ref | Revert F1 Git commit | NONE |
| F2 | 7 PG reclaim tests + 75 deployment tests + syntax check | Revert isolated conditional | SOURCE_ONLY until installed hash/readback |
| F3 | Existing per-Owner/native checks, no new suite | Not applicable | No local check equals domain acceptance |
| F4 | PR/CI readback + Host handoff | Git revert before installed upgrade | MERGED separate from INSTALLED |
