from pfios.core.db.bootstrap import init_db
from pfios.core.db.session import SessionLocal
from pfios.domain.issue.models import Issue
from pfios.domain.issue.repository import IssueRepository


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
