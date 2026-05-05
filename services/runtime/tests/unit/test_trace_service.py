from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from domains.ai_actions.models import AgentAction
from domains.ai_actions.repository import AgentActionRepository
from domains.execution_records.models import ExecutionReceipt, ExecutionRequest
from domains.execution_records.repository import ExecutionRecordRepository
from domains.intelligence_runs.models import IntelligenceRun
from domains.intelligence_runs.repository import IntelligenceRunRepository
from domains.knowledge_feedback.models import KnowledgeFeedbackPacketRecord
from domains.knowledge_feedback.repository import KnowledgeFeedbackPacketRepository
from domains.journal.models import Review
from domains.journal.repository import ReviewRepository
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from governance_engine.audit.auditor import RiskAuditor
from knowledge.feedback import KnowledgeHint
from state.db.base import Base
from state.trace import TraceService
from shared.enums.domain import ReviewStatus


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def test_trace_workflow_run_prefers_direct_relations_over_metadata():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)
        workflow_repo = WorkflowRunRepository(db)
        intelligence_repo = IntelligenceRunRepository(db)
        action_repo = AgentActionRepository(db)
        execution_repo = ExecutionRecordRepository(db)

        analysis = AnalysisResult(
            id="analysis_123",
            query="Analyze BTC",
            symbol="BTC/USDT",
            metadata={
                "intelligence_run_id": "irun_missing",
                "agent_action_id": "act_missing",
                "execution_request_id": "exreq_missing",
                "execution_receipt_id": "exrcpt_missing",
                "document_path": "wiki/reports/analysis_123.md",
            },
        )
        analysis_repo.create(analysis)

        recommendation = Recommendation(
            id="reco_123",
            analysis_id=analysis.id,
            title="Adopt BTC watch",
            summary="Watch BTC",
        )
        recommendation_repo.create(recommendation)

        intelligence_repo.create(
            IntelligenceRun(
                id="irun_real",
                task_type="analysis.generate",
                task_id="task_123",
                idempotency_key="irun-key-123",
                status="completed",
                reason="analyze",
                actor="workflow.analyze",
                context="reason_step",
                input_summary="Analyze BTC",
                output_summary="summary",
            )
        )
        action_repo.create(
            AgentAction(
                id="act_real",
                task_type="analysis.generate",
                reason="analyze",
                idempotency_key="action-key-123",
                input_summary="Analyze BTC",
                output_summary="summary",
            )
        )
        execution_repo.create_request(
            ExecutionRequest(
                id="exreq_real",
                action_id="analysis_report_write",
                family="artifact_write",
                side_effect_level="moderate",
                status="succeeded",
                actor="workflow.analyze",
                context="write_wiki_step",
                reason="write report",
                idempotency_key="exreq-key-123",
                analysis_id=analysis.id,
                recommendation_id=recommendation.id,
            )
        )
        execution_repo.create_receipt(
            ExecutionReceipt(
                id="exrcpt_real",
                request_id="exreq_real",
                action_id="analysis_report_write",
                status="succeeded",
                result_ref="wiki/reports/analysis_123.md",
            )
        )
        workflow_repo.create(
            WorkflowRun(
                id="wfrun_123",
                workflow_name="analyze",
                status="completed",
                request_summary="Analyze BTC",
                analysis_id=analysis.id,
                recommendation_id=recommendation.id,
                intelligence_run_id="irun_real",
                agent_action_id="act_real",
                execution_request_id="exreq_real",
                execution_receipt_id="exrcpt_real",
            )
        )

        bundle = TraceService(db).trace_workflow_run("wfrun_123")

        assert bundle is not None
        assert bundle.intelligence_run.object_id == "irun_real"
        assert bundle.intelligence_run.status == "present"
        assert bundle.intelligence_run.relation_source == "workflow_run"
        assert bundle.agent_action.object_id == "act_real"
        assert bundle.agent_action.relation_source == "workflow_run"
        assert bundle.execution_request.object_id == "exreq_real"
        assert bundle.execution_request.relation_source == "workflow_run"
        assert bundle.execution_receipt.object_id == "exrcpt_real"
        assert bundle.execution_receipt.relation_source == "workflow_run"
        assert bundle.report_artifact.status == "present"
        assert bundle.report_artifact.relation_source == "analysis.metadata"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_trace_recommendation_marks_missing_metadata_relations_honestly():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)

        analysis_repo.create(
            AnalysisResult(
                id="analysis_456",
                query="Analyze ETH",
                symbol="ETH/USDT",
                metadata={
                    "agent_action_id": "act_missing",
                    "document_path": "wiki/reports/analysis_456.md",
                },
            )
        )
        recommendation_repo.create(
            Recommendation(
                id="reco_456",
                analysis_id="analysis_456",
                title="Review ETH",
                summary="Review ETH setup",
            )
        )

        bundle = TraceService(db).trace_recommendation("reco_456")

        assert bundle is not None
        assert bundle.workflow_run.status == "unlinked"
        assert bundle.agent_action.object_id == "act_missing"
        assert bundle.agent_action.status == "missing"
        assert bundle.agent_action.relation_source == "analysis.metadata"
        assert bundle.execution_request.status == "unlinked"
        assert bundle.execution_receipt.status == "unlinked"
        assert bundle.report_artifact.status == "present"
        assert bundle.report_artifact.detail["path"] == "wiki/reports/analysis_456.md"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_trace_review_resolves_review_execution_and_feedback_signal_from_real_objects():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)
        review_repo = ReviewRepository(db)
        execution_repo = ExecutionRecordRepository(db)
        packet_repo = KnowledgeFeedbackPacketRepository(db)
        auditor = RiskAuditor()

        analysis_repo.create(
            AnalysisResult(
                id="analysis_review_trace",
                query="Analyze BTC",
                symbol="BTC/USDT",
            )
        )
        recommendation_repo.create(
            Recommendation(
                id="reco_review_trace",
                analysis_id="analysis_review_trace",
                title="Track BTC",
                summary="Track BTC thesis",
            )
        )
        review_row = review_repo.create(
            Review(
                id="review_trace_123",
                recommendation_id="reco_review_trace",
                status=ReviewStatus.COMPLETED,
                expected_outcome="BTC breakout",
            )
        )
        execution_repo.create_request(
            ExecutionRequest(
                id="exreq_review_trace",
                action_id="review_complete",
                family="review",
                side_effect_level="moderate",
                status="succeeded",
                actor="api.v1.reviews",
                context="complete_review",
                reason="complete review",
                idempotency_key="review-trace-key",
                recommendation_id="reco_review_trace",
                entity_type="review",
                entity_id=review_row.id,
            )
        )
        execution_repo.create_receipt(
            ExecutionReceipt(
                id="exrcpt_review_trace",
                request_id="exreq_review_trace",
                action_id="review_complete",
                status="succeeded",
                result_ref=review_row.id,
            )
        )
        review_repo.attach_complete_execution_refs(
            review_row.id,
            request_id="exreq_review_trace",
            receipt_id="exrcpt_review_trace",
        )
        packet_repo.create(
            KnowledgeFeedbackPacketRecord(
                id="kfpkt_review_trace",
                recommendation_id="reco_review_trace",
                review_id=review_row.id,
                knowledge_entry_ids=("lesson_a",),
                governance_hints=(
                    KnowledgeHint(
                        target="governance",
                        hint_type="caution",
                        summary="Use confirmation",
                        evidence_object_ids=("lesson_a",),
                    ),
                ),
                intelligence_hints=(
                    KnowledgeHint(
                        target="analysis.generate",
                        hint_type="lesson",
                        summary="Use confirmation",
                        evidence_object_ids=("lesson_a",),
                    ),
                ),
            )
        )
        review_repo.attach_knowledge_feedback_packet(
            review_row.id,
            packet_id="kfpkt_review_trace",
        )
        auditor.record_event(
            "review_completed",
            {
                "execution_request_id": "exreq_review_trace",
                "execution_receipt_id": "exrcpt_review_trace",
            },
            entity_type="review",
            entity_id=review_row.id,
            review_id=review_row.id,
            recommendation_id="reco_review_trace",
            db=db,
        )
        auditor.record_event(
            "knowledge_feedback_prepared",
            {
                "knowledge_feedback_packet_id": "kfpkt_review_trace",
                "recommendation_id": "reco_review_trace",
                "knowledge_entry_ids": ["lesson_a"],
                "governance_hint_count": 1,
                "intelligence_hint_count": 1,
            },
            entity_type="knowledge_feedback",
            entity_id="kfpkt_review_trace",
            review_id=review_row.id,
            recommendation_id="reco_review_trace",
            db=db,
        )

        bundle = TraceService(db).trace_review(review_row.id)

        assert bundle is not None
        assert bundle.review.object_id == review_row.id
        assert bundle.review.status == "present"
        assert bundle.review_execution_request.object_id == "exreq_review_trace"
        assert bundle.review_execution_request.status == "present"
        assert bundle.review_execution_request.relation_source == "review.complete_execution_request_id"
        assert bundle.review_execution_receipt.object_id == "exrcpt_review_trace"
        assert bundle.review_execution_receipt.status == "present"
        assert bundle.review_execution_receipt.relation_source == "review.complete_execution_receipt_id"
        assert bundle.knowledge_feedback.status == "present"
        assert bundle.knowledge_feedback.detail["governance_hint_count"] == 1
        assert bundle.knowledge_feedback.relation_source == "review.knowledge_feedback_packet_id"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_trace_review_falls_back_to_audit_when_direct_refs_are_absent():
    engine, TestingSessionLocal = _make_db()
    db = TestingSessionLocal()
    try:
        analysis_repo = AnalysisRepository(db)
        recommendation_repo = RecommendationRepository(db)
        review_repo = ReviewRepository(db)
        execution_repo = ExecutionRecordRepository(db)
        auditor = RiskAuditor()

        analysis_repo.create(
            AnalysisResult(
                id="analysis_review_trace_fallback",
                query="Analyze BTC",
                symbol="BTC/USDT",
            )
        )
        recommendation_repo.create(
            Recommendation(
                id="reco_review_trace_fallback",
                analysis_id="analysis_review_trace_fallback",
                title="Track BTC",
                summary="Track BTC thesis",
            )
        )
        review_row = review_repo.create(
            Review(
                id="review_trace_fallback",
                recommendation_id="reco_review_trace_fallback",
                status=ReviewStatus.COMPLETED,
                expected_outcome="BTC breakout",
            )
        )
        execution_repo.create_request(
            ExecutionRequest(
                id="exreq_review_trace_fallback",
                action_id="review_complete",
                family="review",
                side_effect_level="moderate",
                status="succeeded",
                actor="api.v1.reviews",
                context="complete_review",
                reason="complete review",
                idempotency_key="review-trace-fallback-key",
                recommendation_id="reco_review_trace_fallback",
                entity_type="review",
                entity_id=review_row.id,
            )
        )
        execution_repo.create_receipt(
            ExecutionReceipt(
                id="exrcpt_review_trace_fallback",
                request_id="exreq_review_trace_fallback",
                action_id="review_complete",
                status="succeeded",
                result_ref=review_row.id,
            )
        )
        auditor.record_event(
            "review_completed",
            {
                "execution_request_id": "exreq_review_trace_fallback",
                "execution_receipt_id": "exrcpt_review_trace_fallback",
            },
            entity_type="review",
            entity_id=review_row.id,
            review_id=review_row.id,
            recommendation_id="reco_review_trace_fallback",
            db=db,
        )

        bundle = TraceService(db).trace_review(review_row.id)

        assert bundle is not None
        assert bundle.review_execution_request.object_id == "exreq_review_trace_fallback"
        assert bundle.review_execution_request.relation_source == "audit_event.payload.review_execution"
        assert bundle.review_execution_receipt.object_id == "exrcpt_review_trace_fallback"
        assert bundle.review_execution_receipt.relation_source == "audit_event.payload.review_execution"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
