from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from domains.ai_actions.models import AgentAction
from domains.ai_actions.orm import AgentActionORM
from shared.utils.serialization import from_json_text, to_json_text


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class AgentActionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, action: AgentAction) -> AgentActionORM:
        row = AgentActionORM(
            id=action.id,
            task_type=action.task_type,
            actor_type=action.actor_type,
            actor_runtime=action.actor_runtime,
            provider=action.provider,
            model=action.model,
            session_id=action.session_id,
            status=action.status,
            reason=action.reason,
            idempotency_key=action.idempotency_key,
            trace_id=action.trace_id,
            input_summary=action.input_summary,
            output_summary=action.output_summary,
            input_refs_json=to_json_text(action.input_refs),
            output_refs_json=to_json_text(action.output_refs),
            tool_trace_json=to_json_text(action.tool_trace),
            memory_events_json=to_json_text(action.memory_events),
            delegation_trace_json=to_json_text(action.delegation_trace),
            usage_json=to_json_text(action.usage),
            error=action.error,
            started_at=_parse_dt(action.started_at),
            completed_at=_parse_dt(action.completed_at),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, action_id: str) -> AgentActionORM | None:
        return self.db.get(AgentActionORM, action_id)

    def get_by_idempotency_key(self, idempotency_key: str) -> AgentActionORM | None:
        return self.db.query(AgentActionORM).filter(AgentActionORM.idempotency_key == idempotency_key).first()

    def list_recent(self, limit: int = 20) -> list[AgentActionORM]:
        return self.db.query(AgentActionORM).order_by(AgentActionORM.created_at.desc()).limit(limit).all()

    def to_model(self, row: AgentActionORM) -> AgentAction:
        return AgentAction(
            id=row.id,
            task_type=row.task_type,
            actor_type=row.actor_type,
            actor_runtime=row.actor_runtime,
            provider=row.provider,
            model=row.model,
            session_id=row.session_id,
            status=row.status,
            reason=row.reason,
            idempotency_key=row.idempotency_key,
            trace_id=row.trace_id,
            input_summary=row.input_summary,
            output_summary=row.output_summary,
            input_refs=from_json_text(row.input_refs_json, {}),
            output_refs=from_json_text(row.output_refs_json, {}),
            tool_trace=from_json_text(row.tool_trace_json, []),
            memory_events=from_json_text(row.memory_events_json, []),
            delegation_trace=from_json_text(row.delegation_trace_json, []),
            usage=from_json_text(row.usage_json, {}),
            error=row.error,
            started_at=row.started_at.isoformat() if row.started_at else None,
            completed_at=row.completed_at.isoformat() if row.completed_at else None,
            created_at=row.created_at.isoformat(),
        )
