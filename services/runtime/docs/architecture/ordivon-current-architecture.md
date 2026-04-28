# Ordivon Current Architecture

Status: **CANONICAL**
Date: 2026-04-28
Phase: 3C
Tags: `architecture`, `rebase`, `platform`, `canonical`, `index`

## 1. Purpose

This document is the **canonical architecture reference** for Ordivon as of
Phase 3 completion. It replaces ad-hoc platform documentation scattered across
Phase-specific docs with a single, definitive layer model.

This is NOT a new feature document. It is an architecture rebase: consolidating
what was built, clarifying what each layer means, and defining what Phase 4
should and should not do.

## 2. What Ordivon Is

Ordivon is **not** an AI coding tool, a CI pipeline, or a GitHub bot.

Ordivon is:

> **A governance platform that transforms high-consequence actions — by AI,
> humans, tools, codebases, and financial decisions — into governable,
> verifiable, traceable, learnable, and constrainable objects.**

First-principles definition:

```text
Any high-consequence action must pass through:

  1. Intent      — what is being proposed?
  2. Context     — what information supports it?
  3. Governance  — is it allowed?
  4. Execution   — did it actually happen?
  5. Receipt     — is there evidence?
  6. Outcome     — what was the result?
  7. Review      — did the result match expectations?
  8. Lesson      — what did we learn?
  9. CandidateRule — can experience become a draft rule?
 10. Policy      — should the rule become an active constraint?
```

Ordivon's job is **not** to make AI better at executing. Its job is to make
AI-augmented actions **governable**.

## 3. Current 10-Layer Architecture

```text
L0  Constitution / Work Grammar
L1  Core Control Platform
L2  Domain State / Truth Layer
L3  Pack Platform
L4  Capability / API Facade
L5  Adapter Platform
L6  Evidence Platform
L7  Verification Platform
L8  Learning Platform
L9  Policy Platform
L10 Product Wedges / External Surfaces
```

---

### L0 — Constitution / Work Grammar

**What**: The system's immutable rules. What Ordivon allows, forbids, considers
"done," and demands as evidence.

**Key assets**:
- `policies/constitution.md`
- `docs/architecture/ordivon-work-grammar.md`
- `docs/runbooks/prompt-patterns.md`
- `docs/architecture/ordivon-platform-map.md`

**Invariants**:
- Intelligence is not sovereignty
- Core owns truth/governance/receipt/review
- CandidateRule is not Policy
- Adapter output is evidence, not truth
- Completion requires receipt
- Experience cannot directly become policy

**Maturity**: Stable. Risk of document fragmentation as the system grows;
needs a future system-map or architecture-index.

---

### L1 — Core Control Platform

**What**: The governance engine. Any action enters the governance loop through
Core, which classifies intent and enforces gates.

**Key objects**:
- `DecisionIntake`
- `GovernanceDecision`
- `ExecutionRequest`
- `ExecutionReceipt`
- `Outcome`
- `Review`
- `Lesson`
- `CandidateRule`
- `PolicyProposal`

**Control loop**:
```text
Intake → Governance → Receipt → Outcome → Review → Lesson → CandidateRule → Human Review → PolicyProposal
```

**Invariants**:
- Core does NOT know Finance details (stop_loss, position_size, chasing)
- Core does NOT know Coding details (task_description, file_paths, test_plan)
- Core does NOT know GitHub details (PR, labels, changed files)
- Core does NOT know CodeQL, Bandit, Gitleaks
- Core consumes severity protocol only (`reason.severity`, `reason.message`)

**Maturity**: Stable. Ordivon's most valuable asset. Must resist platform-concept
pull — Core must never import `github`, `codeql`, or pack-specific types.

---

### L2 — Domain State / Truth Layer

**What**: Where system truth is persisted. ORM-mapped entities that form the
authoritative record of governance events.

**Key domains**:
- `domains/decision_intake/` — intake records
- `domains/execution_records/` — receipts and requests
- `domains/journal/` — reviews, lessons
- `domains/candidate_rules/` — draft rules, review paths
- `domains/finance_outcome/` — finance-specific outcomes
- `domains/strategy/` — recommendations
- `domains/knowledge_feedback/` — knowledge packets

**Fact chains**:
```text
DecisionIntake → Governance decision
ExecutionReceipt → Outcome
Outcome → Review
Review → Lesson
Lesson → CandidateRule(draft)
CandidateRule(accepted) → PolicyProposal(draft)
```

**Invariants**:
- SQLAlchemy ORM is the single truth source
- DuckDB is analytics/staging/test ONLY
- Receipts are immutable append-only
- Evidence chains are traceable via source_refs

**Open debts**:
- `FinanceManualOutcome` is pack-specific but lives in `domains/`
- `OutcomeSnapshot` and `FinanceManualOutcome` form a dual-outcome system needing documentation
- `PolicyProposal` is a plain dataclass (no ORM) — correct for now, but needs
  ORM when Policy Platform activates

**Maturity**: Stable, with known classification gaps. Needs `domain-truth-map.md`.

---

### L3 — Pack Platform

**What**: Domain-specific semantics. Each Pack defines its own reason types
with `.severity` protocol. Core knows nothing about pack internals.

**Current Packs**:

| Pack | Domain | Status |
|------|--------|--------|
| `packs/finance/` | Trading discipline: stop_loss, chasing, revenge_trade, risk budget | Stable |
| `packs/coding/` | Code change discipline: task_description, file_paths, test_plan, forbidden paths | Stable |

**Repo Governance identity clarification**:

> **Repo Governance is NOT yet a separate Pack.** It is a **product wedge**
> that reuses Coding Pack policy through CLI and GitHub adapters. It may
> become a dedicated Pack only if repo-specific semantics emerge that
> exceed Coding Pack — e.g., branch protection risk, PR review ownership,
> merge policy, CI status semantics.

**Invariants**:
- Pack never imports `governance/risk_engine` internals
- Pack never imports broker/order/trade/execution
- Pack defines its own reason types with `.severity` and `.message`
- Pack must NOT execute code, call shell, modify files

**Maturity**: Stable. Finance and Coding are proven. No third Pack needed
until domain semantics demand it.

---

### L4 — Capability / API Facade

**What**: External entry points into Core and Pack capabilities. Currently
HTTP API + capability wrappers.

**Key assets**:
- `capabilities/domain/` — finance decisions, planning, outcomes
- `capabilities/workflow/` — reviews, completions
- `apps/api/` — FastAPI application

**Invariants**:
- Capabilities call governance, never bypass it
- Routes call `RiskEngine.validate_intake()`, never re-implement risk checks

**Maturity**: Adequate. Ordivon's center of gravity has shifted from HTTP API
to CLI/CI composability. The API is not the single entry point — it's one of
several adapters.

---

### L5 — Adapter Platform

**What**: Connects external tools (CLI, GitHub, future IDE/MCP) to Core governance.
Adapters produce evidence, not truth.

**Current adapters**:

| Adapter | Type | Status |
|---------|------|--------|
| `scripts/repo_governance_cli.py` | CLI | Stable |
| `scripts/repo_governance_github_adapter.py` | GitHub Actions | Stable |
| GitHub workflow `repo-governance-pr` | CI job | Stable |
| `scripts/render_repo_governance_report.py` | Evidence renderer | Stable |

**Adapter invariants**:
- Adapter output is evidence, not truth
- Adapter cannot write Core truth directly
- Read-only first
- Write requires explicit governance approval
- Every adapter action produces a receipt (artifact or event)

**Future adapters (deferred)**:
- GitHub Checks API (Phase 4.x, after proven correctness)
- PR comment (Phase 4.x, after read-only pattern proven)
- IDE adapter (Phase 5.x, after CLI + GitHub proven)
- MCP adapter (Phase 5.x)
- Claude Code / Codex adapter (Phase 5.x)

**Maturity**: Stable. Phase 3 proved the adapter pattern works. Must NOT
continue deepening Repo Governance adapter — each new adapter expands the
permission surface.

---

### L6 — Evidence Platform

**What**: Immutable records proving what was done, what was decided, and what
was NOT done. Side-effect guarantees are part of evidence.

**Current evidence artifacts**:

| Artifact | Type | Persistence |
|----------|------|-------------|
| `ExecutionReceipt` | ORM record | DB |
| `AuditEvent` | ORM record | DB |
| `source_refs` | JSON field | DB (within records) |
| `repo-governance-report.json` | CI artifact | GitHub (30 days) |
| `repo-governance-report.md` | CI artifact | GitHub (30 days) |
| `side_effects` fields | JSON field | Contract-enforced |
| `evidence_note` | JSON/MD field | Contract-enforced |
| Workflow logs | Text | GitHub (90 days) |

**Key distinctions**:
- GitHub artifact evidence ≠ ExecutionReceipt
- JSON report ≠ Core truth
- Workflow log ≠ audit event
- Artifact is ephemeral evidence; Receipt is persistent evidence

**Maturity**: Strong. Artifact + contract + evidence_note pattern is mature.
Risk is future conflation of artifact evidence with ORM-backed truth.

---

### L7 — Verification Platform

**What**: Validates that Ordivon maintains its invariants. The platform that
proves the system has not drifted.

**Verification layers**:

| Layer | Check | Tool |
|-------|-------|------|
| L0 | Format/lint | Ruff |
| L1 | Unit tests | pytest |
| L2 | Integration tests | pytest |
| L3 | Contract tests | pytest + JSON schema |
| L4 | Architecture boundaries | `check_architecture.py` |
| L5 | Runtime evidence | `check_runtime_evidence.py` |
| L6 | DB-backed audit | `audit_runtime_evidence_db.py` |
| L7 | Eval corpus | `evals/run_evals.py` |
| L8 | Security | Gitleaks, Bandit, pip-audit |
| L9 | PG full regression | pytest on PostgreSQL |
| L10 | Repo CLI smoke | CLI adapter tests |

**Gate classification**:
- **Hard Gate**: failure blocks (ruff, unit tests, eval corpus, architecture checker, contracts, Gitleaks)
- **Escalation Gate**: failure triggers human review (DB audit, CodeQL wip)
- **Advisory Gate**: failure recorded, never blocks (Bandit, pip-audit, dead code)

**Maturity**: The strongest and fastest-growing platform. Already in CI with
`verification-fast` job. Most deserving of continued investment in Phase 4.

---

### L8 — Learning Platform

**What**: Extracts lessons from completed reviews and generates CandidateRule
drafts — without auto-promoting to Policy.

**Current path**:
```text
Review → Lesson → CandidateRule(draft) → Human Review → accepted_candidate or rejected → PolicyProposal(draft)
```

**Invariants**:
- Review is not an automatic rule
- Lesson is not Policy
- CandidateRule is not Policy
- PolicyProposal is not active Policy
- Human approval required for policy promotion
- Draft extraction is idempotent (same lesson never produces duplicate rules)

**Maturity**: Mechanism built, but lacks real-world data. No production
incidents, PR failures, or eval regressions have yet fed into this loop.
Phase 4 should route more evidence through Review before considering
Policy activation.

---

### L9 — Policy Platform

**What**: The path from accepted CandidateRule to active Policy. The highest-risk
platform — because Policy changes future system behavior.

**Current state**:
- `PolicyProposal` dataclass (plain, no ORM)
- `CandidateRuleReviewService` (human review path)
- Constitution change control

**Not yet implemented**:
- `PolicyProposalORM`
- Policy activation
- Policy versioning
- Policy rollback
- Policy owner
- Policy impact audit
- Policy deployment receipt

**Activation preconditions**:
```text
1. Sufficient CandidateRule samples from real usage
2. Human approval mechanism proven
3. Eval gate for proposed policies
4. Rollback capability
5. Versioning
6. Named owner
7. Activation receipt generated
```

**Maturity**: Draft only. Current restraint is correct. Policy Platform must
not be activated prematurely.

---

### L10 — Product Wedges / External Surfaces

**What**: How real users encounter Ordivon. Product wedges prove the platform
works in real scenarios without over-committing to any single use case.

**Current wedge**: Repo Governance

| Component | Status |
|-----------|--------|
| CLI governance entrypoint | ✅ |
| GitHub read-only adapter | ✅ |
| CI workflow integration (`repo-governance-pr`) | ✅ |
| JSON output contract | ✅ |
| Evidence artifact (JSON + Markdown) | ✅ |
| Pull request event validation | ✅ |
| Failure semantics documentation | ✅ |

**What Repo Governance proved**:
- Ordivon can classify real GitHub PRs
- Read-only governance produces value
- Adapter + Evidence + Verification platforms collaborate
- PR events can be governed without auto-writing back

**Repo Governance is NOT**:
- A dedicated Pack (it reuses Coding Pack policy)
- A PR management bot
- An auto-merge system
- A replacement for CI

**Future potential wedges**:
- Finance Governance
- Coding Agent Governance
- Security Governance
- Research Governance
- Planning Governance

## 4. Current Maturity Table

| Layer | Platform | Maturity | Key Risk |
|-------|----------|----------|----------|
| L0 | Constitution | Stable | Document fragmentation |
| L1 | Core Control | Stable | Platform concept pull |
| L2 | Domain Truth | Stable | Classification gaps |
| L3 | Pack Platform | Stable | Repo Gov pack identity |
| L4 | Capability | Adequate | Not current priority |
| L5 | Adapter | Stable | Over-expansion risk |
| L6 | Evidence | Strong | Artifact vs receipt conflation |
| L7 | Verification | Strong | Gate complexity |
| L8 | Learning | Early | Insufficient real-world data |
| L9 | Policy | Draft | Premature activation risk |
| L10 | Product | Adequate | Wedge over-deepening |

## 5. Phase 3 Definition

Phase 3 was **not** just "Repo Governance Pack." It was:

> **Repo Governance Product Wedge + Verification Platform Incubation**

What Phase 3 built:

- Governance CLI (`phase-3-3`)
- Platform map + verification baseline (`phase-3-4`)
- CI gate plan (`phase-3-5`)
- PR Fast Gate in CI (`phase-3-6`)
- GitHub read-only adapter (`phase-3-7`)
- GitHub workflow + JSON contract (`phase-3-8`)
- Evidence artifact (`phase-3-9`)
- Remote CI validation + failure semantics (`phase-3-10`)
- CI format baseline fix (`phase-3-10f`)
- PR event validation (`phase-3-11`)
- Tooling landscape + build/buy ADR (`phase-3-12`)
- Security platform + CodeQL plan (`phase-3-13`)

What Phase 3 proved:

- Adapter pattern works in real CI
- Evidence-first governance is feasible
- Verification Platform can gate PRs
- Read-only GitHub integration is production-ready
- JSON contract + artifact pattern is generalizable

## 6. Phase 4 Definition

Phase 4 should be:

> **Security / Verification / External Tooling Platform Hardening**

What Phase 4 should do:

| Priority | Action | Phase |
|----------|--------|-------|
| 1 | CodeQL dry-run workflow | 4.1 |
| 2 | Dependabot config with governance gate | 4.2 |
| 3 | Verification baseline → hard CI gate | 4.3 |
| 4 | OpenSSF Scorecard (advisory) | 4.4 |
| 5 | Route security findings → Review → Lesson → CandidateRule | 4.5 |
| 6 | Architecture register (naming, ownership) | 4.6 |
| 7 | Domain truth map | 4.7 |
| 8 | Workspace residue cleanup | 4.8 |

What Phase 4 should NOT do:

- ❌ Activate Policy Platform
- ❌ Add PR comments or Checks API
- ❌ Add IDE / MCP / agent execution adapters
- ❌ Create `packs/repo_governance/`
- ❌ Deepen Repo Governance beyond current wedge
- ❌ Add Semgrep, Trivy, OPA, Conftest yet
- ❌ Auto-fix security findings
- ❌ Auto-merge PRs based on governance decisions

## 7. Open Architecture Debts

These are known issues that do not block Phase 4 entry but should be resolved
during Phase 4:

| Debt | Severity | Recommended Resolution |
|------|----------|----------------------|
| Architecture semantic drift | High | Phase 4.6 Architecture Register |
| Domain truth classification map | Medium | Phase 4.7 Domain Truth Map |
| Evidence artifact vs ExecutionReceipt conflation risk | Medium | Document in Evidence Platform docs |
| Repo Governance pack identity ambiguity | Medium | This document clarifies it |
| Policy Platform persistence | Low | Defer to Phase 5+ |
| Workspace residues (uv.lock, .coveragerc, h9f_31_dogfood.py) | Low | Phase 4.8 |
| Dual outcome system (OutcomeSnapshot + FinanceManualOutcome) | Low | Document in Domain Truth Map |
| Constitution document fragmentation | Low | Phase 4 Architecture Register |

## 8. Entry Conditions for Phase 4

Before entering Phase 4.1 (CodeQL), the following must be true:

- [x] Architecture rebase complete (this document)
- [x] Phase 3 sealed with all tags
- [x] CI green baseline: `backend-static`, `verification-fast`, `secret-scan` all success
- [x] `repo-governance-pr` validated on pull_request event
- [x] Build/buy strategy documented (ADR-008)
- [x] Security Platform baseline documented
- [x] CodeQL permissions model defined (`security-events: write`, NOT PR write)

## 9. Recommended Next Phases

| Phase | Action | Type |
|-------|--------|------|
| 3C (this) | Architecture Rebase | Documentation |
| 4.1 | CodeQL dry-run workflow | Security tooling |
| 4.2 | Dependabot with governance gate | Security tooling |
| 4.3 | Verification baseline hard CI gate | Verification hardening |
| 4.4 | OpenSSF Scorecard advisory | Security visibility |
| 4.6 | Architecture Register | Documentation cleanup |
| 4.8 | Workspace residue cleanup | Maintenance |

## 10. Key Principles (Reaffirmed)

1. **Classify before execute** — governance runs before action, not after
2. **Core never imports Pack types** — severity protocol is the contract
3. **Adapter output is evidence, not truth** — read-only by default
4. **CandidateRule is not Policy** — human review required for promotion
5. **Completion requires receipt** — no claim without evidence
6. **Build where semantics are unique** — adopt standard tools for standard problems
7. **One tool per problem** — avoid overlapping capabilities
8. **Do not over-deepen the first wedge** — Repo Governance proved the pattern; now abstract
