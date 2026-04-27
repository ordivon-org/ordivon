import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock, patch

from capabilities.boundary import ActionContext
from state.db.base import Base
from domains.research.models import AnalysisRequest, AnalysisResult
from domains.research.orm import AnalysisORM
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.strategy.orm import RecommendationORM
from orchestrator.runtime.engine import PFIOSOrchestrator
from orchestrator.contracts.workflow import WorkflowContext
from orchestrator.workflows.analyze import WriteWikiStep, AuditTrailStep, GenerateRecommendationStep
from knowledge.wiki.service import MarkdownWikiService

# Setup in-memory SQLite
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestAnalyzeTransaction:
    """
    Ensures the analyze workflow is atomic and wiki writing has compensation.
    """

    def test_workflow_atomicity_on_failure(self, db: Session):
        # 1. Setup
        orchestrator = PFIOSOrchestrator()
        request = AnalysisRequest(query="test", symbol="BTC", timeframe="1d")

        # Mock AuditTrailStep to fail
        with patch.object(AuditTrailStep, "execute", side_effect=Exception("Audit fail")):
            with pytest.raises(Exception, match="Audit fail"):
                orchestrator.execute_analyze(request, db=db)

        # 2. Verification
        # Since the orchestrator only commits at the very end,
        # a failure in the middle should mean NOTHING is committed.
        db.rollback()  # Ensure session state is clean for check
        assert db.query(AnalysisORM).count() == 0
        assert db.query(RecommendationORM).count() == 0

    def test_wiki_compensation_on_db_metadata_fail(self, db: Session):
        # 1. Setup
        # We need a context that has already passed through PersistAnalysisStep
        ctx = WorkflowContext(request=AnalysisRequest(query="test", symbol="BTC", timeframe="1d"), db=db)
        ctx.analysis_id = "ana_test_123"
        ctx.analysis = AnalysisResult(id="ana_test_123", thesis="test", summary="test")
        ctx.metadata["side_effect_contexts"] = {
            "write_report_document": ActionContext(
                actor="test-suite",
                context="write_wiki_step",
                reason="write report doc",
                idempotency_key="write-report-test",
            ),
            "update_analysis_metadata": ActionContext(
                actor="test-suite",
                context="write_wiki_step",
                reason="update analysis metadata",
                idempotency_key="update-metadata-test",
            ),
            "audit_report_write": ActionContext(
                actor="test-suite",
                context="write_wiki_step",
                reason="audit report write",
                idempotency_key="audit-report-test",
            ),
        }

        # Mock the wiki service to write a real (temp) file
        wiki_service = MarkdownWikiService(base_dir="test_wiki")
        step = WriteWikiStep()
        step.wiki_service = wiki_service

        # Mock AnalysisService.update_metadata to fail
        with patch(
            "orchestrator.workflows.analyze.AnalysisService.update_metadata", side_effect=Exception("DB update fail")
        ):
            with pytest.raises(Exception, match="DB update fail"):
                step.execute(ctx)

        # 2. Verification
        # Check if file was deleted
        sym = "BTC"
        expected_path = f"test_wiki/reports/analysis_{sym}_ana_test_123.md"
        assert not os.path.exists(expected_path)
        request_row = db.query(ExecutionRequestORM).one()
        receipt_row = db.query(ExecutionReceiptORM).one()
        assert request_row.action_id == "analysis_report_write"
        assert request_row.status == "failed"
        assert receipt_row.request_id == request_row.id
        assert receipt_row.status == "failed"
        assert receipt_row.error == "DB update fail"
        assert ctx.metadata["_workflow_recovery_detail"].action == "compensation"
        assert ctx.metadata["_workflow_recovery_detail"].detail["compensation_applied"] is True

        # Cleanup test dir if it exists
        if os.path.exists("test_wiki"):
            import shutil

            shutil.rmtree("test_wiki")

    def test_wiki_write_requires_action_context(self, db: Session):
        ctx = WorkflowContext(
            request=AnalysisRequest(query="test", symbol="BTC", timeframe="1d"),
            db=db,
        )
        ctx.analysis_id = "ana_test_123"
        ctx.analysis = AnalysisResult(id="ana_test_123", thesis="test", summary="test")

        step = WriteWikiStep()
        step.wiki_service = MarkdownWikiService(base_dir="test_wiki")

        with pytest.raises(ValueError, match="analysis report document write requires action context"):
            step.execute(ctx)

        if os.path.exists("test_wiki"):
            import shutil

            shutil.rmtree("test_wiki")

    def test_workflow_full_success_commits(self, db: Session):
        # 1. Setup
        orchestrator = PFIOSOrchestrator()
        request = AnalysisRequest(query="test", symbol="BTC", timeframe="1d")

        # 2. Action
        orchestrator.execute_analyze(request, db=db)

        # 3. Verification
        # Everything should be in DB now because commit happened at the end
        assert db.query(AnalysisORM).count() == 1
        assert db.query(RecommendationORM).count() == 1

    def test_recommendation_generation_failure_does_not_leave_completed_state(self, db: Session):
        orchestrator = PFIOSOrchestrator()
        request = AnalysisRequest(query="test", symbol="BTC", timeframe="1d")

        with patch.object(GenerateRecommendationStep, "execute", side_effect=Exception("recommendation failure")):
            with pytest.raises(Exception, match="recommendation failure"):
                orchestrator.execute_analyze(request, db=db)

        db.rollback()
        assert db.query(RecommendationORM).count() == 0
