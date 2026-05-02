# Ordivon System Classification Audit — OSS-1

Status: **current** | Date: 2026-05-02 | Phase: OSS-1
Tags: `oss-1`, `classification`, `architecture`, `audit`
Authority: `supporting_evidence` | AI Read Priority: 2

## L0-L10 Asset Map

### L0 — Constitution / Work Grammar

| Asset | Type | Status |
|-------|------|--------|
| docs/architecture/ordivon-current-architecture.md | architecture | CANONICAL |
| docs/architecture/ordivon-system-definition.md | architecture | CANONICAL |
| docs/architecture/ordivon-work-grammar.md | architecture | current |
| docs/architecture/ordivon-platform-map.md | architecture | current |
| docs/runbooks/ordivon-agent-operating-doctrine.md | runbook | current |
| docs/architecture/ordivon-moat-and-product-identity.md | architecture | current |

### L1 — Core Control Platform

| Asset | Type | Files | Tests |
|-------|------|-------|-------|
| governance/risk_engine | Python | 18 .py | 302 gov tests |
| governance/approval | Python | approval.py, orm, repository | ✓ |
| governance/decision | Python | decision.py | ✓ |
| governance/feedback | Python | feedback.py | ✓ |
| governance/policy_source | Python | policy_source.py | ✓ |
| governance/audit | Python | 7 .py | ✓ |

### L2 — Domain State / Truth Layer

| Asset | Type | Modules |
|-------|------|---------|
| domains/ (89 .py) | Python | 15+ domain modules |
| state/ (16 .py) | Python | State/truth layer |
| domains/decision_intake | Intake | models, repository, service |
| domains/execution_records | Receipt | models, repository |
| domains/finance_outcome | Outcome | models, capture |
| domains/journal | Review/Lesson | models, repository |
| domains/candidate_rules | Learning | models, extraction, service |
| domains/policies | Policy | models, state_machine, evidence_gate |
| domains/ai_actions | Actions | models, repository, service |
| domains/workflow_runs | Workflow | orchestration records |
| domains/intelligence_runs | Intelligence | model runtime records |
| domains/knowledge_feedback | Knowledge | feedback/lesson records |
| domains/dashboard | Dashboard | aggregation service |
| domains/strategy | Strategy | recommendations, outcomes |
| domains/research | Research | research models |

### L3 — Pack Platform

| Pack | Files | Purpose |
|------|-------|---------|
| packs/coding/ | 4 .py | 5-gate coding governance policy |
| packs/finance/ | 9 .py | Trading discipline, context, decision intake |

### L4 — Capability / API Facade

| Asset | Files | Purpose |
|-------|-------|---------|
| capabilities/ | 29 .py | Capability declarations, API bridge |
| apps/api/ | 40 .py | FastAPI backend |

### L5 — Adapter Platform

| Adapter | Files | Type |
|---------|-------|------|
| adapters/finance/ | 3 .py | AlpacaObservationProvider (read-only), paper_execution, health |
| adapters/runtimes/ | 3 .py | Hermes runtime adapter |

### L6 — Evidence Platform

| Asset | Files | Purpose |
|-------|-------|---------|
| execution/ | 8 .py | Execution record implementation |
| docs/runtime/ | ~90 .md | Phase closure evidence, receipts, ledgers |
| docs/governance/verification-debt-ledger.jsonl | JSONL | Debt tracking |

### L7 — Verification Platform

| Asset | Files | Purpose |
|-------|-------|---------|
| scripts/ | 49 .py | Checkers, detectors, validators |
| tests/ | ~700 files | Test suite |
| evals/ | eval corpus | 24 cases, 3 packs |

### L8 — Learning Platform

| Asset | Files | Purpose |
|-------|-------|---------|
| domains/journal/ | Python | Review, Lesson, Issue models |
| knowledge/ | 8 .py | FeedbackPacket, CandidateRule extraction |
| domains/candidate_rules/ | Python | Draft extraction, policy proposal bridge |

### L9 — Policy Platform

| Asset | Files | Purpose |
|-------|-------|---------|
| domains/policies/ | Python | PolicyRecord, state machine, evidence gate |
| domains/candidate_rules/ | Python | CandidateRule lifecycle |
| docs/governance/ | Docs | Risk ladder, gate matrix |

**Status**: CandidateRules exist (3 advisory from Phase 7P).
Policy activation is NO-GO. Promotion requires 4 criteria.

### L10 — Product Wedges / External Surfaces

| Asset | Files | Purpose |
|-------|-------|---------|
| src/ordivon_verify/ | Python package | Ordivon Verify CLI |
| apps/web/ | TypeScript/React | Governance UI |
| examples/hap/ | JSON fixtures | HAP protocol examples |
| examples/ordivon-verify/ | Fixtures | Verify usage examples |

**Status**: No public release. No package published. No license activated.

## Governance Plane Cross-Reference

| Plane | Primary Layers | Key Artifacts | Status |
|-------|---------------|--------------|--------|
| Truth Governance | L0, L1, L2 | DG, registry, wiki, AI onboarding | DG-1 CLOSED |
| Action Governance | L3, L4, L5, L6, L7, L8 | OGAP, HAP, ADP, GOV-X, detector | ADP-3 CLOSED |
| Exposure Governance | L10 | PV, Ordivon Verify, public wedge | Gated |
