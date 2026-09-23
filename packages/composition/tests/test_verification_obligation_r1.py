from __future__ import annotations

import copy

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError, canonical_digest
from ordivon_composition.verification_obligation_r1 import (
    compile_verification_obligations,
    resolve_verifier_bindings,
    validate_obligation_set,
)


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _manifest(*, required: bool = True) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:verification-obligation-r1",
        "objectiveRef": {
            "id": "objective:verified-composition",
            "digest": _digest("objective"),
        },
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:producer",
                "ownerId": "producer",
                "responsibility": "Produce exact bounded output.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["input"],
                "outputs": ["candidate"],
            },
            {
                "id": "stage:consumer",
                "ownerId": "consumer",
                "responsibility": "Consume only a verified candidate.",
                "dependsOn": ["stage:producer"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["candidate"],
                "outputs": ["accepted"],
            },
        ],
        "edges": [
            {
                "id": "edge:producer-consumer",
                "from": {"stageId": "stage:producer", "port": "candidate"},
                "to": {"stageId": "stage:consumer", "port": "candidate"},
                "contractRef": "contract:candidate-r1",
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:candidate-contract",
                "producerStageId": "stage:producer",
                "consumerStageId": "stage:consumer",
                "assumption": "Consumer receives a candidate satisfying contract:candidate-r1.",
                "guarantee": "Producer emits a candidate bound to contract:candidate-r1.",
                "verifierOwnerId": "producer",
                "supportScope": "candidate contract seam only",
                "required": required,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Compilation grants no execution authority.",
            "Mechanical closure does not establish domain acceptance.",
        ],
    }


def _binding_set(obligation_set: dict, *, native: bool = False) -> dict:
    obligation = obligation_set["obligations"][0]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.task-local-verifier-binding-set",
        "circuitRef": copy.deepcopy(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindings": [
            {
                "gateId": obligation["gateId"],
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": obligation["verifierOwnerId"],
                "verifierRef": {
                    "id": "verifier:producer-native-r1",
                    "digest": _digest("producer-native-verifier"),
                },
                "verifierClass": "owner-native",
                "nativeSpecificationRef": (
                    {
                        "id": "spec:producer-contract-r1",
                        "digest": _digest("producer-contract-spec"),
                    }
                    if native
                    else None
                ),
                "supportScope": obligation["supportScope"],
                "nonClaims": ["Binding identifies a verifier; it does not execute or certify it."],
            }
        ],
        "nonClaims": [
            "Bindings are caller-authored and task-local.",
            "This set is not a verifier registry or authority grant.",
        ],
    }


def test_compile_obligations_is_deterministic_and_gate_compatible() -> None:
    manifest = _manifest()
    first = compile_verification_obligations(manifest)
    second = compile_verification_obligations(copy.deepcopy(manifest))

    assert first == second
    assert first["requiredGateIds"] == ["gate:candidate-contract"]
    obligation = first["obligations"][0]
    assert obligation["gateId"] == "gate:candidate-contract"
    assert obligation["requiredStanding"] == "SATISFIED"
    assert obligation["resultKind"] == "ordivon.composition-gate-result"
    assert obligation["circuitRef"] == first["circuitRef"]


def test_obligation_digest_tampering_fails_closed() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    obligation_set["obligations"][0]["guarantee"] = "widened guarantee"

    with pytest.raises(CircuitContractError, match="obligation digest mismatch"):
        validate_obligation_set(obligation_set)


def test_exact_binding_resolves_without_granting_authority() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    resolution = resolve_verifier_bindings(
        obligation_set,
        _binding_set(obligation_set),
    )

    assert resolution["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert resolution["mechanicalResolution"] is True
    assert resolution["executionAuthorityGranted"] is False
    assert resolution["domainAcceptanceEstablished"] is False
    assert resolution["missingRequiredGateIds"] == []


def test_missing_required_binding_remains_open() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    binding_set = _binding_set(obligation_set)
    binding_set["bindings"] = []

    resolution = resolve_verifier_bindings(obligation_set, binding_set)

    assert resolution["standing"] == "VERIFIER_BINDINGS_OPEN"
    assert resolution["mechanicalResolution"] is False
    assert resolution["missingRequiredGateIds"] == ["gate:candidate-contract"]


def test_unbound_optional_obligation_does_not_block_resolution() -> None:
    obligation_set = compile_verification_obligations(_manifest(required=False))
    binding_set = _binding_set(obligation_set)
    binding_set["bindings"] = []

    resolution = resolve_verifier_bindings(obligation_set, binding_set)

    assert resolution["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert resolution["unboundOptionalGateIds"] == ["gate:candidate-contract"]


def test_stale_obligation_set_binding_fails_closed() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    binding_set = _binding_set(obligation_set)
    binding_set["obligationSetDigest"] = _digest("stale-obligation-set")

    with pytest.raises(CircuitContractError, match="stale/different obligation set"):
        resolve_verifier_bindings(obligation_set, binding_set)


def test_binding_obligation_digest_mismatch_fails_closed() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    binding_set = _binding_set(obligation_set)
    binding_set["bindings"][0]["obligationDigest"] = _digest("different-obligation")

    with pytest.raises(CircuitContractError, match="obligation digest mismatch"):
        resolve_verifier_bindings(obligation_set, binding_set)


def test_binding_owner_mismatch_fails_closed() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    binding_set = _binding_set(obligation_set)
    binding_set["bindings"][0]["verifierOwnerId"] = "consumer"

    with pytest.raises(CircuitContractError, match="owner mismatch"):
        resolve_verifier_bindings(obligation_set, binding_set)


def test_binding_cannot_widen_support_scope() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    binding_set = _binding_set(obligation_set)
    binding_set["bindings"][0]["supportScope"] = "all producer and consumer semantics"

    with pytest.raises(CircuitContractError, match="support scope mismatch"):
        resolve_verifier_bindings(obligation_set, binding_set)


def test_unknown_or_duplicate_binding_fails_closed() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    unknown = _binding_set(obligation_set)
    unknown["bindings"][0]["gateId"] = "gate:unknown"

    with pytest.raises(CircuitContractError, match="unknown obligations"):
        resolve_verifier_bindings(obligation_set, unknown)

    duplicate = _binding_set(obligation_set)
    duplicate["bindings"].append(copy.deepcopy(duplicate["bindings"][0]))

    with pytest.raises(CircuitContractError, match="duplicate verifier binding"):
        resolve_verifier_bindings(obligation_set, duplicate)


def test_native_specification_reference_is_bound_but_not_interpreted() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    resolution = resolve_verifier_bindings(
        obligation_set,
        _binding_set(obligation_set, native=True),
    )

    native = resolution["resolvedBindings"][0]["nativeSpecificationRef"]
    assert native is not None
    assert native["id"] == "spec:producer-contract-r1"
    assert resolution["executionAuthorityGranted"] is False
