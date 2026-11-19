"""Pure Runtime effect handoff and observation decoding for Harness.

No Runtime call, PostgreSQL write, or physical side effect is made here.
A committed transport result is never interpreted as semantic Domain success.
"""
from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from ..protocol import HarnessToolStepIntent
from ..runtime_port import HarnessRuntimeClientError, HarnessRuntimeToolRejected
from .tool_errors import ToolBridgeError, ToolBridgeErrorKind


_RUNTIME_DELIVERY_DISPOSITIONS = frozenset(
    {"in_progress", "committed", "reconciliation_required", "unknown"}
)
# Exact Runtime JobResolution states: four conclusive outcomes plus two
# uncertain outcomes form a disjoint sum at the Runtime/Harness boundary.
# These names are the Runtime-owned public JobResolution wire contract.
_RUNTIME_COMMITTED_RESOLUTIONS = frozenset({"succeeded", "failed", "timed_out", "cancelled"})
_RUNTIME_UNCERTAIN_RESOLUTIONS = frozenset({"lost", "orphaned"})
_RUNTIME_JOB_RESOLUTIONS = _RUNTIME_COMMITTED_RESOLUTIONS | _RUNTIME_UNCERTAIN_RESOLUTIONS


def _require_exact_owner_effect_handoff(
    intent: HarnessToolStepIntent,
    fence,
    original_request: dict[str, JsonValue],
    owner_request: dict[str, JsonValue],
) -> None:
    """Qualify actual physical send bytes against the committed Tool Intent.

    The sole allowed post-Journal transformation for workspace.exec is
    appending precisely ONE source-authenticated DispatchFence reference.
    This does NOT create Runtime admission or prove that an external effect
    happened; the Owner remains the physical idempotency/receipt authority.
    """

    def reject() -> None:
        # Do not leak private executable arguments or identity evidence.
        raise ToolBridgeError(
            "Runtime Owner handoff differs from persisted Tool Intent/Fence",
            kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
        )

    try:
        validate_json_value(original_request)
        validate_json_value(owner_request)
        if (
            intent.runtime_operation != fence.runtime_operation
            or intent.harness_run_id != fence.harness_run_id
            or intent.digest != fence.intent_digest
            or intent.client_request_id != fence.client_request_id
            or (
                intent.runtime_operation in {"workspace.exec", "workspace.patch"}
                and (
                    original_request.get("clientRequestId") != intent.client_request_id
                    or owner_request.get("clientRequestId") != intent.client_request_id
                )
            )
            or canonical_digest(original_request) != intent.runtime_arguments_digest
        ):
            reject()

        if intent.runtime_operation != "workspace.exec":
            if canonical_digest(owner_request) != intent.runtime_arguments_digest:
                reject()
            return

        original_execution = original_request.get("execution")
        actual_execution = owner_request.get("execution")
        if not isinstance(original_execution, dict) or not isinstance(actual_execution, dict):
            reject()
        previous_refs = original_execution.get("foreignReferences")
        owner_refs = actual_execution.get("foreignReferences")
        if (
            not isinstance(previous_refs, list)
            or not isinstance(owner_refs, list)
            or any(not isinstance(item, dict) for item in previous_refs)
            or any(item.get("type") == "dispatch_fence" for item in previous_refs)
            or len(owner_refs) != len(previous_refs) + 1
            or owner_refs[:-1] != previous_refs
        ):
            reject()
        expected_fence_ref = {
            "namespace": fence.authority_namespace,
            "type": fence.authority_type,
            "id": fence.fence_id,
            "generation": str(fence.authority_generation),
            "digest": fence.digest,
        }
        if owner_refs[-1] != expected_fence_ref:
            reject()
        without_fence = dict(owner_request)
        without_fence["execution"] = {
            **actual_execution,
            "foreignReferences": previous_refs,
        }
        if canonical_digest(without_fence) != intent.runtime_arguments_digest:
            reject()
    except (TypeError, ValueError, KeyError) as error:
        raise ToolBridgeError(
            "Runtime Owner handoff has invalid canonical JSON or missing identity",
            kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
        ) from error


def _runtime_error_value(error: BaseException) -> dict[str, JsonValue]:
    if isinstance(error, HarnessRuntimeToolRejected):
        return {
            "type": type(error).__name__,
            "operation": error.operation,
            **error.detail.to_dict(),
            "safeToCorrect": error.detail.commit_state in {"not_started", "not_committed"},
        }
    return {
        "type": type(error).__name__,
        "message": str(error)[:2_048],
        "safeToCorrect": False,
    }


def _runtime_delivery_state(payload: dict[str, JsonValue]) -> str:
    """Return the safe Harness observation action from exact Runtime semantics.

    Runtime ``status`` is a compatibility summary and cannot decide whether physical
    execution has mechanically converged.  In particular, a succeeded resolution may
    still carry ``deliveryDisposition=reconciliation_required``.
    """

    execution_terminal = payload.get("executionTerminal")
    execution_disposition = payload.get("executionDisposition")
    delivery_disposition = payload.get("deliveryDisposition")
    recovery_required = payload.get("recoveryRequired")
    result_available = payload.get("resultAvailable")
    semantic_completion_evaluated = payload.get("semanticCompletionEvaluated")

    if not isinstance(execution_terminal, bool):
        raise HarnessRuntimeClientError("Runtime observation omitted executionTerminal")
    if execution_disposition is not None and (
        not isinstance(execution_disposition, str)
        or execution_disposition not in _RUNTIME_JOB_RESOLUTIONS
    ):
        raise HarnessRuntimeClientError("Runtime executionDisposition is invalid")
    if (
        not isinstance(delivery_disposition, str)
        or delivery_disposition not in _RUNTIME_DELIVERY_DISPOSITIONS
    ):
        raise HarnessRuntimeClientError("Runtime deliveryDisposition is invalid")
    if (
        delivery_disposition == "committed"
        and execution_disposition in _RUNTIME_UNCERTAIN_RESOLUTIONS
    ):
        raise HarnessRuntimeClientError(
            "Runtime committed executionDisposition contradicts uncertain resolution"
        )
    if not isinstance(recovery_required, bool):
        raise HarnessRuntimeClientError("Runtime observation omitted recoveryRequired")
    if not isinstance(result_available, bool):
        raise HarnessRuntimeClientError("Runtime observation omitted resultAvailable")
    if semantic_completion_evaluated is not False:
        raise HarnessRuntimeClientError("Runtime must not claim Harness/domain semantic completion")

    if recovery_required or delivery_disposition == "reconciliation_required":
        return "reconcile"
    if delivery_disposition == "unknown":
        # Native PG cancellation can commit a LOST control result with only
        # native-stop evidence, no Runner result.json and resultAvailable=False.
        # This is still an uncertain physical outcome, never an observed Tool
        # success. Older Runtime variants may retain a separate lost receipt.
        if not execution_terminal or execution_disposition != "lost":
            raise HarnessRuntimeClientError("Runtime unknown delivery projection is inconsistent")
        return "unknown"
    if delivery_disposition == "in_progress":
        if execution_terminal or execution_disposition is not None or result_available:
            raise HarnessRuntimeClientError("Runtime in-progress projection is inconsistent")
        return "reconcile"
    if not execution_terminal or execution_disposition is None or not result_available:
        raise HarnessRuntimeClientError("Runtime committed terminal projection is incomplete")
    return "terminal"
