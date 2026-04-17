from pfios.core.db.base import Base
from pfios.core.db.session import engine

# IMPORTANT:
# Import all ORM models here so SQLAlchemy metadata can discover them.
from pfios.domain.analysis.orm import AnalysisORM  # noqa: F401
from pfios.domain.recommendation.orm import RecommendationORM  # noqa: F401
from pfios.domain.outcome.orm import OutcomeSnapshotORM  # noqa: F401
from pfios.domain.review.orm import ReviewORM  # noqa: F401
from pfios.domain.audit.orm import AuditEventORM  # noqa: F401
from pfios.domain.usage.orm import UsageSnapshotORM  # noqa: F401
from pfios.domain.lessons.orm import LessonORM  # noqa: F401
from pfios.domain.issue.orm import IssueORM  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
