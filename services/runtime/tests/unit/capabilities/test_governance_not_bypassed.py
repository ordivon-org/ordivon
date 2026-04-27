"""Task 4.3: Governance-not-bypassed capability chain invariant.

Ensures plan_intake cannot be called without first calling govern_intake,
and that the full chain (create → govern → plan) succeeds.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.domain.finance_decisions import (
    FinanceDecisionCapability,
    PlanReceiptNotAllowed,
)
from state.db.base import Base


# ── Helpers ──────────────────────────────────────────────────────────


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def _valid_payload() -> dict:
    return {
        "symbol": "BTC/USDT",
        "direction": "long",
        "thesis": "BTC breaking above resistance with volume confirmation; invalidated if price closes below 200 EMA.",
        "stop_loss": "Below support",
        "position_size_usdt": 100,
        "max_loss_usdt": 20,
        "risk_unit_usdt": 10,
        "is_chasing": False,
        "is_revenge_trade": False,
        "emotional_state": "calm",
        "confidence": 0.7,
    }


# ── Test 1: plan without governance must fail ────────────────────────


def test_plan_without_governance_fails():
    """plan_intake must raise PlanReceiptNotAllowed when governance was not called."""
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        cap = FinanceDecisionCapability()
        intake = cap.create_intake(_valid_payload(), db)
        db.commit()

        with pytest.raises(PlanReceiptNotAllowed) as exc_info:
            cap.plan_intake(intake.id, db)

        assert exc_info.value.intake_id == intake.id
        assert exc_info.value.governance_status == "not_started"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# ── Test 2: full chain (create → govern → plan) succeeds ─────────────


def test_full_chain_governance_before_plan_succeeds():
    """create_intake → govern_intake → plan_intake must produce a valid receipt."""
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        cap = FinanceDecisionCapability()
        intake = cap.create_intake(_valid_payload(), db)
        db.commit()

        updated_intake, decision = cap.govern_intake(intake.id, db)
        assert decision.decision == "execute", f"Expected execute, got {decision.decision}: {decision.reasons}"

        result = cap.plan_intake(intake.id, db)
        assert result.execution_receipt_id is not None, "plan_intake must return a non-None execution_receipt_id"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
