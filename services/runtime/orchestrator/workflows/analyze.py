"""Workflow: analyze — the core analysis-to-recommendation pipeline.

Steps:
  1. BuildContext — assemble AnalysisContext from request
  2. Reason — call intelligence engine to produce AnalysisResult
  3. PersistAnalysis — save analysis to DB
  4. GovernanceGate — validate analysis through risk engine
  5. GenerateRecommendation — if governance allows, create recommendation
  6. RecordUsage — log usage snapshot
  7. AuditTrail — emit audit events
  8. RenderReport — produce final output dict
"""

from __future__ import annotations

from dataclasses import asdict

from capabilities.boundary import ActionContext, build_action_context, require_action_context
from domains.ai_actions.models import AgentAction
from domains.ai_actions.repository import AgentActionRepository
from domains.ai_actions.service import AgentActionService
from domains.intelligence_runs.models import IntelligenceRun
from domains.intelligence_runs.repository import IntelligenceRunRepository
from domains.intelligence_runs.service import IntelligenceRunService
from domains.research.models import AnalysisResult
from domains.research.repository import AnalysisRepository
from domains.research.service import AnalysisService
from domains.strategy.models import Recommendation
from domains.strategy.repository import RecommendationRepository
from domains.strategy.service import RecommendationService
from governance.audit.auditor import RiskAuditor
from governance.feedback import GovernanceFeedbackReader
from governance.risk_engine.engine import RiskEngine
from execution.catalog import get_execution_action
from execution.adapters import RecommendationExecutionFailure, build_default_execution_adapter_registry
from domains.execution_records.repository import ExecutionRecordRepository
from domains.execution_records.service import ExecutionRecordService
from intelligence.context_builder import HintAwareContextBuilder
from intelligence.engine import ReasoningEngine
from intelligence.runtime.hermes_client import HermesRuntimeError
from intelligence.tasks import build_analysis_task
from intelligence.tasks.contracts import IntelligenceAgentActionPayload
from orchestrator.context.context_builder import ContextBuilder
from orchestrator.contracts.workflow import WorkflowContext, WorkflowStep
from orchestrator.runtime.handoff import attach_handoff_artifact, build_handoff_artifact
from orchestrator.runtime.recovery import FallbackDecision, FallbackResult, RecoveryPolicy, record_recovery_detail
from orchestrator.runtime.wake_resume import ResumeReason, WakeReason
from state.usage.models import UsageSnapshot
from state.usage.repository import UsageSnapshotRepository
from state.usage.service import UsageService
from tools.reports.renderer import ReportRenderer
from knowledge.wiki.service import MarkdownWikiService
from shared.config.settings import settings
from shared.observability import increment_counter, span


def _get_side_effect_context(ctx: WorkflowContext, key: str, action: str) -> ActionContext:
    contexts = ctx.metadata.get("side_effect_contexts", {})
    return require_action_context(action, contexts.get(key))


class BuildContextStep:
    """Step 1: Build AnalysisContext from the raw request."""

    def __init__(self) -> None:
        self.context_builder = ContextBuilder()

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        with span("workflow.build_context", attributes={"workflow.symbol": ctx.request.symbol or "UNKNOWN"}):
            analysis_ctx = self.context_builder.build(ctx.request)
            hint_result = HintAwareContextBuilder(ctx.db).enrich(analysis_ctx, symbol=ctx.request.symbol)
        ctx.metadata["intelligence_feedback_hint_status"] = hint_result.hint_status
        ctx.metadata["intelligence_memory_lesson_count"] = hint_result.memory_lesson_count
        ctx.metadata["intelligence_related_review_count"] = hint_result.related_review_count
        if hint_result.hint_error:
            ctx.metadata["intelligence_feedback_hint_error"] = hint_result.hint_error
        ctx.metadata["analysis_context"] = analysis_ctx
        symbol = ctx.request.symbol or "UNKNOWN"
        ctx.metadata["side_effect_contexts"] = {
            "persist_analysis": build_action_context(
                "analysis persistence",
                actor="workflow.analyze",
                context="persist_analysis_step",
                reason=f"persist analysis for {symbol}",
                idempotency_key=f"analysis:{ctx.request.query}:{symbol}",
            ),
            "generate_recommendation": build_action_context(
                "recommendation generation",
                actor="workflow.analyze",
                context="generate_recommendation_step",
                reason=f"generate recommendation for {symbol}",
                idempotency_key=f"recommendation:{ctx.request.query}:{symbol}",
            ),
            "record_usage": build_action_context(
                "usage snapshot write",
                actor="workflow.analyze",
                context="record_usage_step",
                reason=f"record usage snapshot for analyze run on {symbol}",
                idempotency_key=f"usage:{ctx.request.query}:{symbol}",
            ),
            "audit_analysis": build_action_context(
                "analysis audit write",
                actor="workflow.analyze",
                context="audit_analysis_step",
                reason=f"record analysis audit lineage for {symbol}",
                idempotency_key=f"audit:analysis:{ctx.request.query}:{symbol}",
            ),
            "audit_recommendation": build_action_context(
                "recommendation audit write",
                actor="workflow.analyze",
                context="audit_recommendation_step",
                reason=f"record recommendation audit lineage for {symbol}",
                idempotency_key=f"audit:recommendation:{ctx.request.query}:{symbol}",
            ),
            "write_report_document": build_action_context(
                "analysis report document write",
                actor="workflow.analyze",
                context="write_wiki_step",
                reason=f"write analysis markdown report for {symbol}",
                idempotency_key=f"report-write:{ctx.request.query}:{symbol}",
            ),
            "update_analysis_metadata": build_action_context(
                "analysis metadata update",
                actor="workflow.analyze",
                context="write_wiki_step",
                reason=f"attach report path metadata to analysis for {symbol}",
                idempotency_key=f"report-metadata:{ctx.request.query}:{symbol}",
            ),
            "audit_report_write": build_action_context(
                "analysis report audit write",
                actor="workflow.analyze",
                context="write_wiki_step",
                reason=f"record report-write audit lineage for {symbol}",
                idempotency_key=f"audit:report:{ctx.request.query}:{symbol}",
            ),
        }
        return ctx


class ReasonStep:
    """Step 2: Run the intelligence engine to produce an AnalysisResult."""

    def __init__(self) -> None:
        self.reasoning_engine = ReasoningEngine()
        self.recovery_policy = RecoveryPolicy(
            max_retries=1,
            retryable_error=lambda exc: isinstance(exc, HermesRuntimeError) and bool(exc.retryable),
            terminal_action="none",
        )

    def should_retry(self, exc: Exception) -> bool:
        return self.recovery_policy.should_retry(exc, attempt=1)

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        with span("workflow.reason", attributes={"workflow.symbol": ctx.request.symbol or "UNKNOWN"}):
            return self._execute_reason(ctx)

    def _execute_reason(self, ctx: WorkflowContext) -> WorkflowContext:
        analysis_ctx = ctx.metadata["analysis_context"]
        intelligence_request = None
        run_service = None
        if settings.reasoning_provider == "hermes":
            intelligence_request = build_analysis_task(analysis_ctx)
            if ctx.db:
                run_service = IntelligenceRunService(IntelligenceRunRepository(ctx.db))
                run_row = run_service.create(
                    IntelligenceRun(
                        task_type="analysis.generate",
                        actor_runtime="hermes",
                        provider=intelligence_request.context_refs.provider,
                        model=intelligence_request.context_refs.model,
                        task_id=intelligence_request.task_id,
                        trace_id=intelligence_request.trace_id,
                        idempotency_key=intelligence_request.idempotency_key,
                        status="pending",
                        reason=intelligence_request.reason,
                        actor=intelligence_request.actor,
                        context=intelligence_request.context,
                        input_summary=intelligence_request.input.query,
                        request_payload=intelligence_request.to_payload(),
                        lineage_refs={
                            "query": intelligence_request.lineage.query,
                            "symbol": intelligence_request.lineage.symbol,
                            "timeframe": intelligence_request.lineage.timeframe,
                        },
                    )
                )
                ctx.intelligence_run_id = run_row.id

        try:
            analysis = self.reasoning_engine.analyze(analysis_ctx, request=intelligence_request)
        except HermesRuntimeError as exc:
            if run_service and intelligence_request and ctx.db:
                run_service.mark_failed(
                    intelligence_request.task_id,
                    provider=intelligence_request.context_refs.provider,
                    model=intelligence_request.context_refs.model,
                    error=str(exc),
                )
                ctx.db.commit()
            raise

        analysis.query = ctx.request.query
        analysis.symbol = ctx.request.symbol
        analysis.timeframe = ctx.request.timeframe
        analysis.metadata["intelligence_feedback_hint_status"] = ctx.metadata.get("intelligence_feedback_hint_status")
        analysis.metadata["intelligence_memory_lesson_count"] = ctx.metadata.get("intelligence_memory_lesson_count", 0)
        analysis.metadata["intelligence_related_review_count"] = ctx.metadata.get("intelligence_related_review_count", 0)
        if ctx.metadata.get("intelligence_feedback_hint_error"):
            analysis.metadata["intelligence_feedback_hint_error"] = ctx.metadata.get("intelligence_feedback_hint_error")
        if ctx.intelligence_run_id:
            analysis.metadata["intelligence_run_id"] = ctx.intelligence_run_id
        if ctx.workflow_run_id:
            analysis.metadata["workflow_run_id"] = ctx.workflow_run_id
        if run_service and intelligence_request:
            run_service.mark_completed(
                intelligence_request.task_id,
                provider=analysis.metadata.get("runtime_provider") or intelligence_request.context_refs.provider,
                model=analysis.metadata.get("runtime_model") or intelligence_request.context_refs.model,
                output_summary=analysis.summary,
                started_at=analysis.metadata.get("started_at"),
                completed_at=analysis.metadata.get("completed_at"),
            )
        agent_action_meta = analysis.metadata.pop("agent_action", None)
        if agent_action_meta:
            agent_action = IntelligenceAgentActionPayload(**agent_action_meta)
            if not ctx.db:
                raise ValueError("Database session is required to persist AgentAction.")
            row = AgentActionService(AgentActionRepository(ctx.db)).create(
                AgentAction(
                    task_type=agent_action.task_type,
                    actor_runtime="hermes",
                    provider=agent_action.provider,
                    model=agent_action.model,
                    session_id=agent_action.session_id,
                    status=agent_action.status,
                    reason=agent_action.reason or f"Analyze {ctx.request.symbol or 'UNKNOWN'}",
                    idempotency_key=agent_action.idempotency_key or f"analysis:{analysis.id}",
                    trace_id=agent_action.trace_id,
                    input_summary=agent_action.input_summary or ctx.request.query,
                    output_summary=agent_action.output_summary or analysis.summary,
                    input_refs={
                        "symbol": ctx.request.symbol,
                        "timeframe": ctx.request.timeframe,
                        "query": ctx.request.query,
                    },
                    output_refs={"analysis_id": analysis.id},
                    tool_trace=agent_action.tool_trace,
                    memory_events=agent_action.memory_events,
                    delegation_trace=agent_action.delegation_trace,
                    usage=agent_action.usage,
                    error=agent_action.error,
                    started_at=agent_action.started_at,
                    completed_at=agent_action.completed_at,
                )
            )
            ctx.agent_action_id = row.id
            analysis.metadata["agent_action_id"] = row.id
        ctx.analysis = analysis
        return ctx

    def fallback(self, ctx: WorkflowContext, exc: Exception) -> WorkflowContext:
        decision = FallbackDecision(
            action="degraded_analysis",
            reason=str(exc),
            detail={
                "fallback_type": "degraded_analysis",
                "provider": settings.reasoning_provider,
            },
        )
        record_recovery_detail(
            ctx,
            action="fallback",
            detail=decision.detail | {"reason": decision.reason},
        )
        ctx.metadata["wake_reason"] = WakeReason("runtime_recovered_later").reason
        ctx.metadata["resume_reason"] = ResumeReason("fallback_path_completed").reason
        ctx.metadata["resume_count"] = int(ctx.metadata.get("resume_count", 0) or 0) + 1

        fallback_result = FallbackResult(
            status="degraded",
            detail={
                "reason": decision.reason,
                "fallback_type": decision.detail["fallback_type"],
            },
        )
        analysis = ctx.analysis or AnalysisResult()
        analysis.query = ctx.request.query
        analysis.symbol = ctx.request.symbol
        analysis.timeframe = ctx.request.timeframe
        analysis.summary = "Degraded analysis: runtime failed after retries."
        analysis.thesis = "No trusted model output was produced; human review is required."
        analysis.risks = list(analysis.risks) + [str(exc)]
        analysis.suggested_actions = []
        analysis.metadata["runtime_fallback"] = fallback_result.detail
        analysis.metadata["intelligence_run_id"] = ctx.intelligence_run_id
        analysis.metadata["workflow_run_id"] = ctx.workflow_run_id
        ctx.analysis = analysis
        return ctx


class PersistAnalysisStep:
    """Step 3: Persist the AnalysisResult to the database."""

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        if not ctx.db:
            raise ValueError("Database session is required in WorkflowContext.")
        _get_side_effect_context(ctx, "persist_analysis", "analysis persistence")
        service = AnalysisService(AnalysisRepository(ctx.db))
        if ctx.agent_action_id:
            ctx.analysis.metadata["agent_action_id"] = ctx.agent_action_id
        if ctx.intelligence_run_id:
            ctx.analysis.metadata["intelligence_run_id"] = ctx.intelligence_run_id
        if ctx.workflow_run_id:
            ctx.analysis.metadata["workflow_run_id"] = ctx.workflow_run_id
        row = service.create(ctx.analysis)
        ctx.analysis_id = row.id
        return ctx


class GovernanceGateStep:
    """Step 4: Run governance validation on the analysis."""

    def __init__(self) -> None:
        self.risk_engine = RiskEngine()

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        with span("workflow.governance_gate", attributes={"workflow.symbol": ctx.request.symbol or "UNKNOWN"}):
            return self._execute_gate(ctx)

    def _execute_gate(self, ctx: WorkflowContext) -> WorkflowContext:
        advisory_hints = []
        if ctx.db:
            try:
                advisory_hints = GovernanceFeedbackReader(ctx.db).list_hints_for_symbol(ctx.analysis.symbol)
                ctx.analysis.metadata["governance_advisory_hint_status"] = "available"
            except Exception as exc:
                advisory_hints = []
                ctx.analysis.metadata["governance_advisory_hint_status"] = "unavailable"
                ctx.analysis.metadata["governance_advisory_hint_error"] = str(exc)
        else:
            ctx.analysis.metadata["governance_advisory_hint_status"] = "not_linked_yet"
        ctx.governance = self.risk_engine.validate_analysis(ctx.analysis, advisory_hints=advisory_hints)
        ctx.analysis.metadata["governance_decision"] = ctx.governance.decision
        ctx.analysis.metadata["governance_source"] = ctx.governance.source
        ctx.analysis.metadata["governance_reasons"] = list(ctx.governance.reasons)
        ctx.analysis.metadata["governance_policy_set_id"] = ctx.governance.policy_set_id
        ctx.analysis.metadata["governance_active_policy_ids"] = list(ctx.governance.active_policy_ids)
        ctx.analysis.metadata["governance_default_decision_rule_ids"] = list(ctx.governance.default_decision_rule_ids)
        ctx.analysis.metadata["governance_advisory_hints"] = [
            hint.to_payload() for hint in ctx.governance.advisory_hints
        ]
        if not ctx.governance.allows_execution() and ctx.workflow_run_id:
            increment_counter(
                "workflow_blocked_total",
                attributes={"blocked_reason": f"governance_{ctx.governance.decision}"},
            )
            artifact = build_handoff_artifact(
                task_run_id=ctx.workflow_run_id,
                root_object_ref={
                    "object_type": "analysis",
                    "object_id": ctx.analysis_id,
                },
                blocked_reason=f"governance_{ctx.governance.decision}",
                next_action="human_review",
                partial_results={
                    "decision": ctx.governance.decision,
                    "reasons": list(ctx.governance.reasons),
                },
                evidence_refs=tuple(
                    {
                        "object_type": evidence.object_type,
                        "object_id": evidence.object_id,
                    }
                    for evidence in ctx.governance.evidence
                ),
            )
            attach_handoff_artifact(ctx, artifact)
            ctx.metadata["resume_marker"] = f"handoff:{artifact.id}"
        return ctx


class GenerateRecommendationStep:
    """Step 5: If governance allows, create and persist a recommendation."""

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        with span("workflow.generate_recommendation", attributes={"workflow.symbol": ctx.request.symbol or "UNKNOWN"}):
            return self._execute_generate(ctx)

    def _execute_generate(self, ctx: WorkflowContext) -> WorkflowContext:
        if not ctx.governance or not ctx.governance.allows_execution():
            return ctx
        if not ctx.db:
            raise ValueError("Database session is required in WorkflowContext.")
        action_context = _get_side_effect_context(ctx, "generate_recommendation", "recommendation generation")
        service = RecommendationService(RecommendationRepository(ctx.db))
        adapter = build_default_execution_adapter_registry().resolve("recommendation", ctx.db)
        try:
            result = adapter.generate(
                service=service,
                action_context=action_context,
                recommendation=Recommendation(
                    analysis_id=ctx.analysis_id,
                    title=f"Action for {ctx.request.symbol}",
                    summary=f"Automated recommendation based on {ctx.analysis_id}",
                    rationale=ctx.analysis.thesis,
                    expected_outcome="System stabilization",
                    priority="normal",
                    decision=ctx.governance.decision,
                    decision_reason="; ".join(ctx.governance.reasons) if ctx.governance.reasons else None,
                ),
                analysis_id=ctx.analysis_id,
                symbol=ctx.request.symbol,
                governance_decision=ctx.governance.decision,
                governance_source=ctx.governance.source,
            )
            ctx.recommendation_id = result.recommendation.id
            ctx.metadata["recommendation_generate_request_id"] = result.execution_request_id
            ctx.metadata["recommendation_generate_receipt_id"] = result.execution_receipt_id
            if ctx.analysis:
                ctx.analysis.metadata["recommendation_generate_request_id"] = result.execution_request_id
                ctx.analysis.metadata["recommendation_generate_receipt_id"] = result.execution_receipt_id
                ctx.analysis.metadata["recommendation_id"] = result.recommendation.id
        except RecommendationExecutionFailure as exc:
            ctx.metadata["recommendation_generate_request_id"] = exc.execution_request_id
            ctx.metadata["recommendation_generate_receipt_id"] = exc.execution_receipt_id
            if ctx.analysis:
                ctx.analysis.metadata["recommendation_generate_request_id"] = exc.execution_request_id
                ctx.analysis.metadata["recommendation_generate_receipt_id"] = exc.execution_receipt_id
            raise
        return ctx


class RecordUsageStep:
    """Step 6: Record a usage snapshot for this analysis run."""

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        if not ctx.db:
            raise ValueError("Database session is required in WorkflowContext.")
        context = _get_side_effect_context(ctx, "record_usage", "usage snapshot write")
        service = UsageService(UsageSnapshotRepository(ctx.db))
        service.create(
            UsageSnapshot(
                analyses_count=1,
                recommendations_generated_count=1 if ctx.recommendation_id else 0,
                metadata={
                    "last_symbol": ctx.request.symbol,
                    "actor": context.actor,
                    "context": context.context,
                    "reason": context.reason,
                    "idempotency_key": context.idempotency_key,
                },
            )
        )
        return ctx


class AuditTrailStep:
    """Step 7: Emit audit events for the analysis and optional recommendation."""

    def __init__(self) -> None:
        self.auditor = RiskAuditor()

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        if not ctx.db:
            raise ValueError("Database session is required in WorkflowContext.")
        analysis_audit_context = _get_side_effect_context(ctx, "audit_analysis", "analysis audit write")

        self.auditor.record_event(
            "analysis_completed",
            {
                "analysis_id": ctx.analysis.id,
                "symbol": ctx.request.symbol,
                "decision": ctx.governance.decision if ctx.governance else "reject",
                "governance_source": ctx.governance.source if ctx.governance else "workflow.missing_decision",
                "governance_reasons": list(ctx.governance.reasons) if ctx.governance else ["Governance decision missing."],
                "governance_policy_set_id": ctx.governance.policy_set_id if ctx.governance else "governance.unknown",
                "governance_active_policy_ids": list(ctx.governance.active_policy_ids) if ctx.governance else [],
                "governance_default_decision_rule_ids": list(ctx.governance.default_decision_rule_ids) if ctx.governance else [],
                "governance_advisory_hints": [
                    hint.to_payload() for hint in ctx.governance.advisory_hints
                ]
                if ctx.governance
                else [],
                "recommendation_generate_request_id": ctx.metadata.get("recommendation_generate_request_id"),
                "recommendation_generate_receipt_id": ctx.metadata.get("recommendation_generate_receipt_id"),
                "agent_action_id": ctx.agent_action_id,
                "intelligence_run_id": ctx.intelligence_run_id,
                "workflow_run_id": ctx.workflow_run_id,
                "action_context": asdict(analysis_audit_context),
            },
            entity_type="analysis",
            entity_id=ctx.analysis.id,
            analysis_id=ctx.analysis.id,
            db=ctx.db,
        )

        if ctx.recommendation_id:
            recommendation_audit_context = _get_side_effect_context(
                ctx,
                "audit_recommendation",
                "recommendation audit write",
            )
            self.auditor.record_event(
                "recommendation_generated",
                {
                    "recommendation_id": ctx.recommendation_id,
                    "analysis_id": ctx.analysis.id,
                    "decision": ctx.governance.decision if ctx.governance else "reject",
                    "governance_source": ctx.governance.source if ctx.governance else "workflow.missing_decision",
                    "governance_reasons": list(ctx.governance.reasons) if ctx.governance else ["Governance decision missing."],
                    "governance_policy_set_id": ctx.governance.policy_set_id if ctx.governance else "governance.unknown",
                    "governance_active_policy_ids": list(ctx.governance.active_policy_ids) if ctx.governance else [],
                    "governance_default_decision_rule_ids": list(ctx.governance.default_decision_rule_ids) if ctx.governance else [],
                    "governance_advisory_hints": [
                        hint.to_payload() for hint in ctx.governance.advisory_hints
                    ]
                    if ctx.governance
                    else [],
                    "recommendation_generate_request_id": ctx.metadata.get("recommendation_generate_request_id"),
                    "recommendation_generate_receipt_id": ctx.metadata.get("recommendation_generate_receipt_id"),
                    "agent_action_id": ctx.agent_action_id,
                    "intelligence_run_id": ctx.intelligence_run_id,
                    "workflow_run_id": ctx.workflow_run_id,
                    "action_context": asdict(recommendation_audit_context),
                },
                entity_type="recommendation",
                entity_id=ctx.recommendation_id,
                analysis_id=ctx.analysis.id,
                recommendation_id=ctx.recommendation_id,
                db=ctx.db,
            )
        return ctx


class RenderReportStep:
    """Step 8: Render a report dict from analysis + governance decision."""

    def __init__(self) -> None:
        self.renderer = ReportRenderer()

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        report = self.renderer.render_analysis_report(ctx.analysis, ctx.governance)
        report["recommendation_id"] = ctx.recommendation_id
        report["agent_action_id"] = ctx.agent_action_id
        report["intelligence_run_id"] = ctx.intelligence_run_id
        report["workflow_run_id"] = ctx.workflow_run_id
        report["recommendation_generate_request_id"] = ctx.metadata.get("recommendation_generate_request_id")
        report["recommendation_generate_receipt_id"] = ctx.metadata.get("recommendation_generate_receipt_id")
        ctx.metadata["report"] = report
        return ctx


class WriteWikiStep:
    """Step 9: Persist the analysis as a markdown file for the knowledge system."""

    def __init__(self) -> None:
        self.wiki_service = MarkdownWikiService(base_dir="wiki")

    def execute(self, ctx: WorkflowContext) -> WorkflowContext:
        write_context = _get_side_effect_context(ctx, "write_report_document", "analysis report document write")
        metadata_context = _get_side_effect_context(ctx, "update_analysis_metadata", "analysis metadata update")
        audit_context = _get_side_effect_context(ctx, "audit_report_write", "analysis report audit write")
        if not ctx.db:
            raise ValueError("Database session is required in WorkflowContext.")

        execution_service = ExecutionRecordService(ExecutionRecordRepository(ctx.db))
        action_spec = get_execution_action("analysis_report_write")
        sym = ctx.request.symbol or "UNKNOWN"
        safe_sym = sym.replace("/", "_").replace("\\", "_")
        doc_id = f"analysis_{safe_sym}_{ctx.analysis_id}"
        request_row = execution_service.start_request(
            action_id=action_spec.action_id,
            action_context=write_context,
            entity_type="analysis",
            entity_id=ctx.analysis_id,
            analysis_id=ctx.analysis_id,
            payload={
                "analysis_id": ctx.analysis_id,
                "document_id": doc_id,
                "symbol": sym,
                "agent_action_id": ctx.agent_action_id,
                "intelligence_run_id": ctx.intelligence_run_id,
                "workflow_run_id": ctx.workflow_run_id,
                "action_context": ExecutionRecordService.action_context_payload(write_context),
                "metadata_action_context": ExecutionRecordService.action_context_payload(metadata_context),
                "audit_action_context": ExecutionRecordService.action_context_payload(audit_context),
            },
        )
        ctx.execution_request_id = request_row.id

        md_content = f"# Analysis of {sym}\n\n"
        md_content += f"**Thesis:** {ctx.analysis.thesis}\n\n"
        md_content += f"**Summary:** {ctx.analysis.summary}\n\n"
        md_content += f"**Agent Action ID:** {ctx.agent_action_id or 'unavailable'}\n\n"
        md_content += f"**Intelligence Run ID:** {ctx.intelligence_run_id or 'unavailable'}\n\n"
        md_content += f"**Workflow Run ID:** {ctx.workflow_run_id or 'unavailable'}\n\n"
        
        if ctx.analysis.risks:
            md_content += "## Risks\n"
            for r in ctx.analysis.risks:
                md_content += f"- {r}\n"
            md_content += "\n"
            
        if ctx.analysis.suggested_actions:
            md_content += "## Suggested Actions\n"
            for a in ctx.analysis.suggested_actions:
                md_content += f"- {a}\n"

        path: str | None = None
        service = AnalysisService(AnalysisRepository(ctx.db))
        try:
            path = self.wiki_service.write_document("reports", doc_id, md_content)
            receipt_row = execution_service.record_success(
                request_row.id,
                result_ref=path,
                detail={
                    "analysis_id": ctx.analysis_id,
                    "document_id": doc_id,
                    "document_path": path,
                    "action_context": asdict(write_context),
                },
            )
            ctx.execution_receipt_id = receipt_row.id
            report = ctx.metadata.get("report")
            if isinstance(report, dict):
                report["execution_request_id"] = request_row.id
                report["execution_receipt_id"] = receipt_row.id
            ctx.analysis.metadata["document_path"] = path
            ctx.analysis.metadata["status"] = "generated"
            ctx.analysis.metadata["agent_action_id"] = ctx.agent_action_id
            ctx.analysis.metadata["intelligence_run_id"] = ctx.intelligence_run_id
            ctx.analysis.metadata["workflow_run_id"] = ctx.workflow_run_id
            ctx.analysis.metadata["execution_request_id"] = request_row.id
            ctx.analysis.metadata["execution_receipt_id"] = receipt_row.id
            service.update_metadata(ctx.analysis_id, {
                "document_path": path,
                "status": "generated",
                "agent_action_id": ctx.agent_action_id,
                "intelligence_run_id": ctx.intelligence_run_id,
                "workflow_run_id": ctx.workflow_run_id,
                "execution_request_id": request_row.id,
                "execution_receipt_id": receipt_row.id,
                "recommendation_generate_request_id": ctx.metadata.get("recommendation_generate_request_id"),
                "recommendation_generate_receipt_id": ctx.metadata.get("recommendation_generate_receipt_id"),
                "governance_decision": ctx.governance.decision if ctx.governance else None,
                "governance_source": ctx.governance.source if ctx.governance else None,
                "governance_reasons": list(ctx.governance.reasons) if ctx.governance else [],
                "governance_policy_set_id": ctx.governance.policy_set_id if ctx.governance else None,
                "governance_active_policy_ids": list(ctx.governance.active_policy_ids) if ctx.governance else [],
                "governance_default_decision_rule_ids": list(ctx.governance.default_decision_rule_ids) if ctx.governance else [],
                "governance_advisory_hint_status": ctx.analysis.metadata.get("governance_advisory_hint_status"),
                "governance_advisory_hints": ctx.analysis.metadata.get("governance_advisory_hints", []),
                "governance_advisory_hint_error": ctx.analysis.metadata.get("governance_advisory_hint_error"),
                "report_write_action_context": asdict(write_context),
                "metadata_update_action_context": asdict(metadata_context),
            })
            RiskAuditor().record_event(
                "analysis_report_written",
                {
                    "analysis_id": ctx.analysis_id,
                    "document_path": path,
                    "agent_action_id": ctx.agent_action_id,
                    "intelligence_run_id": ctx.intelligence_run_id,
                    "workflow_run_id": ctx.workflow_run_id,
                    "execution_request_id": request_row.id,
                    "execution_receipt_id": receipt_row.id,
                    "write_action_context": asdict(write_context),
                    "metadata_action_context": asdict(metadata_context),
                    "audit_action_context": asdict(audit_context),
                },
                entity_type="analysis",
                entity_id=ctx.analysis_id,
                analysis_id=ctx.analysis_id,
                db=ctx.db,
            )
        except Exception as e:
            # Compensating deletion: DB update failed, remove the orphaned markdown file.
            import os
            compensation_applied = False
            try:
                if path and os.path.exists(path):
                    os.remove(path)
                    compensation_applied = True
            except OSError:
                pass
            record_recovery_detail(
                ctx,
                action="compensation",
                detail={
                    "compensation_applied": compensation_applied,
                    "document_path": path,
                },
            )
            receipt_row = execution_service.record_failure(
                request_row.id,
                error=str(e),
                detail={
                    "analysis_id": ctx.analysis_id,
                    "document_id": doc_id,
                    "document_path": path,
                    "compensation_applied": compensation_applied,
                    "action_context": asdict(write_context),
                },
            )
            ctx.execution_receipt_id = receipt_row.id
            report = ctx.metadata.get("report")
            if isinstance(report, dict):
                report["execution_request_id"] = request_row.id
                report["execution_receipt_id"] = receipt_row.id
            raise e
            
        return ctx


# ── Assembled pipeline ───────────────────────────────────────────

ANALYZE_WORKFLOW: list[WorkflowStep] = [
    BuildContextStep(),
    ReasonStep(),
    PersistAnalysisStep(),
    GovernanceGateStep(),
    GenerateRecommendationStep(),
    RecordUsageStep(),
    AuditTrailStep(),
    RenderReportStep(),
    WriteWikiStep(),
]
