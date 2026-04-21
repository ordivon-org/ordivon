from domains.ai_actions.models import AgentAction
from domains.ai_actions.repository import AgentActionRepository


class AgentActionService:
    def __init__(self, repository: AgentActionRepository) -> None:
        self.repository = repository

    def create(self, action: AgentAction):
        existing = self.repository.get_by_idempotency_key(action.idempotency_key)
        if existing is not None:
            return existing
        return self.repository.create(action)

    def get_model(self, action_id: str) -> AgentAction | None:
        row = self.repository.get(action_id)
        if row is None:
            return None
        return self.repository.to_model(row)

    def list_recent(self, limit: int = 20) -> list[AgentAction]:
        return [self.repository.to_model(row) for row in self.repository.list_recent(limit=limit)]
