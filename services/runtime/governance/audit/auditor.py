import json
from pathlib import Path

from governance.audit.models import AuditEvent
from governance.audit.repository import AuditEventRepository
from shared.config.settings import settings
from shared.logging.logger import get_logger
from shared.time.clock import utc_now
from sqlalchemy.orm import Session

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
        db: Session | None = None,
    ) -> None:
        if db is None:
            raise ValueError("RiskAuditor.record_event requires a db Session argument.")
        
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

        path = self.log_dir / "audit.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

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
        # Do not db.commit() here! Handled by caller to ensure atomic boundary.

        logger.info("Audit event recorded: %s", event_type)
