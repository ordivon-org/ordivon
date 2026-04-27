"""CandidateRule persistence regression — verifies new fields survive DB round-trip."""

from sqlalchemy.orm import Session

from domains.candidate_rules.models import CandidateRule
from domains.candidate_rules.orm import CandidateRuleORM
from domains.candidate_rules.repository import CandidateRuleRepository
from shared.utils.ids import new_id
from state.db.bootstrap import init_db
from state.db.session import SessionLocal


def test_candidate_rule_lesson_ids_persist():
    """lesson_ids + source_refs survive create → DB → read cycle."""
    init_db()
    db: Session = SessionLocal()
    try:
        repo = CandidateRuleRepository(db)
        rule = CandidateRule(
            id=new_id("crule"),
            issue_key="test_lesson_ids_roundtrip",
            summary="Test lesson_ids persistence",
            status="draft",
            lesson_ids=("lesson_001", "lesson_002"),
            review_ids=("review_001",),
            source_refs=("review:review_001", "lesson:lesson_001", "lesson:lesson_002"),
        )
        created = repo.create(rule)
        db.commit()

        # Read back from DB
        row = db.query(CandidateRuleORM).filter(CandidateRuleORM.id == created.id).first()
        assert row is not None
        model = repo.to_model(row)

        assert model.lesson_ids == ("lesson_001", "lesson_002")
        assert model.source_refs == ("review:review_001", "lesson:lesson_001", "lesson:lesson_002")
        assert model.status == "draft"
        assert "review:review_001" in model.source_refs
        assert "lesson:lesson_001" in model.source_refs
    finally:
        db.rollback()
        db.close()


def test_candidate_rule_empty_lesson_ids_persist():
    """Empty lesson_ids/source_refs default to empty tuples and survive round-trip."""
    init_db()
    db: Session = SessionLocal()
    try:
        repo = CandidateRuleRepository(db)
        rule = CandidateRule(
            id=new_id("crule"),
            issue_key="test_empty_roundtrip",
            summary="Test empty fields",
            status="draft",
        )
        created = repo.create(rule)
        db.commit()

        row = db.query(CandidateRuleORM).filter(CandidateRuleORM.id == created.id).first()
        assert row is not None
        model = repo.to_model(row)

        assert model.lesson_ids == ()
        assert model.source_refs == ()
    finally:
        db.rollback()
        db.close()
