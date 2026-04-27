from domains.strategy.state_machine import RecommendationStateMachine
from shared.enums.domain import RecommendationStatus
from shared.errors.domain import InvalidStateTransition


def test_recommendation_valid_transition():
    sm = RecommendationStateMachine()
    assert (
        sm.can_transition(
            RecommendationStatus.GENERATED,
            RecommendationStatus.ADOPTED,
        )
        is True
    )


def test_recommendation_invalid_transition():
    sm = RecommendationStateMachine()
    try:
        sm.ensure_transition(
            RecommendationStatus.GENERATED,
            RecommendationStatus.REVIEWED,
        )
        assert False, "Expected InvalidStateTransition"
    except InvalidStateTransition:
        assert True
