# Coding Trust Adoption Round 1 Receipt

Status: **CLOSED** | Date: 2026-05-08
Phase: Coding-Trust-Adoption-R1
Task type: adoption source-of-truth + dogfood matrix + report UX + project AI playbook
Risk level: AP-R0 / R0
Authority impact: current_truth only; no authorization semantics

## Summary

Round 1 moves Ordivon Verify from CTTS foundation closure into Coding Trust
Adoption. The implementation strengthens the adoption source of truth, dogfood
matrix, report UX, and emitted project AI playbook while preserving OV's
read-only trust boundary.

## Files Changed

- `docs/product/coding-trust-adoption-plan.md`
- `docs/runtime/coding-trust-adoption-dogfood-matrix.md`
- `docs/runtime/coding-trust-adoption-round-1-receipt.md`
- `src/ordivon_verify/report.py`
- `src/ordivon_verify/discovery.py`
- `tests/unit/product/test_ordivon_verify_cli.py`
- `AGENTS.md`
- `docs/ai/README.md`
- `docs/ai/current-phase-boundaries.md`
- `docs/governance/document-registry.jsonl`

## Dogfood Matrix

The matrix now defines three generic dogfood families:

- tiny fixture repo for `minimal` / `vibe` adoption
- medium AI-heavy repo for `standard` / `merge` adoption
- agent-native repo sample for `deep` / `release` adoption

Hermes remains allowed only as a read-only dogfood sample. Hermes-specific
paths, gates, owners, workflows, or skills must not become generic OV template
rules.

## Report UX Changes

- Summary output is capped to top findings and explicit next action.
- Markdown output includes top findings and adoption boundaries.
- Adoption boundaries distinguish claim/evidence/review status and candidate
  gates from canonical gates.
- Full Markdown still carries agent-native appendix details for project AI
  repair work.

## Template / Playbook Changes

The emitted `PROJECT_AI_LOCALIZATION.md` and
`governance/project-ai-onboarding-playbook.md` now give project AI a concrete
localization workflow:

- read discovery candidates as hints
- fill agent claim bindings
- request owner/reviewer confirmation for canonical gates
- convert DEGRADED/BLOCKED into evidence repair, claim downgrade, or debt
- record receipts and lessons
- keep CandidateRule drafts separate from active policy

## Trust Behavior Changes

No new authorization behavior was added.

OV still emits only:

- `READY_WITHOUT_AUTHORIZATION`
- `DEGRADED`
- `BLOCKED`

## Tests Added

Tests cover:

- compact summary semantics
- Markdown adoption boundary sections
- full appendix retention
- emitted project AI playbook instructions
- template purity and no target repo writes
- non-authorization wording invariants

## Test Command Results

Passed:

```bash
uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_cli.py -q
# 83 passed

uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_*.py tests/unit/product/test_coding_trust_template_localization_ctts2.py -q
# 320 passed

uv run ruff check .
# All checks passed

uv run ruff format --check .
# 367 files already formatted

python -m compileall -q src/ordivon_verify scripts tests/unit/product
# PASS

git diff --check
# PASS
```

## Governance Check Results

Passed:

```bash
uv run python scripts/check_document_registry.py
# 240 registered docs, 0 completeness violations

python scripts/check_artifact_registry.py
# 705 registered artifacts, 0 ungoverned, 0 class errors

python checkers/current-truth/run.py
# PASS

uv run python scripts/run_baseline.py --read-only
# READY, 26/26 hard gates PASS

uv run python scripts/run_baseline.py --pr-fast
# READY, 12/12 hard gates PASS

uv run python scripts/audit_ordivon_verify_public_wedge.py
# 0 blocking findings
```

Current-truth drift was repaired after registering the three CTA documents:

```bash
python checkers/current-truth/run.py --auto-fix
# DG entries: 237 -> 240 across AI onboarding/current truth docs
python checkers/current-truth/run.py
# PASS
```

## Known Debts

- More real external dogfood repositories are still needed.
- Report UX can later gain an even shorter `--pr-comment` mode if user testing
  shows Markdown is still too long.
- Skill/memory/trace checks remain file-level heuristics, not semantic proof.

## NO-GO Boundary Confirmation

This phase did not add SaaS, GitHub bot behavior, agent runner behavior, MCP
server behavior, auto-fixer behavior, public schema-standard claims,
compliance/certification claims, production-readiness claims, Trade/Health
profiles, target repo mutation by default, or action authorization.

## Git Status

Working tree had CTA changes staged for local commit at closure.

## Commit SHA

Not committed at receipt creation. Use `git log -1 --oneline` after commit.
