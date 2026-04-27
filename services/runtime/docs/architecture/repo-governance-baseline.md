# Repo Governance Baseline

Status: **DOCUMENTED**
Date: 2026-04-28
Tags: `governance`, `reflexive`, `t0-gates`, `candidate-rule`, `baseline`

## 1. Philosophical Foundation

This repository is a governed system. The same governance philosophy that Ordivon
applies to financial decisions — Intake, Governance, Receipt, Outcome, Review,
Lesson, CandidateRule, Policy — also applies to the codebase itself.

This is **Recursive Governance Externalization**: a system externalizing its
internal governance principles into the tools, checks, documents, and rituals
that govern its own evolution.

```
Principle  →  Artifact  →  Practice  →  Recursion
    ↑                                         │
    └─────────────────────────────────────────┘
```

A governance principle is not complete until it has:
1. **Principle** — a clear rule or invariant
2. **Artifact** — a tool, test, checker, or CI gate that enforces it
3. **Practice** — humans and AI agents working under that artifact
4. **Recursion** — the artifact evolving based on real-world feedback

## 2. Ordivon ↔ Repo Mapping

| Ordivon Concept | Repo Governance Equivalent |
|-----------------|---------------------------|
| Intake          | PR brief / task plan / branch |
| Governance      | CI gates / architecture checker / T0 tools |
| Receipt         | CI logs / snapshots / test reports |
| Outcome         | CI result / dogfood result / incident |
| Review          | Postmortem / audit report / PR review |
| Lesson          | Regression test / new checker / ADR |
| CandidateRule   | Proposed CI gate (advisory, not blocking) |
| Policy          | Required branch protection / blocking T0 gate |

## 3. T0 Tool Definition

A **T0 tool** is a mandatory, pre-merge enforcement gate. Five criteria:

1. **Deterministic** — same code + same environment = same result
2. **Blocking** — failure prevents merge
3. **Scoped** — checks a defined target, not arbitrary scan
4. **Reproducible** — same command works locally and in CI
5. **Auditable** — output explains why it failed

## 4. The 12-Layer Governance Matrix

Each layer maps to one governance object. The status columns track how far
each layer has progressed through the Principle → Artifact → Practice → Recursion
cycle.

| # | Layer | Principle | Artifact | Practice | Recursion |
|---|-------|-----------|----------|----------|-----------|
| L0 | Toolchain / Environment | ✅ | ⚠ | ⚠ | — |
| L1 | Formatting / Lint | ✅ | ✅ | ✅ | ✅ |
| L2 | Type / Contract | ✅ | ✅ | ✅ | ⚠ |
| L3 | Unit Logic | ✅ | ✅ | ✅ | ✅ |
| L4 | Integration Boundary | ✅ | ✅ | ✅ | ✅ |
| L5 | API Contract | ✅ | ⚠ | ✅ | — |
| L6 | Database / State Truth | ✅ | ⚠ | — | — |
| L7 | Security / Supply Chain | ✅ | ✅ | ✅ | ✅ |
| L8 | Architecture Boundary | ✅ | ✅ | ✅ | ✅ |
| L9 | Runtime / Observability | ✅ | — | — | — |
| L10 | Docs / Decision Records | ✅ | ✅ | ✅ | ✅ |
| L11 | Dogfood / Evidence | ✅ | ⚠ | — | — |

**Legend:**
- ✅ Complete
- ⚠ Partial (principle exists, artifact incomplete or practice not yet established)
- — Not started

## 5. Layer-by-Layer Current State

### L0 — Toolchain / Environment

**Principle:** All developers, CI, and IDE must share identical toolchain entry points.

**Current state:**
- `uv` manages Python dependencies; `pnpm` manages JS/TS
- `package.json` scripts provide canonical commands
- `pyproject.toml` declares `requires-python = ">=3.11"`
- **No toolchain version fingerprint script exists**
- **pip version was not controlled** — CVE-2026-3219 discovered 2026-04-28

**Gap:** `scripts/check_toolchain.sh` needed — verify python, uv, pnpm, pip, ruff, basedpyright versions.

---

### L1 — Formatting / Lint

**Principle:** Code style and common errors must never enter human attention.

**Current state:**
- `ruff format --check` enforces formatting (CI + ci-quality-gates.sh Gate 3)
- `ruff check` with `E9` (syntax) + `F` (Pyflakes) rules (CI + Gate 2)
- `compileall` checks Python syntax across all modules (CI only)
- `import-linter` checks import cycles (CI, advisory)
- `vulture` checks dead code (CI, advisory)

**Complete.** No gaps.

---

### L2 — Type / Contract

**Principle:** Structural errors must be caught before runtime.

**Current state:**
- `basedpyright` with `typeCheckingMode = "basic"` — **CI hard gate** (ci-quality-gates.sh Gate 1/7)
- `mypy governance/` — CI advisory (`continue-on-error: true`)
- Pydantic models provide runtime validation

**Complete.** Type checking is already a blocking gate, exceeding the original plan.

**Recursion note:** `typeCheckingMode = "basic"` is not `strict`. Future tightening
to `strict` on core directories must follow CandidateRule → Policy path.

---

### L3 — Unit Logic

**Principle:** Each module's behavior must be verifiable in isolation.

**Current state:**
- 117 unit test files under `tests/unit/`
- Coverage: capabilities, db, execution, finance, finance_outcome, governance, journal, knowledge, services
- CI: `backend-unit` and `backend-unit-pg` jobs

**Complete.** No gaps.

---

### L4 — Integration Boundary

**Principle:** Modules must work together, not just individually.

**Current state:**
- 26 integration test files under `tests/integration/`
- 6 core integration files run in CI and PG regression
- Covers: API product surfaces, semantic outputs, health monitoring, scheduler persistence, workflow run lineage

**Complete.** No gaps.

---

### L5 — API Contract

**Principle:** The API surface must never change silently.

**Current state:**
- `tests/contracts/openapi.snapshot.json` (4,354 lines)
- 3 contract test files
- CI `api-contract` job: regenerate snapshot → `git diff --exit-code` → run contract tests
- **Path/schema count sanity check does not exist**

**Gap:** `scripts/check_openapi_snapshot.py` needed — distinguish "real API change"
from "generator drift" by checking path count, schema count, and critical path existence.

---

### L6 — Database / State Truth

**Principle:** SQLAlchemy ORM is the single source of truth. DuckDB is analytics/staging/test ONLY.

**Current state:**
- `docs/architecture/state-truth-boundary.md` documents the boundary (192 lines)
- `scripts/check_schema_drift.sh` detects ORM ↔ DB schema mismatch (Alembic autogenerate)
- 15 ORM models registered in `state/db/bootstrap.py`
- **No automated checker verifies DuckDB is not used as domain truth source**
- **No automated checker verifies absence of manual ALTER TABLE**

**Gap:** `scripts/check_state_truth.py` needed — static analysis of DuckDB write paths
in domain/governance/capabilities code, ORM registration completeness check.

---

### L7 — Security / Supply Chain

**Principle:** Known vulnerabilities, dangerous code, and dependency pollution must never enter main.

**Current state:**
- `gitleaks` — secret scanning (dedicated CI job `secret-scan`)
- `bandit` — static security analysis (`pnpm scan:security`)
- `pip-audit` — dependency vulnerability audit (security.yml)
- `pip upgrade >=26.1` — pip self-vulnerability patching (security.yml, added 2026-04-28)

**Complete.** No critical gaps. GitHub Dependency Review Action and OpenSSF Scorecard
can be added later but are lower priority for the current team size.

---

### L8 — Architecture Boundary

**Principle:** Core must not be polluted by Pack, Adapter, or Runtime concerns.

**Current state:**
- `scripts/check_architecture.py` — regex-based forbidden pattern checker
- `tests/architecture/test_adr006_boundary.py` — ADR-006 boundary tests
- `tests/architecture/test_no_broker_in_core.py` — broker/trade/order zero-tolerance test
- CI `backend-static` job runs `check_architecture.py`
- ci-quality-gates.sh Gate 4: architecture tests

**Rules enforced:**
```
Forbidden in Core:
  - pack tool_refs / policy imports
  - stop_loss, max_loss_usdt, position_size_usdt, is_chasing, is_revenge_trade fields
  - place_order, execute_trade calls
  - broker/trade/exchange pack imports

Whitelist (ADR-006 type-only / metadata):
  - governance/policy_source.py
  - state/db/schema.py
  - execution/catalog.py
  - capabilities/domain/finance_outcome.py
  - capabilities/domain/finance_decisions.py
  - execution/adapters/finance.py
```

**Complete.** This layer is the strongest example of Recursive Governance Externalization
in the codebase — the whitelist has grown through real feedback loops.

---

### L9 — Runtime / Observability

**Principle:** System behavior after deployment must be observable and auditable.

**Current state:**
- `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp` in dependencies
- `sentry-sdk[fastapi]` in dependencies
- `governance/audit/` — full audit subsystem (auditor, builders, contracts, models, ORM, repository, service)
- **No runtime receipt integrity checker**
- **No audit event count validator**
- OpenTelemetry export configuration not verified

**Gap:** `scripts/check_runtime_receipts.py` needed — but lower priority.
Infrastructure dependencies are in place; the checker can follow after Phase 1.

---

### L10 — Docs / Decision Records

**Principle:** Design intent must stay synchronized with code.

**Current state:**
- 6 ADRs (001–006) covering repo structure, knowledge vs state, language choice, governance layer, tool boundary, pack policy binding
- 45+ architecture documents
- Product docs, runbooks, development guides
- **No automated doc checker** (link validity, naming consistency, ADR-required-on-change)

**Complete.** Doc checker is a future enhancement, not a current gap.

---

### L11 — Dogfood / Evidence

**Principle:** The system must be correct in real usage, not only in tests.

**Current state:**
- `scripts/h9_dogfood_runs.py` (1,011 lines) — full H-9B dogfood runner
- `scripts/h9c_verification.py` — verification script
- `scripts/h9f_31_dogfood.py` — additional dogfood run
- `docs/runtime/h9-evidence-report-v2.txt` — evidence report
- **No automated evidence validator**
- **No checker for: run count = summary count, verdict enum legality, error consistency**

**Gap:** `scripts/check_dogfood_evidence.py` needed — validate evidence report integrity.

---

## 6. Gap Summary (Priority-Ordered)

| Priority | Layer | Artifact Needed | Risk of Not Having It |
|----------|-------|-----------------|----------------------|
| P0 | L0 | `scripts/check_toolchain.sh` | CI/IDE version drift → silent failures |
| P0 | L6 | `scripts/check_state_truth.py` | DuckDB pollution → data corruption |
| P1 | L11 | `scripts/check_dogfood_evidence.py` | Dogfood runs but nobody validates |
| P2 | L5 | `scripts/check_openapi_snapshot.py` | Generator drift vs. real API change confusion |
| P3 | L9 | `scripts/check_runtime_receipts.py` | Audit integrity unverified |

## 7. CandidateRule → Policy Upgrade Rules

To prevent governance system sclerosis, new blocking gates must earn their status:

**Rule 1 — Three Real Interceptions:**
A new checker runs as advisory (CandidateRule) for at least 2 weeks.
It must find 3 or more real problems before being considered for blocking (Policy) upgrade.
"Real problem" = an issue that would have caused a bug, data corruption, or incorrect
behavior if not caught.

**Rule 2 — Bypass Documentation:**
Every blocking gate must have documented bypass conditions:
- When can it be bypassed?
- How to bypass it?
- Who approves the bypass?
- When must it be restored?

**Rule 3 — No Single-Incident Policy:**
A single CI failure does not automatically create a new blocking gate.
The pattern must repeat before the gate is hardened.

## 8. Phase 1 Execution Plan

All Phase 1 artifacts start as **CandidateRule (advisory, not blocking).**
They live in `verify:release`, not `verify:full` or `verify:fast`.

### Wave RG-0: This Document ✅

### Wave RG-1: L0 — Toolchain Fingerprint

`scripts/check_toolchain.sh` — verify toolchain version consistency.

### Wave RG-2: L6 — State Truth Checker

`scripts/check_state_truth.py` — static analysis for DuckDB write paths
in domain/governance/capabilities code, ORM registration completeness.

### Wave RG-3: L11 — Dogfood Evidence Checker

`scripts/check_dogfood_evidence.py` — validate evidence report integrity.

### Wave RG-4: L5 — OpenAPI Snapshot Sanity

`scripts/check_openapi_snapshot.py` — path count, schema count, critical path checks.

### Wave RG-5: Unified Entry Point

Add `verify:state-truth`, `verify:dogfood`, `verify:openapi` to `package.json`.
New checkers go in `verify:release` initially.

## 9. The Recursive Governance Loop

This document itself is a **Receipt** in the recursive governance loop:

```
Principle:  Codebase must be governed like Ordivon governs decisions
    ↓
Artifact:   This baseline document + the 12-layer matrix
    ↓
Practice:   Every future PR is an Intake; every CI gate is Governance;
            every test log is a Receipt; every incident is an Outcome;
            every postmortem is a Review; every fixed test is a Lesson;
            every proposed gate is a CandidateRule; every blocking gate is a Policy
    ↓
Recursion:  This document is updated when the matrix changes
```

When a new layer completes its Principle → Artifact → Practice → Recursion cycle,
update Section 4 of this document. When a CandidateRule is promoted to Policy,
update Section 5 and the relevant CI configuration.
