from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.candidate_rules.models import CandidateRule
from domains.candidate_rules.orm import CandidateRuleORM
from shared.utils.serialization import from_json_text, to_json_text


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class CandidateRuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, rule: CandidateRule) -> CandidateRuleORM:
        row = CandidateRuleORM(
            id=rule.id,
            issue_key=rule.issue_key,
            summary=rule.summary,
            status=rule.status,
            recommendation_ids_json=to_json_text(list(rule.recommendation_ids)),
            review_ids_json=to_json_text(list(rule.review_ids)),
            lesson_ids_json=to_json_text(list(rule.lesson_ids)),
            knowledge_entry_ids_json=to_json_text(list(rule.knowledge_entry_ids)),
            source_refs_json=to_json_text(list(rule.source_refs)),
            created_at=_parse_dt(rule.created_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def find_by_lesson_id(self, lesson_id: str) -> CandidateRuleORM | None:
        """Check if a CandidateRule already exists for a given lesson (idempotency)."""
        return self.db.query(CandidateRuleORM).filter(CandidateRuleORM.lesson_ids_json.contains(lesson_id)).first()

    def list_all(self) -> list[CandidateRuleORM]:
        return self.db.query(CandidateRuleORM).order_by(CandidateRuleORM.created_at.desc()).all()

    def to_model(self, row: CandidateRuleORM) -> CandidateRule:
        return CandidateRule(
            id=row.id,
            issue_key=row.issue_key,
            summary=row.summary,
            status=row.status,
            recommendation_ids=tuple(from_json_text(row.recommendation_ids_json, [])),
            review_ids=tuple(from_json_text(row.review_ids_json, [])),
            lesson_ids=tuple(from_json_text(row.lesson_ids_json, [])),
            knowledge_entry_ids=tuple(from_json_text(row.knowledge_entry_ids_json, [])),
            source_refs=tuple(from_json_text(row.source_refs_json, [])),
            created_at=row.created_at.isoformat(),
        )
