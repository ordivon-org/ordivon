"""Orchestrator workflow contracts — defines the protocol for workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from domains.research.models import AnalysisRequest, AnalysisResult
from governance.risk_engine.engine import GovernanceDecision


from sqlalchemy.orm import Session
from shared.time.clock import utc_now


@dataclass(slots=True)
class WorkflowContext:
    """Mutable context bag carried through an orchestration workflow."""

    request: AnalysisRequest
    db: Session | None = None
    analysis: AnalysisResult | None = None
    governance: GovernanceDecision | None = None
    analysis_id: str | None = None
    recommendation_id: str | None = None
    agent_action_id: str | None = None
    intelligence_run_id: str | None = None
    workflow_run_id: str | None = None
    execution_request_id: str | None = None
    execution_receipt_id: str | None = None
    workflow_step_statuses: list[dict[str, Any]] = field(default_factory=list)
    workflow_started_at: str = field(default_factory=lambda: utc_now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowStep(Protocol):
    """Protocol that every workflow step must implement."""

    def execute(self, ctx: WorkflowContext) -> WorkflowContext: ...
