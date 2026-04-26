from state.db.base import Base
from state.db.session import engine

# IMPORTANT:
# Import all ORM models here so SQLAlchemy metadata can discover them.
from domains.ai_actions.orm import AgentActionORM  # noqa: F401
from domains.candidate_rules.orm import CandidateRuleORM  # noqa: F401
from domains.decision_intake.orm import DecisionIntakeORM  # noqa: F401
from domains.execution_records.orm import ExecutionReceiptORM  # noqa: F401
from domains.execution_records.orm import ExecutionProgressRecordORM  # noqa: F401
from domains.execution_records.orm import ExecutionRequestORM  # noqa: F401
from domains.finance_outcome.orm import FinanceManualOutcomeORM  # noqa: F401
from domains.intelligence_runs.orm import IntelligenceRunORM  # noqa: F401
from domains.research.orm import AnalysisORM  # noqa: F401
from domains.workflow_runs.orm import WorkflowRunORM  # noqa: F401
from domains.journal.issue_orm import IssueORM  # noqa: F401
from domains.journal.lesson_orm import LessonORM  # noqa: F401
from domains.journal.orm import ReviewORM  # noqa: F401
from domains.knowledge_feedback.feedback_record_orm import FeedbackRecordORM  # noqa: F401
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM  # noqa: F401
from domains.strategy.orm import RecommendationORM  # noqa: F401
from domains.strategy.outcome_orm import OutcomeSnapshotORM  # noqa: F401
from governance.approval_orm import ApprovalRecordORM  # noqa: F401
from governance.audit.orm import AuditEventORM  # noqa: F401
from infra.scheduler.orm import ScheduledTriggerORM  # noqa: F401
from state.usage.orm import UsageSnapshotORM  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    # Run idempotent migrations for schema drift on existing databases.
    # Each migration checks IF NOT EXISTS before adding columns.
    from state.db.migrations.runner import run_migrations
    with engine.connect() as conn:
        run_migrations(conn)
