from governance_engine.audit.repository import AuditEventRepository


class AuditService:
    def __init__(self, repository: AuditEventRepository) -> None:
        self.repository = repository

    def list_recent(self, limit: int = 100):
        return self.repository.list_recent(limit=limit)
