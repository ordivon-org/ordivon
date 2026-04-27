"""FinanceManualOutcome duplicate execution_receipt_id conflict test.

Verifies the behavior when two FinanceManualOutcome rows
reference the same execution_receipt_id.  The ORM does NOT
enforce a unique constraint on execution_receipt_id (only an
index), so the repository allows both rows.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from domains.finance_outcome.models import FinanceManualOutcome
from domains.finance_outcome.orm import FinanceManualOutcomeORM
from domains.finance_outcome.repository import FinanceManualOutcomeRepository
from state.db.base import Base


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(bind=engine)


# ── Test: duplicate execution_receipt_id is not rejected at DB level ─────


def test_duplicate_execution_receipt_id_allowed(db: Session):
    """Create two outcomes with the same execution_receipt_id.

    The ORM has no unique constraint on execution_receipt_id, so the
    second create succeeds.  The repository does not enforce uniqueness
    either — it simply inserts a new row with a new primary-key id.
    """
    repo = FinanceManualOutcomeRepository(db)

    # Shared ids
    intake_id = "di_test_dup_001"
    receipt_id = "exrcpt_test_dup_001"

    # ── First outcome ──────────────────────────────────────────────────
    outcome1 = FinanceManualOutcome(
        decision_intake_id=intake_id,
        execution_receipt_id=receipt_id,
        observed_outcome="First outcome.",
        verdict="validated",
    )
    row1 = repo.create(outcome1)
    db.commit()

    assert row1.id.startswith("fmout_")
    assert row1.execution_receipt_id == receipt_id

    # ── Second outcome — same receipt, different id ────────────────────
    outcome2 = FinanceManualOutcome(
        decision_intake_id=intake_id,
        execution_receipt_id=receipt_id,
        observed_outcome="Second outcome.",
        verdict="invalidated",
    )
    # Neither the model nor the ORM rejects this.
    row2 = repo.create(outcome2)
    db.commit()

    # Both rows exist with different primary keys
    assert row2.id.startswith("fmout_")
    assert row2.id != row1.id
    assert row2.execution_receipt_id == receipt_id

    # Verify both persisted at the ORM level
    rows = db.query(FinanceManualOutcomeORM).filter(FinanceManualOutcomeORM.execution_receipt_id == receipt_id).all()
    assert len(rows) == 2, (
        "Expected 2 rows with same execution_receipt_id; ORM does not enforce uniqueness on this column."
    )
