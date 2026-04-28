# Ordivon Stage Summit — Phase 4 Close

Status: **PUBLISHED** (Phase 4C)
Date: 2026-04-29
Phase: 4C
Tags: `stage-summit`, `closure`, `architecture`, `platform`, `maturity`, `roadmap`, `canonical`

## 1. Executive Summary

Ordivon has completed its first four phases — from a governance engine proof-of-concept
to a multi-ecosystem security platform with external actor governance. This document
serves as the Stage Summit: a company-style review of what was built, what was proven,
what remains open, and where the project should go next.

**Key numbers**:
- **4 phases** completed (Phase 1 through Phase 4C)
- **14 sub-phases** in Phase 4 alone
- **10 governance layers** in the canonical architecture
- **7 security tools** active in CI
- **3 Dependabot ecosystems** governed
- **5 Dependabot PRs merged**
- **24 eval cases** across 3 packs, 100% passing
- **7 hard gates** passing every CI run
- **1 PR held** (React compatibility)
- **0 regressions**
- **0 CandidateRules** created from incidents (root causes addressed directly)

## 2. First-Principles Definition of Ordivon

Ordivon is **not** an AI coding tool, a CI pipeline, or a GitHub bot.

> **Ordivon is a governance platform that transforms high-consequence actions —
> by AI, humans, tools, codebases, and financial decisions — into governable,
> verifiable, traceable, learnable, and constrainable objects.**

The 10-step governance loop:

```
Intent → Context → Governance → Execution → Receipt
  → Outcome → Review → Lesson → CandidateRule → Policy
```

Ordivon's job is not to make AI better at executing. Its job is to make
AI-augmented actions **governable**.

## 3. Phase Timeline

### 3.1 Phase 1–2: Core Governance Loop

**What was built**:
- `governance/risk_engine/engine.py` — the RiskEngine
- `domains/decision_intake/` — DecisionIntake, the universal intake model
- Severity protocol: reject → escalate → execute, with traceable reasons
- First Pack: `packs/finance/` (TradingDisciplinePolicy)
- Second Pack: `packs/coding/` (CodingDisciplinePolicy)
- `.severity` protocol file (ADR-006)
- Core/Pack separation: Core never imports Pack domain nouns

**What was proven**:
- The governance loop works end-to-end: intake → validate → decide → record
- Two packs validate Core Pack-agnosticism
- Reject takes priority over escalate, escalate over execute
- Architecture boundaries are enforceable (check_architecture.py)

### 3.2 Phase 3: Repo Governance Wedge + Verification Platform Incubation

**What was built**:
- `scripts/repo_governance_cli.py` — CLI adapter for governance
- `scripts/repo_governance_github_adapter.py` — GitHub Actions adapter
- Verification Platform with 10-layer architecture
- Verification baseline runner (run_verification_baseline.py)
- Eval Corpus v1 (24 cases: 10 Finance, 10 Coding, 4 Cross-Pack)
- Runtime evidence checkers (static analysis + DB-backed)
- CandidateRule → PolicyProposal lifecycle documented
- CandidateRule → Policy upgrade protocol (≥2 weeks, ≥3 real interceptions)
- Architecture boundary checker (forbidden import patterns)
- CI gates: backend-static, backend-integration, verification-fast, secret-scan

**What was proven**:
- The adapter pattern works: CLI, GitHub Actions, same governance engine
- Eval Corpus validates governance classification accuracy
- Zero false negatives on eval cases
- CandidateRule ≠ Policy Protocol prevents premature hardening
- The platformization threshold is crossed — explicit boundaries are necessary

### 3.3 Phase 4: Security / External Tooling Platform Hardening

**What was built**:
- CodeQL onboarding (4.1), triage (4.2), workflow-health hard gate (4.3)
- Dependabot strategy plan (4.4)
- Dependabot github-actions ecosystem (4.5)
- Dependabot PR observation + artifact validation (4.6–4.7)
- Dependabot uv/pnpm strategy refinement (4.8)
- Dependabot uv ecosystem (4.9)
- Dependabot npm/pnpm ecosystem (4.10)
- Bot actor governance adapter fix (4.11)
- Identity hardening — title-only signals removed (4.11 patch)
- Fresh governance materialization + low-risk merge (4.12F)
- Security platform closure review (4.13)
- Agent Operating Doctrine (4D)

**What was proven**:
- External tools produce **evidence**; Ordivon governance produces **decisions**
- Phased ecosystem rollout works (github-actions → uv → npm, zero PR floods)
- Bot actor governance requires adapter awareness (not bypass)
- Identity must come from trusted metadata, not text patterns
- Fresh evidence beats stale evidence (doctrine §3.2 validated in practice)
- 5 Dependabot PRs merged across 3 ecosystems with zero regressions

## 4. Current Architecture Map

### 4.1 Core

| Component | Status | Maturity |
|-----------|--------|----------|
| RiskEngine (validate_intake) | Active | Mature |
| DecisionIntake (universal model) | Active | Mature |
| Severity Protocol (reject/escalate/execute) | Active | Mature |
| Core/Pack separation (ADR-006) | Active | Mature |
| PolicySource (tool namespace refs) | Active | Stable |

### 4.2 Pack

| Component | Status | Maturity |
|-----------|--------|----------|
| packs/finance (TradingDisciplinePolicy) | Active | Mature |
| packs/coding (CodingDisciplinePolicy) | Active | Mature |
| Cross-pack validation | Active | Stable |

### 4.3 Product Wedge

| Component | Status | Maturity |
|-----------|--------|----------|
| Repo Governance (GitHub adapter) | Active | Stable prototype |
| Finance Decision Governance | Active | Stable prototype |
| Coding Decision Governance | Active | Stable prototype |

### 4.4 Adapter

| Component | Status | Maturity |
|-----------|--------|----------|
| repo_governance_cli.py | Active | Mature |
| repo_governance_github_adapter.py | Active | Mature |
| Bot actor awareness (Dependabot) | Active | Stable |
| Identity hardening (metadata-only) | Active | Mature |

### 4.5 Evidence

| Component | Status | Maturity |
|-----------|--------|----------|
| CI artifacts (JSON reports) | Active | Stable |
| repo-governance-report.json/.md | Active | Stable |
| CodeQL SARIF (Security tab) | Active | Stable |
| ExecutionReceipt (ORM) | Active | Stable prototype |
| DB-backed audit | Active | Stable prototype |
| Unified evidence dashboard | Not built | Deferred |

### 4.6 Verification

| Component | Status | Maturity |
|-----------|--------|----------|
| run_verification_baseline.py | Active | Mature |
| check_architecture.py | Active | Mature |
| check_runtime_evidence.py | Active | Mature |
| Eval Corpus (24 cases) | Active | Mature |
| CI gate matrix (PR Fast / PR Full / Main / Scheduled) | Active | Stable |

### 4.7 Security

| Component | Status | Maturity |
|-----------|--------|----------|
| Gitleaks | Active (Hard) | Mature |
| Bandit | Active (Advisory) | Stable |
| pip-audit | Active (Advisory) | Stable |
| CodeQL (workflow-health Hard) | Active | Mature |
| Dependabot (3 ecosystems) | Active (Advisory) | Stable |
| Finding-severity hard gate | Not designed | Deferred |
| Semgrep / Trivy / OPA | Not evaluated | Deferred |

### 4.8 Learning

| Component | Status | Maturity |
|-----------|--------|----------|
| CandidateRule model | Active | Stable |
| CandidateRule → Policy protocol | Active | Stable |
| Lesson → CandidateRule draft path | Documented | Advisory |
| Policy activation | Not started | Deferred |

### 4.9 Policy

| Component | Status | Maturity |
|-----------|--------|----------|
| CodingDisciplinePolicy (hard gates) | Active | Mature |
| TradingDisciplinePolicy (hard gates) | Active | Mature |
| PolicyProposal path | Documented | Advisory |
| Auto-generated Policy from CandidateRule | Not activated | Deferred |

## 5. What Has Been Proven

### 5.1 Core/Pack Separation

Two independent Packs (Finance + Coding) validate that the RiskEngine is
Pack-agnostic. The architecture boundary checker enforces that Core never
imports Pack domain nouns, tool refs, or policy overlays.

### 5.2 Severity Protocol

The 3-tier reject → escalate → execute protocol works deterministically
in both Packs. Eval Corpus validates 24/24 correct classifications.

### 5.3 GitHub Adapter Read-Only Path

The repo-governance-github-adapter reads PR metadata, classifies through
RiskEngine, and outputs JSON — without writing files, commenting on PRs,
or pushing commits. The read-only invariant is preserved.

### 5.4 Evidence Artifact

Every repo-governance-pr run produces a JSON artifact with decision,
reasons, side_effects (all false), and changed_files_count. The artifact
is CI-addressable and human-readable.

### 5.5 CodeQL Zero-Alert Baseline + Workflow-Health Hard Gate

CodeQL was onboarded in one workflow file, triaged to zero alerts, and
promoted to a workflow-health hard gate. Finding severity remains advisory —
requiring human triage before any blocking decision.

### 5.6 Dependabot External Actor Governance

Dependabot — an external actor that writes to the repo — was integrated
through the governance adapter, not around it. Bot PRs get synthetic
test_plans, expected dependency files are allowlisted, and forbidden
files still trigger reject.

### 5.7 Fresh Evidence Doctrine

Phase 4.11–4.12F validated that stale governance evidence must not be
treated as current. The "Update branch" → fresh CI → fresh governance →
merge pipeline proved that evidence freshness is a first-class governance
concern.

## 6. Current Platform Maturity Table

| Maturity Level | Components |
|---------------|-----------|
| **Mature** (proven, monitored, documented) | RiskEngine, DecisionIntake, Severity Protocol, Core/Pack separation, Repo Governance CLI, GitHub adapter (bot-aware), Identity hardening, Verification baseline, Architecture checker, Eval Corpus, CodeQL workflow-health gate, Gitleaks, CodingDisciplinePolicy, TradingDisciplinePolicy |
| **Stable prototype** (proven, may scale) | Repo Governance Wedge, CI gate matrix, Dependabot (3 ecosystems), CI artifacts, DB-backed audit, CandidateRule model, CandidateRule→Policy protocol |
| **Advisory** (active, non-blocking) | Bandit, pip-audit, Dependabot advisory gate, CodeQL finding severity, PolicyProposal path, Lesson→CandidateRule path |
| **Observation-only** | Dependabot PR patterns (not yet tuned), Evidence freshness in practice (one validated incident) |
| **Deferred** | Auto-merge, PR comments, Checks API, IDE/MCP/agent execution, Semgrep, Trivy, OPA, Policy activation, Finding-severity hard gate, Bun Dependabot ecosystem, Unified evidence dashboard |

## 7. Open Debts

### 7.1 Active Debts

| Debt | Severity | Owner | Notes |
|------|----------|-------|-------|
| PR #7 React compatibility | Medium | TBD | frontend-build/components fail; needs dedicated fix |
| uv.lock pre-existing diff | Low | TBD | Working tree dirty since before Phase 4.8; not from any governed change |
| Untracked workspace residues | Low | TBD | .coveragerc, .pre-commit-config.yaml, h9f_31_dogfood.py |

### 7.2 Design Debts

| Debt | Severity | Notes |
|------|----------|-------|
| Finding-severity hard gate not designed | Medium | Requires alert policy, false positive protocol, stakeholder sign-off |
| Auto-merge policy not defined | Low | Requires 3+ months of clean Dependabot history first |
| Policy Platform not activated | Medium | CandidateRule→Policy protocol exists but has never been exercised end-to-end |
| No unified evidence dashboard | Low | CI artifacts + Security tab suffice for current scale |

### 7.3 Documentation Debts

| Debt | Severity | Notes |
|------|----------|-------|
| Phase 1–3 individual docs may be stale | Low | Canonical architecture doc is current; older docs may reference outdated names |
| Hermes Model Layer Integration doc needs rewrite | Low | Pre-H-1 design doc, referenced from runtime README |

## 8. What NOT To Do Next

The following are explicitly deferred and should NOT be started without
Stage Summit re-approval:

1. **No auto-merge** — 3+ month clean history requirement not met
2. **No PR comments** — requires write tokens and proven artifact stability
3. **No Checks API** — same rationale as PR comments
4. **No IDE / MCP / agent execution** — adapter pattern not yet extended to these surfaces
5. **No Semgrep / Trivy / OPA** — no use case yet
6. **No Policy activation** — CandidateRule→Policy protocol needs real data before activation
7. **No finding-severity hard gate** — alert policy not designed
8. **No Bun Dependabot ecosystem** — bun.lock not governed
9. **No new CandidateRules from Phase 4 incidents** — root causes were addressed directly (governance adapter fix, not symptom-policy)

## 9. Recommended Next Phase Options

### Option A: Productization of Repo Governance

Turn the Repo Governance Wedge from a stable prototype into a mature product:
- Refactor the GitHub adapter to support pluggable actor profiles
- Add a governance decision dashboard
- Design the "auto-mergeable" advisory flag
- Productize the evidence artifact chain
- Write external-facing documentation

**Why**: The adapter is the most exercised component after Phase 4.
It has proven bot actor awareness. It's ready for productization.

### Option B: Second Pack / Second Domain Validation

Add a third Pack (e.g., `packs/infra/` for infrastructure decisions) to
further validate Core Pack-agnosticism:
- Define a new domain with its own policy
- Create eval cases for the new domain
- Validate that RiskEngine requires zero changes

**Why**: Two Packs validate the pattern. Three Packs would prove it.
Increases confidence in the Core/Pack separation.

### Option C: Policy Platform Design

Design the Policy activation pipeline end-to-end:
- Create a real CandidateRule from operational data
- Let it run advisory for ≥2 weeks
- If it catches ≥3 real problems, draft the PolicyProposal
- Design the Policy activation mechanism (how does a Policy become active?)

**Why**: The CandidateRule→Policy protocol is documented but never exercised.
Activating it would close the governance loop from observation to constraint.

### Option D: Agent Execution Adapter Research

Research how the adapter pattern extends to IDE/agent execution surfaces:
- What does an MCP adapter look like?
- What does an IDE agent adapter look like?
- What new risks does agent execution introduce vs. PR-based governance?

**Why**: The adapter pattern is proven for CLI and GitHub Actions.
The next frontier is agent-in-the-loop execution. Research-first,
not implementation-first.

### Option E: UI / Dashboard Consolidation

Build a minimal governance dashboard:
- Show active PR governance decisions
- Display evidence artifacts
- Surface Dependabot PR status
- Provide a human reviewer interface for escalation decisions

**Why**: Current governance is CLI/API-only. A dashboard would make
governance decisions visible to non-engineers and enable Stage Summit
reviewers to see platform health at a glance.

## 10. Recommended Primary Next Move

**Recommendation: Option C — Policy Platform Design**

**Rationale**:

1. **Closes the governance loop**: Phases 1–4 built the intake → governance →
   evidence pipeline. The missing piece is the feedback loop: observation →
   CandidateRule → Policy → active constraint. Closing this loop turns
   Ordivon from a classification platform into a **learning governance system**.

2. **Highest leverage**: Policy activation affects every other option.
   Productization (A) is stronger with active policies. Second Pack (B)
   benefits from policy infrastructure. Agent adapters (D) need policy
   to govern execution. Dashboard (E) is most useful when policies are
   active and generating decisions.

3. **Phase 4 was about external tooling**: The external tools (CodeQL,
   Dependabot) are now active and governed. The natural next step is to
   turn inward and activate the learning loop that makes governance
   self-improving.

4. **Low risk, high learning**: Policy Platform design is a design-and-document
   phase. No production code changes are required until the design is reviewed.
   If the design reveals issues, the cost of revision is minimal.

**Secondary recommendation**: Run Option E (Dashboard) as a parallel
lightweight track. A minimal dashboard would make Policy Platform decisions
visible and auditable, accelerating the Stage Summit review cycle.

## 11. Related Documents

| Document | Relationship |
|----------|-------------|
| `docs/architecture/ordivon-current-architecture.md` | Canonical architecture reference |
| `docs/architecture/ordivon-platform-map.md` | Platform boundaries |
| `docs/architecture/security-platform-baseline.md` | Security gate classification (closed) |
| `docs/runtime/security-external-tooling-closure.md` | Phase 4 closure review |
| `docs/runtime/dependabot-strategy.md` | Dependabot adoption strategy |
| `docs/runbooks/ordivon-agent-operating-doctrine.md` | Agent operating rules |
| `docs/adr/ADR-008-tooling-adoption-strategy.md` | Build/buy decisions |
| `docs/product/repo-governance-pack.md` | Repo Governance product strategy |
