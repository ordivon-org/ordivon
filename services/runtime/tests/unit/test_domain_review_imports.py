from domains.journal.models import Review
from domains.journal.orm import ReviewORM
from domains.journal.repository import ReviewRepository
from domains.journal.service import ReviewService
from domains.journal.models import Review as LegacyReview
from domains.journal.orm import ReviewORM as LegacyReviewORM
from domains.journal.repository import ReviewRepository as LegacyReviewRepository
from domains.journal.service import ReviewService as LegacyReviewService


def test_root_review_domain_imports_are_available():
    assert Review is not None
    assert ReviewORM is not None
    assert ReviewRepository is not None
    assert ReviewService is not None


def test_legacy_review_domain_imports_still_resolve():
    assert LegacyReview.__name__ == Review.__name__
    assert LegacyReviewORM.__name__ == ReviewORM.__name__
    assert LegacyReviewRepository.__name__ == ReviewRepository.__name__
    assert LegacyReviewService.__name__ == ReviewService.__name__
