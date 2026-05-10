# Ordivon Macro Structure — System Architecture Overview

> **For new AI collaborators.** This is the structural map of what Ordivon IS:
> what exists, where it lives, how it's organized. Read this once to
> build a mental model of the entire governance operating system.

**Authority**: `source_of_truth`
**Status**: `current`
**Phase**: `CI-SelfCalibration`
**Owner**: `ordivon-core-maintainer`
**Freshness**: 2026-05-10
**AI Read Priority**: 0 (read first)
**Layer**: L0

---

## 1. What Ordivon Is

Ordivon is a **governance operating system for agent-native work**. It is NOT a
trading bot, AI wrapper, or generic dashboard. It is a repo-native system where
governance is executable code — testable, attestable, replayable.

```
438 registered documents · 38 governance checkers · 30 JSON schemas
10 lessons · 2 debt records · 1,437 tests · ~34.5K LOC
```

The governance system and the governed system are made of the same materials
(code, documents, CI, JSONL ledgers) and live in the same repository. This
means **the governance system can audit itself**.

---

## 2. Document Universe — 438 entries, 22 types, 6 layers

```
L0 — Constitution & Methodology (5 docs)
 ├── ordivon-methodology-core.md          ← 12 invariants, dual-gate loop, A1-A4 matrix
 ├── ordivon-companion-governance-constitution.md
 ├── philosophical-governance-layer.md
 ├── ordivon-moat-and-product-identity.md
 └── ordivon-core-pack-adapter-ontology.md

L1 — AI Onboarding (21 docs)
 ├── AGENTS.md                            ← Root entry point
 ├── current-phase-boundaries.md          ← Active/deferred/NO-GO boundaries
 ├── agent-output-contract.md             ← Required AI output shape
 ├── current-system-map.md                ← Phase status summary
 ├── ordivon-macro-structure.md           ← This document
 └── new-ai-reading-order.md, onboarding-protocol, ...

L2 — Governance Body (181 docs)
 ├── DGP 2-9:   Document lifecycle, authority, medium, metabolism, CI
 ├── LGC 0-5f:  13-phase legacy governance
 ├── RG 1-14:   Registry governance
 ├── Ledgers:   lesson-ledger (10), dependency-audit-debts (2)
 └── Maps:      current-truth-entry-map, owner-routing-rules, knowledge-map...

L3 — Runtime & Products (168 docs)
 ├── receipt:       121 phase closure receipts
 ├── product:        51 product documents
 ├── runtime:        27 operational records
 └── stage_summit:    8 phase summit compressions

L4 — Architecture & Design (62 docs)
 ├── architecture:   61 architecture specifications
 └── design_spec:    21 design documents
```

---

## 3. Checker Ecosystem — 38 governance checkers

Every checker is a self-contained directory under `checkers/<name>/` with a
`CHECKER.md` and `run.py`. They are auto-discovered by `pr-fast` and
`ordivon-verify all`.

```
Moat Layer — 7 inalienable checks
├── agentic-patterns          ← Agent behavior: CandidateRule promotion, READY overclaim
├── agent-native-evidence     ← Agent output evidence boundaries
├── architecture-boundaries   ← Core/Pack/Adapter separation
├── protected-paths           ← Sensitive path references (.env, secrets, pyproject.toml)
├── philosophy-misuse         ← Philosophical concept misuse
├── philosophical-claims      ← Unsupported philosophical overclaims
└── ownership-manifest        ← Code ownership documentation

Document Governance Layer — 6 checks
├── document-registry         ← Registry invariants (dual-checker, schema-first)
├── document-freshness        ← Staleness detection
├── current-truth             ← Truth protocol: "permanent", "forever", cross-doc drift
├── receipt-integrity         ← Receipt standard enforcement
├── dogfood-evidence          ← Self-use evidence tracking
└── runtime-evidence          ← Operational evidence integrity

Coding Governance Layer — 6 checks
├── coding-smoke, coding-fixtures, coverage-governance
├── dependabot-governance, trading-discipline, finance-boundary

PGI Layer — 4 checks
├── pgi-confidence, pgi-decision-gate
├── pgi-evidence-record, pgi-failure-predicate

Protocol Layer — 3 checks
├── ogap-payload, hap-payload, oep-governance

Operational Layer — 12+ checks
├── entropy-telemetry, entropy-gate, checker-maturity
├── owner-activation, gate-manifest, external-source-registry
├── policy-shadow, lesson-extraction, state-truth
├── verification-debt, egb3-operating-governance
```

### Key commands

```bash
ordivon-verify all                    # Full verification (CI: verify-native job)
ordivon-verify document-governance --check  # Document registry hard gate
ordivon-verify registry-index --check       # Reconciler status (1221 objects)
uv run python scripts/run_baseline.py --pr-fast  # Auto-discovered baseline
uv run python scripts/update-registry-stats.py --check  # Generated view drift
```

---

## 4. Registry Control Plane

The single source of truth for document metadata.

```
document-registry.jsonl (438 entries)
     │
     ├──▶ document-types.json          ← Valid doc_types (schema-first)
     │       ↓ loaded by
     │    scripts/check_document_registry.py  (CLI checker)
     │    checkers/document-registry/run.py   (CI checker)
     │       ↓ verified by
     │    governance-self-check (CI job)
     │
     ├──▶ update-registry-stats.py     ← Generator (K8s hack/update)
     │       ↓ writes
     │    _registry-stats.md           ← Generated view (do not edit)
     │       ↓ verified by
     │    update-registry-stats.py --check (CI)
     │
     └──▶ current-truth-protocol       ← Cross-doc consistency checker
```

**Design principle**: Schema-first. One schema, multiple consumers.
Adding a new doc_type requires editing one file (document-types.json).
Never maintain the same set in two places (L-CI-SELFCAL-002).

---

## 5. Code Architecture — ~34.5K LOC, 36 Python files

```
src/ordivon_verify/          ← Main package
├── cli.py                   ← CLI entry point
├── discovery.py             ← Auto-discovers checkers
├── report.py                ← Generates READY/BLOCKED/DEGRADED reports
├── registry.py              ← Registry import/export
├── checker_registry.py      ← Checker registration
│
├── control/ (9 files)       ← Control plane
│   └── StageManifest, ExecutionReceipt, ClosureSeal...
│
├── checks/ (5 files)        ← Check implementations
│   └── receipts, governance, evidence...
│
├── metabolic/ (4 files)     ← Document lifecycle engine
│   └── Discover, models, lifecycle registry
│
├── registry/ (5 files)      ← Registry object model
│   └── Reconciler, adapters, sources, models
│
├── scanners/ (4 files)      ← Agent-native scanners
│   └── memory_hygiene, skill_boundary, trace_evidence
│
└── schemas/ (30 JSON)       ← JSON Schema definitions
    └── registry-object, closure-receipt, stage-manifest,
        hap-*, ogap-*, pgi-*, document-*, ...
```

---

## 6. CI Gate System — 5 workflows, ~33 jobs

```
ci.yml (15 jobs)
├── ruff                  ← Format + lint (blocking)
├── pr-fast                ← Auto-discovered checker baseline (blocking)
├── governance-self-check  ← Generated views + dual-checker sync (blocking) [NEW]
├── verify-native          ← ordivon-verify all → READY (blocking)
├── product-tests          ← 737 tests (blocking)
├── governance-tests       ← 464 tests (blocking)
├── finance-tests          ← Finance tests (blocking)
├── coding-tests           ← Coding pack tests (blocking)
├── frontend               ← Next.js lint + typecheck + build + test
├── evals                  ← 24 eval cases
├── entropy-telemetry      ← Advisory metrics
├── policy-shadow          ← Advisory CandidateRule evaluation
├── coding-governance      ← Coding discipline smoke
├── manifest-check         ← Manifest consistency
└── verify-external-ladder ← External repo fixtures (READY/DEGRADED/BLOCKED)

security.yml (3 jobs)
├── pip-audit              ← Python vulnerability scan (--skip-editable)
├── pnpm audit             ← Frontend vulnerability scan
└── gitleaks               ← Secret scanning

codeql.yml, delivery.yml, nightly-regression.yml
```

---

## 7. Knowledge Assets

### Lesson Ledger (10 entries)

```
Epoch 1 — Checkerization (5):
  L-DG-CHECKERIZATION-001~005  ← Freshness, overclaim, patterns, boundaries

Epoch 2 — Self-Calibration (5):
  L-CI-SELFCAL-001  ← Hardcoded count drift → generated_view
  L-CI-SELFCAL-002  ← Dual-checker trap → schema-first
  L-CI-SELFCAL-003  ← Batch commit incoherence → atomic gates
  L-CI-SELFCAL-004  ← Methodology extraction from CI event
  L-CI-SELFCAL-005  ← CI environment parity investigation
```

### Debt Ledger (2 entries)

```
DEP-AUDIT-PIP-CVE-2026-3219    ← CVE awaiting upstream fix (weekly cron)
DEP-CI-PRODUCT-TESTS-ENV       ← CI environment investigation
```

### Methodology Core

```
docs/governance/ordivon-methodology-core.md
  §2  L0 Invariants (12)          Evidence≠Claim, READY≠Authorization...
  §3  Dual-Gate Loop              Pre-Execution + Post-Execution
  §4  State Algebra               READY/DEGRADED/BLOCKED + closure states
  §5  Disposition Matrix          A1(fix)→A2(refine)→A3(redesign)→A4(debt)
  §6  Self-Calibration            Governance audits itself
  §7  Anti-Patterns (6)           Hardcoded drift, dual-checker, silent ignore...
  §8  Receipt Standard            git diff + before/after + raw CLI + per-doc
```

---

## 8. Development Epochs

```
Epoch 1: Foundation (DGP)
  10 phases (DGP-1 → DGP-9 + DGP-E1 + DGP-S) → CLOSED
  38 checkers deployed, document governance operational

Epoch 2: Legacy Governance (LGC)
  13 phases (LGC-0 → LGC-5f + LGC-S) → CLOSED_AS_GOVERNED_LEGACY
  26 legacy dirs governed, 0 deletions, 0 behavior changes
  209 legacy terms inventoried and migrated

Epoch 3: Self-Calibration (CI-SELFCAL)
  CI BLOCKED itself → systematic A1-A4 fix
  Schema-first architecture deployed
  Doc count generator + CI verify gate (K8s hack/verify pattern)
  Methodology Core extracted from the event
  10 lessons, 2 debts, 1 cron job
  1,437 tests · ordivon-verify → READY (35/35)
```

---

## 9. Operational Reference

```bash
# Document governance
ordivon-verify document-governance --check   # CI hard gate (BLOCKED > 0 → exit 1)
ordivon-verify registry-index --check        # Reconciler status
ordivon-verify registry-index --snapshot     # Write index snapshot
ordivon-verify registry-index --diff         # Compare vs last snapshot

# Verification
ordivon-verify all                           # Full 35-check RUN
uv run python scripts/run_baseline.py --pr-fast  # Auto-discovered baseline

# Generated views
uv run python scripts/update-registry-stats.py          # Generate
uv run python scripts/update-registry-stats.py --check  # CI verify

# Testing
uv run pytest tests/unit/product -q          # 737 tests
uv run pytest tests/unit/governance -q       # 464 tests
```

---

## 10. Critical Boundaries

```
Live trading                    DEFERRED (requires Stage Gate)
Policy activation                NO-GO
CandidateRule → Policy           NO-GO without PolicyActivation
Document governance PASS         ≠ merge/release/deploy authorization
Generated view                   ≠ source_of_truth
Owner                            ≠ approver
Archive                          ≠ current truth
Alembic migrations               do-not-edit by default
26 legacy dirs                   governed, not deleted
Ordion Verify READY              ≠ authorization (READY_WITHOUT_AUTHORIZATION)
```

---

```text
READY means selected checks passed; it does not authorize execution,
does not authorize merge, does not authorize deployment, and does not
authorize release, tool use, policy activation, or external action.
```
