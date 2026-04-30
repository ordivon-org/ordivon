# State Truth Boundary

Status: **DOCUMENTED**  
Date: 2026-04-26  
Tags: `h2`, `state`, `truth-boundary`, `sqlalchemy`, `duckdb`, `orm`, `p4-prep`

## Purpose

Define the authoritative boundary between SQLAlchemy ORM (domain truth) and
DuckDB (analytics / legacy pipeline). This boundary is a **hard invariant**
for P4 and all future development.

---

## Active Truth Source

**SQLAlchemy ORM is the single source of truth** for all domain entities.
Every write that affects governance, workflow state, audit history, or
business decisions MUST go through a SQLAlchemy repository.

The canonical schema initialization path is `state/db/bootstrap.py`:

```python
# state/db/bootstrap.py — the ONLY schema authority
from state.db.base import Base

Base.metadata.create_all(bind=engine)
```

---

## SQLAlchemy-Owned Domain Truth

These ORM models are registered in `state/db/bootstrap.py` and managed
through repositories in `domains/*/repository.py`. They are the exclusive
truth source for their respective domains:

| ORM Class | Table | Domain | Location |
|-----------|-------|--------|----------|
| `AnalysisORM` | `analysis` | Research | `domains/research/orm.py` |
| `RecommendationORM` | `recommendations` | Strategy | `domains/strategy/orm.py` |
| `ReviewORM` | `reviews` | Journal | `domains/journal/orm.py` |
| `LessonORM` | `lessons` | Journal | `domains/journal/orm.py` |
| `OutcomeSnapshotORM` | `outcome_snapshots` | Strategy | `domains/strategy/orm.py` |
| `ExecutionRequestORM` | `execution_requests` | Execution | `domains/execution_records/orm.py` |
| `ExecutionReceiptORM` | `execution_receipts` | Execution | `domains/execution_records/orm.py` |
| `ExecutionProgressRecordORM` | `execution_progress_records` | Execution | `domains/execution_records/orm.py` |
| `AuditEventORM` | `audit_events` | Governance | `governance/audit/orm.py` |
| `IntelligenceRunORM` | `intelligence_runs` | Intelligence | `domains/intelligence_runs/orm.py` |
| `AgentActionORM` | `agent_actions` | AI Actions | `domains/ai_actions/orm.py` |
| `DecisionIntakeORM` | `decision_intakes` | Decision | `domains/decision_intake/orm.py` |
| `CandidateRuleORM` | `candidate_rules` | Governance | `domains/candidate_rules/orm.py` |
| `WorkflowRunORM` | `workflow_runs` | Workflow | `domains/workflow_runs/orm.py` |
| `FeedbackRecordORM` | `feedback_records` | Knowledge | `domains/knowledge_feedback/` |
| `KnowledgeFeedbackPacketORM` | `knowledge_feedback_packets` | Knowledge | `domains/knowledge_feedback/` |

All repositories (`*Repository` classes) operate exclusively on these ORM
models. No domain write bypasses the repository layer.

---

## DuckDB Scope

DuckDB is a secondary engine, NOT a truth source. Its current authorized
uses:

### Allowed DuckDB Usage

1. **Analytics queries** — market data aggregation, time-series analysis,
   statistical computation (post-PostgreSQL migration, optional).
2. **Market data snapshots** — OHLCV, features, signals (historical pre-PFIOS
   data that has not been migrated).
3. **Quality / E2E test databases** — `quality-*.duckdb` files used by CI
   and local testing (see `package.json` seed scripts).
4. **Legacy pipeline data** — tables in `state/db/schema.py` marked LEGACY,
   retained for backward compatibility with historical `.duckdb` files.
5. **Non-authoritative reports** — read-only queries for dashboards that do
   not make governance decisions.

### DuckDB MUST NOT Be Used As Truth Source For

| Domain | Why |
|--------|-----|
| Governance decision | Decisions flow through RiskEngine → AuditEventORM |
| Recommendation lifecycle | Managed by RecommendationRepository (SQLAlchemy) |
| Review lifecycle | Managed by ReviewRepository (SQLAlchemy) |
| Execution receipt | Managed by ExecutionRecordRepository (SQLAlchemy) |
| Audit event | Managed by AuditEventRepository (SQLAlchemy) |
| Candidate rule | Managed by CandidateRuleRepository (SQLAlchemy) |
| Decision intake | Managed by DecisionIntakeRepository (SQLAlchemy) |
| Intelligence run | Managed by IntelligenceRunRepository (SQLAlchemy) |
| Agent action | Managed by AgentActionRepository (SQLAlchemy) |
| Workflow run | Managed by WorkflowRunRepository (SQLAlchemy) |

**Any code that writes governance/domain truth directly to DuckDB is a
P4-blocker and must be rejected in review.**

---

## Legacy DuckDB Tables

`state/db/schema.py` defines DuckDB-native tables inherited from the
pre-PFIOS monolithic trading system. These tables are:

- **All marked LEGACY** — no active Python read/write code.
- **Retained for backward compatibility** with existing `.duckdb` files.
- **Not authoritative** — the SQLAlchemy ORM tables are the truth.

### Legacy Table Mapping

| DuckDB Legacy Table | Current SQLAlchemy Equivalent |
|---------------------|-------------------------------|
| `executions` | `ExecutionReceiptORM` |
| `risk_audits` | `AuditEventORM` |
| `recommendations` (legacy) | `RecommendationORM` |
| `performance_reviews` | `ReviewORM` |
| `policies` (legacy) | `GovernancePolicySource` |
| `approvals` | `ApprovalRecordORM` |
| `usage_logs` | `UsageSnapshotORM` |
| `issue_triage` | `IssueORM` |

---

## Prohibited Usage

The following patterns are **forbidden** and will be rejected in code review:

1. Writing to DuckDB tables from domain logic or repositories.
2. Reading governance/audit state from DuckDB instead of SQLAlchemy.
3. Using DuckDB as a fallback when PostgreSQL/SQLAlchemy is unavailable
   (fail closed, not open).
4. Adding new DuckDB tables in `state/db/schema.py` for domain truth.
5. Bypassing SQLAlchemy repositories to write directly to DuckDB.

---

## P4 Implications

P4 (finance control loop vertical slice) will introduce real market data
and trading discipline. When P4 begins:

- **Market data ingestion** may use DuckDB as a staging area, but the
  governance-significant pipeline (analysis → recommendation → review →
  execution receipt) MUST remain SQLAlchemy-only.
- **Analytics dashboards** may query DuckDB for performance metrics, but
  must cross-reference SQLAlchemy truth for audit trail.
- **No new DuckDB tables** may be created for domain objects — extend
  the ORM instead.

---

## Validation Commands

```bash
# Verify all ORM tables exist in bootstrap
uv run python -c "
from state.db.bootstrap import *
print('All ORM models imported successfully')
"

# Verify schema.py does not contain active write code
rg "INSERT|UPDATE|DELETE" state/db/schema.py
# Expected: no output (schema.py only creates tables, never writes data)

# Run unit tests (all use SQLAlchemy, not DuckDB-native)
uv run pytest -q tests/unit -p no:cacheprovider

# Run integration tests
uv run pytest -q tests/integration -p no:cacheprovider

# Confirm DuckDB references in test code are for quality/e2e, not domain truth
rg "duckdb:///./data" tests -l
# Expected: only test databases (quality-*.duckdb), no domain truth writes
```

---

## Open Questions

1. **DuckDB removal timeline**: When can the LEGACY tables in
   `state/db/schema.py` be removed? Depends on whether historical `.duckdb`
   files are still needed for audit/reference.

2. **Market data migration**: Does P4 require migrating OHLCV/features data
   from DuckDB to PostgreSQL, or will DuckDB remain the market data engine?

3. **Dual-engine queries**: Should cross-engine analytics (SQLAlchemy truth
   JOIN DuckDB market data) be supported, or should the boundary remain
   strictly separate?

4. **`ensure_pipeline_schema` retention**: Is this entrypoint still called
   in production, or is it only for development/CI? If the latter, it can
   be moved to a dev-only path.
