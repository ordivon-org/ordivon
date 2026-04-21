import pytest

from domains.journal.state_machine import ReviewStateMachine
from shared.enums.domain import ReviewStatus
from shared.errors.domain import InvalidStateTransition


def test_review_state_machine_allows_pending_to_completed():
    sm = ReviewStateMachine()
    sm.ensure_transition(ReviewStatus.PENDING, ReviewStatus.COMPLETED)


def test_review_state_machine_rejects_completed_to_in_progress():
    sm = ReviewStateMachine()
    with pytest.raises(InvalidStateTransition, match="Invalid review transition"):
        sm.ensure_transition(ReviewStatus.COMPLETED, ReviewStatus.IN_PROGRESS)
