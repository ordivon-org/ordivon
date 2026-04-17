from pfios.domain.analysis.models import AnalysisResult
from pfios.domain.analysis.repository import AnalysisRepository
from pfios.domain.common.errors import DomainNotFound


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

    def list_recent(self, limit: int = 20):
        return self.repository.list_recent(limit=limit)
