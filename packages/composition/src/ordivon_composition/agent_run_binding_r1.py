"""Deterministic, non-authoritative Agent Run binding projection.

This module binds already-selected, exact component references. It deliberately does not
select Providers, discover Tools or Skills, grant authority, execute work, own workflow
state, interpret HarnessRunContract payloads, or establish domain completion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cognitive_circuit_r1 import CircuitContractError, canonical_digest

ROOT = Path(__file__).resolve().parent
BINDING_SCHEMA = ROOT / "schemas" / "agent-run-binding-v1.schema.json"


class AgentRunBindingError(CircuitContractError):
    """Machine-classified binding error without inventing owner semantics."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _schema() -> dict[str, Any]:
    value = json.loads(BINDING_SCHEMA.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AgentRunBindingError(
            "INVALID_BINDING_SCHEMA", "binding schema root must be an object"
        )
    return value


def _validate_schema(value: dict[str, Any]) -> None:
    validator = Draft202012Validator(_schema())
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise AgentRunBindingError(
            "INVALID_BINDING",
            f"agent run binding schema violation at {location}: {first.message}",
        )


def _copy_ref(value: dict[str, str], label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise AgentRunBindingError("INVALID_BINDING_REF", f"{label} must be an object")
    if set(value) != {"id", "digest"}:
        raise AgentRunBindingError(
            "INVALID_BINDING_REF", f"{label} must contain exactly id and digest"
        )
    identifier = value.get("id")
    digest = value.get("digest")
    if not isinstance(identifier, str) or not identifier:
        raise AgentRunBindingError("INVALID_BINDING_REF", f"{label}.id must be non-empty")
    if not isinstance(digest, str) or not digest.startswith("sha256:") or len(digest) != 71:
        raise AgentRunBindingError("INVALID_BINDING_REF", f"{label}.digest must be sha256")
    return {"id": identifier, "digest": digest}


def compile_agent_run_binding(
    *,
    source_circuit_ref: dict[str, str],
    run_contract_ref: dict[str, str],
    adapter_binding_ref: dict[str, str],
    tool_binding_ref: dict[str, str] | None = None,
    execution_binding_ref: dict[str, str] | None = None,
    cognition_binding_refs: tuple[dict[str, str], ...] = (),
    unresolved_inputs: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Compile exact caller-selected references into one disposable Run binding projection."""

    cognition = [
        _copy_ref(value, f"cognition_binding_refs[{index}]")
        for index, value in enumerate(cognition_binding_refs)
    ]
    cognition_ids = [value["id"] for value in cognition]
    if len(cognition_ids) != len(set(cognition_ids)):
        raise AgentRunBindingError(
            "DUPLICATE_COGNITION_BINDING",
            "cognition binding references must have unique ids",
        )

    unresolved = sorted(set(unresolved_inputs))
    if any(
        not isinstance(value, str) or not value or value != value.strip() for value in unresolved
    ):
        raise AgentRunBindingError(
            "INVALID_UNRESOLVED_INPUT",
            "unresolved input identifiers must be non-empty trimmed strings",
        )

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.agent-run-binding",
        "truthRole": "task-local-non-authoritative-agent-run-binding-projection",
        "sourceCircuitRef": _copy_ref(source_circuit_ref, "source_circuit_ref"),
        "runContractRef": _copy_ref(run_contract_ref, "run_contract_ref"),
        "adapterBindingRef": _copy_ref(adapter_binding_ref, "adapter_binding_ref"),
        "toolBindingRef": (
            None if tool_binding_ref is None else _copy_ref(tool_binding_ref, "tool_binding_ref")
        ),
        "executionBindingRef": (
            None
            if execution_binding_ref is None
            else _copy_ref(execution_binding_ref, "execution_binding_ref")
        ),
        "cognitionBindingRefs": sorted(cognition, key=lambda item: (item["id"], item["digest"])),
        "unresolvedInputs": unresolved,
        "readyForHarness": not unresolved,
        "authorityGranted": False,
        "executionDispatched": False,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "This projection only binds exact caller-selected component identities for a bounded "
            "Agent Run. It does not interpret owner-native payloads, discover or rank providers, "
            "grant Tool/credential/execution authority, dispatch work, own workflow state, or "
            "establish semantic/domain acceptance."
        ),
    }
    projection["bindingDigest"] = canonical_digest(projection)
    validate_agent_run_binding(projection)
    return projection


def validate_agent_run_binding(value: dict[str, Any]) -> None:
    """Validate schema, deterministic digest, uniqueness, and readiness invariants."""

    _validate_schema(value)

    cognition_ids = [item["id"] for item in value["cognitionBindingRefs"]]
    if len(cognition_ids) != len(set(cognition_ids)):
        raise AgentRunBindingError(
            "DUPLICATE_COGNITION_BINDING",
            "cognition binding references must have unique ids",
        )

    if value["readyForHarness"] is not (not value["unresolvedInputs"]):
        raise AgentRunBindingError(
            "READINESS_MISMATCH",
            "readyForHarness must equal the absence of unresolvedInputs",
        )

    embedded = value["bindingDigest"]
    base = dict(value)
    del base["bindingDigest"]
    if canonical_digest(base) != embedded:
        raise AgentRunBindingError(
            "BINDING_DIGEST_MISMATCH",
            "agent run binding digest mismatch",
        )


def require_ready_agent_run_binding(value: dict[str, Any]) -> None:
    """Fail closed before a consumer attempts owner-specific lowering/execution."""

    validate_agent_run_binding(value)
    if value["unresolvedInputs"]:
        raise AgentRunBindingError(
            "UNRESOLVED_INPUTS",
            "agent run binding has unresolved inputs: " + ", ".join(value["unresolvedInputs"]),
        )


__all__ = [
    "AgentRunBindingError",
    "compile_agent_run_binding",
    "require_ready_agent_run_binding",
    "validate_agent_run_binding",
]
