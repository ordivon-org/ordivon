from apps.api.app.services.object_service import ObjectService
from apps.api.app.services.recommendation_service import RecommendationService
from apps.api.app.services.review_service import ReviewService
from apps.api.app.services.validation_service import ValidationService


def test_app_service_facades_are_importable():
    assert ObjectService is not None
    assert RecommendationService is not None
    assert ReviewService is not None
    assert ValidationService is not None
