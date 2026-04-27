"""ReviewRepository create/get consistency test.

Verifies that a Review created via ReviewRepository.create() can be
read back via ReviewRepository.get() with key fields preserved, especially
outcome_ref_type and outcome_ref_id.
"""

from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from shared.enums.domain import ReviewStatus
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository


def test_review_repository_create_and_get():
    """Create a Review → persist via repository → read back → verify key fields."""
    init_db()
    db = SessionLocal()

    try:
        repo = ReviewRepository(db)
        review = Review(
            recommendation_id="rec_tm_001",
            outcome_ref_type="finance_manual_outcome",
            outcome_ref_id="out_tm_001",
            review_type="recommendation_postmortem",
            status=ReviewStatus.PENDING,
            expected_outcome="price moves up by 2% within 24h",
            cause_tags=["market_volatility", "news_event"],
            lessons=["always check correlation", "use stop-loss"],
            followup_actions=["monitor position", "adjust SL"],
        )

        row = repo.create(review)
        loaded = repo.get(row.id)

        assert loaded is not None
        assert loaded.outcome_ref_type == "finance_manual_outcome"
        assert loaded.outcome_ref_id == "out_tm_001"
        assert loaded.review_type == "recommendation_postmortem"
        assert loaded.status == ReviewStatus.PENDING.value
        assert loaded.expected_outcome == "price moves up by 2% within 24h"
    finally:
        db.close()
