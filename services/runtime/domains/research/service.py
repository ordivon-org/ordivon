from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from shared.errors.domain import DomainNotFound


class AnalysisService:
    def __init__(self, repository: AnalysisRepository) -> None:
        self.repository = repository

    def create(self, analysis: AnalysisResult):
        return self.repository.create(analysis)

    def get_model(self, analysis_id: str) -> AnalysisResult:
        row = self.repository.get(analysis_id)
        if row is None:
            raise DomainNotFound(f"Analysis not found: {analysis_id}")
        return self.repository.to_model(row)

    def list_recent(self, limit: int = 20) -> list[AnalysisResult]:
        rows = self.repository.list_recent(limit=limit)
        return [self.repository.to_model(row) for row in rows]

    def update_metadata(self, analysis_id: str, new_meta: dict):
        row = self.repository.update_metadata(analysis_id, new_meta)
        if row is None:
            raise DomainNotFound(f"Analysis not found: {analysis_id}")
        return self.repository.to_model(row)
