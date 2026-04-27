from __future__ import annotations

from dataclasses import dataclass


VALID_SIDE_EFFECT_LEVELS = {
    "none",
    "state_mutation",
    "artifact_write",
    "audit_write",
    "operational_write",
}

VALID_BOUNDARY_STATUSES = {
    "covered",
    "partially_covered",
    "not_covered",
}


@dataclass(frozen=True, slots=True)
class ExecutionActionSpec:
    action_id: str
    family: str
    side_effect_level: str
    owner_path: str
    boundary_status: str
    state_targets: tuple[str, ...]
    primary_receipt_candidate: bool
    notes: str = ""


EXECUTION_ACTION_CATALOG: tuple[ExecutionActionSpec, ...] = (
    ExecutionActionSpec(
        action_id="analysis_persist",
        family="analysis",
        side_effect_level="state_mutation",
        owner_path="orchestrator.workflows.analyze.PersistAnalysisStep",
        boundary_status="covered",
        state_targets=("analyses",),
        primary_receipt_candidate=False,
        notes="Persists the canonical analysis fact object.",
    ),
    ExecutionActionSpec(
        action_id="recommendation_generate",
        family="recommendation",
        side_effect_level="state_mutation",
        owner_path="execution.adapters.recommendations.RecommendationExecutionAdapter.generate",
        boundary_status="covered",
        state_targets=("recommendations",),
        primary_receipt_candidate=True,
        notes="Main-chain recommendation creation after governance allow.",
    ),
    ExecutionActionSpec(
        action_id="usage_snapshot_write",
        family="usage",
        side_effect_level="operational_write",
        owner_path="orchestrator.workflows.analyze.RecordUsageStep",
        boundary_status="covered",
        state_targets=("usage_snapshots",),
        primary_receipt_candidate=False,
        notes="Operational snapshot write for validation and monitoring.",
    ),
    ExecutionActionSpec(
        action_id="analysis_audit_write",
        family="audit",
        side_effect_level="audit_write",
        owner_path="orchestrator.workflows.analyze.AuditTrailStep",
        boundary_status="covered",
        state_targets=("audit_events",),
        primary_receipt_candidate=False,
        notes="Records analysis_completed audit lineage.",
    ),
    ExecutionActionSpec(
        action_id="recommendation_audit_write",
        family="audit",
        side_effect_level="audit_write",
        owner_path="orchestrator.workflows.analyze.AuditTrailStep",
        boundary_status="covered",
        state_targets=("audit_events",),
        primary_receipt_candidate=False,
        notes="Records recommendation_generated audit lineage.",
    ),
    ExecutionActionSpec(
        action_id="analysis_report_render",
        family="report",
        side_effect_level="artifact_write",
        owner_path="orchestrator.workflows.analyze.RenderReportStep",
        boundary_status="not_covered",
        state_targets=(),
        primary_receipt_candidate=False,
        notes="In-memory report artifact only; not treated as a consequential write by itself.",
    ),
    ExecutionActionSpec(
        action_id="analysis_report_write",
        family="report",
        side_effect_level="artifact_write",
        owner_path="orchestrator.workflows.analyze.WriteWikiStep",
        boundary_status="covered",
        state_targets=("wiki/reports/*.md",),
        primary_receipt_candidate=True,
        notes="Writes markdown analysis report artifact to wiki storage.",
    ),
    ExecutionActionSpec(
        action_id="analysis_metadata_update",
        family="analysis",
        side_effect_level="state_mutation",
        owner_path="orchestrator.workflows.analyze.WriteWikiStep",
        boundary_status="covered",
        state_targets=("analyses.metadata",),
        primary_receipt_candidate=True,
        notes="Attaches report path and lineage metadata to persisted analysis.",
    ),
    ExecutionActionSpec(
        action_id="analysis_report_audit_write",
        family="audit",
        side_effect_level="audit_write",
        owner_path="orchestrator.workflows.analyze.WriteWikiStep",
        boundary_status="covered",
        state_targets=("audit_events",),
        primary_receipt_candidate=False,
        notes="Records analysis_report_written audit lineage.",
    ),
    ExecutionActionSpec(
        action_id="recommendation_status_update",
        family="recommendation",
        side_effect_level="state_mutation",
        owner_path="execution.adapters.recommendations.RecommendationExecutionAdapter.update_status",
        boundary_status="covered",
        state_targets=("recommendations", "audit_events"),
        primary_receipt_candidate=True,
        notes="Lifecycle transition on recommendation object.",
    ),
    ExecutionActionSpec(
        action_id="review_submit",
        family="review",
        side_effect_level="state_mutation",
        owner_path="execution.adapters.reviews.ReviewExecutionAdapter.submit",
        boundary_status="covered",
        state_targets=("reviews", "audit_events"),
        primary_receipt_candidate=True,
        notes="Creates review fact and emits review_submitted audit.",
    ),
    ExecutionActionSpec(
        action_id="review_complete",
        family="review",
        side_effect_level="state_mutation",
        owner_path="execution.adapters.reviews.ReviewExecutionAdapter.complete",
        boundary_status="covered",
        state_targets=("reviews", "lessons", "audit_events"),
        primary_receipt_candidate=True,
        notes="Completes review, persists lesson rows, and emits audit records.",
    ),
    ExecutionActionSpec(
        action_id="validation_issue_report",
        family="validation",
        side_effect_level="state_mutation",
        owner_path="execution.adapters.validation.ValidationExecutionAdapter.report_issue",
        boundary_status="covered",
        state_targets=("issues", "audit_events"),
        primary_receipt_candidate=True,
        notes="Persists validation issue and emits validation_issue_reported audit.",
    ),
    ExecutionActionSpec(
        action_id="validation_usage_sync",
        family="validation",
        side_effect_level="operational_write",
        owner_path="capabilities.diagnostic.validation.ValidationCapability.sync_usage",
        boundary_status="covered",
        state_targets=("usage_snapshots",),
        primary_receipt_candidate=False,
        notes="Manual operational usage snapshot sync.",
    ),
    ExecutionActionSpec(
        action_id="intelligence_run_write",
        family="intelligence",
        side_effect_level="operational_write",
        owner_path="domains.intelligence_runs.service.IntelligenceRunService",
        boundary_status="partially_covered",
        state_targets=("intelligence_runs",),
        primary_receipt_candidate=True,
        notes="State-backed runtime lifecycle write, not yet modeled as a receipt family.",
    ),
    ExecutionActionSpec(
        action_id="agent_action_write",
        family="intelligence",
        side_effect_level="state_mutation",
        owner_path="domains.ai_actions.service.AgentActionService",
        boundary_status="partially_covered",
        state_targets=("agent_actions",),
        primary_receipt_candidate=True,
        notes="AI artifact persistence with idempotency, still awaiting receipt alignment.",
    ),
    ExecutionActionSpec(
        action_id="finance_decision_plan",
        family="finance",
        side_effect_level="none",
        owner_path="execution.adapters.finance.FinancePlanReceiptAdapter.create_plan_receipt",
        boundary_status="covered",
        state_targets=(),
        primary_receipt_candidate=True,
        notes="H-6: Plan-only receipt — records intent, zero broker/order/trade execution.",
    ),
)


def validate_execution_catalog(
    catalog: tuple[ExecutionActionSpec, ...] = EXECUTION_ACTION_CATALOG,
) -> tuple[ExecutionActionSpec, ...]:
    seen_ids: set[str] = set()

    for spec in catalog:
        if not spec.action_id.strip():
            raise ValueError("Execution catalog action_id must be non-empty.")
        if spec.action_id in seen_ids:
            raise ValueError(f"Duplicate execution action_id detected: {spec.action_id}")
        seen_ids.add(spec.action_id)

        if spec.side_effect_level not in VALID_SIDE_EFFECT_LEVELS:
            raise ValueError(
                f"Execution catalog action {spec.action_id} uses unsupported side_effect_level "
                f"{spec.side_effect_level!r}."
            )
        if spec.boundary_status not in VALID_BOUNDARY_STATUSES:
            raise ValueError(
                f"Execution catalog action {spec.action_id} uses unsupported boundary_status {spec.boundary_status!r}."
            )
        if not spec.owner_path.strip():
            raise ValueError(f"Execution catalog action {spec.action_id} is missing owner_path.")
    return catalog


def list_execution_actions() -> list[ExecutionActionSpec]:
    return list(validate_execution_catalog())


def get_execution_action(action_id: str) -> ExecutionActionSpec:
    for spec in validate_execution_catalog():
        if spec.action_id == action_id:
            return spec
    raise KeyError(f"Unknown execution action: {action_id}")


def get_primary_receipt_candidates() -> list[ExecutionActionSpec]:
    return [spec for spec in validate_execution_catalog() if spec.primary_receipt_candidate]
