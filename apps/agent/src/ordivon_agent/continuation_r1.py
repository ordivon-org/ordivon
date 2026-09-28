from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ordivon_harness.api import HarnessAgentRun

from .response_continuity_r1 import (
    ResponseContinuityReceipt,
    ResponseContinuityStore,
    ResponseDeliveryState,
)


class AgentContinuationError(RuntimeError):
    pass


class ContinuationAction(StrEnum):
    REPRESENT_UNCONFIRMED_RESPONSE = "represent-unconfirmed-response"
    RECOVER_EXISTING_RUN = "recover-existing-run"
    AWAIT_CALLER_INPUT = "await-caller-input"
    INSPECT_TERMINAL = "inspect-terminal"
    CONTINUE_EXISTING_RUN = "continue-existing-run"


@dataclass(frozen=True, slots=True)
class AgentContinuationPlan:
    action: ContinuationAction
    caller_id: str
    caller_run_ref: str
    harness_run_id: str
    run_revision: int
    native_status: str
    latest_response: ResponseContinuityReceipt | None
    recovery_status: dict[str, Any]
    response_rehydration_required: bool

    @property
    def effect_redispatch_allowed(self) -> bool:
        """Continuation never authorizes a new physical effect identity."""
        return False


class AgentContinuationCoordinator:
    """Reconnect one caller interaction to existing durable Ordivon truth.

    The product-side coordinator owns no execution, Provider, Host, or domain authority.
    It locates the already-bound Harness Run by the caller's stable Run reference, reads
    Agent-owned response delivery state, and chooses only a continuation action. It never
    creates a Harness Run and never interprets response uncertainty as effect redispatch
    permission.
    """

    def __init__(self, responses: ResponseContinuityStore) -> None:
        self.responses = responses

    def locate(
        self,
        state_root: str | Path,
        caller_id: str,
        caller_run_ref: str,
        adapter_factory,
        **run_open_kwargs,
    ) -> HarnessAgentRun:
        return HarnessAgentRun.open_for_caller(
            state_root,
            caller_id,
            caller_run_ref,
            adapter_factory,
            **run_open_kwargs,
        )

    def inspect(self, run: HarnessAgentRun) -> AgentContinuationPlan:
        recovery = dict(run.recovery_status())
        caller_id = self._text(recovery.get("callerId"), "callerId")
        caller_run_ref = self._text(recovery.get("callerRunRef"), "callerRunRef")
        harness_run_id = self._text(recovery.get("harnessRunId"), "harnessRunId")
        if harness_run_id != run.harness_run_id:
            raise AgentContinuationError("Harness recovery projection changed Run identity")

        run_revision = recovery.get("runRevision")
        if type(run_revision) is not int or run_revision < 1:
            raise AgentContinuationError("Harness recovery projection omitted Run revision")
        native_status = self._text(recovery.get("nativeStatus"), "nativeStatus")

        latest = self.responses.latest_for_caller(caller_id, caller_run_ref)
        if latest is not None:
            if latest.harness_run_id != harness_run_id:
                raise AgentContinuationError("response continuity is bound to another Harness Run")
            if latest.source_run_revision > run_revision:
                raise AgentContinuationError(
                    "response continuity references a future Harness Run revision"
                )

        response_unconfirmed = (
            latest is not None and latest.state is not ResponseDeliveryState.CONFIRMED
        )
        mechanical = recovery.get("mechanicalRecoveryRequired")
        resume_required = recovery.get("resumeRequired")
        if type(mechanical) is not bool or type(resume_required) is not bool:
            raise AgentContinuationError(
                "Harness recovery projection omitted continuation booleans"
            )

        if response_unconfirmed:
            action = ContinuationAction.REPRESENT_UNCONFIRMED_RESPONSE
        elif mechanical:
            action = ContinuationAction.RECOVER_EXISTING_RUN
        elif resume_required:
            action = ContinuationAction.AWAIT_CALLER_INPUT
        elif native_status in {"completed", "failed", "stopped"}:
            action = ContinuationAction.INSPECT_TERMINAL
        else:
            action = ContinuationAction.CONTINUE_EXISTING_RUN

        return AgentContinuationPlan(
            action=action,
            caller_id=caller_id,
            caller_run_ref=caller_run_ref,
            harness_run_id=harness_run_id,
            run_revision=run_revision,
            native_status=native_status,
            latest_response=latest,
            recovery_status=recovery,
            response_rehydration_required=response_unconfirmed,
        )

    def locate_and_inspect(
        self,
        state_root: str | Path,
        caller_id: str,
        caller_run_ref: str,
        adapter_factory,
        **run_open_kwargs,
    ) -> tuple[HarnessAgentRun, AgentContinuationPlan]:
        run = self.locate(
            state_root,
            caller_id,
            caller_run_ref,
            adapter_factory,
            **run_open_kwargs,
        )
        return run, self.inspect(run)

    def recover_existing_run(
        self,
        run: HarnessAgentRun,
        plan: AgentContinuationPlan,
        *,
        cancellation=None,
    ):
        """Resume only the already-bound Run when durable evidence requires recovery."""
        if plan.harness_run_id != run.harness_run_id:
            raise AgentContinuationError("continuation plan belongs to another Harness Run")
        if plan.action is not ContinuationAction.RECOVER_EXISTING_RUN:
            raise AgentContinuationError(
                f"continuation action {plan.action.value} does not authorize Run recovery"
            )
        return run.resume(cancellation=cancellation)

    @staticmethod
    def _text(value: object, label: str) -> str:
        if not isinstance(value, str) or not value or value != value.strip():
            raise AgentContinuationError(f"{label} is missing or invalid")
        return value


__all__ = [
    "AgentContinuationCoordinator",
    "AgentContinuationError",
    "AgentContinuationPlan",
    "ContinuationAction",
]
