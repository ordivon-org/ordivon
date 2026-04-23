from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from domains.ai_actions.orm import AgentActionORM
from domains.execution_records.orm import ExecutionReceiptORM, ExecutionRequestORM
from domains.intelligence_runs.orm import IntelligenceRunORM
from domains.knowledge_feedback.orm import KnowledgeFeedbackPacketORM
from domains.journal.orm import ReviewORM
from domains.research.orm import AnalysisORM
from domains.strategy.orm import RecommendationORM
from domains.strategy.outcome_graph import OutcomeGraph
from domains.workflow_runs.orm import WorkflowRunORM
from governance.audit.orm import AuditEventORM
from shared.utils.serialization import from_json_text
from state.trace.models import TraceBundle, TraceReference


class TraceGraph:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.outcome_graph = OutcomeGraph(db)

    def trace_workflow_run(self, workflow_run_id: str) -> TraceBundle | None:
        run = self.db.get(WorkflowRunORM, workflow_run_id)
        if run is None:
            return None

        analysis = self._get_analysis(run.analysis_id)
        recommendation = self._get_recommendation(run.recommendation_id)
        analysis_meta = self._analysis_metadata(analysis)
        review = self._latest_review_for_recommendation(run.recommendation_id)
        review_execution_request, review_execution_receipt = self._review_execution_refs(
            review_id=review.id if review is not None else None,
            recommendation_id=run.recommendation_id,
        )

        intelligence_run = self._resolve_by_direct_or_metadata(
            object_type="intelligence_run",
            direct_id=run.intelligence_run_id,
            metadata_id=analysis_meta.get("intelligence_run_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_intelligence_run,
        )
        agent_action = self._resolve_by_direct_or_metadata(
            object_type="agent_action",
            direct_id=run.agent_action_id,
            metadata_id=analysis_meta.get("agent_action_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_agent_action,
        )
        execution_request = self._resolve_by_direct_or_metadata(
            object_type="execution_request",
            direct_id=run.execution_request_id,
            metadata_id=analysis_meta.get("execution_request_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_execution_request,
        )
        execution_receipt = self._resolve_by_direct_or_metadata(
            object_type="execution_receipt",
            direct_id=run.execution_receipt_id,
            metadata_id=analysis_meta.get("execution_receipt_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_execution_receipt,
        )

        return TraceBundle(
            root_type="workflow_run",
            root_id=workflow_run_id,
            analysis=self._present_or_missing("analysis", run.analysis_id, analysis, "workflow_run"),
            recommendation=self._present_or_missing(
                "recommendation",
                run.recommendation_id,
                recommendation,
                "workflow_run",
            ),
            review=self._trace_reference_for_row(
                "review",
                review.id if review is not None else None,
                review,
                "recommendation.latest_review",
            ),
            workflow_run=self._present_or_missing("workflow_run", run.id, run, "root"),
            intelligence_run=intelligence_run,
            agent_action=agent_action,
            execution_request=execution_request,
            execution_receipt=execution_receipt,
            review_execution_request=review_execution_request,
            review_execution_receipt=review_execution_receipt,
            latest_audit_events=self._audit_refs(
                analysis_id=run.analysis_id,
                recommendation_id=run.recommendation_id,
                review_id=review.id if review is not None else None,
            ),
            report_artifact=self._report_artifact_ref(analysis_meta),
            outcome=self._outcome_ref(recommendation),
            knowledge_feedback=self._knowledge_feedback_ref(
                review_id=review.id if review is not None else None,
                recommendation_id=run.recommendation_id,
            ),
        )

    def trace_recommendation(self, recommendation_id: str) -> TraceBundle | None:
        recommendation = self._get_recommendation(recommendation_id)
        if recommendation is None:
            return None

        analysis = self._get_analysis(recommendation.analysis_id)
        analysis_meta = self._analysis_metadata(analysis)
        workflow_run = self._workflow_run_for_recommendation(recommendation_id, recommendation.analysis_id)
        review = self._latest_review_for_recommendation(recommendation_id)
        review_execution_request, review_execution_receipt = self._review_execution_refs(
            review_id=review.id if review is not None else None,
            recommendation_id=recommendation.id,
        )

        intelligence_run = self._resolve_by_direct_or_metadata(
            object_type="intelligence_run",
            direct_id=workflow_run.intelligence_run_id if workflow_run else None,
            metadata_id=analysis_meta.get("intelligence_run_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_intelligence_run,
        )
        agent_action = self._resolve_by_direct_or_metadata(
            object_type="agent_action",
            direct_id=workflow_run.agent_action_id if workflow_run else None,
            metadata_id=analysis_meta.get("agent_action_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_agent_action,
        )
        execution_request = self._resolve_by_direct_or_metadata(
            object_type="execution_request",
            direct_id=workflow_run.execution_request_id if workflow_run else None,
            metadata_id=analysis_meta.get("execution_request_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_execution_request,
        )
        execution_receipt = self._resolve_by_direct_or_metadata(
            object_type="execution_receipt",
            direct_id=workflow_run.execution_receipt_id if workflow_run else None,
            metadata_id=analysis_meta.get("execution_receipt_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_execution_receipt,
        )

        return TraceBundle(
            root_type="recommendation",
            root_id=recommendation_id,
            analysis=self._present_or_missing(
                "analysis",
                recommendation.analysis_id,
                analysis,
                "recommendation.analysis_id",
            ),
            recommendation=self._present_or_missing("recommendation", recommendation.id, recommendation, "root"),
            review=self._trace_reference_for_row(
                "review",
                review.id if review is not None else None,
                review,
                "recommendation.latest_review",
            ),
            workflow_run=self._trace_reference_for_row(
                "workflow_run",
                workflow_run.id if workflow_run else None,
                workflow_run,
                "recommendation/workflow lookup",
            ),
            intelligence_run=intelligence_run,
            agent_action=agent_action,
            execution_request=execution_request,
            execution_receipt=execution_receipt,
            review_execution_request=review_execution_request,
            review_execution_receipt=review_execution_receipt,
            latest_audit_events=self._audit_refs(
                analysis_id=recommendation.analysis_id,
                recommendation_id=recommendation.id,
                review_id=review.id if review is not None else None,
            ),
            report_artifact=self._report_artifact_ref(analysis_meta),
            outcome=self._outcome_ref(recommendation),
            knowledge_feedback=self._knowledge_feedback_ref(
                review_id=review.id if review is not None else None,
                recommendation_id=recommendation.id,
            ),
        )

    def trace_review(self, review_id: str) -> TraceBundle | None:
        review = self._get_review(review_id)
        if review is None:
            return None

        recommendation = self._get_recommendation(review.recommendation_id)
        analysis_id = review.analysis_id or (recommendation.analysis_id if recommendation is not None else None)
        analysis = self._get_analysis(analysis_id)
        analysis_meta = self._analysis_metadata(analysis)
        workflow_run = None
        if review.recommendation_id or analysis_id:
            workflow_run = self._workflow_run_for_recommendation(review.recommendation_id or "", analysis_id)
        review_execution_request, review_execution_receipt = self._review_execution_refs(
            review_id=review.id,
            recommendation_id=review.recommendation_id,
        )

        intelligence_run = self._resolve_by_direct_or_metadata(
            object_type="intelligence_run",
            direct_id=workflow_run.intelligence_run_id if workflow_run else None,
            metadata_id=analysis_meta.get("intelligence_run_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_intelligence_run,
        )
        agent_action = self._resolve_by_direct_or_metadata(
            object_type="agent_action",
            direct_id=workflow_run.agent_action_id if workflow_run else None,
            metadata_id=analysis_meta.get("agent_action_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_agent_action,
        )
        execution_request = self._resolve_by_direct_or_metadata(
            object_type="execution_request",
            direct_id=workflow_run.execution_request_id if workflow_run else None,
            metadata_id=analysis_meta.get("execution_request_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_execution_request,
        )
        execution_receipt = self._resolve_by_direct_or_metadata(
            object_type="execution_receipt",
            direct_id=workflow_run.execution_receipt_id if workflow_run else None,
            metadata_id=analysis_meta.get("execution_receipt_id"),
            direct_source="workflow_run",
            metadata_source="analysis.metadata",
            loader=self._get_execution_receipt,
        )

        return TraceBundle(
            root_type="review",
            root_id=review_id,
            analysis=self._present_or_missing(
                "analysis",
                analysis_id,
                analysis,
                "review/recommendation.analysis_id",
            ),
            recommendation=self._present_or_missing(
                "recommendation",
                review.recommendation_id,
                recommendation,
                "review.recommendation_id",
            ),
            review=self._present_or_missing("review", review.id, review, "root"),
            workflow_run=self._trace_reference_for_row(
                "workflow_run",
                workflow_run.id if workflow_run else None,
                workflow_run,
                "review/recommendation.workflow lookup",
            ),
            intelligence_run=intelligence_run,
            agent_action=agent_action,
            execution_request=execution_request,
            execution_receipt=execution_receipt,
            review_execution_request=review_execution_request,
            review_execution_receipt=review_execution_receipt,
            latest_audit_events=self._audit_refs(
                analysis_id=analysis_id,
                recommendation_id=review.recommendation_id,
                review_id=review.id,
            ),
            report_artifact=self._report_artifact_ref(analysis_meta),
            outcome=self._outcome_ref(recommendation),
            knowledge_feedback=self._knowledge_feedback_ref(
                review_id=review.id,
                recommendation_id=review.recommendation_id,
            ),
        )

    def _analysis_metadata(self, analysis: AnalysisORM | None) -> dict[str, Any]:
        if analysis is None:
            return {}
        return from_json_text(analysis.metadata_json, {})

    def _resolve_by_direct_or_metadata(
        self,
        *,
        object_type: str,
        direct_id: str | None,
        metadata_id: str | None,
        direct_source: str,
        metadata_source: str,
        loader,
    ) -> TraceReference:
        if direct_id:
            row = loader(direct_id)
            return self._trace_reference_for_row(object_type, direct_id, row, direct_source)
        if metadata_id:
            row = loader(metadata_id)
            return self._trace_reference_for_row(object_type, metadata_id, row, metadata_source)
        return TraceReference(
            object_type=object_type,
            object_id=None,
            status="unlinked",
            relation_source="none",
            detail={},
        )

    def _present_or_missing(
        self,
        object_type: str,
        object_id: str | None,
        row,
        relation_source: str,
    ) -> TraceReference:
        return self._trace_reference_for_row(object_type, object_id, row, relation_source)

    def _trace_reference_for_row(
        self,
        object_type: str,
        object_id: str | None,
        row,
        relation_source: str,
    ) -> TraceReference:
        if object_id is None:
            return TraceReference(
                object_type=object_type,
                object_id=None,
                status="unlinked",
                relation_source="none",
                detail={},
            )
        if row is None:
            return TraceReference(
                object_type=object_type,
                object_id=object_id,
                status="missing",
                relation_source=relation_source,
                detail={},
            )
        return TraceReference(
            object_type=object_type,
            object_id=object_id,
            status="present",
            relation_source=relation_source,
            detail={},
        )

    def _report_artifact_ref(self, analysis_meta: dict[str, Any]) -> TraceReference:
        report_path = analysis_meta.get("document_path")
        if not report_path:
            return TraceReference(
                object_type="report_artifact",
                object_id=None,
                status="unlinked",
                relation_source="none",
                detail={},
            )
        return TraceReference(
            object_type="report_artifact",
            object_id=report_path,
            status="present",
            relation_source="analysis.metadata",
            detail={"path": report_path},
        )

    def _outcome_ref(self, recommendation: RecommendationORM | None) -> TraceReference:
        if recommendation is None:
            return TraceReference(
                object_type="outcome_snapshot",
                object_id=None,
                status="unlinked",
                relation_source="none",
                detail={},
            )
        graph_node = self.outcome_graph.for_recommendation(recommendation)
        if not graph_node.latest_outcome_snapshot_id:
            return TraceReference(
                object_type="outcome_snapshot",
                object_id=None,
                status="unlinked",
                relation_source="none",
                detail={"latest_review_id": graph_node.latest_review_id},
            )
        outcome = self.outcome_graph.latest_outcome_for_recommendation(recommendation)
        return self._trace_reference_for_row(
            "outcome_snapshot",
            graph_node.latest_outcome_snapshot_id,
            outcome,
            "recommendation.latest_outcome_snapshot_id",
        )

    def _audit_refs(
        self,
        *,
        analysis_id: str | None,
        recommendation_id: str | None,
        review_id: str | None = None,
    ) -> list[TraceReference]:
        query = self.db.query(AuditEventORM)
        if review_id:
            rows = (
                query.filter(
                    (AuditEventORM.review_id == review_id)
                    | (AuditEventORM.recommendation_id == recommendation_id)
                    | (AuditEventORM.analysis_id == analysis_id)
                )
                .order_by(AuditEventORM.created_at.desc())
                .limit(10)
                .all()
            )
        elif recommendation_id:
            rows = (
                query.filter(
                    (AuditEventORM.recommendation_id == recommendation_id)
                    | (AuditEventORM.analysis_id == analysis_id)
                )
                .order_by(AuditEventORM.created_at.desc())
                .limit(10)
                .all()
            )
        elif analysis_id:
            rows = (
                query.filter(AuditEventORM.analysis_id == analysis_id)
                .order_by(AuditEventORM.created_at.desc())
                .limit(10)
                .all()
            )
        else:
            rows = []
        return [
            TraceReference(
                object_type="audit_event",
                object_id=row.id,
                status="present",
                relation_source="audit_event",
                detail={"event_type": row.event_type},
            )
            for row in rows
        ]

    def _review_execution_refs(
        self,
        *,
        review_id: str | None,
        recommendation_id: str | None,
    ) -> tuple[TraceReference, TraceReference]:
        if review_id is None:
            return (
                TraceReference(
                    object_type="execution_request",
                    object_id=None,
                    status="unlinked",
                    relation_source="none",
                    detail={"family": "review"},
                ),
                TraceReference(
                    object_type="execution_receipt",
                    object_id=None,
                    status="unlinked",
                    relation_source="none",
                    detail={"family": "review"},
                ),
            )

        review_row = self._get_review(review_id)
        if review_row is not None and (
            review_row.complete_execution_request_id
            or review_row.complete_execution_receipt_id
        ):
            request_row = self._get_execution_request(review_row.complete_execution_request_id)
            receipt_row = self._get_execution_receipt(review_row.complete_execution_receipt_id)
            request_ref = self._trace_reference_for_row(
                "execution_request",
                review_row.complete_execution_request_id,
                request_row,
                "review.complete_execution_request_id",
            )
            receipt_ref = self._trace_reference_for_row(
                "execution_receipt",
                review_row.complete_execution_receipt_id,
                receipt_row,
                "review.complete_execution_receipt_id",
            )
            request_ref.detail["family"] = "review"
            receipt_ref.detail["family"] = "review"
            return request_ref, receipt_ref

        audit_row = (
            self.db.query(AuditEventORM)
            .filter(
                AuditEventORM.review_id == review_id,
                AuditEventORM.event_type.in_(["review_completed", "review_completed_failed"]),
            )
            .order_by(AuditEventORM.created_at.desc())
            .first()
        )
        if audit_row is None:
            return (
                TraceReference(
                    object_type="execution_request",
                    object_id=None,
                    status="unlinked",
                    relation_source="none",
                    detail={"family": "review"},
                ),
                TraceReference(
                    object_type="execution_receipt",
                    object_id=None,
                    status="unlinked",
                    relation_source="none",
                    detail={"family": "review"},
                ),
            )

        payload = from_json_text(audit_row.payload_json, {})
        request_id = payload.get("execution_request_id")
        receipt_id = payload.get("execution_receipt_id")
        request_row = self._get_execution_request(request_id)
        receipt_row = self._get_execution_receipt(receipt_id)
        request_ref = (
            self._trace_reference_for_row(
                "execution_request",
                request_id,
                request_row,
                "audit_event.payload.review_execution",
            )
            if request_id
            else TraceReference(
                object_type="execution_request",
                object_id=None,
                status="unlinked",
                relation_source="audit_event.payload.review_execution",
                detail={"family": "review", "review_id": review_id, "recommendation_id": recommendation_id},
            )
        )
        receipt_ref = (
            self._trace_reference_for_row(
                "execution_receipt",
                receipt_id,
                receipt_row,
                "audit_event.payload.review_execution",
            )
            if receipt_id
            else TraceReference(
                object_type="execution_receipt",
                object_id=None,
                status="unlinked",
                relation_source="audit_event.payload.review_execution",
                detail={"family": "review", "review_id": review_id, "recommendation_id": recommendation_id},
            )
        )
        return request_ref, receipt_ref

    def _knowledge_feedback_ref(
        self,
        *,
        review_id: str | None,
        recommendation_id: str | None,
    ) -> TraceReference:
        if review_id is None and recommendation_id is None:
            return TraceReference(
                object_type="knowledge_feedback_signal",
                object_id=None,
                status="unlinked",
                relation_source="none",
                detail={},
            )

        review_row = self._get_review(review_id) if review_id is not None else None
        if review_row is not None and review_row.knowledge_feedback_packet_id:
            packet = self._get_knowledge_feedback_packet(review_row.knowledge_feedback_packet_id)
            status = "present" if packet is not None else "missing"
            detail = {
                "packet_id": review_row.knowledge_feedback_packet_id,
                "recommendation_id": recommendation_id,
                "review_id": review_id,
            }
            if packet is not None:
                detail["governance_hint_count"] = len(from_json_text(packet.governance_hints_json, []))
                detail["intelligence_hint_count"] = len(from_json_text(packet.intelligence_hints_json, []))
                detail["knowledge_entry_ids"] = from_json_text(packet.knowledge_entry_ids_json, [])
            return TraceReference(
                object_type="knowledge_feedback_packet",
                object_id=review_row.knowledge_feedback_packet_id,
                status=status,
                relation_source="review.knowledge_feedback_packet_id",
                detail=detail,
            )

        query = self.db.query(AuditEventORM).filter(AuditEventORM.event_type == "knowledge_feedback_prepared")
        if review_id is not None:
            query = query.filter(AuditEventORM.review_id == review_id)
        elif recommendation_id is not None:
            query = query.filter(AuditEventORM.recommendation_id == recommendation_id)
        row = query.order_by(AuditEventORM.created_at.desc()).first()
        if row is None:
            return TraceReference(
                object_type="knowledge_feedback_signal",
                object_id=None,
                status="unlinked",
                relation_source="none",
                detail={},
            )

        payload = from_json_text(row.payload_json, {})
        packet_id = payload.get("knowledge_feedback_packet_id")
        packet = self._get_knowledge_feedback_packet(packet_id)
        status = "present"
        relation_source = "audit_event.knowledge_feedback_prepared"
        if packet_id:
            if packet is None:
                status = "missing"
            else:
                relation_source = "knowledge_feedback_packet"
        return TraceReference(
            object_type="knowledge_feedback_packet" if packet_id else "knowledge_feedback_signal",
            object_id=packet_id or row.entity_id or row.id,
            status=status,
            relation_source=relation_source,
            detail={
                "packet_id": packet_id,
                "recommendation_id": payload.get("recommendation_id"),
                "review_id": payload.get("review_id"),
                "knowledge_entry_ids": payload.get("knowledge_entry_ids", []),
                "governance_hint_count": payload.get("governance_hint_count", 0),
                "intelligence_hint_count": payload.get("intelligence_hint_count", 0),
            },
        )

    def _workflow_run_for_recommendation(
        self,
        recommendation_id: str,
        analysis_id: str | None,
    ) -> WorkflowRunORM | None:
        row = (
            self.db.query(WorkflowRunORM)
            .filter(WorkflowRunORM.recommendation_id == recommendation_id)
            .order_by(WorkflowRunORM.started_at.desc())
            .first()
        )
        if row is not None:
            return row
        if analysis_id is None:
            return None
        return (
            self.db.query(WorkflowRunORM)
            .filter(WorkflowRunORM.analysis_id == analysis_id)
            .order_by(WorkflowRunORM.started_at.desc())
            .first()
        )

    def _latest_review_for_recommendation(self, recommendation_id: str | None) -> ReviewORM | None:
        if recommendation_id is None:
            return None
        return (
            self.db.query(ReviewORM)
            .filter(ReviewORM.recommendation_id == recommendation_id)
            .order_by(ReviewORM.created_at.desc())
            .first()
        )

    def _get_analysis(self, analysis_id: str | None) -> AnalysisORM | None:
        if analysis_id is None:
            return None
        return self.db.get(AnalysisORM, analysis_id)

    def _get_recommendation(self, recommendation_id: str | None) -> RecommendationORM | None:
        if recommendation_id is None:
            return None
        return self.db.get(RecommendationORM, recommendation_id)

    def _get_review(self, review_id: str | None) -> ReviewORM | None:
        if review_id is None:
            return None
        return self.db.get(ReviewORM, review_id)

    def _get_intelligence_run(self, run_id: str | None) -> IntelligenceRunORM | None:
        if run_id is None:
            return None
        return self.db.get(IntelligenceRunORM, run_id)

    def _get_agent_action(self, action_id: str | None) -> AgentActionORM | None:
        if action_id is None:
            return None
        return self.db.get(AgentActionORM, action_id)

    def _get_execution_request(self, request_id: str | None) -> ExecutionRequestORM | None:
        if request_id is None:
            return None
        return self.db.get(ExecutionRequestORM, request_id)

    def _get_execution_receipt(self, receipt_id: str | None) -> ExecutionReceiptORM | None:
        if receipt_id is None:
            return None
        return self.db.get(ExecutionReceiptORM, receipt_id)

    def _get_knowledge_feedback_packet(self, packet_id: str | None) -> KnowledgeFeedbackPacketORM | None:
        if packet_id is None:
            return None
        return self.db.get(KnowledgeFeedbackPacketORM, packet_id)


class TraceService(TraceGraph):
    pass
