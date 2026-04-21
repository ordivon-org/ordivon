"""PFIOS Orchestrator — workflow-based execution engine.

The orchestrator coordinates domain services via composable workflow steps.
It does NOT contain business logic, storage, policy, or rendering — those
live in their respective layers (domains, state, governance, tools).
"""

from __future__ import annotations

from typing import Any

from domains.research.models import AnalysisRequest
from domains.workflow_runs.models import WorkflowRun
from domains.workflow_runs.repository import WorkflowRunRepository
from domains.workflow_runs.service import WorkflowRunService
from orchestrator.contracts.workflow import WorkflowContext, WorkflowStep
from orchestrator.runtime.recovery import consume_recovery_detail, get_step_recovery_policy
from orchestrator.workflows.analyze import ANALYZE_WORKFLOW
from sqlalchemy.orm import Session
from shared.time.clock import utc_now


class PFIOSOrchestrator:
    """Top-level orchestration harness.

    Runs a named workflow as a sequence of WorkflowStep instances.
    """

    def __init__(self, workflows: dict[str, list[WorkflowStep]] | None = None) -> None:
        self._workflows = workflows or {
            "analyze": ANALYZE_WORKFLOW,
        }

    # ── public API ──────────────────────────────────────────────

    def execute_analyze(self, request: AnalysisRequest, db: Session | None = None) -> dict[str, Any]:
        """Run the full analyze workflow and return the rendered report."""
        ctx = WorkflowContext(request=request, db=db)
        ctx = self._run_workflow("analyze", ctx)
        
        # Atomically commit the entire workflow if DB session exists
        if db:
            db.commit()
            
        return ctx.metadata.get("report", {})

    # ── internal ────────────────────────────────────────────────

    def _run_workflow(self, name: str, ctx: WorkflowContext) -> WorkflowContext:
        steps = self._workflows.get(name)
        if steps is None:
            raise ValueError(f"Unknown workflow: {name}")
        workflow_run = self._build_workflow_run(name, ctx)
        ctx.workflow_run_id = workflow_run.id
        if ctx.db:
            WorkflowRunService(WorkflowRunRepository(ctx.db)).create(workflow_run)

        try:
            for step in steps:
                step_name = step.__class__.__name__
                recovery_policy = get_step_recovery_policy(step)
                attempt = 0
                while True:
                    attempt += 1
                    started_at = utc_now().isoformat()
                    try:
                        ctx = step.execute(ctx)
                    except Exception as exc:
                        completed_at = utc_now().isoformat()
                        recovery_detail = consume_recovery_detail(ctx)
                        should_retry = recovery_policy.should_retry(exc, attempt=attempt)
                        if should_retry:
                            ctx.workflow_step_statuses.append(
                                {
                                    "step": step_name,
                                    "status": "retrying",
                                    "started_at": started_at,
                                    "completed_at": completed_at,
                                    "attempt": attempt,
                                    "error": str(exc),
                                    "recovery_action": "retry",
                                }
                            )
                            continue

                        ctx.workflow_step_statuses.append(
                            {
                                "step": step_name,
                                "status": "failed",
                                "started_at": started_at,
                                "completed_at": completed_at,
                                "attempt": attempt,
                                "error": str(exc),
                                "recovery_action": recovery_policy.failure_action(recovery_detail),
                                "recovery_detail": recovery_policy.failure_detail(recovery_detail),
                            }
                        )
                        self._persist_failed_workflow_run(
                            workflow_run,
                            ctx,
                            failed_step=step_name,
                            failure_reason=str(exc),
                        )
                        raise

                    completed_at = utc_now().isoformat()
                    ctx.workflow_step_statuses.append(
                        {
                            "step": step_name,
                            "status": "completed",
                            "started_at": started_at,
                            "completed_at": completed_at,
                            "attempt": attempt,
                        }
                    )
                    break

            self._persist_completed_workflow_run(workflow_run, ctx)
            report = ctx.metadata.get("report")
            if isinstance(report, dict):
                report["workflow_run_id"] = ctx.workflow_run_id
            return ctx
        except Exception:
            raise

    def _build_workflow_run(self, name: str, ctx: WorkflowContext) -> WorkflowRun:
        request_summary = ctx.request.query
        if ctx.request.symbol:
            request_summary = f"{request_summary} [{ctx.request.symbol}]"
        return WorkflowRun(
            workflow_name=name,
            status="pending",
            request_summary=request_summary,
            trigger="api",
            lineage_refs={
                "query": ctx.request.query,
                "symbol": ctx.request.symbol,
                "timeframe": ctx.request.timeframe,
            },
            started_at=ctx.workflow_started_at,
        )

    def _persist_completed_workflow_run(self, workflow_run: WorkflowRun, ctx: WorkflowContext) -> None:
        if not ctx.db:
            return
        workflow_run.status = "completed"
        workflow_run.analysis_id = ctx.analysis_id
        workflow_run.recommendation_id = ctx.recommendation_id
        workflow_run.intelligence_run_id = ctx.intelligence_run_id
        workflow_run.agent_action_id = ctx.agent_action_id
        workflow_run.execution_request_id = ctx.execution_request_id
        workflow_run.execution_receipt_id = ctx.execution_receipt_id
        workflow_run.step_statuses = list(ctx.workflow_step_statuses)
        workflow_run.completed_at = utc_now().isoformat()
        WorkflowRunService(WorkflowRunRepository(ctx.db)).save(workflow_run)

    def _persist_failed_workflow_run(
        self,
        workflow_run: WorkflowRun,
        ctx: WorkflowContext,
        *,
        failed_step: str,
        failure_reason: str,
    ) -> None:
        if not ctx.db:
            return
        ctx.db.rollback()
        workflow_run.status = "failed"
        workflow_run.analysis_id = ctx.analysis_id
        workflow_run.recommendation_id = ctx.recommendation_id
        workflow_run.intelligence_run_id = ctx.intelligence_run_id
        workflow_run.agent_action_id = ctx.agent_action_id
        workflow_run.execution_request_id = ctx.execution_request_id
        workflow_run.execution_receipt_id = ctx.execution_receipt_id
        workflow_run.failed_step = failed_step
        workflow_run.failure_reason = failure_reason
        workflow_run.step_statuses = list(ctx.workflow_step_statuses)
        workflow_run.completed_at = utc_now().isoformat()
        WorkflowRunService(WorkflowRunRepository(ctx.db)).save(workflow_run)
        ctx.db.commit()
