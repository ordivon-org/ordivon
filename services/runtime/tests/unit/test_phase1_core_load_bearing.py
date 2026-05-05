from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from capabilities.boundary import ActionContext
from domains.candidate_rules.service import CandidateRuleService
from domains.candidate_rules.repository import CandidateRuleRepository
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from domains.knowledge_feedback.feedback_record_repository import FeedbackRecordRepository
from domains.knowledge_feedback.feedback_record_service import FeedbackRecordService
from domains.knowledge_feedback.models import KnowledgeFeedbackPacketRecord
from domains.workflow_runs.checkpoint_state import CheckpointState
from domains.workflow_runs.models import WorkflowRun
from execution.adapters.recommendations import RecommendationExecutionAdapter
from execution.registry import (
    ExecutionAdapterContractError,
    ExecutionAdapterRegistry,
    build_default_execution_adapter_registry,
)
from governance_engine.approval import ApprovalRequiredError, HumanApprovalGate
from governance_engine.approval_repository import ApprovalRepository
from intelligence.context_builder import HintAwareContextBuilder
from intelligence.feedback import IntelligenceFeedbackContext
from intelligence.runtime.policy import MemoryPolicy
from knowledge.feedback import KnowledgeHint
from knowledge.retrieval import RecurringIssueSummary
from orchestrator.context.context_builder import AnalysisContext
from orchestrator.context.governance_context import GovernanceContext
from orchestrator.context.market_context import MarketContext
from orchestrator.context.memory_context import MemoryContext
from orchestrator.context.portfolio_context import PortfolioContext
from orchestrator.context.query_context import QueryContext
from state.db.base import Base


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, testing_session_local


def test_execution_adapter_registry_resolves_registered_families_and_validates_contract():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        registry = build_default_execution_adapter_registry()
        adapter = registry.resolve("recommendation", db)
        assert isinstance(adapter, RecommendationExecutionAdapter)

        class BadAdapter:
            family_name = "not-review"

        custom_registry = ExecutionAdapterRegistry()
        try:
            custom_registry.register("review", BadAdapter)
        except ExecutionAdapterContractError as exc:
            assert "family_name='review'" in str(exc)
        else:
            raise AssertionError("Expected ExecutionAdapterContractError")
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_execution_progress_records_and_heartbeat_persist():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        service = ExecutionRecordService(ExecutionRecordRepository(db))
        request_row = service.start_request(
            action_id="review_submit",
            action_context=ActionContext(
                actor="test-suite",
                context="phase1_progress",
                reason="phase1 progress test",
                idempotency_key="phase1-progress:review-submit",
            ),
            entity_type="review",
            entity_id="review_phase1_progress",
            payload={"review_id": "review_phase1_progress"},
        )

        started = service.record_progress(
            request_row.id,
            progress_state="started",
            progress_message="work started",
        )
        heartbeat = service.record_heartbeat(
            request_row.id,
            progress_message="still running",
        )
        rows = service.repository.list_progress_for_request(request_row.id)

        assert started.progress_state == "started"
        assert heartbeat.progress_state == "heartbeat"
        assert len(rows) == 2
        latest = service.repository.to_progress_model(rows[-1])
        assert latest.progress_state == "heartbeat"
        assert latest.progress_message == "still running"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_approval_gate_lifecycle_blocks_until_explicit_approval():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        gate = HumanApprovalGate(ApprovalRepository(db))
        pending = gate.request_approval(
            action_key="review.complete",
            entity_type="review",
            entity_id="review_phase1_approval",
            requested_by="workflow.analyze",
            reason="high consequence review completion",
        )
        assert pending.status == "pending"

        try:
            gate.ensure_approved(
                action_key="review.complete",
                entity_type="review",
                entity_id="review_phase1_approval",
                approval_id=pending.id,
                require_approval=True,
            )
        except ApprovalRequiredError as exc:
            assert exc.approval_id == pending.id
            assert "not approved" in exc.message
        else:
            raise AssertionError("Expected ApprovalRequiredError")

        approved = gate.approve(pending.id, actor="supervisor")
        ensured = gate.ensure_approved(
            action_key="review.complete",
            entity_type="review",
            entity_id="review_phase1_approval",
            approval_id=approved.id,
            require_approval=True,
        )
        assert ensured is not None
        assert ensured.status == "approved"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_hint_aware_context_builder_respects_memory_policy(monkeypatch):
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        ctx = AnalysisContext(
            query=QueryContext(query="Analyze BTC"),
            market=MarketContext(symbol="BTC-USDT", timeframe="1h"),
            portfolio=PortfolioContext(),
            memory=MemoryContext(
                policy=MemoryPolicy(
                    allow_transient_context=True,
                    allow_persisted_memory=False,
                    allow_feedback_hints=False,
                    forbid_state_truth_write=True,
                )
            ),
            governance=GovernanceContext(active_policies=["forbidden_symbols_policy"]),
        )

        monkeypatch.setattr(
            "intelligence.feedback.IntelligenceFeedbackReader.read_for_symbol",
            lambda self, symbol, limit=3: IntelligenceFeedbackContext(
                memory_lessons=("Wait for confirmation",),
                related_reviews=("review_1",),
            ),
        )

        result = HintAwareContextBuilder(db).enrich(ctx, symbol="BTC-USDT")

        assert result.hint_status == "available"
        assert result.memory_lesson_count == 1
        assert result.related_review_count == 1
        assert result.context.memory.lessons == []
        assert result.context.memory.related_reviews == []
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_feedback_record_deduplicates_and_candidate_rule_starts_as_draft():
    engine, testing_session_local = _make_db()
    db = testing_session_local()
    try:
        packet = KnowledgeFeedbackPacketRecord(
            id="kfpkt_phase1",
            recommendation_id="reco_phase1",
            review_id="review_phase1",
            knowledge_entry_ids=("lesson_1", "lesson_2"),
            governance_hints=(
                KnowledgeHint(
                    target="governance",
                    hint_type="caution",
                    summary="Wait for confirmation",
                    evidence_object_ids=("lesson_1",),
                ),
            ),
            intelligence_hints=(
                KnowledgeHint(
                    target="analysis.generate",
                    hint_type="lesson",
                    summary="Wait for confirmation",
                    evidence_object_ids=("lesson_1",),
                ),
            ),
        )
        feedback_service = FeedbackRecordService(FeedbackRecordRepository(db))
        first = feedback_service.record_consumption(
            packet,
            consumer_type="governance",
            subject_key="BTC-USDT",
            consumed_hint_count=1,
        )
        second = feedback_service.record_consumption(
            packet,
            consumer_type="governance",
            subject_key="BTC-USDT",
            consumed_hint_count=1,
        )
        rows = FeedbackRecordRepository(db).list_for_recommendation("reco_phase1")

        assert first.id == second.id
        assert len(rows) == 1

        recurring_issue = RecurringIssueSummary(
            issue_key="wait_for_confirmation",
            occurrence_count=2,
            sample_narratives=("Wait for confirmation", "Wait for confirmation candle"),
            recommendation_ids=("reco_phase1",),
            review_ids=("review_phase1",),
            knowledge_entry_ids=("lesson_1", "lesson_2"),
        )
        repository = CandidateRuleRepository(db)
        candidate_row = CandidateRuleService(repository).create_from_recurring_issue(recurring_issue)
        candidate = repository.to_model(candidate_row)
        assert candidate.issue_key == "wait_for_confirmation"
        assert candidate.status == "draft"
        assert candidate.recommendation_ids == ("reco_phase1",)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_checkpoint_state_round_trips_through_workflow_run_lineage_refs():
    checkpoint = CheckpointState(
        blocked_reason="approval_pending",
        wake_reason="human_approval_granted",
        resume_marker="resume:review.complete",
    )
    lineage_refs = checkpoint.to_lineage_refs({"workflow": "analyze"})
    run = WorkflowRun(
        id="wfrun_phase1",
        workflow_name="analyze",
        status="blocked",
        request_summary="Analyze BTC",
        lineage_refs=lineage_refs,
    )

    round_tripped = CheckpointState.from_workflow_run(run)

    assert round_tripped.blocked_reason == "approval_pending"
    assert round_tripped.wake_reason == "human_approval_granted"
    assert round_tripped.resume_marker == "resume:review.complete"
