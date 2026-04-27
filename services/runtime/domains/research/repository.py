from sqlalchemy.orm import Session

from domains.research.models import AnalysisResult
from domains.research.orm import AnalysisORM
from shared.utils.serialization import from_json_text, to_json_text


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, result: AnalysisResult) -> AnalysisORM:
        row = AnalysisORM(
            id=result.id,
            query=result.query,
            symbol=result.symbol,
            timeframe=result.timeframe,
            summary=result.summary,
            thesis=result.thesis,
            risks_json=to_json_text(result.risks),
            suggested_actions_json=to_json_text(result.suggested_actions),
            metadata_json=to_json_text(result.metadata),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def get(self, analysis_id: str) -> AnalysisORM | None:
        return self.db.get(AnalysisORM, analysis_id)

    def update_metadata(self, analysis_id: str, new_meta: dict) -> AnalysisORM | None:
        row = self.get(analysis_id)
        if row:
            current_meta = from_json_text(row.metadata_json, {})
            current_meta.update(new_meta)
            row.metadata_json = to_json_text(current_meta)
            self.db.flush()
        return row

    def list_recent(self, limit: int = 20) -> list[AnalysisORM]:
        return self.db.query(AnalysisORM).order_by(AnalysisORM.created_at.desc()).limit(limit).all()

    def to_model(self, row: AnalysisORM) -> AnalysisResult:
        return AnalysisResult(
            id=row.id,
            query=row.query,
            symbol=row.symbol,
            timeframe=row.timeframe,
            summary=row.summary,
            thesis=row.thesis,
            risks=from_json_text(row.risks_json, []),
            suggested_actions=from_json_text(row.suggested_actions_json, []),
            metadata=from_json_text(row.metadata_json, {}),
            created_at=row.created_at.isoformat(),
        )
