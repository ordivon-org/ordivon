"""Compatibility service facade for review workflows."""

from typing import Any

from capabilities.boundary import ActionContext
from capabilities.reviews import ReviewCapability


class ReviewService:
    _capability = ReviewCapability()

    @classmethod
    def generate_skeleton(cls, report_id: str, recommendation_id: str | None = None) -> dict[str, Any]:
        return cls._capability.generate_skeleton(report_id, recommendation_id)

    @classmethod
    def submit_review(cls, service, payload: dict[str, Any], action_context: ActionContext):
        return cls._capability.submit_review(service, payload, action_context)

    @classmethod
    def create_review(
        cls,
        service,
        recommendation_id: str,
        action_context: ActionContext,
        review_type: str = "recommendation_postmortem",
        expected_outcome: str | None = None,
        outcome_ref_type: str | None = None,
        outcome_ref_id: str | None = None,
    ) -> dict[str, str]:
        return cls._capability.create_review(
            service=service,
            recommendation_id=recommendation_id,
            action_context=action_context,
            review_type=review_type,
            expected_outcome=expected_outcome,
            outcome_ref_type=outcome_ref_type,
            outcome_ref_id=outcome_ref_id,
        )

    @classmethod
    def complete_review(
        cls,
        service,
        review_id: str,
        observed_outcome: str,
        verdict: Any,
        variance_summary: str | None,
        cause_tags: list[str],
        lessons: list[str],
        followup_actions: list[str],
        action_context: ActionContext,
    ) -> dict[str, Any]:
        return cls._capability.complete_review(
            service=service,
            review_id=review_id,
            observed_outcome=observed_outcome,
            verdict=verdict,
            variance_summary=variance_summary,
            cause_tags=cause_tags,
            lessons=lessons,
            followup_actions=followup_actions,
            action_context=action_context,
        )
