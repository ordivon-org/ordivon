from pfios.domain.usage.models import UsageSnapshot
from pfios.domain.usage.repository import UsageSnapshotRepository


class UsageService:
    def __init__(self, repository: UsageSnapshotRepository) -> None:
        self.repository = repository

    def create(self, snapshot: UsageSnapshot):
        return self.repository.create(snapshot)

    def list_recent(self, limit: int = 30):
        return self.repository.list_recent(limit=limit)
