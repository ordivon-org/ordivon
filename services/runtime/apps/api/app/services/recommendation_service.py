"""Compatibility service facade for recommendation workflows."""

from capabilities.boundary import ActionContext
from capabilities.recommendations import RecommendationCapability


class RecommendationService:
    _capability = RecommendationCapability()

    @classmethod
    def list_recent(cls, limit: int = 10):
        return cls._capability.list_recent(limit=limit)

    @classmethod
    def get_by_id(cls, recommendation_id: str):
        return cls._capability.get_by_id(recommendation_id)

    @classmethod
    def update_status(cls, service, recommendation_id: str, lifecycle_status: str, action_context: ActionContext):
        return cls._capability.update_status(service, recommendation_id, lifecycle_status, action_context)
