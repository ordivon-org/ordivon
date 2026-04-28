# Ordivon Platform Map

Status: **DOCUMENTED**
Date: 2026-04-28
Phase: 3.4
Tags: `platform`, `architecture`, `boundary`, `verification`

## 1. Purpose

Define Ordivon's platform boundaries as the project crosses the platformization
threshold. Prevent directory explosion, adapter sprawl, and governance decay by
establishing clear platform identities with explicit inputs, outputs, and
non-goals.

This document is a **map**, not a directory tree. It answers "what belongs
where" and "what must not leak between platforms."

## 2. Why Platformization Now

Ordivon has crossed the platformization threshold:

- A CLI adapter exists (`scripts/repo_governance_cli.py`)
- An Eval Corpus exists (24 cases, 3 packs)
- Runtime evidence checkers exist (static + DB-backed)
- Two Packs (Finance + Coding) validate Core Pack-agnosticism
- Architecture boundary checker runs in CI
- CandidateRule → PolicyProposal path is defined

Without explicit platform identities, the next step — adding GitHub Actions,
IDE, and MCP adapters — would cause:
1. **Adapter sprawl**: each adapter reinvents governance classification
2. **Verification fragmentation**: no single runner validates all gates
3. **Platform ambiguity**: "is this Core? Pack? Adapter?" questions multiply

Platformization prevents these by making platform boundaries explicit.

## 3. Platformization Is Not Directory Explosion

Platformization does NOT mean:
- Moving files around
- Renaming directories
- Creating new package structures
- Adding abstraction layers between existing code

Platformization IS:
- Documenting what already exists
- Defining what each platform owns and rejects
- Making cross-platform contracts explicit
- Enabling independent verification per platform

The 9 platforms below describe the LOGICAL architecture. Physical file layout
changes only when multiple scenarios demand it (see §5 Platform Promotion Rule).

## 4. The 9 Platforms

### 1. Core Control Platform

**Responsibility**: The governance engine. Classifies intakes, enforces gates,
produces decisions. Never imports Pack-specific types.

**Non-goals**: Does not execute trades, read files, call APIs, or know domain types.

| Aspect | Detail |
|--------|--------|
| Inputs | DecisionIntake, pack_policy (interface) |
| Outputs | GovernanceDecision (execute/escalate/reject) |
| Key files | `governance/risk_engine/engine.py`, `governance/decision.py` |
| Invariant | Core imports zero Pack-specific types (ADR-006) |

---

### 2. Pack Platform

**Responsibility**: Domain-specific discipline policies. Each Pack provides
`validate_fields / validate_numeric / validate_limits / validate_behavioral`
methods. Packs define their own reason types with `.severity` protocol.

**Non-goals**: Does not execute trades or code. Does not call shell/MCP/IDE.

| Aspect | Detail |
|--------|--------|
| Inputs | Payload dict from DecisionIntake |
| Outputs | Reason objects with .severity (reject/escalate) |
| Key files | `packs/finance/`, `packs/coding/` |
| Invariant | Pack never imports `governance/risk_engine` internals |

---

### 3. Adapter Platform

**Responsibility**: Connect external tools (CLI, GitHub Actions, IDE, MCP) to
the Core governance pipeline. Adapters produce evidence, not truth.

**Non-goals**: Does not execute. Does not write Core truth directly. Does not bypass governance.

| Aspect | Detail |
|--------|--------|
| Inputs | CLI args, PR metadata, editor context, tool invocations |
| Outputs | JSON governance decision + side-effect guarantees |
| Key files | `scripts/repo_governance_cli.py` |
| Invariant | Adapter output is evidence — never truth |

---

### 4. Evidence Platform

**Responsibility**: Immutable records of governance events. ExecutionReceipt,
FinanceManualOutcome, AuditEvent. Append-only. Traceable from Intake to Lesson.

**Non-goals**: Does not modify historical records. Does not delete evidence.

| Aspect | Detail |
|--------|--------|
| Inputs | Governance events (intake validated, receipt created, review completed) |
| Outputs | Immutable records with source_refs chains |
| Key files | `domains/execution_records/`, `governance/audit/` |
| Invariant | Receipt = immutable append-only |

---

### 5. Verification Platform

**Responsibility**: Validate that all platforms maintain their invariants.
Static checks, unit tests, integration tests, contract tests, architecture
boundary checks, runtime evidence checks, DB-backed audits, eval corpus,
security scans, PG full regression.

**Non-goals**: Does not write data. Does not modify state. Does not execute trades or code.

| Aspect | Detail |
|--------|--------|
| Inputs | Codebase, test suite, eval corpus, database |
| Outputs | Pass/fail per gate, JSON summary, exit codes |
| Key files | `scripts/run_verification_baseline.py`, `scripts/check_architecture.py`, `scripts/check_runtime_evidence.py`, `scripts/audit_runtime_evidence_db.py`, `evals/run_evals.py` |
| Invariant | Verification is read-only — zero writes, zero side effects |

See `docs/architecture/verification-platform.md` for gate classification.

---

### 6. Learning Platform

**Responsibility**: Extract lessons from completed Reviews. Generate
CandidateRule drafts from `rule_candidate` lessons. Feed knowledge back into
governance refinement.

**Non-goals**: Does not auto-promote CandidateRules to Policy. Does not execute.

| Aspect | Detail |
|--------|--------|
| Inputs | Completed Reviews, Lesson records |
| Outputs | CandidateRule(draft), KnowledgeFeedback packets |
| Key files | `domains/candidate_rules/draft_extraction.py`, `domains/journal/` |
| Invariant | Draft only — never `accepted_candidate` without human review |

---

### 7. Policy Platform

**Responsibility**: CandidateRule → PolicyProposal → Policy activation path.
Human-reviewed rule lifecycle. Policy overlay management.

**Non-goals**: Does not auto-activate. Does not bypass the CandidateRule lifecycle.

| Aspect | Detail |
|--------|--------|
| Inputs | CandidateRule(accepted_candidate), PolicyProposal(draft) |
| Outputs | Policy overrides, active policy IDs |
| Key files | `domains/candidate_rules/review_service.py`, `domains/candidate_rules/policy_proposal.py` |
| Invariant | Policy activation requires explicit human approval |

---

### 8. Product Platform

**Responsibility**: User-facing product strategy, competitive positioning,
MVP scope, adapter roadmap. Product docs live here.

**Non-goals**: Does not contain implementation code. Does not define architecture.

| Aspect | Detail |
|--------|--------|
| Inputs | User research, competitive analysis, pain points |
| Outputs | Product strategy docs, MVP scope, success metrics |
| Key files | `docs/product/repo-governance-pack.md` |
| Invariant | Product platform describes what to build — not how |

---

### 9. Operations / Observability Platform

**Responsibility**: Monitoring, logging, telemetry, health checks. Infrastructure
wiring (Docker, Redis, PG, Alembic).

**Non-goals**: Does not contain business logic. Does not govern.

| Aspect | Detail |
|--------|--------|
| Inputs | Application metrics, service health, error traces |
| Outputs | Logs, dashboards, alerts, health endpoints |
| Key files | `infra/`, `state/db/bootstrap.py`, `scripts/check_redis.py` |
| Invariant | Observability observes — it does not decide |

---

## 5. Platform Promotion Rule

A code unit can be *promoted* to its own platform when ALL five conditions are met:

| # | Condition | Rationale |
|---|-----------|-----------|
| a | Reused by at least **two** scenarios | Proves the abstraction is not single-use |
| b | Has input/output **contract** | Consumer and producer can be tested independently |
| c | Protected by **tests/evals/checkers** | Regression safety net |
| d | Has **evidence/receipt** | Traceable from use to verification |
| e | Has **owner and non-goals** | Clear boundary prevents scope creep |

Anti-pattern: creating a platform directory "because it might be needed later."
Platforms emerge from actual use, not speculative design.

## 6. Current Maturity Table

| Platform | Status | Gates Covered | Evidence |
|----------|--------|---------------|----------|
| Core Control | **Stable** | RiskEngine, severity protocol | Eval corpus 24/24 |
| Pack | **Stable** | Finance + Coding gates | Cross-pack dogfood 20/20 |
| Adapter | **Prototype** | CLI only | 20 unit tests |
| Evidence | **Stable** | ExecutionReceipt, Outcome, AuditEvent | Runtime evidence checker |
| Verification | **Baseline** | 10 gates (this phase) | Verification baseline runner |
| Learning | **Stable** | Draft extraction, review path | 10 + 14 unit tests |
| Policy | **Draft** | PolicyProposal path (no activation) | 15 unit tests |
| Product | **Documented** | Strategy, MVP scope | Product doc |
| Operations | **Stable** | Docker, PG, Redis, monitoring | Health endpoints |

## 7. Next Platform Priorities

1. **Verification Platform** (Phase 3.4 — this phase): converge all existing
   checkers/test suites into a single baseline runner with gate classification.

2. **Repo Governance Product Platform** (Phase 3.5+): GitHub Actions adapter,
   PR metadata intake, CI annotation output.

3. **Adapter Platform CLI layer** (Phase 3.6+): structured CLI framework for
   future adapters (consistent arg parsing, JSON output schema, exit codes).

## 8. Platform Boundary Violations (Anti-Patterns)

| Violation | Why It's Bad | Detection |
|-----------|-------------|-----------|
| Adapter calls shell/MCP/IDE | Adapters classify, never execute | Tests + runtime evidence checker |
| Pack imports governance internals | Breaks ADR-006 | Architecture checker |
| Core imports Pack type (not protocol) | Breaks Pack-agnosticism | Architecture checker |
| Verification writes to DB | Verification is read-only | Self-check in verification runner |
| CandidateRule auto-promoted | Bypasses human review | DB audit check |
| Product doc contains implementation code | Confuses strategy with implementation | Manual review |

## 9. Relationship to Existing Docs

| Document | Platform |
|----------|----------|
| `docs/architecture/ordivon-work-grammar.md` | All (constitution) |
| `docs/architecture/repo-governance-pack-architecture.md` | Pack + Adapter + Product |
| `docs/product/repo-governance-pack.md` | Product |
| `docs/runtime/eval-corpus-v1-plan.md` | Verification |
| `docs/runtime/repo-governance-cli.md` | Adapter |
| `docs/architecture/verification-platform.md` | Verification |
