"""CandidateRule≠Policy structural invariant tests.

Verifies that CandidateRule and Policy are properly separated:
- CandidateRule states cannot include "active" or "policy".
- Creating a CandidateRule does not affect the active governance policy snapshot.
- CandidateRule rejects creation with an unsupported status like "active".
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.candidate_rules.models import CandidateRule, VALID_CANDIDATE_RULE_STATES
from domains.candidate_rules.repository import CandidateRuleRepository
from governance.policy_source import GovernancePolicySource
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def test_candidate_rule_status_cannot_be_active():
    """Structural invariant: VALID_CANDIDATE_RULE_STATES excludes 'active' and 'policy'."""
    assert "active" not in VALID_CANDIDATE_RULE_STATES, (
        "VALID_CANDIDATE_RULE_STATES must not contain 'active' — CandidateRule is NOT a live/active policy."
    )
    assert "policy" not in VALID_CANDIDATE_RULE_STATES, (
        "VALID_CANDIDATE_RULE_STATES must not contain 'policy' — CandidateRule is NOT a policy itself."
    )


def test_candidate_rule_creation_does_not_change_governance_snapshot():
    """Side-effect isolation: creating a CandidateRule must not mutate the
    active governance policy snapshot."""
    engine, testing_session_local = _make_db()
    policy_source = GovernancePolicySource()

    # Snapshot BEFORE creating a CandidateRule
    before = policy_source.get_active_snapshot()

    db = testing_session_local()
    try:
        repo = CandidateRuleRepository(db)
        rule = CandidateRule(
            issue_key="NEED-CONFIRMATION",
            summary="Require confirmation candle before entry",
            status="draft",
        )
        repo.create(rule)
        db.commit()
    finally:
        db.close()

    # Snapshot AFTER creating a CandidateRule
    after = policy_source.get_active_snapshot()

    assert after.active_policy_ids == before.active_policy_ids, (
        "Creating a CandidateRule must not change the active_policy_ids in the governance snapshot."
    )
    assert after.policy_set_id == before.policy_set_id, (
        "Creating a CandidateRule must not change the policy_set_id in the governance snapshot."
    )


def test_candidate_rule_cannot_be_created_with_active_status():
    """CandidateRule rejects status='active' — it is NOT a live policy."""
    with pytest.raises(ValueError, match="Unsupported candidate rule status"):
        CandidateRule(
            issue_key="missed confirmation candle",
            summary="Wait for confirmation",
            status="active",
        )

    with pytest.raises(ValueError, match="Unsupported candidate rule status"):
        CandidateRule(
            issue_key="some issue",
            summary="some summary",
            status="policy",
        )
