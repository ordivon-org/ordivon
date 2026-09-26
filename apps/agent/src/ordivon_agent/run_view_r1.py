from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ordivon_harness.api import HarnessAgentRun


class AgentRunViewError(ValueError):
    """A supplied Harness projection cannot be represented as a bounded product view."""


_PRODUCT_STATE = {
    "created": "ready",
    "active": "running",
    "paused": "attention_required",
    "stopped": "stopped",
    "completed": "run_finished",
    "failed": "failed",
}


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AgentRunViewError(f"{label} must be an object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AgentRunViewError(f"{label} must be a non-empty string")
    return value


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise AgentRunViewError(f"{label} must be boolean")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise AgentRunViewError(f"{label} must be a non-negative integer")
    return value


def project_harness_run_view_projection(
    composition_projection: Mapping[str, Any],
) -> dict[str, object]:
    """Lower one exact Harness explain projection into a read-only product view.

    This is deliberately lossy. The Harness projection remains the proof surface.
    The view never probes Provider/Runtime liveness and never establishes Task or
    domain completion.
    """

    projection = _mapping(composition_projection, "Harness composition projection")
    if projection.get("kind") != "ordivon.harness-process-composition-projection":
        raise AgentRunViewError("unsupported Harness composition projection kind")
    if projection.get("truthRole") != "derived-read-only-composition-projection":
        raise AgentRunViewError("Harness composition projection truth role differs")

    run = _mapping(projection.get("run"), "Harness composition run")
    durable = _mapping(projection.get("durableRun"), "Harness durable Run")
    process = _mapping(projection.get("processLocal"), "Harness process-local projection")

    harness_run_id = _text(run.get("harnessRunId"), "Harness Run identity")
    if _text(durable.get("harnessRunId"), "durable Harness Run identity") != harness_run_id:
        raise AgentRunViewError("Harness composition and durable Run identities differ")

    contract_digest = _text(run.get("contractDigest"), "Harness Contract digest")
    if _text(durable.get("contractDigest"), "durable Harness Contract digest") != contract_digest:
        raise AgentRunViewError("Harness composition and durable Contract digests differ")

    native_status = _text(durable.get("status"), "Harness Run status")
    try:
        state = _PRODUCT_STATE[native_status]
    except KeyError as error:
        raise AgentRunViewError(f"unsupported Harness Run status: {native_status}") from error

    adapter = _mapping(process.get("adapter"), "Harness Adapter projection")
    cognition = _mapping(process.get("cognition"), "Harness cognition projection")
    execution = _mapping(process.get("executionBinding"), "Harness execution binding projection")
    runtime = _mapping(process.get("runtimeClient"), "Harness Runtime client projection")
    tools = _mapping(process.get("customToolBridge"), "Harness Tool bridge projection")

    view: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.agent-run-view",
        "truthRole": "derived-read-only-product-projection",
        "harnessRunId": harness_run_id,
        "contractDigest": contract_digest,
        "state": state,
        "nativeStatus": native_status,
        "revision": _non_negative_int(durable.get("revision"), "Harness Run revision"),
        "updatedAtMs": _non_negative_int(durable.get("updatedAtMs"), "Harness Run update time"),
        "requestedModelId": _text(run.get("requestedModelId"), "requested model identity"),
        "composition": {
            "adapterBound": _boolean(adapter.get("supplied"), "Adapter supplied"),
            "cognitionBound": _boolean(cognition.get("supplied"), "cognition supplied"),
            "executionBindingBound": _boolean(
                execution.get("supplied"), "execution binding supplied"
            ),
            "runtimeClientBound": _boolean(runtime.get("supplied"), "Runtime client supplied"),
            "customToolBridgeBound": _boolean(tools.get("supplied"), "custom Tool bridge supplied"),
        },
        "semanticAcceptance": {
            "establishedByHarness": False,
            "state": "not-established",
        },
        "externalLiveness": "not-probed",
        "proofBoundary": (
            "This view is a lossy product projection. Harness status/composition remain the "
            "exact proof surface; Provider/Runtime liveness and Task/domain acceptance are "
            "not inferred."
        ),
    }
    return view


def project_harness_run_view(run: HarnessAgentRun) -> dict[str, object]:
    """Project one already validated in-process Harness Run for product display."""

    return project_harness_run_view_projection(run.explain())


__all__ = [
    "AgentRunViewError",
    "project_harness_run_view",
    "project_harness_run_view_projection",
]
