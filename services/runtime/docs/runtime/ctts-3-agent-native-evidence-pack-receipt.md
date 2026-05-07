# CTTS-3 Agent-Native Evidence Pack Receipt

Status: **CLOSED** | Date: 2026-05-08
Phase: CTTS-3 — Template Adoption Pack + Agent-Native Evidence Pack
Task type: template export + read-only evidence surface hardening
Risk level: AP-R0 / R0
Authority impact: current_truth only; no authorization semantics

## Summary

CTTS-3 moves Coding Trust from dry-run templates to an explicit adoption pack.
OV can now emit project-independent template files to a user-selected output
directory while keeping project observations separated in
`governance/discovery-candidates.json`.

The phase also extends release-stage Coding Trust evidence with read-only
memory/content and harness/trace checks. These checks verify structure and
boundary language only. They do not run agents, execute tools, start servers,
refresh tokens, approve workflows, or authorize merge/release/deploy/action.

## Files Changed

- `src/ordivon_verify/cli.py`
- `src/ordivon_verify/discovery.py`
- `src/ordivon_verify/report.py`
- `src/ordivon_verify/__init__.py`
- `tests/unit/product/test_ordivon_verify_cli.py`
- `docs/product/coding-trust-profile-template-system.md`
- `docs/product/ordivon-verify-quickstart.md`
- `AGENTS.md`
- `docs/ai/README.md`
- `docs/ai/current-phase-boundaries.md`
- `docs/governance/document-registry.jsonl`
- `docs/runtime/ctts-3-agent-native-evidence-pack-receipt.md`

## Behavior Added

- `--emit-template-dir <out>` writes the selected template pack to an explicit
  output directory.
- Emitted template packs include:
  - `PROJECT_AI_LOCALIZATION.md`
  - `AI_TRUST_LEVELS.md`
  - `ordivon.verify.json`
  - tier-specific governance placeholders
  - `governance/discovery-candidates.json`
- Default discovery remains read-only and writes no target repo files.
- Release-stage evidence appendix now includes memory/content hygiene and
  harness evidence import.
- Release-stage blockers now include:
  - memory source/freshness/scope/authority confusion
  - CandidateRule treated as policy
  - degraded/blocked signal treated as truth
  - checkpoint approval leakage
  - missing failed tool call evidence
  - trace presence treated as truth

## Trust Boundary

OV emits only trust evidence states:

- `READY_WITHOUT_AUTHORIZATION`
- `DEGRADED`
- `BLOCKED`

OV does not emit L6 Authorized. Project owner/reviewer remains responsible for
merge, release, deploy, execution, tool use, skill permission, and business
workflow authorization.

## Tests Added

Added product coverage for:

- explicit template export
- no target repo writes by default
- `--emit-template-dir` requiring `--suggest-config`
- emitted `PROJECT_AI_LOCALIZATION.md`
- emitted `AI_TRUST_LEVELS.md`
- memory/content release-stage blockers
- harness/trace release-stage blockers
- full markdown appendix for memory and harness evidence

## Verification

Run evidence for closure:

```bash
uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_cli.py -q
78 passed

uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_cli.py tests/unit/product/test_coding_trust_template_localization_ctts2.py -q
91 passed

uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_*.py tests/unit/product/test_coding_trust_template_localization_ctts2.py -q
315 passed

uv run ruff check src/ordivon_verify tests/unit/product/test_ordivon_verify_cli.py
All checks passed

python -m compileall -q src/ordivon_verify
PASS
```

Full governance regression:

```bash
uv run ruff check .
All checks passed

uv run ruff format --check .
367 files already formatted

uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_*.py -q
315 product tests passed when run with CTTS-2 localization test module

uv run python scripts/check_document_registry.py
236 registered docs, 0 completeness violations

python scripts/check_artifact_registry.py
705 registered artifacts, 0 ungoverned, 0 class errors

uv run python scripts/run_baseline.py --read-only
READY, 26/26 hard gates PASS

uv run python scripts/run_baseline.py --pr-fast
READY, 12/12 hard gates PASS

uv run python scripts/audit_ordivon_verify_public_wedge.py
0 blocking findings

git diff --check
PASS
```

Current-truth drift was repaired after registering this receipt:

```bash
python checkers/current-truth/run.py --auto-fix
python checkers/current-truth/run.py
PASS
```

## Known Debts

- CTTS-3 does not write templates directly into target repos unless the user
  deliberately chooses an output directory inside that repo.
- CTTS-3 does not publish a schema standard.
- CTTS-3 does not implement Trade, Health, Finance, SaaS, GitHub bot, MCP
  server, or agent runner behavior.
- Memory/content and harness/trace import are file-level heuristics, not
  business truth adjudication.

## NO-GO Confirmation

This phase did not add:

- public schema-standard claims
- compliance/certification claims
- production-readiness claims
- external project authorization
- SDK/API/MCP server behavior
- agent/tool execution
- token handling or refresh
- automatic repair

## Git Status

Git status after commit amend: clean.

## Commit SHA

Committed locally. Exact self-referential SHA is intentionally not embedded in
the receipt to avoid an amend loop; use `git log -1 --oneline` as the source of
truth for the final commit id.
