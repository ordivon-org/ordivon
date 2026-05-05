import pytest

from domains.execution_records.models import ExecutionReceipt, ExecutionRequest
from domains.strategy.outcome_models import OutcomeSnapshot
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.task_run import TaskRun
from governance_engine.decision import (
    GovernanceActor,
    GovernanceDecision,
    GovernanceEvidence,
    GovernanceScope,
)
from intelligence.models.mock_provider import MockReasoningProvider
from intelligence.runtime.base import AgentRuntime
from intelligence.runtime.policy import MemoryPolicy
from intelligence.tasks.hermes import build_analysis_task
from knowledge.feedback import KnowledgeFeedbackPacket, KnowledgeHint
from orchestrator.context.context_builder import AnalysisContext
from orchestrator.context.governance_context import GovernanceContext
from orchestrator.context.market_context import MarketContext
from orchestrator.context.memory_context import MemoryContext
from orchestrator.context.portfolio_context import PortfolioContext
from orchestrator.context.query_context import QueryContext
from shared.enums.domain import OutcomeState
from state.trace.models import TraceLink


def test_governance_decision_freezes_actor_scope_and_evidence():
    decision = GovernanceDecision(
        decision="execute",
        reasons=["policy passed"],
        source="governance_engine.risk_engine",
        actor=GovernanceActor(actor_id="risk_engine.default", actor_type="system"),
        scope=GovernanceScope(scope_type="workflow", scope_id="analyze"),
        evidence=(GovernanceEvidence(object_type="policy", object_id="policy_default"),),
    )

    payload = decision.to_payload()

    assert payload["actor"]["actor_id"] == "risk_engine.default"
    assert payload["scope"]["scope_type"] == "workflow"
    assert payload["evidence"][0]["object_id"] == "policy_default"


def test_execution_request_and_receipt_validate_core_contract():
    request = ExecutionRequest(
        action_id="recommendation_generate",
        family="recommendation",
        side_effect_level="moderate",
        actor="workflow.analyze",
        context="recommendation_step",
        reason="generate recommendation",
        idempotency_key="request-1",
    )
    receipt = ExecutionReceipt(
        request_id=request.id,
        action_id=request.action_id,
        status="succeeded",
    )

    assert request.is_terminal is False
    assert receipt.is_success is True

    with pytest.raises(ValueError):
        ExecutionReceipt(
            request_id=request.id,
            action_id=request.action_id,
            status="failed",
        )


def test_outcome_snapshot_freezes_subject_semantics():
    outcome = OutcomeSnapshot(
        recommendation_id="reco_123",
        outcome_state=OutcomeState.IMPROVING,
        observed_metrics={"pnl_delta": 2.1},
        evidence_refs=["review:review_123"],
        trigger_reason="review_completion_backfill",
    )

    assert outcome.subject_type == "recommendation"
    assert outcome.subject_id == "reco_123"

    with pytest.raises(ValueError):
        OutcomeSnapshot(
            recommendation_id="reco_123",
            outcome_state=OutcomeState.IMPROVING,
            observed_metrics={},
            evidence_refs=[],
            trigger_reason="review_completion_backfill",
            subject_type="portfolio",
        )


def test_feedback_packet_stays_advisory_only():
    packet = KnowledgeFeedbackPacket(
        recommendation_id="reco_123",
        review_id="review_123",
        knowledge_entry_ids=("lesson_1",),
        intelligence_hints=(
            KnowledgeHint(
                target="intelligence",
                hint_type="memory_lesson",
                summary="Wait for confirmation",
                evidence_object_ids=("lesson_1",),
            ),
        ),
    )

    payload = packet.to_payload()

    assert packet.is_advisory_only is True
    assert payload["semantic_class"] == "derived_feedback_packet"
    assert payload["advisory_only"] is True


def test_trace_link_requires_real_relation_source():
    link = TraceLink(
        object_type="recommendation",
        object_id="reco_123",
        status="present",
        relation_source="workflow_run",
    )

    assert link.is_resolved is True

    with pytest.raises(ValueError):
        TraceLink(
            object_type="recommendation",
            object_id="reco_123",
            status="invented",
            relation_source="metadata",
        )


def test_task_run_can_be_derived_from_workflow_run_checkpoint_state():
    workflow_run = WorkflowRun(
        id="wfrun_123",
        workflow_name="analyze",
        status="running",
        request_summary="Analyze BTC",
        lineage_refs={
            "blocked_reason": "awaiting_approval",
            "wake_reason": "approval_granted",
            "resume_marker": "step:reason",
        },
    )

    task_run = TaskRun.from_workflow_run(workflow_run)

    assert task_run.status == "blocked"
    assert task_run.checkpoint.blocked_reason == "awaiting_approval"
    assert task_run.checkpoint.wake_reason == "approval_granted"


def test_mock_runtime_implements_agent_runtime_contract():
    runtime = MockReasoningProvider()
    ctx = AnalysisContext(
        query=QueryContext(query="Analyze BTC"),
        market=MarketContext(symbol="BTC/USDT", timeframe="1d"),
        portfolio=PortfolioContext(),
        memory=MemoryContext(),
        governance=GovernanceContext(active_policies=["default_risk_policy"]),
    )

    result = runtime.analyze(ctx)

    assert isinstance(runtime, AgentRuntime)
    assert result.metadata["runtime_name"] == "mock"
    assert result.metadata["runtime_adapter"].endswith("MockReasoningProvider")


def test_memory_policy_can_block_feedback_hint_injection():
    ctx = AnalysisContext(
        query=QueryContext(query="Analyze BTC"),
        market=MarketContext(symbol="BTC/USDT", timeframe="1d"),
        portfolio=PortfolioContext(),
        memory=MemoryContext(
            lessons=["lesson one"],
            related_reviews=["review_123"],
            policy=MemoryPolicy(allow_feedback_hints=False),
        ),
        governance=GovernanceContext(active_policies=["default_risk_policy"]),
    )

    task = build_analysis_task(ctx)

    assert task.input.memory_lessons == []
    assert task.input.related_reviews == []
