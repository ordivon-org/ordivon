# H-9C Dogfood Remediation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Close the three system gaps discovered by H-9B dogfood testing before P4 Closure.

**Architecture:** Three independent but sequential remediation phases. Each phase adds deterministic governance rules, no NLP/ML dependency. All changes are idempotent, testable, and reversible.

**Tech Stack:** Python 3.11+, SQLAlchemy 2.x (PostgreSQL pgvector/pgvector:pg17), Pytest

**Status after H-9B:**
- Schema drift: `outcome_ref_type` / `outcome_ref_id` in ORM but not in existing PG databases
- Escalate path: only 2 triggers (`is_revenge_trade`, `is_chasing`), no coverage for emotional state / rule exceptions / low confidence
- Thesis quality: no quality gate — "just feels right" passes governance

---

## Phase 1: H-9C1 — Schema Drift Closure

**Objective:** Ensure `reviews.outcome_ref_type` and `reviews.outcome_ref_id` columns exist in any PostgreSQL environment (fresh or existing) without manual `ALTER TABLE`.

**Current state:**
- `ReviewORM` (domains/journal/orm.py:19-20) defines `outcome_ref_type` and `outcome_ref_id` as `Mapped[str | None]`
- `init_db()` (state/db/bootstrap.py:29-30) calls `Base.metadata.create_all(bind=engine)` — this creates new tables but does NOT alter existing tables
- Test fixtures create fresh DBs with `create_all`, so tests pass
- Existing dev/prod PG databases lack these columns → `AttributeError` or silent NULL on insert

**Approach:**
Add lightweight, idempotent migration support after `create_all`. NOT Alembic — just a simple column-existence check + `ALTER TABLE ADD COLUMN IF NOT EXISTS`.

**Files to create:**
- `state/db/migrations/__init__.py` — empty
- `state/db/migrations/runner.py` — migration runner with idempotent column additions
- `tests/unit/db/test_migrations.py` — unit tests for migration idempotency

**Files to modify:**
- `state/db/bootstrap.py` — call `run_migrations()` after `create_all`

---

### Task 1.1: Create migration runner module

**Objective:** Add a `run_migrations()` function that adds missing columns idempotently.

**Files:**
- Create: `state/db/migrations/__init__.py`
- Create: `state/db/migrations/runner.py`

**Step 1: Create empty `__init__.py`**

File: `state/db/migrations/__init__.py`
```python
"""Database migration support.

Migrations are idempotent column additions that run after
Base.metadata.create_all() to handle schema drift on existing databases.
"""
```

**Step 2: Create `runner.py` with migration registry**

File: `state/db/migrations/runner.py`
```python
"""Idempotent migration runner.

Each migration is a function that receives a SQLAlchemy connection
and performs its changes only if they haven't been applied yet.
"""

from __future__ import annotations

from sqlalchemy import Connection, text

# ── Migration registry ──────────────────────────────────────────────────
# Ordered list of (migration_id, migration_fn).  Each fn is idempotent.

_MIGRATIONS: list[tuple[str, object]] = []


def migration(migration_id: str):
    """Decorator: register an idempotent migration function."""

    def decorator(fn):
        _MIGRATIONS.append((migration_id, fn))
        return fn

    return decorator


# ── H9C1-001: Add outcome_ref columns to reviews table ──────────────────


@migration("h9c1_001_add_outcome_ref_columns")
def add_outcome_ref_columns(conn: Connection) -> None:
    """Add outcome_ref_type and outcome_ref_id to reviews table.

    These columns exist in ReviewORM but may be missing from existing
    PostgreSQL databases that were created before the ORM change.
    """
    conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS outcome_ref_type VARCHAR(64)"))
    conn.execute(text("ALTER TABLE reviews ADD COLUMN IF NOT EXISTS outcome_ref_id VARCHAR(64)"))
    conn.commit()


# ── Runner ─────────────────────────────────────────────────────────────


def run_migrations(conn: Connection) -> int:
    """Execute all registered migrations in order.

    Each migration is idempotent — safe to run repeatedly.

    Returns the number of migrations executed.
    """
    count = 0
    for migration_id, fn in _MIGRATIONS:
        fn(conn)
        count += 1
    return count
```

**Verification:**
```bash
# Check syntax
cd /root/projects/financial-ai-os && python -c "from state.db.migrations.runner import run_migrations; print('import OK')"
```

**Step 3: Commit**

```bash
git add state/db/migrations/
git commit -m "feat(h9c1): add idempotent migration runner with outcome_ref columns"
```

---

### Task 1.2: Wire migration runner into init_db()

**Objective:** Call `run_migrations()` after `create_all` so columns are added on every app startup.

**Files:**
- Modify: `state/db/bootstrap.py`

**Step 1: Update bootstrap.py**

Change `init_db()` to run migrations after table creation.

File: `state/db/bootstrap.py` — replace the `init_db()` function body:

```python
from state.db.base import Base
from state.db.session import engine

# IMPORTANT:
# Import all ORM models here so SQLAlchemy metadata can discover them.
from domains.ai_actions.orm import AgentActionORM  # noqa: F401
from domains.candidate_rules.orm import CandidateRuleORM  # noqa: F401
from domains.decision_intake.orm import DecisionIntakeORM  # noqa: F401
from domains.execution_records.orm import ExecutionReceiptORM  # noqa: F401
from domains.execution_records.orm import ExecutionProgressRecordORM  # noqa: F401
from domains.execution_records.orm import ExecutionRequestORM  # noqa: F401
from domains.finance_outcome.orm import FinanceManualOutcomeORM  # noqa: F401
from domains.intelligence_runs.orm import IntelligenceRunORM  # noqa: F401
from domains.research.orm import AnalysisORM  # noqa: F401
from domains.workflow_runs.orm import WorkflowRunORM  # noqa: F401
from domains.journal.issue_orm import IssueORM  # noqa: F401
from domains.journal.lesson_orm import LessonORM  # noqa: F401
from domains.journal.orm import ReviewORM  # noqa: F401
from domains.knowledge_feedback.feedback_record_orm import FeedbackRecordORM  # noqa: F401
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM  # noqa: F401
from domains.strategy.orm import RecommendationORM  # noqa: F401
from domains.strategy.outcome_orm import OutcomeSnapshotORM  # noqa: F401
from governance.approval_orm import ApprovalRecordORM  # noqa: F401
from governance.audit.orm import AuditEventORM  # noqa: F401
from infra.scheduler.orm import ScheduledTriggerORM  # noqa: F401
from state.usage.orm import UsageSnapshotORM  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    # Run idempotent migrations for schema drift on existing databases.
    # Each migration checks IF NOT EXISTS before adding columns.
    from state.db.migrations.runner import run_migrations

    with engine.connect() as conn:
        run_migrations(conn)
```

**Step 2: Run existing tests to verify no regression**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/db/ -v 2>&1 | tail -20
cd /root/projects/financial-ai-os && uv run pytest tests/integration/test_h8_review_closure.py -v 2>&1 | tail -20
```

Expected: all existing tests pass (migrations are idempotent, don't interfere with fresh DBs).

**Step 3: Commit**

```bash
git add state/db/bootstrap.py
git commit -m "feat(h9c1): wire idempotent migrations into init_db startup"
```

---

### Task 1.3: Write unit tests for migration idempotency

**Objective:** Verify that `run_migrations()` is safe to call multiple times (idempotent) and that it adds the expected columns.

**Files:**
- Create: `tests/unit/db/test_migrations.py`

**Step 1: Write tests**

File: `tests/unit/db/test_migrations.py`

```python
"""H-9C1: Migration runner idempotency tests.

Uses a fresh in-memory SQLite DB to verify migrations are safe to run
repeatedly and correctly add missing columns.
"""

import pytest
from sqlalchemy import Connection, create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class _TestBase(DeclarativeBase):
    pass


class _TestTable(_TestBase):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="pending")


@pytest.fixture
def fresh_db():
    """Create an in-memory SQLite DB with the base table but without outcome_ref columns."""
    engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(bind=engine)
    return engine


def test_migration_adds_outcome_ref_columns(fresh_db):
    """run_migrations adds outcome_ref columns when they're missing."""
    from state.db.migrations.runner import run_migrations

    with fresh_db.connect() as conn:
        run_migrations(conn)

    inspector = inspect(fresh_db)
    columns = {col["name"] for col in inspector.get_columns("reviews")}
    assert "outcome_ref_type" in columns
    assert "outcome_ref_id" in columns


def test_migration_is_idempotent(fresh_db):
    """Running migrations twice does not error."""
    from state.db.migrations.runner import run_migrations

    with fresh_db.connect() as conn:
        run_migrations(conn)  # first run
        run_migrations(conn)  # second run — should be no-op

    inspector = inspect(fresh_db)
    columns = {col["name"] for col in inspector.get_columns("reviews")}
    assert "outcome_ref_type" in columns
    assert "outcome_ref_id" in columns


def test_run_migrations_returns_count():
    """run_migrations returns the number of registered migrations."""
    from state.db.migrations.runner import run_migrations, _MIGRATIONS

    engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        count = run_migrations(conn)

    assert count == len(_MIGRATIONS)
    assert count >= 1
```

**Step 2: Run tests**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/db/test_migrations.py -v
```

Expected: 3 passed.

**Step 3: Commit**

```bash
git add tests/unit/db/test_migrations.py
git commit -m "test(h9c1): add migration idempotency and column existence tests"
```

---

### Task 1.4: Verify fresh DB scenario

**Objective:** Confirm that `init_db()` works correctly on a fresh PostgreSQL database (via test fixtures).

**Step 1: Run the H-8 integration tests which use fresh PG fixtures**

```bash
cd /root/projects/financial-ai-os && \
  PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test \
  uv run pytest tests/integration/test_h8_review_closure.py -v
```

Expected: all tests pass, outcome_ref columns are auto-created.

**Step 2: Run the H-7 manual outcome tests (also use outcome_ref)**

```bash
cd /root/projects/financial-ai-os && \
  PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test \
  uv run pytest tests/integration/test_h7_manual_outcome_api.py -v
```

Expected: all tests pass.

**Verification complete — no commit needed (verification only).**

---

## Phase 2: H-9C2 — Escalation Path Coverage

**Objective:** Expand Gate 4 in `RiskEngine.validate_intake()` to cover emotional state, rule exceptions, and low confidence as escalate triggers. Current state: only 2 triggers (`is_revenge_trade`, `is_chasing`).

**Design:**
```
hard missing / hard limit violation → reject
behavioral risk / ambiguous input → escalate
clean valid input → execute
```

New escalate triggers (deterministic, not NLP):
- `emotional_state` matches stress/fear/anger/fomo keywords → escalate
- `rule_exceptions` list not empty → escalate
- `confidence` < 0.3 (too low, but not missing) → escalate

**Files to create:**
- `tests/unit/governance/test_h9c2_escalate_coverage.py`

**Files to modify:**
- `governance/risk_engine/engine.py` — add Gate 4 escalation rules

---

### Task 2.1: Write failing tests for missing escalate triggers

**Objective:** Write tests that currently FAIL because the escalation rules don't exist yet.

**Files:**
- Create: `tests/unit/governance/test_h9c2_escalate_coverage.py`

**Step 1: Write all escalation tests**

File: `tests/unit/governance/test_h9c2_escalate_coverage.py`

```python
"""H-9C2: Escalation path coverage — unit tests.

Verifies that emotional state, rule exceptions, and low confidence
trigger escalate (not reject, not execute).
"""

import pytest

from domains.decision_intake.models import DecisionIntake
from governance.risk_engine.engine import RiskEngine


def _make_intake(*, status="validated", payload=None) -> DecisionIntake:
    """Create a valid DecisionIntake for testing."""
    p = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "Valid thesis with sufficient detail for analysis.",
        "entry_condition": "Breakout confirmed.",
        "invalidation_condition": "Range reclaim.",
        "stop_loss": "Below support",
        "target": "Local high",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.7,
        "rule_exceptions": [],
        "notes": "Controlled",
    }
    if payload is not None:
        p.update(payload)
    return DecisionIntake(
        pack_id="finance",
        intake_type="controlled_decision",
        status=status,
        payload=p,
    )


# ── H-9C2 Rule 1: emotional_state stress → escalate ─────────────────────


def test_h9c2_emotional_stress_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "stressed"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any("emotional_state" in r.lower() for r in decision.reasons)


def test_h9c2_emotional_fear_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "fearful"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c2_emotional_anger_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "angry"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c2_emotional_fomo_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "FOMO"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c2_emotional_calm_not_escalated():
    """calm emotional_state should NOT trigger escalate on its own."""
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "calm"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"


def test_h9c2_emotional_neutral_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"emotional_state": "neutral"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"


# ── H-9C2 Rule 2: rule_exceptions not empty → escalate ────────────────


def test_h9c2_rule_exceptions_not_empty_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"rule_exceptions": ["override position limit"]})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any("rule_exceptions" in r.lower() for r in decision.reasons)


def test_h9c2_rule_exceptions_empty_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"rule_exceptions": []})
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"


def test_h9c2_rule_exceptions_none_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"rule_exceptions": None})
    decision = engine.validate_intake(intake)
    # None → treat as empty, no escalate
    assert decision.decision == "execute"


# ── H-9C2 Rule 3: confidence < 0.3 → escalate ─────────────────────────


def test_h9c2_confidence_too_low_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.2})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any("confidence" in r.lower() for r in decision.reasons)


def test_h9c2_confidence_low_boundary_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.299})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c2_confidence_acceptable_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.5})
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"


def test_h9c2_confidence_high_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"confidence": 0.9})
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"


# ── Priority: reject still beats escalate ──────────────────────────────


def test_h9c2_priority_reject_over_escalate_emotion():
    """missing stop_loss + stressed → reject (not escalate)."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "stop_loss": None,
            "emotional_state": "stressed",
        }
    )
    decision = engine.validate_intake(intake)
    assert decision.decision == "reject"


def test_h9c2_priority_reject_over_escalate_low_confidence():
    """missing thesis + low confidence → reject (not escalate)."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "thesis": None,
            "confidence": 0.2,
        }
    )
    decision = engine.validate_intake(intake)
    assert decision.decision == "reject"


# ── Existing triggers still work ───────────────────────────────────────


def test_h9c2_existing_revenge_trade_still_escalates():
    engine = RiskEngine()
    intake = _make_intake(payload={"is_revenge_trade": True})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c2_existing_chasing_still_escalates():
    engine = RiskEngine()
    intake = _make_intake(payload={"is_chasing": True})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
```

**Step 2: Run tests to verify FAILURE**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/test_h9c2_escalate_coverage.py -v 2>&1 | tail -40
```

Expected: 12+ tests FAIL — the escalation rules don't exist yet.

**Step 3: Commit failing tests**

```bash
git add tests/unit/governance/test_h9c2_escalate_coverage.py
git commit -m "test(h9c2): add failing escalate coverage tests"
```

---

### Task 2.2: Implement new escalation rules

**Objective:** Add emotional state, rule exceptions, and low confidence triggers to Gate 4.

**Files:**
- Modify: `governance/risk_engine/engine.py`

**Step 1: Add escalation helpers and rules**

In `engine.py`, after the existing Gate 4 block (line 147), insert new escalation rules.

The Gate 4 section (lines 142-147) currently is:
```python
        # ── Gate 4: Behavioural red flags (escalate, not reject) ─────
        if payload.get("is_revenge_trade") is True:
            escalate_reasons.append("is_revenge_trade=true — requires human review.")

        if payload.get("is_chasing") is True:
            escalate_reasons.append("is_chasing=true — requires human review.")
```

Replace with:
```python
# ── Gate 4: Behavioural red flags (escalate, not reject) ─────
if payload.get("is_revenge_trade") is True:
    escalate_reasons.append("is_revenge_trade=true — requires human review.")

if payload.get("is_chasing") is True:
    escalate_reasons.append("is_chasing=true — requires human review.")

# H-9C2: Emotional state risk indicators → escalate
emotional = _as_str(payload.get("emotional_state"))
if emotional and _contains_emotional_risk(emotional):
    escalate_reasons.append(f"emotional_state='{emotional}' indicates elevated risk — requires human review.")

# H-9C2: Rule exceptions present → escalate (any exception needs review)
rule_exceptions = payload.get("rule_exceptions")
if isinstance(rule_exceptions, list) and len(rule_exceptions) > 0:
    escalate_reasons.append(f"rule_exceptions not empty ({len(rule_exceptions)} item(s)) — requires human review.")

# H-9C2: Confidence too low → escalate (but not missing, which is not checked here)
confidence = payload.get("confidence")
if isinstance(confidence, (int, float)) and 0 <= confidence < 0.3:
    escalate_reasons.append(f"confidence={confidence} is below 0.3 threshold — requires human review.")
```

**Step 2: Add the `_contains_emotional_risk()` helper**

After the existing `_as_positive_float()` function (line 200), add:

```python
# ── Emotional risk keyword detection ────────────────────────────────────────

_EMOTIONAL_RISK_KEYWORDS: frozenset[str] = frozenset({
    "stress",
    "stressed",
    "stressful",
    "fear",
    "fearful",
    "scared",
    "terrified",
    "panicked",
    "panic",
    "anger",
    "angry",
    "furious",
    "frustrated",
    "fomo",
    "greedy",
    "desperate",
    "reckless",
    "revenge",
    "impulsive",
})


def _contains_emotional_risk(emotional_state: str) -> bool:
    """Return True if emotional_state contains known risk keywords.

    Case-insensitive substring match against the tokenized input.
    """
    lowered = emotional_state.lower()
    return any(keyword in lowered for keyword in _EMOTIONAL_RISK_KEYWORDS)
```

**Step 3: Run tests to verify PASS**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/test_h9c2_escalate_coverage.py -v
```

Expected: all tests PASS.

**Step 4: Run existing H-5 tests to verify no regression**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/test_h5_finance_governance_hard_gate.py -v
```

Expected: all existing tests still PASS.

**Step 5: Commit**

```bash
git add governance/risk_engine/engine.py
git commit -m "feat(h9c2): add emotional state, rule exceptions, low confidence escalate triggers"
```

---

## Phase 3: H-9C3 — Thesis Quality Gate

**Objective:** Add deterministic thesis quality checks to prevent empty/generic/weak theses from passing governance.

**Design:**
```
thesis missing → reject (existing H-5 Gate 1)
thesis < 50 chars → escalate (too short to be meaningful)
thesis matches banned pattern → reject (generic/empty phrase)
thesis lacks invalidation/confirmation wording → escalate (no verifiability)
```

**Banned patterns (case-insensitive substring match):**
```
just feels right
feels right
looks good
probably pump
should go up
vibes
no specific thesis
trust me
yolo
because i said so
i think so
let's see
```

**Files to create:**
- `governance/risk_engine/thesis_quality.py` — thesis quality checker
- `tests/unit/governance/test_h9c3_thesis_quality.py` — tests

**Files to modify:**
- `governance/risk_engine/engine.py` — call thesis quality checks in Gate 1

---

### Task 3.1: Write failing thesis quality tests

**Objective:** Write tests that FAIL because thesis quality checks don't exist yet.

**Files:**
- Create: `tests/unit/governance/test_h9c3_thesis_quality.py`

**Step 1: Write all thesis quality tests**

File: `tests/unit/governance/test_h9c3_thesis_quality.py`

```python
"""H-9C3: Thesis quality gate — unit tests.

Verifies deterministic thesis quality checks: minimum length,
banned patterns, missing invalidation wording.
"""

import pytest

from domains.decision_intake.models import DecisionIntake
from governance.risk_engine.engine import RiskEngine


def _make_intake(*, status="validated", payload=None) -> DecisionIntake:
    p = {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC is breaking out above the 4h resistance with volume confirmation "
        "and the 200 EMA is sloping upward, targeting the range high of 72k.",
        "entry_condition": "Breakout confirmed.",
        "invalidation_condition": "Range reclaim.",
        "stop_loss": "Below support",
        "target": "Local high",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.7,
        "rule_exceptions": [],
        "notes": "Controlled",
    }
    if payload is not None:
        p.update(payload)
    return DecisionIntake(
        pack_id="finance",
        intake_type="controlled_decision",
        status=status,
        payload=p,
    )


# ── Thesis too short (< 50 chars) → escalate ──────────────────────────


def test_h9c3_thesis_too_short_escalated():
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "BTC looks good"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any("thesis" in r.lower() for r in decision.reasons)


def test_h9c3_thesis_boundary_short_escalated():
    """49 chars → escalate (below 50 threshold)."""
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "B" * 49})
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"


def test_h9c3_thesis_boundary_ok_not_escalated():
    """50 chars → not escalated for length."""
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "B" * 50})
    decision = engine.validate_intake(intake)
    # Length is OK — decision depends on other factors
    if decision.decision == "escalate":
        assert not any("shorter than 50" in r.lower() for r in decision.reasons)


# ── Banned patterns → reject ──────────────────────────────────────────


@pytest.mark.parametrize(
    "bad_thesis",
    [
        "No specific thesis, just feels right",
        "It just feels right to buy here",
        "Looks good, should pump",
        "No specific thesis provided",
        "Vibes are good, trust me",
        "YOLO all in",
        "Because I said so",
        "I think so, let's see what happens",
    ],
)
def test_h9c3_banned_pattern_rejected(bad_thesis):
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": bad_thesis})
    decision = engine.validate_intake(intake)
    assert decision.decision == "reject"
    assert any("thesis" in r.lower() for r in decision.reasons)
    assert any(("quality" in r.lower() or "pattern" in r.lower() or "generic" in r.lower()) for r in decision.reasons)


def test_h9c3_banned_pattern_case_insensitive():
    engine = RiskEngine()
    intake = _make_intake(payload={"thesis": "JUST FEELS RIGHT"})
    decision = engine.validate_intake(intake)
    assert decision.decision == "reject"


# ── Missing invalidation/confirmation wording → escalate ──────────────


def test_h9c3_no_invalidation_wording_escalated():
    """Thesis has no invalidation or confirmation language → escalate."""
    engine = RiskEngine()
    # Long enough but purely directional, no "if"/"unless"/"invalid"/"confirm"
    intake = _make_intake(
        payload={
            "thesis": "BTC is going up because the trend is strong and volume is high "
            "and the market sentiment is bullish across all timeframes."
        }
    )
    decision = engine.validate_intake(intake)
    assert decision.decision == "escalate"
    assert any(
        w in str(decision.reasons).lower() for w in ("invalidation", "verifiable", "confirmation", "falsifiable")
    )


def test_h9c3_has_invalidation_wording_not_escalated():
    """Thesis with 'unless' or 'if not' — acceptable."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "thesis": "BTC is going up because the trend is strong, invalidated if price closes below the 200 EMA."
        }
    )
    decision = engine.validate_intake(intake)
    # Should NOT escalate for invalidation wording
    if decision.decision == "escalate":
        assert not any("invalidation" in r.lower() for r in decision.reasons)


def test_h9c3_has_confirmation_wording_not_escalated():
    """Thesis with 'confirmed when' — acceptable."""
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "thesis": "ETH breakout target is 2500, confirmed when 4h candle "
            "closes above resistance with volume > 2x average."
        }
    )
    decision = engine.validate_intake(intake)
    if decision.decision == "escalate":
        assert not any("invalidation" in r.lower() for r in decision.reasons)


def test_h9c3_has_unless_not_escalated():
    engine = RiskEngine()
    intake = _make_intake(
        payload={
            "thesis": "SOL will continue its uptrend unless it loses the 100 level "
            "on daily close, which would invalidate the momentum thesis."
        }
    )
    decision = engine.validate_intake(intake)
    if decision.decision == "escalate":
        assert not any("invalidation" in r.lower() for r in decision.reasons)


# ── Valid thesis still passes ──────────────────────────────────────────


def test_h9c3_valid_thesis_executed():
    engine = RiskEngine()
    intake = _make_intake()
    decision = engine.validate_intake(intake)
    assert decision.decision == "execute"
```

**Step 2: Run tests to verify FAILURE**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/test_h9c3_thesis_quality.py -v 2>&1 | tail -40
```

Expected: 12+ tests FAIL.

**Step 3: Commit failing tests**

```bash
git add tests/unit/governance/test_h9c3_thesis_quality.py
git commit -m "test(h9c3): add failing thesis quality gate tests"
```

---

### Task 3.2: Create thesis quality checker module

**Objective:** A standalone module for thesis quality checks — deterministic, no NLP.

**Files:**
- Create: `governance/risk_engine/thesis_quality.py`

**Step 1: Write the module**

File: `governance/risk_engine/thesis_quality.py`

```python
"""H-9C3: Deterministic thesis quality checks.

All checks are rule-based (length, patterns, wording) — no NLP/ML.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Constants ──────────────────────────────────────────────────────────

THESIS_MIN_LENGTH: int = 50

BANNED_THESIS_PATTERNS: tuple[str, ...] = (
    "just feels right",
    "feels right",
    "looks good",
    "probably pump",
    "should go up",
    "should go down",
    "vibes",
    "no specific thesis",
    "trust me",
    "yolo",
    "because i said so",
    "i think so",
    "let's see",
    "we'll see",
    "who knows",
    "idk",
    "just a hunch",
    "gut feeling",
    "hoping for",
    "praying for",
)

INVALIDATION_WORDS: tuple[str, ...] = (
    "unless",
    "invalid",
    "invalidate",
    "falsif",
    "if not",
    "stop if",
    "exit if",
    "cut if",
)

CONFIRMATION_WORDS: tuple[str, ...] = (
    "confirm",
    "confirmed when",
    "verif",
    "must hold",
    "must close",
    "needs to",
    "requires",
)


@dataclass(slots=True)
class ThesisQualityResult:
    """Result of thesis quality evaluation."""

    is_banned: bool = False
    banned_match: str | None = None
    is_too_short: bool = False
    lacks_verifiability: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return self.is_banned or self.is_too_short or self.lacks_verifiability


def check_thesis_quality(thesis: str) -> ThesisQualityResult:
    """Evaluate thesis quality against deterministic rules.

    Returns a ThesisQualityResult with:
    - is_banned: thesis matches a banned generic pattern → reject
    - is_too_short: thesis < 50 chars → escalate
    - lacks_verifiability: no invalidation/confirmation wording → escalate
    """
    result = ThesisQualityResult()
    lowered = thesis.lower().strip()

    # Check 1: Banned patterns
    for pattern in BANNED_THESIS_PATTERNS:
        if pattern in lowered:
            result.is_banned = True
            result.banned_match = pattern
            result.reasons.append(f"Thesis matches banned generic pattern: '{pattern}'.")
            break

    # Check 2: Minimum length
    if len(thesis.strip()) < THESIS_MIN_LENGTH:
        result.is_too_short = True
        result.reasons.append(
            f"Thesis is shorter than {THESIS_MIN_LENGTH} characters "
            f"({len(thesis.strip())} chars) — too short to be meaningful."
        )

    # Check 3: Verifiability (invalidation or confirmation language)
    has_invalidation = any(w in lowered for w in INVALIDATION_WORDS)
    has_confirmation = any(w in lowered for w in CONFIRMATION_WORDS)

    if not has_invalidation and not has_confirmation:
        result.lacks_verifiability = True
        result.reasons.append("Thesis lacks invalidation or confirmation criteria — not verifiable.")

    return result
```

**Step 2: Verify syntax**

```bash
cd /root/projects/financial-ai-os && python -c "from governance.risk_engine.thesis_quality import check_thesis_quality; print('OK')"
```

**Step 3: Commit**

```bash
git add governance/risk_engine/thesis_quality.py
git commit -m "feat(h9c3): add deterministic thesis quality checker"
```

---

### Task 3.3: Wire thesis quality into RiskEngine

**Objective:** Call `check_thesis_quality()` in `validate_intake()` Gate 1, after the existing thesis-exists check.

**Files:**
- Modify: `governance/risk_engine/engine.py`

**Step 1: Add import**

At the top of `engine.py`, add:
```python
from governance.risk_engine.thesis_quality import check_thesis_quality
```

**Step 2: Add thesis quality checks in Gate 1**

In `validate_intake()`, after the existing thesis check (lines 101-103):
```python
        thesis = _as_str(payload.get("thesis"))
        if not thesis:
            reject_reasons.append("Missing required field: thesis.")
```

Add:
```python
# H-9C3: Thesis quality checks (only if thesis is present)
if thesis:
    quality = check_thesis_quality(thesis)
    if quality.is_banned:
        reject_reasons.append(f"Thesis quality rejected: {quality.banned_match or 'generic pattern'}.")
    if quality.is_too_short:
        escalate_reasons.append(
            f"Thesis is too short ({len(thesis.strip())} chars, minimum {50}) — requires human review."
        )
    if quality.lacks_verifiability:
        escalate_reasons.append(
            "Thesis lacks verifiability criteria (no invalidation or confirmation conditions) — requires human review."
        )
```

**Step 3: Run new tests to verify PASS**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/test_h9c3_thesis_quality.py -v
```

Expected: all tests PASS.

**Step 4: Run all governance unit tests**

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/ -v
```

Expected: all tests PASS (H-5, H-9C2, H-9C3).

**Step 5: Commit**

```bash
git add governance/risk_engine/engine.py
git commit -m "feat(h9c3): wire thesis quality gate into RiskEngine.validate_intake"
```

---

## Final Verification

### H-9C Full Test Suite

After all three phases are complete, run the full governance test suite:

```bash
cd /root/projects/financial-ai-os && uv run pytest tests/unit/governance/ tests/unit/db/ -v
```

Expected: all tests pass (H-5, H-9C1, H-9C2, H-9C3).

### Integration Tests

```bash
cd /root/projects/financial-ai-os && \
  PFIOS_DB_URL=postgresql://pfios:pfios@127.0.0.1:5432/pfios_test \
  uv run pytest tests/integration/test_h8_review_closure.py \
               tests/integration/test_h7_manual_outcome_api.py \
               tests/integration/test_finance_decision_intake_api.py -v
```

Expected: all integration tests pass.

### Tag

```bash
git tag h9c-remediation-complete
```

---

## Summary of Changes

| Phase | Files Created | Files Modified | New Tests |
|-------|-------------|----------------|-----------|
| H-9C1 | `state/db/migrations/__init__.py`, `state/db/migrations/runner.py`, `tests/unit/db/test_migrations.py` | `state/db/bootstrap.py` | 3 |
| H-9C2 | `tests/unit/governance/test_h9c2_escalate_coverage.py` | `governance/risk_engine/engine.py` | 16 |
| H-9C3 | `governance/risk_engine/thesis_quality.py`, `tests/unit/governance/test_h9c3_thesis_quality.py` | `governance/risk_engine/engine.py` | 14 |

**Total: 5 new files, 2 modified files, ~33 new tests.**

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Migration `ALTER TABLE` runs on SQLite (tests) | `ADD COLUMN IF NOT EXISTS` is SQL-standard and supported by SQLite 3.35+ |
| Banned patterns too aggressive | Patterns are narrow and case-insensitive substring matches; easy to tune |
| Emotional keyword false positives | Keywords are conservative; "calm"/"neutral"/"focused" are not flagged |
| Thesis length 50 chars too strict | Threshold is a starting point; can adjust based on dogfood feedback |
