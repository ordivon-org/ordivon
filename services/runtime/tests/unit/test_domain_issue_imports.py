from domains.journal.issue_models import Issue
from domains.journal.issue_orm import IssueORM
from domains.journal.issue_repository import IssueRepository
from domains.journal.issue_models import Issue as LegacyIssue
from domains.journal.issue_orm import IssueORM as LegacyIssueORM
from domains.journal.issue_repository import IssueRepository as LegacyIssueRepository


def test_root_issue_imports_are_available():
    assert Issue is not None
    assert IssueORM is not None
    assert IssueRepository is not None


def test_legacy_issue_imports_still_resolve():
    assert LegacyIssue.__name__ == Issue.__name__
    assert LegacyIssueORM.__name__ == IssueORM.__name__
    assert LegacyIssueRepository.__name__ == IssueRepository.__name__
