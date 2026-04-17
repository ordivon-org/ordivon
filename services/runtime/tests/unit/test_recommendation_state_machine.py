from pfios.domain.recommendation.state_machine import RecommendationStateMachine
from pfios.domain.common.enums import RecommendationStatus
from pfios.domain.common.errors import InvalidStateTransition


def test_recommendation_valid_transition():
    sm = RecommendationStateMachine()
    assert sm.can_transition(
        RecommendationStatus.GENERATED,
        RecommendationStatus.ADOPTED,
    ) is True


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
