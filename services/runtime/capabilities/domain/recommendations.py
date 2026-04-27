from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from capabilities.boundary import ActionContext, require_action_context
from capabilities.contracts import RecommendationResult
from domains.research.repository import AnalysisRepository
from domains.strategy.outcome_repository import OutcomeRepository
from execution.adapters import RecommendationExecutionAdapter
from governance.audit.auditor import RiskAuditor
from governance.decision import recommendation_governance_view
from governance.policy_source import GovernancePolicySource
from knowledge.extraction import LessonExtractionService
from shared.enums.domain import RecommendationStatus

if TYPE_CHECKING:
    from domains.strategy.service import RecommendationService


class RecommendationCapability:
    """Domain capability for recommendation object reads and lifecycle transitions."""

    abstraction_type = "domain"

    def list_recent(self, service: RecommendationService, limit: int = 10) -> list[RecommendationResult]:
        rows = service.list_recent(limit=limit)
        return [self._row_to_response(service, row) for row in rows]

    def get_by_id(self, service: RecommendationService, recommendation_id: str) -> RecommendationResult:
        model = service.get_model(recommendation_id)
        return self._row_to_response(service, model)

    def update_status(
        self,
        service: RecommendationService,
        recommendation_id: str,
        lifecycle_status: str,
        action_context: ActionContext | None,
    ) -> dict[str, Any]:
        context = require_action_context("recommendation status update", action_context)
        target = RecommendationStatus(lifecycle_status)
        adapter = RecommendationExecutionAdapter(service.repository.db, auditor=RiskAuditor())
        result = adapter.update_status(
            service=service,
            recommendation_id=recommendation_id,
            target_status=target,
            action_context=context,
        )

        return {
            "status": "success",
            "recommendation_id": recommendation_id,
            "lifecycle_status": lifecycle_status,
            "execution_request_id": result.execution_request_id,
            "execution_receipt_id": result.execution_receipt_id,
            "action_context": {
                "actor": context.actor,
                "context": context.context,
                "reason": context.reason,
                "idempotency_key": context.idempotency_key,
            },
        }

    def _row_to_response(self, service: RecommendationService, row: Any) -> RecommendationResult:
        status_str = row.status.value if hasattr(row.status, "value") else row.status
        inferred_symbol = self._extract_symbol(row)
        recorded_confidence = self._extract_confidence(row)
        analysis_metadata = self._analysis_metadata(service, getattr(row, "analysis_id", None))
        latest_outcome = self._latest_outcome(service, getattr(row, "id", None))
        knowledge_entries = self._knowledge_entries(service, getattr(row, "id", None))
        policy_snapshot = GovernancePolicySource().get_active_snapshot()

        metadata: dict[str, Any] = {
            "symbol_source": "recorded"
            if getattr(row, "symbol", None)
            else ("inferred_from_title" if inferred_symbol else "unavailable"),
            "outcome_snapshot_id": getattr(row, "latest_outcome_snapshot_id", None),
            "workflow_run_id": analysis_metadata.get("workflow_run_id"),
            "intelligence_run_id": analysis_metadata.get("intelligence_run_id"),
            "execution_receipt_id": analysis_metadata.get("execution_receipt_id"),
            "recommendation_generate_receipt_id": analysis_metadata.get("recommendation_generate_receipt_id"),
            "knowledge_hint_count": len(knowledge_entries),
            "knowledge_hint_summaries": [entry.narrative for entry in knowledge_entries[:2]],
            "governance_policy_set_id": analysis_metadata.get(
                "governance_policy_set_id", policy_snapshot.policy_set_id
            ),
            "governance_active_policy_ids": analysis_metadata.get(
                "governance_active_policy_ids", list(policy_snapshot.active_policy_ids)
            ),
            "governance_default_decision_rule_ids": analysis_metadata.get(
                "governance_default_decision_rule_ids", list(policy_snapshot.default_decision_rule_ids)
            ),
            "governance": recommendation_governance_view(
                decision=getattr(row, "decision", None),
                reason=getattr(row, "decision_reason", None),
                source=analysis_metadata.get("governance_source"),
                policy_set_id=analysis_metadata.get("governance_policy_set_id", policy_snapshot.policy_set_id),
                active_policy_ids=analysis_metadata.get(
                    "governance_active_policy_ids", list(policy_snapshot.active_policy_ids)
                ),
                default_decision_rule_ids=analysis_metadata.get(
                    "governance_default_decision_rule_ids", list(policy_snapshot.default_decision_rule_ids)
                ),
            ),
        }
        if recorded_confidence is None:
            metadata["confidence_status"] = "not_recorded"
        if latest_outcome is None:
            metadata["latest_outcome_reason"] = None
            metadata["latest_outcome_note"] = None
        else:
            metadata["latest_outcome_reason"] = latest_outcome.trigger_reason or None
            metadata["latest_outcome_note"] = latest_outcome.note
        metadata["knowledge_hint_status"] = "prepared" if knowledge_entries else "not_linked_yet"

        return RecommendationResult(
            id=row.id,
            status=status_str,
            created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
            analysis_id=row.analysis_id,
            symbol=inferred_symbol,
            action_summary=row.title or row.summary or None,
            confidence=recorded_confidence,
            decision=row.decision,
            decision_reason=row.decision_reason,
            adopted=status_str == RecommendationStatus.ADOPTED.value,
            review_status="pending" if row.review_required else None,
            outcome_status=latest_outcome.outcome_state.value if latest_outcome else None,
            metadata=metadata,
        )

    def _analysis_metadata(self, service: RecommendationService, analysis_id: str | None) -> dict[str, Any]:
        if not analysis_id:
            return {}
        try:
            repository = AnalysisRepository(service.repository.db)
            row = repository.get(analysis_id)
        except Exception:
            return {}
        if row is None:
            return {}
        try:
            return repository.to_model(row).metadata
        except Exception:
            return {}

    def _latest_outcome(self, service: RecommendationService, recommendation_id: str | None):
        if not recommendation_id:
            return None
        try:
            repository = OutcomeRepository(service.repository.db)
            rows = repository.list_for_recommendation(recommendation_id)
        except Exception:
            return None
        if not rows:
            return None
        try:
            return repository.to_model(rows[0])
        except Exception:
            return None

    def _knowledge_entries(self, service: RecommendationService, recommendation_id: str | None):
        if not recommendation_id:
            return []
        try:
            return LessonExtractionService(service.repository.db).extract_for_recommendation(recommendation_id)
        except Exception:
            return []

    def _extract_symbol(self, row: Any) -> str | None:
        explicit_symbol = getattr(row, "symbol", None)
        if isinstance(explicit_symbol, str) and explicit_symbol:
            return explicit_symbol

        for raw in (getattr(row, "title", None), getattr(row, "summary", None), getattr(row, "expected_outcome", None)):
            symbol = self._parse_symbol(raw)
            if symbol:
                return symbol
        return None

    def _parse_symbol(self, value: Any) -> str | None:
        if not isinstance(value, str) or not value:
            return None

        contextual_match = re.search(
            r"\b(?:for|buy|sell|hold|exit|reduce|accumulate)\s+([A-Za-z]{2,10}(?:[-/][A-Za-z]{2,10})?)\b",
            value,
            re.IGNORECASE,
        )
        if contextual_match:
            return contextual_match.group(1).replace("/", "-").upper()

        tokens = value.replace("/", "-").replace("_", "-").split()
        for token in tokens:
            normalized = token.strip(",:;()[]{}").upper()
            if normalized.endswith("-USDT") or normalized.endswith("-USD"):
                return normalized
        return None

    def _extract_confidence(self, row: Any) -> float | None:
        confidence = getattr(row, "confidence", None)
        if confidence is None:
            return None
        try:
            parsed = float(confidence)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None
        return parsed
