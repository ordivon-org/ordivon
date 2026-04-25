# AegisOS Layer & Module Inventory

> **Date**: 2026-04-24
> **Purpose**: A factual mapping of what code exists where, completely stripped of aspirational architecture definitions. If a directory only has a README, it is marked as `STUB`.

## 1. Interface Layer (Apps & Scripts)
*   **`apps/api/`**: `IMPLEMENTED` - Main FastAPI application. Routes are functional but some contain heavy business logic (e.g., `reviews.py`).
*   **`apps/console/`**: `IMPLEMENTED` - Next.js frontend. Pages render and read from APIs, though some UI data is mocked.
*   **`scripts/`**: `IMPLEMENTED` - Developer utilities (DB migrations, MVP seeding).

## 2. API Facade Layer (Capabilities)
*   **`capabilities/domain/`**: `IMPLEMENTED` - Facades for stable objects (`recommendations.py`).
*   **`capabilities/workflow/`**: `IMPLEMENTED` - Facades for multi-step logic (`analyze.py`, `reviews.py`).
*   **`capabilities/view/`**: `IMPLEMENTED` - View aggregates (`dashboard.py`, `reports.py`, `audits.py`).
*   **`capabilities/diagnostic/`**: `IMPLEMENTED` - System health/eval reads (`validation.py`, `evals.py`).
*   **`capabilities/*.py` (Top Level)**: `RE-EXPORT` - Thin wrappers exposing the sub-directories.

## 3. Orchestration Layer
*   **`orchestrator/runtime/`**: `IMPLEMENTED` - `engine.py` (PFIOSOrchestrator) handles atomic workflow execution.
*   **`orchestrator/context/`**: `IMPLEMENTED` - `context_builder.py` handles injection, but has finance-hardcoded defaults.
*   **`orchestrator/workflows/`**: `IMPLEMENTED` - Contains exactly one workflow: `analyze.py`.
*   **`orchestrator/dispatch/`**: `STUB` - Empty, placeholder for future dynamic routing.

## 4. Execution & Adapters
*   **`execution/`**: `IMPLEMENTED` - `catalog.py` registers allowed system side-effects.
*   **`intelligence/runtime/`**: `IMPLEMENTED` - `hermes_client.py` handles external LLM interactions.
*   **`intelligence/evaluators/`**: `STUB` - No automatic quality checks exist.

## 5. Governance & Audit Layer
*   **`governance/risk_engine/`**: `IMPLEMENTED` - Validates constraints (e.g. forbidden symbols).
*   **`governance/audit/`**: `IMPLEMENTED` - `auditor.py` handles dual-write logging (JSONL + DB).
*   **`governance/approval.py`**: `IMPLEMENTED` - Human-in-the-loop gate logic.

## 6. Domain Layer (The Business Truth)
### Fully Implemented
*   `domains/strategy/`
*   `domains/journal/`
*   `domains/decision_intake/`
*   `domains/candidate_rules/`
*   `domains/ai_actions/`
*   `domains/knowledge_feedback/`
*   `domains/execution_records/`

### Stubs (Empty Placeholder Directories)
*   `domains/portfolio/`
*   `domains/market/`
*   `domains/risk/`
*   `domains/trading/`
*   `domains/userprefs/`
*   `domains/reporting/`

## 7. Knowledge Layer (Advisory Memory)
*   **`knowledge/retrieval.py`**: `IMPLEMENTED` - Exact-match SQL retrieval logic.
*   **`knowledge/memory/`**: `STUB` - No memory summarization pipelines.
*   **`knowledge/indexes/`**: `STUB` - No vector or semantic search indexes.
*   **`knowledge/retrieval/` (Directory)**: `STUB` - Empty placeholder.

## 8. State Layer (Persistence & DB)
*   **`state/db/`**: `MIXED` - `bootstrap.py` (SQLAlchemy) handles active ORM truth. `schema.py` (DuckDB) contains heavily legacy, unused tables.
*   **`state/usage/`**: `IMPLEMENTED` - Tracks system adoption and validation metrics.
*   **`state/repositories/`**: `STUB`
*   **`state/schemas/`**: `STUB`
*   **`state/services/`**: `STUB`
*   **`state/snapshots/`**: `STUB`
*   **`state/trace/`**: `STUB` - (Note: Trace query resolution exists, but it lives in the API route, not here).
