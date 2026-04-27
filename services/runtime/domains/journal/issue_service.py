from domains.journal.issue_models import Issue
from domains.journal.issue_repository import IssueRepository
from governance.audit.auditor import RiskAuditor


class IssueService:
    def __init__(self, repository: IssueRepository, auditor: RiskAuditor | None = None) -> None:
        self.repository = repository
        self.auditor = auditor

    def create(self, issue: Issue):
        return self.create_with_options(issue, emit_validation_issue_audit=True)

    def create_with_options(self, issue: Issue, *, emit_validation_issue_audit: bool):
        row = self.repository.create(issue)

        if self.auditor is not None and emit_validation_issue_audit:
            self.auditor.record_event(
                event_type="validation_issue_reported",
                payload={"severity": issue.severity, "area": issue.category, "description": issue.summary},
                entity_type="issue",
                entity_id=row.id,
                db=self.repository.db,
            )

        return row
