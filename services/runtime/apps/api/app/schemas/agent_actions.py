from pydantic import BaseModel

from apps.api.app.schemas.common import AgentActionSummaryResponse


class AgentActionListResponse(BaseModel):
    actions: list[AgentActionSummaryResponse]


class TraceabilityResponse(BaseModel):
    recommendation_id: str
    analysis_id: str | None = None
    agent_action_id: str | None = None
    report_path: str | None = None
    audit_event_ids: list[str]
