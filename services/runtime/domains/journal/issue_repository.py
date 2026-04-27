from sqlalchemy.orm import Session

from domains.journal.issue_models import Issue
from domains.journal.issue_orm import IssueORM
from shared.utils.serialization import from_json_text, to_json_text


class IssueRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, issue: Issue) -> IssueORM:
        row = IssueORM(
            id=issue.id,
            title=issue.title,
            summary=issue.summary,
            severity=issue.severity,
            category=issue.category,
            status=issue.status,
            source_type=issue.source_type,
            source_id=issue.source_id,
            detail_json=to_json_text(issue.detail),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def list_open(self) -> list[IssueORM]:
        return self.db.query(IssueORM).filter(IssueORM.status == "open").order_by(IssueORM.created_at.desc()).all()

    def to_model(self, row: IssueORM) -> Issue:
        return Issue(
            id=row.id,
            title=row.title,
            summary=row.summary,
            severity=row.severity,
            category=row.category,
            status=row.status,
            source_type=row.source_type,
            source_id=row.source_id,
            detail=from_json_text(row.detail_json, {}),
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
            resolved_at=row.resolved_at.isoformat() if row.resolved_at else None,
        )
