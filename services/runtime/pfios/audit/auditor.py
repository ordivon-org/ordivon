import json
from pathlib import Path

from pfios.core.config.settings import settings
from pfios.core.logging.logger import get_logger
from pfios.core.db.session import SessionLocal
from pfios.core.utils.time import utc_now
from pfios.domain.audit.models import AuditEvent
from pfios.domain.audit.repository import AuditEventRepository

logger = get_logger(__name__)


class RiskAuditor:
    def __init__(self) -> None:
        self.log_dir = Path(settings.audit_log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def record_event(
        self,
        event_type: str,
        payload: dict,
        entity_type: str | None = None,
        entity_id: str | None = None,
        analysis_id: str | None = None,
        recommendation_id: str | None = None,
        outcome_snapshot_id: str | None = None,
        review_id: str | None = None,
    ) -> None:
        record = {
            "ts": utc_now().isoformat(),
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "analysis_id": analysis_id,
            "recommendation_id": recommendation_id,
            "outcome_snapshot_id": outcome_snapshot_id,
            "review_id": review_id,
            "payload": payload,
        }

        # JSONL raw log
        path = self.log_dir / "audit.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Structured DB log
        db = SessionLocal()
        try:
            repo = AuditEventRepository(db)
            repo.create(
                AuditEvent(
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    analysis_id=analysis_id,
                    recommendation_id=recommendation_id,
                    outcome_snapshot_id=outcome_snapshot_id,
                    review_id=review_id,
                    payload=payload,
                )
            )
        finally:
            db.close()

        logger.info("Audit event recorded: %s", event_type)
