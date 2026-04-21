from state.db.bootstrap import init_db
from state.db.session import SessionLocal
from domains.journal.issue_models import Issue
from domains.journal.issue_repository import IssueRepository


def test_issue_repository_create():
    init_db()
    db = SessionLocal()

    try:
        repo = IssueRepository(db)
        row = repo.create(
            Issue(
                title="Test issue",
                summary="Issue summary",
                severity="p1",
                category="workflow",
            )
        )
        assert row.severity == "p1"
    finally:
        db.close()
