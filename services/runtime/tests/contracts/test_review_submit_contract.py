"""Contract tests for POST /api/v1/reviews/submit with outcome_ref fields.

Tests the review submit endpoint's contract around outcome_ref_type and
outcome_ref_id parameters, ensuring they accept a valid FinanceManualOutcome
reference from the full intake→govern→plan→outcome chain.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("PFIOS_ENV", "test")
os.environ.setdefault("PFIOS_DEBUG", "false")
os.environ.setdefault("PFIOS_REASONING_PROVIDER", "mock")
os.environ.setdefault("PFIOS_DB_URL", "sqlite:///:memory:")

from apps.api.app.deps import get_db
from apps.api.app.main import app
from state.db.base import Base

# Import all ORM models so metadata is discoverable
import domains.ai_actions.orm  # noqa: F401
import domains.candidate_rules.orm  # noqa: F401
import domains.decision_intake.orm  # noqa: F401
import domains.execution_records.orm  # noqa: F401
import domains.finance_outcome.orm  # noqa: F401
import domains.intelligence_runs.orm  # noqa: F401
import domains.research.orm  # noqa: F401
import domains.workflow_runs.orm  # noqa: F401
import domains.journal.issue_orm  # noqa: F401
import domains.journal.lesson_orm  # noqa: F401
import domains.journal.orm  # noqa: F401
import domains.knowledge_feedback.feedback_record_orm  # noqa: F401
import domains.knowledge_feedback.orm  # noqa: F401
import domains.strategy.orm  # noqa: F401
import domains.strategy.outcome_orm  # noqa: F401
import governance_engine.approval_orm  # noqa: F401
import governance_engine.audit.orm  # noqa: F401
import infra.scheduler.orm  # noqa: F401
import state.usage.orm  # noqa: F401


def _make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


@contextmanager
def _client_with_db():
    engine, testing_session_local = _make_engine()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, testing_session_local
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def _valid_intake_payload() -> dict:
    return {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "BTC breakout with volume confirmation and 200 EMA invalidation.",
        "entry_condition": "Breakout with retest.",
        "invalidation_condition": "Range reclaim fails.",
        "stop_loss": "Below support",
        "target": "Retest local high",
        "position_size_usdt": 100.0,
        "max_loss_usdt": 20.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.7,
        "rule_exceptions": [],
        "notes": "Controlled setup",
    }


def _create_intake_govern_plan_outcome(client) -> dict:
    """Full chain: intake → govern → plan → outcome. Returns outcome response JSON."""
    # 1. Create intake
    resp = client.post("/api/v1/finance-decisions/intake", json=_valid_intake_payload())
    assert resp.status_code == 200, resp.text
    intake_id = resp.json()["id"]

    # 2. Govern
    gov_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/govern")
    assert gov_resp.status_code == 200, gov_resp.text
    assert gov_resp.json()["governance_decision"] == "execute"

    # 3. Plan
    plan_resp = client.post(f"/api/v1/finance-decisions/intake/{intake_id}/plan")
    assert plan_resp.status_code == 200, plan_resp.text
    receipt_id = plan_resp.json()["execution_receipt_id"]

    # 4. Outcome
    outcome_payload = {
        "execution_receipt_id": receipt_id,
        "observed_outcome": "Stop loss hit at -2.5%.",
        "verdict": "validated",
        "variance_summary": "Expected -1%, actual -2.5%.",
        "plan_followed": True,
    }
    outcome_resp = client.post(
        f"/api/v1/finance-decisions/intake/{intake_id}/outcome",
        json=outcome_payload,
    )
    assert outcome_resp.status_code == 200, outcome_resp.text
    return outcome_resp.json()


def _review_submit_payload() -> dict:
    return {
        "recommendation_id": None,
        "review_type": "recommendation_postmortem",
        "expected_outcome": "Price target",
        "actual_outcome": "Price reached target",
        "deviation": "None",
        "mistake_tags": "plan_execution",
        "lessons": [{"lesson_text": "Follow plan"}],
        "new_rule_candidate": None,
    }


# ── Test 1: Review submit accepts outcome_ref_type and outcome_ref_id ──────


def test_submit_review_accepts_outcome_ref_fields():
    """Full chain intake→govern→plan→outcome, then POST reviews/submit
    with outcome_ref_type and outcome_ref_id referencing the outcome."""
    with _client_with_db() as (client, _):
        # Create intake, govern, plan, outcome
        outcome = _create_intake_govern_plan_outcome(client)
        outcome_id = outcome["outcome_id"]

        # Submit review with outcome_ref fields
        payload = _review_submit_payload()
        payload["outcome_ref_type"] = "finance_manual_outcome"
        payload["outcome_ref_id"] = outcome_id

        resp = client.post("/api/v1/reviews/submit", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        assert body["outcome_ref_type"] == "finance_manual_outcome"
        assert body["outcome_ref_id"] == outcome_id
        assert body["id"].startswith("review_")
        assert body["status"] == "pending"


# ── Test 2: Review submit without outcome_ref still succeeds ────────────────


def test_submit_review_without_outcome_ref_still_succeeds():
    """POST reviews/submit without outcome_ref fields should return 200."""
    with _client_with_db() as (client, _):
        payload = _review_submit_payload()

        resp = client.post("/api/v1/reviews/submit", json=payload)
        assert resp.status_code == 200, resp.text
        body = resp.json()

        assert body["id"].startswith("review_")
        assert body["status"] == "pending"
