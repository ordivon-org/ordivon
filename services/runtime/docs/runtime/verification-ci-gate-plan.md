# Verification Platform CI Gate Plan

Status: **PLAN**
Date: 2026-04-28
Phase: 3.5
Tags: `verification`, `ci`, `gates`, `plan`, `github-actions`

## 1. Purpose

Define how the Verification Platform (Phase 3.4) enters CI — which gates run
when, at what classification (Hard / Escalation / Advisory), and how failures
feed into the Learning Platform.

This document is a **plan**, not an implementation. No CI workflow files are
modified in Phase 3.5. Actual CI integration begins in Phase 3.6+.

## 2. Why CI Gate Design Is Needed Now

The Verification Platform is now runnable (`scripts/run_verification_baseline.py`)
but is not connected to CI. Without CI gates:

- Verification gates degrade to manual-only checks (run inconsistently)
- Governance classification regressions pass silently between pushes
- Evidence chain integrity violations go undetected until the next manual audit
- Repo Governance CLI behavior can drift without contract enforcement

The existing CI (`ci.yml`, `nightly-regression.yml`, `security.yml`) already
covers layers L0 (ruff, mypy), L1 (unit tests), L2 (integration tests), L3
(contract tests), L4 (architecture checker), and L8 (security). But it does NOT
cover L5 (runtime evidence), L6 (DB-backed audit), L7 (eval corpus), or L10
(repo CLI smoke).

This plan bridges the gap without disrupting existing CI.

## 3. Current Verification Assets

| Asset | CI Status | Layer | Gate Class |
|-------|-----------|-------|------------|
| ruff check + format | ✅ in `ci.yml` `backend-static` | L0 | Hard |
| mypy (type check) | ⚠️ `continue-on-error: true` | L0 | Escalation |
| vulture (dead code) | ⚠️ `continue-on-error: true` | L0 | Advisory |
| Architecture checker | ✅ in `ci.yml` `backend-static` | L4 | Hard |
| Unit tests (DuckDB) | ✅ in `ci.yml` `backend-unit` | L1 | Hard |
| Unit tests (PG) | ✅ in `ci.yml` `backend-unit-pg` | L9 | Hard |
| Integration tests | ✅ in `ci.yml` `backend-integration` | L2 | Hard |
| Contract tests | ✅ in `ci.yml` `api-contract` | L3 | Hard |
| Security scan | ✅ in `security.yml` | L8 | Advisory |
| **Runtime evidence checker** | ❌ not in CI | L5 | Hard |
| **DB-backed audit** | ❌ not in CI | L6 | Escalation |
| **Eval corpus** | ❌ not in CI | L7 | Hard |
| **Repo CLI smoke** | ❌ not in CI | L10 | Hard |
| **Verification baseline runner** | ❌ not in CI | All | — |

## 4. Proposed CI Gate Levels

CI runs at different frequencies and scopes. The Verification Platform maps
to four levels:

### 4.1 PR Fast Gate

Runs on every push to a PR. Must complete in **< 2 minutes**. Hard gates only.
Blocks merge on failure.

| Gate | Script | Est. Time |
|------|--------|-----------|
| ruff check + format | `ruff check/format` | ~3s |
| Architecture checker | `scripts/check_architecture.py` | ~2s |
| Runtime evidence (static) | `scripts/check_runtime_evidence.py` | ~2s |
| Eval corpus | `evals/run_evals.py` | ~10s |
| Repo CLI smoke | `scripts/repo_governance_cli.py` (2 cases) | ~15s |
| **Total** | | **~30s** |

### 4.2 PR Full Gate

Runs on every push to a PR. Must complete in **< 10 minutes**. Extends PR Fast
Gate with test suites.

| Gate | Script | Est. Time |
|------|--------|-----------|
| All PR Fast Gates | (above) | ~30s |
| Unit tests (DuckDB) | `pytest tests/unit -q` | ~2m |
| Integration tests | `pytest tests/integration -q` | ~2m |
| Contract tests | `pytest tests/contracts -q` | ~30s |
| **Total** | | **~5m** |

### 4.3 Main Branch Gate

Runs on push to `main`. Hard gates — no merge bypass. Includes PG regression.

| Gate | Script | Est. Time |
|------|--------|-----------|
| All PR Full Gates | (above) | ~5m |
| Unit tests (PG) | `PFIOS_DB_URL=postgresql://... pytest tests/unit` | ~3m |
| Integration tests (PG) | `PFIOS_DB_URL=postgresql://... pytest tests/integration` | ~3m |
| DB-backed audit | `scripts/audit_runtime_evidence_db.py` | ~5s |
| **Total** | | **~11m** |

### 4.4 Scheduled Deep Gate

Runs on cron (nightly). Includes expensive/advisory gates.

| Gate | Script | Est. Time |
|------|--------|-----------|
| All Main Branch Gates | (above) | ~11m |
| Security (bandit, pip-audit) | already in `security.yml` | ~2m |
| Dead code (vulture) | `vulture governance/ domains/ ...` | ~30s |
| Full PG regression (unit + integration + contracts) | `PFIOS_DB_URL=postgresql://... pytest tests/` | ~20m |
| Coverage report | `pytest --cov` | ~3m |
| **Total** | | **~36m** |

## 5. Gate Classification

### 5.1 Hard Gates (fail → block)

| Gate | Rationale |
|------|-----------|
| ruff format/check | Code must follow project style |
| Architecture boundaries | Core/Pack boundary violation = governance compromise |
| Runtime evidence (static) | Missing receipt/outcome linkage = silent failures |
| Eval corpus (100%) | Governance classification regression = silent misclassification |
| Repo CLI smoke | Adapter correctness = user-facing correctness |
| Unit tests | Logic correctness |
| Integration tests | Service wiring correctness |
| Contract tests | API surface conformance |
| Schema drift check | ORM/SQL alignment |

### 5.2 Escalation Gates (fail → warn, review required)

| Gate | Rationale |
|------|-----------|
| DB-backed audit | Pre-existing data issues or transient conditions |
| PG regression (non-DB PRs) | Schema changes may need PG-specific drift handling |
| mypy (type check) | Pre-existing type debt from earlier waves |
| Low-severity security warnings | May have false positives or accepted risk |

### 5.3 Advisory Gates (fail → record, never block)

| Gate | Rationale |
|------|-----------|
| Dead code (vulture) | No runtime impact, cleanup debt |
| Coverage report | Informational — coverage is a snapshot, not a gate |
| import-linter | Module boundary analysis, may have false positives |

## 6. Recommended Priority Order for CI Integration

1. **PR Fast Gate** — smallest surface, highest impact. Catches governance
   regressions, architecture violations, and evidence gaps within 30 seconds.
   This should be the first CI step to add.

2. **Eval Corpus** — moves from manual-only to CI. Prevents governance
   classification regressions. Already integrated into
   `scripts/run_verification_baseline.py` as a hard gate.

3. **Runtime Evidence Checker** — static check, no DB dependency. Catches
   ORM model drift (missing fields, broken linkages). Already a hard gate
   in the verification baseline.

4. **DB-Backed Audit** — requires PG service container. Should run on Main
   Branch Gate and Scheduled Deep Gate. Kept as escalation initially until
   historical data issues stabilize.

5. **Repo CLI Smoke** — lightweight contract test for the CLI adapter.
   Validates that `execute` and `reject` decisions remain correct. Hard gate.

6. **PG Full Regression** — already partially in CI (`backend-unit-pg`).
   Extend to include integration and contract tests on PG for Main Branch Gate.

## 7. Verification Baseline Runner CI Role

`scripts/run_verification_baseline.py` currently orchestrates all gates locally.
Its CI role is:

- **Development**: run locally before pushing — gives developers the same
  feedback CI will give.
- **CI wrapper**: instead of calling individual checkers separately, CI can
  call `run_verification_baseline.py` and parse the JSON summary.
- **Gate consistency**: ensures local and CI use identical gate classification
  and exit code semantics.

Recommendation: CI jobs should call individual checkers (for granular failure
output), but `run_verification_baseline.py` should be the canonical reference
for which gates run and how they are classified.

## 8. Eval Corpus CI Role

`evals/run_evals.py` runs 24 cases (10 finance + 10 coding + 4 cross-pack)
in ~10 seconds. It produces a JSON summary with per-case pass/fail.

CI integration:
- **PR Fast Gate**: `uv run python evals/run_evals.py` → exit 0 = all pass.
- **Failure handling**: outputs failed case IDs and expected vs actual.
- **Future**: when eval corpus grows beyond 50 cases, consider splitting
  into per-pack CI steps.

## 9. Repo Governance CLI Contract Plan

The CLI is an Adapter-layer component. Its behavior must be contract-verified
in CI to prevent drift.

Current state:
- 20 unit tests cover CLI behavior directly (subprocess-based)
- `scripts/run_verification_baseline.py` runs 2 smoke cases (valid→execute,
  forbidden→reject) as hard gates

Future contract plan:
- Add a JSON schema for CLI output (Phase 3.6+)
- Add contract tests that validate CLI output against the schema
- CI gate: `pytest tests/contracts/test_cli_output_schema.py`
- Ensure side_effects fields are always `false`

## 10. DB-Backed Audit CI Strategy

`scripts/audit_runtime_evidence_db.py` requires a live database with evidence
chain data. For CI:

- **Main Branch Gate**: run against the test PG database after seeding
  with known-good evidence chain data.
- **Scheduled Deep Gate**: run against a production-like dataset.
- **Escalation Gate**: failures are recorded but do not block. Repeated
  failures trigger Review → Lesson → CandidateRule(draft).
- **Empty database**: the audit handles empty databases gracefully
  (0 objects scanned, 0 violations).

### Known issue (Phase 3.4)

After fixing the import issue, the DB audit runs correctly. Historical
CandidateRule drafts with empty lesson_ids/source_refs are correctly
detected. These are pre-existing data conditions. The audit's CI behavior
should treat these as escalation, not hard gate failures.

## 11. PG Full Regression Strategy

PG full regression (`PFIOS_DB_URL=postgresql://... pytest tests/`) is already
partially in CI (`backend-unit-pg`). The strategy is:

- **Current**: `backend-unit-pg` runs unit tests on PG + schema drift check
  on every push to PR/main.
- **Recommended**: add `backend-integration-pg` (already exists in ci.yml)
  and `backend-contracts-pg` to Main Branch Gate.
- **Scheduled Deep Gate**: run all tests on PG (unit + integration + contracts).
  Already 757 tests at ~20s. Cost is acceptable for nightly.

## 12. Security Scan Strategy

Security scanning already exists in `security.yml` (Bandit + pip-audit on push
to main + PR + weekly schedule).

No changes needed in Phase 3.5. The existing security job maps to Advisory Gate
classification (record failures, do not block non-security PRs).

## 13. Migration Path

| Phase | Action | CI Change |
|-------|--------|-----------|
| **3.5** | Plan only | Zero CI workflow changes |
| **3.6** (this phase) | ✅ Add PR Fast Gate | New `verification-fast` job in `ci.yml`: eval corpus + runtime evidence + repo CLI smoke + architecture checker |
| **3.7** | GitHub Actions Adapter | Repo Governance CLI runs as a GHA action; PR receives governance annotation |
| **3.8** | Add Main Branch Gate | DB-backed audit + PG full regression on push to main |
| **3.9** | Add Scheduled Deep Gate | Nightly full regression + coverage |

## 14. Non-Goals (Phase 3.5)

- Does NOT add PR Full Gate / Main Branch Gate / Scheduled Deep Gate
- Does NOT add PG full regression or DB-backed audit to PR Fast Gate
- Does NOT change gate classification of existing CI steps
- Does NOT require new infrastructure or services
- Does NOT force all gates to be hard gates
- Does NOT connect to shell/MCP/IDE
- Does NOT create ExecutionRequest/ExecutionReceipt

## 15. Risks

| Risk | Mitigation |
|------|-----------|
| Eval corpus too slow for PR Fast Gate | Currently ~10s for 24 cases; monitor as corpus grows |
| DB audit unstable in CI | Escalation gate — does not block; runs on main branch only |
| PG service container cost | Already used in `backend-unit-pg`; marginal additional cost |
| Ruff pre-existing debt triggers false CI failures | Scope ruff to changed files only (Wave file pattern) |
| Verification baseline runner diverges from CI | Keep runner as canonical reference; CI calls individual checkers |

## 16. Next Recommended Phase

**Phase 3.6 — PR Fast Gate Implementation**: Add a new `verification-fast` job
to `ci.yml` that runs eval corpus + runtime evidence checker + architecture
checker + repo CLI smoke as Hard Gates. This is the smallest CI step with the
highest governance value — it catches classification regressions, evidence
gaps, and adapter drift within 30 seconds.
