from __future__ import annotations

import copy

import pytest

from ordivon_composition import (
    AgentRunBindingError,
    canonical_digest,
    compile_agent_run_binding,
    require_ready_agent_run_binding,
    validate_agent_run_binding,
)


def _ref(label: str) -> dict[str, str]:
    return {"id": label, "digest": canonical_digest({"fixture": label})}


def _compile(**overrides):
    values = {
        "source_circuit_ref": _ref("circuit:engineering-r1"),
        "run_contract_ref": _ref("harness-run-contract:r1"),
        "adapter_binding_ref": _ref("adapter:provider-a"),
        "tool_binding_ref": _ref("tool-binding:engineering"),
        "execution_binding_ref": _ref("execution-binding:linux"),
        "cognition_binding_refs": (_ref("cognition:method-router"),),
        "unresolved_inputs": (),
    }
    values.update(overrides)
    return compile_agent_run_binding(**values)


def test_binding_is_deterministic_disposable_projection() -> None:
    first = _compile()
    second = _compile()

    assert first == second
    assert first["readyForHarness"] is True
    assert first["authorityGranted"] is False
    assert first["executionDispatched"] is False
    assert first["domainAcceptanceEstablished"] is False
    assert first["truthRole"] == "task-local-non-authoritative-agent-run-binding-projection"


def test_rebuild_after_projection_deletion_is_identical() -> None:
    first = _compile()
    retained_inputs = {
        "source_circuit_ref": copy.deepcopy(first["sourceCircuitRef"]),
        "run_contract_ref": copy.deepcopy(first["runContractRef"]),
        "adapter_binding_ref": copy.deepcopy(first["adapterBindingRef"]),
        "tool_binding_ref": copy.deepcopy(first["toolBindingRef"]),
        "execution_binding_ref": copy.deepcopy(first["executionBindingRef"]),
        "cognition_binding_refs": tuple(copy.deepcopy(first["cognitionBindingRefs"])),
        "unresolved_inputs": tuple(first["unresolvedInputs"]),
    }

    del first
    rebuilt = compile_agent_run_binding(**retained_inputs)

    assert rebuilt == _compile()


def test_unresolved_inputs_are_explicit_and_fail_ready_gate() -> None:
    value = _compile(unresolved_inputs=("tool-surface", "provider-currentness"))

    assert value["readyForHarness"] is False
    assert value["unresolvedInputs"] == ["provider-currentness", "tool-surface"]
    with pytest.raises(AgentRunBindingError) as error:
        require_ready_agent_run_binding(value)
    assert error.value.code == "UNRESOLVED_INPUTS"


def test_digest_tampering_fails_closed() -> None:
    value = _compile()
    value["claimBoundary"] = "widened authority claim"

    with pytest.raises(AgentRunBindingError) as error:
        validate_agent_run_binding(value)
    assert error.value.code == "BINDING_DIGEST_MISMATCH"


def test_duplicate_cognition_binding_fails_closed() -> None:
    duplicate = _ref("cognition:method-router")
    with pytest.raises(AgentRunBindingError) as error:
        _compile(cognition_binding_refs=(duplicate, copy.deepcopy(duplicate)))
    assert error.value.code == "DUPLICATE_COGNITION_BINDING"


def test_owner_native_refs_are_opaque_to_composition() -> None:
    value = _compile(
        run_contract_ref=_ref("harness-private-format:any-version"),
        adapter_binding_ref=_ref("provider-native:opaque"),
    )

    assert value["runContractRef"]["id"] == "harness-private-format:any-version"
    assert value["adapterBindingRef"]["id"] == "provider-native:opaque"
    assert value["authorityGranted"] is False


def test_unknown_authority_fields_are_rejected_by_schema() -> None:
    value = _compile()
    value["permissions"] = ["execution.linux"]

    with pytest.raises(AgentRunBindingError) as error:
        validate_agent_run_binding(value)
    assert error.value.code == "INVALID_BINDING"


def test_binding_module_does_not_import_owner_internals() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "ordivon_composition"
        / "agent_run_binding_r1.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "ordivon_harness",
        "ordivon_runtime",
        "ordivon_gateway",
        "ordivon_host",
    ):
        assert forbidden not in source


def test_binding_schema_cannot_grow_authority_payloads() -> None:
    import json
    from pathlib import Path

    schema = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "src"
            / "ordivon_composition"
            / "schemas"
            / "agent-run-binding-v1.schema.json"
        ).read_text(encoding="utf-8")
    )
    properties = set(schema["properties"])
    assert properties.isdisjoint(
        {
            "permissions",
            "credentials",
            "workflowState",
            "taskState",
            "providerSelection",
            "toolRegistry",
            "domainVerdict",
        }
    )
    assert schema["additionalProperties"] is False
