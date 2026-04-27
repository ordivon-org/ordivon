import pytest
from unittest.mock import MagicMock, patch
from dataclasses import is_dataclass, asdict
from datetime import datetime

from capabilities.boundary import ActionContext
from capabilities.contracts import (
    AnalyzeResult,
    RecommendationResult,
    ReviewResult,
    ReviewSkeletonResult,
    ValidationSummaryResult,
    UsageSyncResult,
    ReportResult,
    DashboardResult,
)
from capabilities.analyze import AnalyzeCapability, AnalyzeCapabilityInput
from capabilities.recommendations import RecommendationCapability
from capabilities.reviews import ReviewCapability
from capabilities.validation import ValidationCapability
from capabilities.reports import ReportCapability
from capabilities.dashboard import DashboardCapability

from shared.enums.domain import RecommendationStatus, ReviewStatus


def make_action_context() -> ActionContext:
    return ActionContext(
        actor="test-suite",
        context="integration-test",
        reason="exercise side-effect boundary",
        idempotency_key="test-suite-key",
    )


class TestCapabilityContracts:
    """
    Contract tests to ensure Capability layer returns strictly typed dataclasses
    or dictionaries that perfectly match the schema, without placeholders.
    """

    # --- Analyze Capability ---
    @pytest.mark.anyio
    async def test_analyze_capability_returns_strict_contract(self):
        orchestrator = MagicMock()
        orchestrator.execute_analyze.return_value = {
            "summary": "Market is bullish",
            "risks": ["Volatility"],
            "suggested_actions": ["Buy"],
            "analysis_id": "ana_123",
            "recommendation_id": "reco_456",
            "governance": {"decision": "execute", "source": "test-suite", "reasons": []},
        }

        cap = AnalyzeCapability(orchestrator=orchestrator)
        result_dict = await cap.analyze_and_suggest(AnalyzeCapabilityInput(query="test", symbols=["BTC"]))

        # Verify it can be mapped back to the contract or has all keys
        assert result_dict["status"] == "success"
        assert result_dict["decision"] == "execute"
        assert result_dict["analysis_id"] == "ana_123"
        assert result_dict["recommendation_id"] == "reco_456"
        assert isinstance(result_dict["risk_flags"], list)
        assert result_dict["metadata"]["symbol"] == "BTC"
        assert result_dict["metadata"]["governance_decision"] == "execute"

    # --- Recommendation Capability ---
    def test_recommendation_capability_conversion_is_honest(self):
        service = MagicMock()
        mock_row = MagicMock()
        mock_row.id = "reco_1"
        mock_row.status = RecommendationStatus.GENERATED
        mock_row.created_at = datetime(2024, 1, 1)
        mock_row.analysis_id = "ana_1"
        mock_row.title = "Buy BTC"
        mock_row.summary = "BULLISH"
        mock_row.confidence = 0.0
        mock_row.decision = None
        mock_row.decision_reason = None
        mock_row.review_required = True
        mock_row.latest_outcome_snapshot_id = None

        service.list_recent.return_value = [mock_row]

        cap = RecommendationCapability()
        results = cap.list_recent(service)

        assert len(results) == 1
        res = results[0]
        assert isinstance(res, RecommendationResult)
        assert res.id == "reco_1"
        assert res.symbol == "BTC"
        assert res.confidence is None
        assert res.decision_reason is None  # Honest None, not placeholder
        assert res.review_status == "pending"
        assert res.outcome_status is None
        assert res.metadata["governance"] is None

    # --- Review Capability ---
    def test_review_capability_skeleton_honest_none(self):
        cap = ReviewCapability()
        res = cap.generate_skeleton("rep_1", "reco_1")

        assert isinstance(res, ReviewSkeletonResult)
        assert res.id is None  # Honest None for draft
        assert res.status == "draft"
        assert res.recommendation_id == "reco_1"
        assert res.sections == [
            "expected_outcome",
            "actual_outcome",
            "deviation",
            "mistake_tags",
            "lessons",
            "new_rule_candidate",
        ]
        assert "sections" not in res.metadata

    def test_review_capability_submit_returns_contract(self):
        service = MagicMock()
        service.review_repository.db = MagicMock()
        adapter = MagicMock()
        registry = MagicMock()
        registry.resolve.return_value = adapter
        adapter_result = MagicMock()
        adapter_result.review_row = MagicMock()
        adapter_result.review_row.id = "rev_123"
        adapter_result.review_row.status = "submitted"
        adapter_result.review_row.recommendation_id = "reco_1"
        adapter_result.execution_request_id = "exreq_123"
        adapter_result.execution_receipt_id = "exrcpt_123"

        cap = ReviewCapability()
        with patch("capabilities.workflow.reviews.build_default_execution_adapter_registry", return_value=registry):
            adapter.submit.return_value = adapter_result
            res = cap.submit_review(
                service,
                {
                    "linked_recommendation_id": "reco_1",
                    "lessons": [{"lesson_text": "L1"}],
                },
                make_action_context(),
            )

        assert isinstance(res, ReviewResult)
        assert res.id == "rev_123"
        assert res.lessons_created == 1
        assert res.metadata["execution_request_id"] == "exreq_123"

    # --- Validation Capability ---
    def test_validation_capability_summary_contract(self):
        usage_service = MagicMock()
        issue_repo = MagicMock()
        usage_service.list_recent.return_value = []
        usage_service.get_aggregate_metrics.return_value = {
            "days_used": 5,
            "analysis_count": 10,
            "recommendations_count": 2,
            "open_p0_count": 0,
            "open_p1_count": 1,
            "go_no_go": "STABLE",
        }

        cap = ValidationCapability()
        res = cap.get_summary(usage_service, issue_repo)

        assert isinstance(res, ValidationSummaryResult)
        assert res.days_active == 5
        assert res.open_critical_issues == 1
        assert res.period_id is None

    def test_validation_capability_sync_contract(self):
        usage_service = MagicMock()
        mock_row = MagicMock()
        mock_row.id = "snap_1"
        mock_row.created_at = datetime(2024, 1, 1)
        usage_service.create.return_value = mock_row

        cap = ValidationCapability()
        res = cap.sync_usage(usage_service, make_action_context())

        assert isinstance(res, UsageSyncResult)
        assert res.snapshot_id == "snap_1"

    # --- Report Capability ---
    def test_report_capability_mapping_is_strict(self):
        service = MagicMock()
        mock_row = MagicMock()
        mock_row.id = "ana_1"
        mock_row.symbol = "ETH"
        mock_row.metadata = {"status": "generated", "document_path": "/path/to/doc.md"}
        mock_row.created_at = datetime(2024, 1, 1)
        mock_row.query = "Is ETH a buy?"

        service.list_recent.return_value = [mock_row]

        cap = ReportCapability()
        results = cap.list_latest(service)

        assert len(results) == 1
        res = results[0]
        assert isinstance(res, ReportResult)
        assert res.report_id == "ana_1"
        assert res.report_path == "/path/to/doc.md"
        assert res.status == "generated"
        assert res.metadata["query"] == "Is ETH a buy?"

    # --- Dashboard Capability ---
    def test_dashboard_capability_contract(self):
        service = MagicMock()
        service.get_aggregated_metrics.return_value = {
            "recommendation_stats": {"active": 5},
            "recent_outcomes": [{"state": "success"}],
            "pending_review_count": 2,
            "system_health": "good",
            "total_balance_estimate": 1000.5,
        }

        cap = DashboardCapability()
        res = cap.get_summary(service)

        assert isinstance(res, DashboardResult)
        assert res.recommendation_stats["active"] == 5
        assert res.total_balance_estimate == 1000.5

    def test_recommendation_status_update_requires_action_context(self):
        service = MagicMock()
        cap = RecommendationCapability()

        with pytest.raises(ValueError):
            cap.update_status(service, "reco_1", "adopted", None)
