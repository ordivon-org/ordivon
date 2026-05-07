# CTTS-2 Template Localization Dogfood Receipt

Status: **CLOSED** | Date: 2026-05-08
Phase: CTTS-2 — Template Localization Dogfood & Evidence Casebook
Task type: Localization dogfood + evidence casebook + report semantics hardening
Risk level: AP-R0 / R0
Authority impact: current_truth only; no authorization semantics

## 1. Files Changed

Core behavior:

- `src/ordivon_verify/checks/gates.py`
- `src/ordivon_verify/report.py`

Product and AI docs:

- `docs/product/coding-trust-localization-casebook-ctts-2.md`
- `docs/product/coding-trust-profile-template-system.md`
- `docs/product/ordivon-verify-quickstart.md`
- `AGENTS.md`
- `docs/ai/README.md`
- `docs/ai/current-phase-boundaries.md`
- `docs/ai/new-ai-collaborator-guide.md`

Tests and fixtures:

- `tests/unit/product/test_coding_trust_template_localization_ctts2.py`
- `tests/fixtures/coding_trust_localization/minimal_localization/**`
- `tests/fixtures/coding_trust_localization/standard_localization/**`
- `tests/fixtures/coding_trust_localization/deep_localization/**`

Registries:

- `docs/governance/document-registry.jsonl`
- `docs/governance/artifact-registry.jsonl`

Current-truth drift:

- `docs/ai/systems-reference.md`
- `docs/ai/new-ai-collaborator-guide.md`
- `docs/ai/current-phase-boundaries.md`

## 2. New Fixtures

Three generic fixture families were added under
`tests/fixtures/coding_trust_localization/`.

- `minimal_localization`: fake tiny project, source/test artifact, clean claim
  binding, missing-evidence claim binding, receipt, project AI playbook, and
  discovery candidates.
- `standard_localization`: merge-stage evidence system with claim binding,
  owner-confirmed gate manifest, debt ledger, document registry, receipt, and
  project AI playbook.
- `deep_localization`: release/skill/tool/memory/lesson/CandidateRule surfaces
  with intentional release and skill safety gaps for release-stage blocking.

All fixture content uses fake project names and placeholder roles. No
Hermes-private path, Ordivon-private path, real owner, real deployment
authority, or real business workflow is embedded in template bodies.

## 3. Casebook Summary

Added `docs/product/coding-trust-localization-casebook-ctts-2.md`.

The casebook documents:

- minimal, standard, and deep localization examples
- Claim -> Evidence -> Review -> Decision Boundary -> Receipt -> Debt/Lesson
  -> CandidateRule/no-rule loop
- proper downgrades for missing tests, missing review, workflow candidates,
  release claims, skill/tool capability, and CandidateRule drafts
- safe wording and blocked wording
- Hermes read-only dogfood boundary

## 4. Report Wording Changes

The trust report disclaimer now preserves existing compatibility wording while
covering CTTS-2 boundaries:

```text
READY means selected checks passed; it does not authorize execution,
does not authorize merge, does not authorize deployment, and does not authorize
release, tool use, policy activation, or external action.
```

Tests now assert that positive authorization wording such as approved-to,
authorizes, safe-to-merge, safe-to-deploy, certification, compliance, and
production-ready language does not appear in READY output.

## 5. Trust Behavior Changes

For Coding Trust gate manifests (`profile: ai_coding_trust_audit`), external
gate validation now requires:

- `owner_confirmed: true`
- non-empty `reviewer`
- non-empty `approver`

This prevents workflow or command candidates from becoming canonical evidence
gates merely because they were discovered. Existing non-Coding external gate
fixtures remain compatible.

## 6. Tests Added

Added `tests/unit/product/test_coding_trust_template_localization_ctts2.py`.

Coverage includes:

- minimal claim -> artifact -> test -> receipt binding
- compact summary behavior
- standard merge-stage READY_WITHOUT_AUTHORIZATION path
- missing claim binding BLOCKED
- owner confirmation required for canonical gate
- evidence without review not treated as Reviewed/Gate-Checked
- deep release/skill gaps BLOCKED
- CandidateRule draft remains non-policy
- allowed-tools remains non-permission
- report wording invariants
- template purity and discovery candidate separation
- CLI template regressions
- New AI Context Check discoverability

## 7. Test Command Results

Passed:

```bash
uv run --with pytest python -m pytest tests/unit/product/test_coding_trust_template_localization_ctts2.py tests/unit/product/test_ordivon_verify_cli.py -q
# 86 passed

uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_*.py tests/unit/product/test_coding_trust_template_localization_ctts2.py -q
# 310 passed

python -m compileall -q src/ordivon_verify tests/unit/product scripts

uv run ruff format --check src/ordivon_verify/cli.py src/ordivon_verify/discovery.py src/ordivon_verify/report.py src/ordivon_verify/checks/gates.py tests/unit/product/test_coding_trust_template_localization_ctts2.py tests/unit/product/test_ordivon_verify_cli.py
# 6 files already formatted

uv run ruff check src/ordivon_verify/cli.py src/ordivon_verify/discovery.py src/ordivon_verify/report.py src/ordivon_verify/checks/gates.py tests/unit/product/test_coding_trust_template_localization_ctts2.py tests/unit/product/test_ordivon_verify_cli.py
# All checks passed

pnpm --dir apps/web test
# 10 test files passed, 57 tests passed

pnpm --dir apps/web build:quality
# Next.js build passed

uv run python evals/run_evals.py
# 24/24 passed

uv run python checkers/architecture-boundaries/run.py
# Files: 159 | Violations: 0

uv run python checkers/runtime-evidence/run.py
# Present: 4 | Violations: 0
```

Whole-repo ruff remains a known broader codebase debt:

```bash
uv run ruff format --check .
# FAIL: 62 files would be reformatted

uv run ruff check .
# FAIL: 32 existing lint findings across historical areas
```

CTTS-2 touched Python files pass local ruff format/check.

## 8. Governance Check Results

Passed:

```bash
uv run python scripts/check_document_registry.py
# 235 registered docs, 0 completeness violations

python scripts/check_artifact_registry.py
# 705 registered artifacts, 0 ungoverned, 0 class errors

uv run python scripts/run_baseline.py --read-only
# READY, 26/26 hard gates PASS

uv run python scripts/run_baseline.py --pr-fast
# READY, 12/12 hard gates PASS

uv run python scripts/audit_ordivon_verify_public_wedge.py
# 0 blocking findings

git diff --check
# PASS
```

Current truth drift was auto-fixed after registering the CTTS-2 casebook:

```bash
python checkers/current-truth/run.py --auto-fix
# Auto-fixed DG count drift after casebook/receipt registration

python checkers/current-truth/run.py
# PASS
```

## 9. Known Debts

- Whole-repo ruff format/check is not clean. This is pre-existing broad repo
  style/lint debt and was not expanded in CTTS-2.
- CTTS-2 does not emit template files to a target repo. It remains dry-run only.
- CTTS-2 validates representative deep surfaces but does not implement a full
  public schema standard or adapter system.

## 10. NO-GO Boundary Confirmation

CTTS-2 did not add:

- new profiles
- SaaS behavior
- GitHub bot behavior
- public schema-standard claims
- compliance or certification claims
- production-readiness claims
- project-specific Hermes logic
- merge/release/deploy/execution/tool/skill/business workflow authorization

`READY_WITHOUT_AUTHORIZATION` remains evidence sufficiency only.

## 11. New AI Context Check

The New AI Context Check is documented in:

- `docs/product/coding-trust-profile-template-system.md`
- `docs/ai/README.md`
- `docs/ai/new-ai-collaborator-guide.md`
- `AGENTS.md`
- `docs/ai/current-phase-boundaries.md`

The test
`test_new_ai_context_check_is_discoverable_from_onboarding_docs` verifies that a
new AI can discover CTTS, template placeholders vs project-local evidence,
`discovery-candidates.json`, tier meanings, READY_WITHOUT_AUTHORIZATION,
CandidateRule boundaries, owner/reviewer confirmation, and skill/tool/workflow
non-permission boundaries from normal onboarding docs.

## 12. Git Status

Git status at receipt creation: working tree modified with CTTS-1 baseline
changes plus CTTS-2 additions; not committed.

## 13. Commit SHA

Not committed.
