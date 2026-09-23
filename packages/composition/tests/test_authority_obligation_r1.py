from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ordivon_composition import (
    AuthorityObligationError,
    canonical_digest,
    compile_authority_obligations,
    compile_manifest,
    validate_authority_obligation_set,
)


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _manifest() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:authority-obligation-r1",
        "objectiveRef": {"id": "objective:bounded-effect", "digest": _digest("objective")},
        "methodBindings": [],
        "capabilityBindings": [
            {
                "id": "capability:artifact-read",
                "capability": "artifact.runtime",
                "ownerId": "runtime.linux",
                "sourceKind": "gateway-projection",
                "bindingDigest": _digest("capability"),
                "truthBoundary": "Runtime owns artifact bytes; Gateway is routing only.",
            }
        ],
        "stages": [
            {
                "id": "stage:read-artifact",
                "ownerId": "runtime.linux",
                "responsibility": "Read one exact Runtime artifact after external authority admission.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": ["capability:artifact-read"],
                "inputs": ["operation-ref"],
                "outputs": ["artifact-bytes"],
            }
        ],
        "edges": [],
        "gateRequirements": [],
        "unresolvedAssumptions": [],
        "nonClaims": ["Circuit compilation does not authorize artifact access."],
    }


def _requirements(manifest: dict | None = None) -> dict:
    manifest = manifest or _manifest()
    compiled = compile_manifest(manifest)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.authority-requirement-set",
        "circuitRef": {
            "id": manifest["circuitId"],
            "digest": compiled["manifestDigest"],
        },
        "requirements": [
            {
                "id": "authority:artifact-read",
                "stageId": "stage:read-artifact",
                "capabilityBindingId": "capability:artifact-read",
                "authorityOwnerId": "security",
                "authorityContractRef": {
                    "id": "security:gateway-capability-authz-v1",
                    "digest": _digest("gateway-capability-authz-v1"),
                },
                "required": True,
                "nonClaims": [
                    "The referenced Security contract remains the external authority owner."
                ],
            }
        ],
        "nonClaims": [
            "Requirement authorship declares a prerequisite; it does not prove effect coverage."
        ],
    }


def test_compile_is_deterministic_and_grants_no_authority() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    first = compile_authority_obligations(manifest, requirements)
    second = compile_authority_obligations(copy.deepcopy(manifest), copy.deepcopy(requirements))

    assert first == second
    assert first["requiredObligationIds"] == ["authority:artifact-read"]
    assert first["mechanicalBindingEstablished"] is True
    assert first["effectCoverageEstablished"] is False
    assert first["authorityGranted"] is False
    assert first["executionAuthorityGranted"] is False
    obligation = first["obligations"][0]
    assert obligation["capability"] == "artifact.runtime"
    assert obligation["capabilityOwnerId"] == "runtime.linux"
    assert obligation["authorityOwnerId"] == "security"
    assert obligation["authorityGranted"] is False


def test_empty_requirements_do_not_claim_effect_coverage() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    requirements["requirements"] = []
    result = compile_authority_obligations(manifest, requirements)

    assert result["obligations"] == []
    assert result["effectCoverageEstablished"] is False
    assert result["authorityGranted"] is False


def test_stale_circuit_ref_fails_closed() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    requirements["circuitRef"]["digest"] = _digest("stale")

    with pytest.raises(AuthorityObligationError) as error:
        compile_authority_obligations(manifest, requirements)
    assert error.value.code == "CIRCUIT_REF_MISMATCH"


def test_unknown_stage_fails_closed() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    requirements["requirements"][0]["stageId"] = "stage:unknown"

    with pytest.raises(AuthorityObligationError) as error:
        compile_authority_obligations(manifest, requirements)
    assert error.value.code == "UNKNOWN_STAGE"


def test_unknown_capability_binding_fails_closed() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    requirements["requirements"][0]["capabilityBindingId"] = "capability:unknown"

    with pytest.raises(AuthorityObligationError) as error:
        compile_authority_obligations(manifest, requirements)
    assert error.value.code == "UNKNOWN_CAPABILITY_BINDING"


def test_capability_must_be_bound_to_target_stage() -> None:
    manifest = _manifest()
    manifest["stages"][0]["capabilityBindings"] = []
    requirements = _requirements(manifest)

    with pytest.raises(AuthorityObligationError) as error:
        compile_authority_obligations(manifest, requirements)
    assert error.value.code == "CAPABILITY_NOT_BOUND_TO_STAGE"


def test_duplicate_requirement_id_fails_closed() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    requirements["requirements"].append(copy.deepcopy(requirements["requirements"][0]))

    with pytest.raises(AuthorityObligationError) as error:
        compile_authority_obligations(manifest, requirements)
    assert error.value.code == "DUPLICATE_AUTHORITY_REQUIREMENT"


def test_authority_decision_payloads_are_rejected() -> None:
    manifest = _manifest()
    requirements = _requirements(manifest)
    requirements["requirements"][0]["decision"] = "ALLOW"

    with pytest.raises(AuthorityObligationError) as error:
        compile_authority_obligations(manifest, requirements)
    assert error.value.code == "INVALID_AUTHORITY_CONTRACT"


def test_tampered_compiled_obligation_fails_closed() -> None:
    value = compile_authority_obligations(_manifest(), _requirements())
    value["obligations"][0]["authorityOwnerId"] = "composition"

    with pytest.raises(AuthorityObligationError) as error:
        validate_authority_obligation_set(value)
    assert error.value.code == "AUTHORITY_OBLIGATION_DIGEST_MISMATCH"


def test_module_does_not_import_owner_internals() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "ordivon_composition"
        / "authority_obligation_r1.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "ordivon_security",
        "ordivon_gateway",
        "ordivon_runtime",
        "ordivon_harness",
        "ordivon_host",
    ):
        assert forbidden not in source
