from domains.strategy.models import Recommendation
from domains.strategy.orm import RecommendationORM
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from domains.strategy.state_machine import RecommendationStateMachine
from domains.strategy.models import Recommendation as LegacyRecommendation
from domains.strategy.orm import RecommendationORM as LegacyRecommendationORM
from domains.strategy.repository import (
    RecommendationRepository as LegacyRecommendationRepository,
)
from domains.strategy.service import RecommendationService as LegacyRecommendationService
from domains.strategy.state_machine import (
    RecommendationStateMachine as LegacyRecommendationStateMachine,
)


def test_root_recommendation_domain_imports_are_available():
    assert Recommendation is not None
    assert RecommendationORM is not None
    assert RecommendationRepository is not None
    assert RecommendationService is not None
    assert RecommendationStateMachine is not None


def test_legacy_recommendation_domain_imports_still_resolve():
    assert LegacyRecommendation.__name__ == Recommendation.__name__
    assert LegacyRecommendationORM.__name__ == RecommendationORM.__name__
    assert LegacyRecommendationRepository.__name__ == RecommendationRepository.__name__
    assert LegacyRecommendationService.__name__ == RecommendationService.__name__
    assert LegacyRecommendationStateMachine.__name__ == RecommendationStateMachine.__name__
