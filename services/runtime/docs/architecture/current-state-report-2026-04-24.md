# AegisOS Architecture Current State Report

> **Date**: 2026-04-24

This document serves as the baseline snapshot of the AegisOS (PFIOS) repository as we enter Phase 4 (Personal Control Loop). It follows a rigorous engineering audit designed to strip away placeholder assumptions and document the *actual* running code.

## 1. The Core Baseline

The system is currently a robust **Step 4–6 embryo**. The primary execution chain (`Analysis → Governance → Recommendation → Audit → Reporting`) is functional and backed by integration tests. 

However, many capabilities are heavily hardcoded toward this single path.

### 1.1 Verified Strengths

*   **Orchestrator Pattern**: The `PFIOSOrchestrator` successfully handles step-based execution, atomicity, and rollback boundaries.
*   **Decoupled Intelligence**: The `Hermes` adapter pattern correctly isolates LLM calls from core business logic, supporting timeouts and retries.
*   **Domain Models**: Stable domains (`strategy`, `journal`, `decision_intake`, `knowledge_feedback`) successfully decouple business rules from persistence routing.
*   **Governance Engine**: `RiskEngine` enforces basic policies and the `HumanApprovalGate` functions as designed.

### 1.2 Core Limitations

*   Only **one** workflow exists (`analyze.py`). All other loops (like Review closure) are currently manual API triggers.
*   The system lacks dynamic workflow dispatch; the `orchestrator/dispatch` directory is empty.
*   `infra/scheduler` exists but is completely disconnected from the Orchestrator.

## 2. Directory & Module Truth

Many directories created during Step 1 skeleton initialization are either empty or contain only placeholders.

### 2.1 Fully Implemented / Stable Domains
- `research`
- `strategy`
- `journal`
- `intelligence_runs`
- `workflow_runs`
- `execution_records`
- `decision_intake`
- `candidate_rules`
- `ai_actions`
- `knowledge_feedback`

### 2.2 Stub / Placeholder Directories (No logic)
*These directories contain a README indicating they are placeholders.*
- `domains/portfolio/`
- `domains/market/`
- `domains/risk/`
- `domains/trading/`
- `domains/userprefs/`
- `domains/reporting/`
- `state/repositories/`
- `state/schemas/`
- `state/services/`
- `state/snapshots/`
- `state/trace/` (Logic lives in API route instead)
- `knowledge/memory/`
- `knowledge/indexes/`
- `knowledge/retrieval/` (Logic lives in a single `retrieval.py` file)
- `intelligence/evaluators/`
- `orchestrator/dispatch/`

### 2.3 The Capability Layer
The `capabilities/` directory contains actual facade implementations in `workflow/` and `domain/`. The top-level files (e.g., `capabilities/analyze.py`) are deliberately thin re-exports. *This is not tech debt.*

## 3. Persistent Tech Debt & Gaps

### 3.1 The DuckDB / SQLAlchemy Split (P0)
**Status**: `state/db/schema.py` contains ~27 tables in DuckDB DDL inherited from an old monolithic codebase. *None of these tables are read or written by the current Python domain layer.*
**Mitigation**: DDL statements have been tagged `# LEGACY`. True domain state lives exclusively via SQLAlchemy ORM models. This dual-schema split will remain until we migrate fully or delete the old DuckDB files.

### 3.2 Audit Event Gaps (P2)
**Status**: The system correctly emitted `analysis_completed` and `review_submitted`, but was missing key state transitions.
**Mitigation**: A `recommendation_adopted` audit event was added to capture user intent. `outcome_detected` remains a TODO until independent outcome capture is built.

### 3.3 Semantic Search Gap (P3)
**Status**: Knowledge retrieval (`knowledge/retrieval.py`) relies entirely on exact-match SQL (symbol, recommendation_id). There is no vector similarity search for cross-referencing past mistakes.
**Mitigation**: Deferred to Phase 5.

### 3.4 Missing Feedback Loop Logic (P2)
**Status**: `advisory_hints` are extracted from past lessons and passed to the `GovernanceDecision`, but the Governance engine completely ignores them when deciding to Execute/Escalate/Reject.
**Mitigation**: Phase 4 will expose these hints in the UI. Phase 5 will implement logic to force escalation based on past negative outcomes.

## 4. Frontend Truth Status

The Next.js frontend has not been fully audited for data authenticity. While `DashboardService` loads real metrics, placeholders (like `total_balance_estimate: None`) persist. 
**Rule for Phase 4**: All new frontend components built for the control loop must bind to live API data. No mocking permitted.
