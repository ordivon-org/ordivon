from datetime import datetime
from sqlalchemy.orm import Session

from pfios.domain.recommendation.models import Recommendation
from pfios.domain.recommendation.orm import RecommendationORM
from pfios.domain.common.enums import RecommendationStatus
from pfios.core.utils.serialization import to_json_text, from_json_text


class RecommendationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, recommendation: Recommendation) -> RecommendationORM:
        row = RecommendationORM(
            id=recommendation.id,
            analysis_id=recommendation.analysis_id,
            title=recommendation.title,
            summary=recommendation.summary,
            rationale=recommendation.rationale,
            expected_outcome=recommendation.expected_outcome,
            outcome_metric_type=recommendation.outcome_metric_type,
            outcome_metric_config_json=to_json_text(recommendation.outcome_metric_config),
            confidence=recommendation.confidence,
            priority=recommendation.priority,
            owner=recommendation.owner,
            status=recommendation.status.value,
            decision=recommendation.decision,
            decision_reason=recommendation.decision_reason,
            review_required=recommendation.review_required,
            latest_outcome_snapshot_id=recommendation.latest_outcome_snapshot_id,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get(self, recommendation_id: str) -> RecommendationORM | None:
        return self.db.get(RecommendationORM, recommendation_id)

    def list_recent(self, limit: int = 20) -> list[RecommendationORM]:
        return (
            self.db.query(RecommendationORM)
            .order_by(RecommendationORM.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_by_status(self, status: RecommendationStatus) -> list[RecommendationORM]:
        return (
            self.db.query(RecommendationORM)
            .filter(RecommendationORM.status == status.value)
            .order_by(RecommendationORM.created_at.desc())
            .all()
        )

    def update_status(
        self,
        recommendation_id: str,
        status: RecommendationStatus,
        latest_outcome_snapshot_id: str | None = None,
    ) -> RecommendationORM | None:
        row = self.get(recommendation_id)
        if row is None:
            return None
        row.status = status.value
        if latest_outcome_snapshot_id is not None:
            row.latest_outcome_snapshot_id = latest_outcome_snapshot_id
        self.db.commit()
        self.db.refresh(row)
        return row

    def to_model(self, row: RecommendationORM) -> Recommendation:
        return Recommendation(
            id=row.id,
            analysis_id=row.analysis_id,
            title=row.title,
            summary=row.summary,
            rationale=row.rationale,
            expected_outcome=row.expected_outcome,
            outcome_metric_type=row.outcome_metric_type,
            outcome_metric_config=from_json_text(row.outcome_metric_config_json, {}),
            confidence=row.confidence,
            priority=row.priority,
            owner=row.owner,
            status=RecommendationStatus(row.status),
            decision=row.decision,
            decision_reason=row.decision_reason,
            review_required=row.review_required,
            review_due_at=row.review_due_at.isoformat() if row.review_due_at else None,
            due_at=row.due_at.isoformat() if row.due_at else None,
            expires_at=row.expires_at.isoformat() if row.expires_at else None,
            adopted_at=row.adopted_at.isoformat() if row.adopted_at else None,
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
            latest_outcome_snapshot_id=row.latest_outcome_snapshot_id,
            created_at=row.created_at.isoformat(),
            updated_at=row.updated_at.isoformat(),
        )
