from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from orchestrator.contracts.workflow import WorkflowContext


@dataclass(slots=True)
class RecoveryDetail:
    action: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FallbackDecision:
    action: str
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FallbackResult:
    status: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RecoveryPolicy:
    max_retries: int = 0
    retryable_error: Callable[[Exception], bool] | None = None
    terminal_action: str = "none"

    def should_retry(self, exc: Exception, *, attempt: int) -> bool:
        if attempt > self.max_retries:
            return False
        if self.retryable_error is None:
            return False
        return bool(self.retryable_error(exc))

    def failure_action(self, detail: RecoveryDetail | None) -> str:
        if detail is not None:
            return detail.action
        return self.terminal_action

    def failure_detail(self, detail: RecoveryDetail | None) -> dict[str, Any]:
        if detail is not None:
            return dict(detail.detail)
        return {}


def get_step_recovery_policy(step: object) -> RecoveryPolicy:
    policy = getattr(step, "recovery_policy", None)
    if isinstance(policy, RecoveryPolicy):
        return policy

    max_retries = int(getattr(step, "max_retries", 0) or 0)
    retryable_error = getattr(step, "should_retry", None)
    if callable(retryable_error) or max_retries:
        return RecoveryPolicy(
            max_retries=max_retries,
            retryable_error=retryable_error if callable(retryable_error) else None,
        )
    return RecoveryPolicy()


def record_recovery_detail(ctx: WorkflowContext, *, action: str, detail: dict[str, Any] | None = None) -> None:
    ctx.metadata["_workflow_recovery_detail"] = RecoveryDetail(
        action=action,
        detail=dict(detail or {}),
    )


def consume_recovery_detail(ctx: WorkflowContext) -> RecoveryDetail | None:
    raw = ctx.metadata.pop("_workflow_recovery_detail", None)
    if raw is None:
        return None
    if isinstance(raw, RecoveryDetail):
        return raw
    if isinstance(raw, dict) and "action" in raw:
        return RecoveryDetail(
            action=str(raw["action"]),
            detail=dict(raw.get("detail", {})),
        )
    return RecoveryDetail(action="none", detail={})
