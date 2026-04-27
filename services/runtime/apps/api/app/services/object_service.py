"""Compatibility service facade for report listing."""

from capabilities.reports import ReportCapability


class ObjectService:
    _capability = ReportCapability()

    @classmethod
    def get_recent_reports(cls, limit: int = 10):
        from state.db.session import SessionLocal
        from domains.research.repository import AnalysisRepository
        from domains.research.service import AnalysisService

        db = SessionLocal()
        try:
            service = AnalysisService(AnalysisRepository(db))
            return cls._capability.list_latest(service, limit=limit)
        finally:
            db.close()
