# Verification Platform

Status: **DOCUMENTED**
Date: 2026-04-28
Phase: 3.4
Tags: `verification`, `testing`, `gates`, `evidence`, `baseline`

## 1. Purpose

Define Ordivon's Verification Platform — the collection of gates, tools, and
failure handling that validates all other platforms maintain their invariants.

The Verification Platform is NOT "the test suite." It is the unified layer that
organizes testing, evidence checking, architecture boundary enforcement, eval
corpus validation, and DB-backed audits into a single baseline.

## 2. Why Testing Is Too Narrow

"Testing" (unit/integration/contract) only covers code correctness. It does
not cover:

- Architecture boundary violations (ADR-006)
- Evidence chain integrity (Receipt → Outcome → Review → Lesson)
- Governance classification regression (eval corpus)
- DB schema + data integrity (DB-backed audit)
- Security/supply-chain risk (bandit, pip-audit)
- Cross-platform invariant preservation

The Verification Platform covers ALL of these under a single classification
system of Hard / Escalation / Advisory gates.

## 3. Verification Layers

### Layer 0: Static Analysis

| Check | Tool | Scope |
|-------|------|-------|
| Type checking | pyright/basedpyright | All .py files |
| Lint | ruff check | All .py files |
| Format | ruff format --check | All .py files |
| Dead code | vulture | All .py files |

### Layer 1: Unit Tests

| Check | Tool | Scope |
|-------|------|-------|
| Domain logic | pytest tests/unit | ~586 tests |
| Governance gates | pytest tests/unit/governance | ADR-006, RiskEngine, Pack policies |
| CLI adapter | pytest tests/unit/test_repo_governance_cli.py | 20 tests |

### Layer 2: Integration Tests

| Check | Tool | Scope |
|-------|------|-------|
| API endpoints | pytest tests/integration | HTTP request/response chains |
| DB operations | pytest tests/integration | ORM persistence round-trips |
| Service wiring | pytest tests/integration | End-to-end service chains |

### Layer 3: Contract Tests

| Check | Tool | Scope |
|-------|------|-------|
| API response shape | pytest tests/contracts | OpenAPI conformance |
| Payload validation | pytest tests/contracts | Field existence, types, enums |

### Layer 4: Architecture Boundaries

| Check | Tool | Scope |
|-------|------|-------|
| Core imports Pack types? | `scripts/check_architecture.py` | governance/, state/, domains/, capabilities/, execution/, shared/ |
| Pack imports governance? | Architecture test | packs/finance/, packs/coding/ |
| Shell/MCP/IDE in governance? | Architecture test | governance/ |

### Layer 5: Runtime Evidence (Static)

| Check | Tool | Scope |
|-------|------|-------|
| ExecutionReceipt.request_id | `scripts/check_runtime_evidence.py` | ORM model inspection |
| Finance outcome receipt linkage | Same | ORM + model validation |
| Plan receipt constraints | Same | Spec doc + execution catalog |
| Review outcome_ref pairing | Same | ORM inspection |
| CandidateRule source_refs | Same | Model file text analysis |
| No Policy promotion path | Same | Service method inspection |
| Checker self-read-only | Same | Own source code scan |

### Layer 6: DB-Backed Audit

| Check | Tool | Scope |
|-------|------|-------|
| Receipt request_id non-empty | `scripts/audit_runtime_evidence_db.py` | Live DB query |
| Plan receipt broker_execution=false | Same | Live DB query |
| Outcome → receipt linkage | Same | Live DB cross-reference |
| Review → outcome linkage | Same | Live DB cross-reference |
| Lesson source_refs | Same | Live DB + JSON parsing |
| CandidateRule draft linkage | Same | Live DB + JSON parsing |
| No Policy promotion | Same | Live DB query |
| AuditEvent coverage | Same | Live DB query |
| Audit is read-only | Same | Object count before/after |

### Layer 7: Eval Corpus

| Check | Tool | Scope |
|-------|------|-------|
| Finance classification | `evals/run_evals.py` | 10 cases |
| Coding classification | Same | 10 cases |
| Cross-pack independence | Same | 4 cases |

### Layer 8: Security / Supply-Chain

| Check | Tool | Scope |
|-------|------|-------|
| Code security | bandit | All .py files |
| Dependency audit | pip-audit | All dependencies |
| Import boundaries | import-linter | Cross-module imports |

### Layer 9: PG Full Regression

| Check | Tool | Scope |
|-------|------|-------|
| All tests on PostgreSQL | `PFIOS_DB_URL=postgresql://... pytest tests/` | Full test suite |

### Layer 10: Adapter Smoke

| Check | Tool | Scope |
|-------|------|-------|
| Repo CLI smoke case | `scripts/repo_governance_cli.py` | One valid + one reject case |

## 4. Gate Classification

### Hard Gates (fail = block)

Hard gates must pass. A failure means a real invariant is broken.

| Gate | Layer | Rationale |
|------|-------|-----------|
| Architecture boundaries clean | L4 | Core/Pack boundary violation = governance compromise |
| Runtime evidence integrity | L5 | Missing receipt/outcome linkage = untraceable decisions |
| Eval corpus 100% | L7 | Governance classification regression = silent misclassification |
| Repo CLI smoke | L10 | Adapter produces wrong decision = user-facing failure |

### Escalation Gates (fail = warn, require review)

Escalation gates indicate potential issues. Failures should be reviewed but
may not block CI depending on project policy.

| Gate | Layer | Rationale |
|------|-------|-----------|
| DB-backed audit | L6 | Pre-existing data issues or transient conditions |
| Type checking | L0 | May have pre-existing debt from other waves |

### Advisory Gates (fail = record, do not block)

Advisory gates provide information. Failures are recorded but never block.

| Gate | Layer | Rationale |
|------|-------|-----------|
| Dead code | L0 | No runtime impact, cleanup debt |
| Security scan | L8 | May have false positives or accepted risk |

## 5. Existing Tools → Layer Mapping

| Tool / Script | Layer | Gate Class | Exit Code |
|---------------|-------|------------|-----------|
| `scripts/check_architecture.py` | L4 | Hard | 1 on violation |
| `scripts/check_runtime_evidence.py` | L5 | Hard | 1 on violation |
| `scripts/audit_runtime_evidence_db.py` | L6 | Escalation | 1 on violation |
| `evals/run_evals.py` | L7 | Hard | 1 on any failure |
| `scripts/repo_governance_cli.py` | L10 | Hard | 2/3 on escalate/reject |
| `ruff check` | L0 | Hard | 1 on error |
| `ruff format --check` | L0 | Hard | 1 on unformatted |
| `pytest tests/unit` | L1 | Hard | 1 on failure |
| `pytest tests/integration` | L2 | Hard | 1 on failure |
| `pytest tests/contracts` | L3 | Hard | 1 on failure |
| PG full regression | L9 | Hard | 1 on failure |
| bandit | L8 | Advisory | Non-zero on finding |
| pip-audit | L8 | Advisory | Non-zero on vulnerability |
| vulture | L0 | Advisory | Non-zero on dead code |

## 6. Failure Handling

### Hard Gate Failure

```
Hard Gate fails
  → CI blocks
  → Developer fixes issue
  → Re-runs verification baseline
  → All hard gates pass → CI proceeds
```

### Repeated Hard Gate Failure

```
Same Hard Gate fails ≥ 3 times across different intakes
  → Review created with outcome_ref = gate failure
  → Lesson extracted with lesson_type = "rule_candidate"
  → CandidateRule(draft) generated
  → (Future) stable rule → PolicyProposal(draft) → Policy(active)
```

### Pattern: "The checker found a real gap"

When a verification gate catches a genuine invariant violation:
1. Fix the code that broke the invariant
2. Do NOT weaken the gate to make the failure disappear
3. If the gate itself has a bug, fix the gate — not the code being checked

## 7. Current Known Issue

**DB-backed audit — pre-existing data violations (Phase 3.4):**

After fixing the import issue in `scripts/audit_runtime_evidence_db.py`
(the `knowledge` module path + `__init__.py` eager import), the audit
runs successfully but reports 20 violations:

- 10 CandidateRule drafts with empty `lesson_ids` and `source_refs`
  (pre-existing test data from Wave B draft extraction testing)

This is an **Escalation Gate** failure — not a Hard Gate. These are
pre-existing data conditions from earlier waves. The audit correctly
detects them. Resolution is deferred to a future data cleanup wave.

**Status after Phase 3.4**: Known, documented, not blocking.

## 8. Run the Verification Baseline

```bash
uv run python scripts/run_verification_baseline.py
```

Output:
```
=== Ordivon Verification Baseline ===
[Hard Gate]  Architecture boundaries ........... ✅ PASS
[Hard Gate]  Runtime evidence integrity ........ ✅ PASS
[Hard Gate]  Eval corpus (24 cases) ............ ✅ PASS (24/24)
[Hard Gate]  Repo CLI smoke .................... ✅ PASS
[Hard Gate]  Unit tests (586) .................. ✅ PASS
[Hard Gate]  Integration tests (143) ........... ✅ PASS
[Hard Gate]  Contract tests (8) ................ ✅ PASS
[Escalation] DB-backed audit ................... ❌ 20 violations
[Advisory]   Security scan ..................... (not run)

=== SUMMARY ===
Hard gates:    7/7 PASS
Escalation:    0/1 PASS
Advisory:      0/0 run
OVERALL:       READY (all hard gates pass)
```

## 9. Platform Invariants

The Verification Platform enforces:

1. **Read-only**: zero database writes, zero file modifications
2. **Comprehensive**: covers static→unit→integration→contract→architecture→evidence→eval→security→PG
3. **Classified**: every gate is Hard / Escalation / Advisory
4. **Self-verifying**: the verification runner itself has tests
5. **Fail-learn**: repeated failures feed into the Learning Platform
