from domains.research.models import AnalysisRequest, AnalysisResult
from domains.research.orm import AnalysisORM
from domains.research.repository import AnalysisRepository
from domains.research.service import AnalysisService
from domains.research.models import AnalysisRequest as LegacyAnalysisRequest
from domains.research.models import AnalysisResult as LegacyAnalysisResult
from domains.research.orm import AnalysisORM as LegacyAnalysisORM
from domains.research.repository import AnalysisRepository as LegacyAnalysisRepository
from domains.research.service import AnalysisService as LegacyAnalysisService


def test_root_analysis_domain_imports_are_available():
    assert AnalysisRequest is not None
    assert AnalysisResult is not None
    assert AnalysisORM is not None
    assert AnalysisRepository is not None
    assert AnalysisService is not None


def test_legacy_analysis_domain_imports_still_resolve():
    assert LegacyAnalysisRequest.__name__ == AnalysisRequest.__name__
    assert LegacyAnalysisResult.__name__ == AnalysisResult.__name__
    assert LegacyAnalysisORM.__name__ == AnalysisORM.__name__
    assert LegacyAnalysisRepository.__name__ == AnalysisRepository.__name__
    assert LegacyAnalysisService.__name__ == AnalysisService.__name__
