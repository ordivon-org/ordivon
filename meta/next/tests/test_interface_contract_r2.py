from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.cognitive_circuit_r1 import (
    CircuitContractError,
    canonical_digest,
    compile_manifest,
    evaluate_gate_results,
    validate_manifest,
)
from scripts.interface_contract_r2 import evaluate_interface

ROOT = Path(__file__).resolve().parents[1]
DOGFOOD = (
    ROOT
    / "evidence"
    / "acceptance"
    / "interface-contract-r2-gateway-client-dogfood-20260922.json"
)


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _default_circuit_ref() -> dict:
    return {
        "id": "circuit:gateway-client-r2",
        "digest": _digest("circuit-manifest"),
    }


def direct_observation(
    *,
    digest: str | None = None,
    interface_id: str = "mcp:gateway-tools",
    circuit_ref: dict | None = None,
) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.interface-contract-observation",
        "observationId": "observation:gateway-direct-r2",
        "circuitRef": copy.deepcopy(circuit_ref or _default_circuit_ref()),
        "producerOwnerId": "gateway",
        "sourceKind": "direct-owner-observation",
        "sourceRef": "evidence:gateway-tools-list-r2",
        "sourceDigest": _digest("gateway-tools-list-evidence"),
        "interfaceRef": {
            "id": interface_id,
            "digest": digest or _digest("gateway-interface-required"),
        },
        "projectedAuthorityVersionRef": None,
        "liveAuthorityVersionRef": None,
        "nonClaims": [
            "A direct owner observation is point-in-time evidence, not durable freshness."
        ],
    }


def retained_observation(
    *,
    live: str | None,
    projected: str,
    digest: str | None = None,
    circuit_ref: dict | None = None,
) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.interface-contract-observation",
        "observationId": "observation:retained-gateway-r2",
        "circuitRef": copy.deepcopy(circuit_ref or _default_circuit_ref()),
        "producerOwnerId": "gateway",
        "sourceKind": "retained-projection",
        "sourceRef": "evidence:retained-gateway-projection",
        "sourceDigest": _digest("retained-projection"),
        "interfaceRef": {
            "id": "mcp:gateway-tools",
            "digest": digest or _digest("gateway-interface-required"),
        },
        "projectedAuthorityVersionRef": projected,
        "liveAuthorityVersionRef": live,
        "nonClaims": ["Transport or Git recency does not mint interface authority."],
    }


def expectation() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.interface-contract-expectation",
        "expectationId": "expectation:gateway-tools-r2",
        "consumerId": "consumer:test",
        "circuitRef": _default_circuit_ref(),
        "interfaceId": "mcp:gateway-tools",
        "requiredDigest": _digest("gateway-interface-required"),
        "acceptedSourceKinds": [
            "direct-owner-observation",
            "client-effective-surface",
            "retained-projection",
        ],
        "acceptedAlternates": [],
        "supportScope": "Gateway MCP Tool identity/schema seam only",
        "nonClaims": [
            "A matching owner surface does not prove a connector refreshed its snapshot."
        ],
    }


def dogfood() -> dict:
    return json.loads(DOGFOOD.read_text(encoding="utf-8"))


def gateway_connector_manifest() -> dict:
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:gateway-client-interface-r2",
        "objectiveRef": {
            "id": "objective:gateway-client-surface-currentness",
            "digest": _digest("gateway-client-surface-objective"),
        },
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:gateway-owner",
                "ownerId": "gateway",
                "responsibility": "Expose the accepted Gateway interface surface.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["accepted-release"],
                "outputs": ["gateway-interface"],
            },
            {
                "id": "stage:connector-client",
                "ownerId": "connector-client",
                "responsibility": "Expose the client-effective Gateway interface surface.",
                "dependsOn": ["stage:gateway-owner"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["gateway-interface"],
                "outputs": ["client-interface"],
            },
        ],
        "edges": [
            {
                "id": "edge:gateway-to-client",
                "from": {
                    "stageId": "stage:gateway-owner",
                    "port": "gateway-interface",
                },
                "to": {
                    "stageId": "stage:connector-client",
                    "port": "gateway-interface",
                },
                "contractRef": "contract:gateway-interface",
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:gateway-client-currentness",
                "producerStageId": "stage:gateway-owner",
                "consumerStageId": "stage:connector-client",
                "assumption": "The client sees an explicitly accepted Gateway interface.",
                "guarantee": "Gateway owner surface has an exact interface digest.",
                "verifierOwnerId": "connector-client",
                "supportScope": "Gateway MCP Tool identity/schema seam only",
                "required": True,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Circuit compilation does not refresh the connector catalog.",
            "Interface compatibility does not establish domain acceptance.",
        ],
    }
    validate_manifest(manifest)
    return manifest


def _manifest_circuit_ref(manifest: dict) -> dict:
    return {
        "id": manifest["circuitId"],
        "digest": canonical_digest(manifest),
    }


def test_real_gateway_connector_dogfood_reproduces_mismatch() -> None:
    case = dogfood()
    assert case["ownerSurface"]["digest"] == canonical_digest(
        case["ownerSurface"]["tools"]
    )
    assert case["clientEffectiveSurface"]["digest"] == canonical_digest(
        case["clientEffectiveSurface"]["tools"]
    )

    manifest = gateway_connector_manifest()
    circuit_ref = _manifest_circuit_ref(manifest)
    exp = expectation()
    exp["circuitRef"] = circuit_ref
    exp["requiredDigest"] = case["ownerSurface"]["digest"]
    exp["acceptedSourceKinds"] = ["client-effective-surface"]

    observation = direct_observation(
        digest=case["clientEffectiveSurface"]["digest"],
        circuit_ref=circuit_ref,
    )
    observation["sourceKind"] = "client-effective-surface"
    observation["observationId"] = "observation:gateway-attached-connector-20260922"
    observation["sourceRef"] = "connector:chatgpt:ordivon-gateway:attached-20260922"
    observation["sourceDigest"] = case["clientEffectiveSurface"]["digest"]

    result = evaluate_interface(observation, exp)

    expected = case["expectedR2Classification"]
    assert result["compatibilityStanding"] == expected["compatibilityStanding"]
    assert result["compatibilityReasonCode"] == expected["compatibilityReasonCode"]
    assert result["currentnessStanding"] == expected["currentnessStanding"]
    assert result["evidenceAdmissibility"] == expected["evidenceAdmissibility"]
    assert result["admissibilityReasonCode"] == expected["admissibilityReasonCode"]


def test_r2_result_can_carry_evidence_into_r1_gate_without_lifting_domain_truth() -> (
    None
):
    case = dogfood()
    manifest = gateway_connector_manifest()
    compiled = compile_manifest(manifest)
    circuit_ref = _manifest_circuit_ref(manifest)
    exp = expectation()
    exp["circuitRef"] = circuit_ref
    exp["requiredDigest"] = case["ownerSurface"]["digest"]

    owner_observation = direct_observation(
        digest=case["ownerSurface"]["digest"],
        circuit_ref=circuit_ref,
    )
    owner_observation["sourceRef"] = (
        "docs:architecture:GATEWAY_HOST_NORTHBOUND_ACCEPTANCE_20260922"
    )
    owner_observation["sourceDigest"] = case["ownerSurface"]["digest"]

    evaluation = evaluate_interface(owner_observation, exp)
    assert evaluation["compatibilityStanding"] == "EXACT_MATCH"
    assert evaluation["currentnessStanding"] == "POINT_IN_TIME_OBSERVED"
    assert evaluation["evidenceAdmissibility"] == "ADMISSIBLE"

    gate_result = {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compiled["manifestDigest"],
        "gateId": "gate:gateway-client-currentness",
        "verifierOwnerId": "connector-client",
        "standing": "SATISFIED",
        "evidenceRefs": [evaluation["evidenceRef"]],
        "supportScope": "Gateway MCP Tool identity/schema seam only",
        "nonClaims": ["Interface compatibility does not establish domain acceptance."],
    }
    projection = evaluate_gate_results(manifest, [gate_result])

    assert projection["mechanicalClosure"] is True
    assert projection["domainAcceptanceEstablished"] is False


def test_expectation_binds_a_valid_r1_cognitive_circuit() -> None:
    manifest = gateway_connector_manifest()
    circuit_ref = _manifest_circuit_ref(manifest)
    exp = expectation()
    exp["circuitRef"] = circuit_ref

    result = evaluate_interface(
        direct_observation(circuit_ref=circuit_ref),
        exp,
    )

    assert result["circuitRef"] == circuit_ref
    assert result["compatibilityStanding"] == "EXACT_MATCH"


def test_exact_digest_match_is_deterministic_and_point_in_time() -> None:
    observation = direct_observation()
    exp = expectation()

    first = evaluate_interface(observation, exp)
    second = evaluate_interface(copy.deepcopy(observation), copy.deepcopy(exp))

    assert first == second
    assert first["compatibilityStanding"] == "EXACT_MATCH"
    assert first["compatibilityReasonCode"] == "EXACT_DIGEST_MATCH"
    assert first["currentnessStanding"] == "POINT_IN_TIME_OBSERVED"
    assert first["evidenceAdmissibility"] == "ADMISSIBLE"
    assert first["admissibilityReasonCode"] == "ACCEPTED_POINT_IN_TIME"
    assert first["domainAcceptanceEstablished"] is False
    assert first["evidenceRef"].startswith("interface-compatibility:sha256:")


def test_alternate_digest_requires_explicit_compatibility_declaration() -> None:
    alternate = _digest("compatible-alternate")
    observation = direct_observation(digest=alternate)
    exp = expectation()

    mismatch = evaluate_interface(observation, exp)
    assert mismatch["compatibilityStanding"] == "MISMATCH"
    assert mismatch["evidenceAdmissibility"] == "INADMISSIBLE"

    exp["acceptedAlternates"] = [
        {
            "digest": alternate,
            "compatibilityEvidenceRef": "evidence:gateway-backcompat-r2",
        }
    ]
    compatible = evaluate_interface(observation, exp)
    assert compatible["compatibilityStanding"] == "COMPATIBLE_BY_DECLARATION"
    assert compatible["compatibilityReasonCode"] == "EXPLICIT_ALTERNATE_ACCEPTED"
    assert compatible["evidenceAdmissibility"] == "ADMISSIBLE"
    assert "evidence:gateway-backcompat-r2" in compatible["evidenceRefs"]


def test_duplicate_alternate_digest_fails_closed() -> None:
    alternate = _digest("compatible-alternate")
    exp = expectation()
    exp["acceptedAlternates"] = [
        {
            "digest": alternate,
            "compatibilityEvidenceRef": "evidence:compatibility-a",
        },
        {
            "digest": alternate,
            "compatibilityEvidenceRef": "evidence:compatibility-b",
        },
    ]

    with pytest.raises(CircuitContractError, match="duplicate accepted alternate"):
        evaluate_interface(direct_observation(digest=alternate), exp)


def test_semver_or_version_label_is_not_a_compatibility_input() -> None:
    observation = direct_observation(digest=_digest("new-major-looking-interface"))
    observation["serverVersion"] = "99.0.0"

    with pytest.raises(CircuitContractError, match="schema violation"):
        evaluate_interface(observation, expectation())


def test_wrong_interface_id_is_mismatch_without_corrupting_currentness() -> None:
    result = evaluate_interface(
        direct_observation(interface_id="mcp:different-tools"),
        expectation(),
    )

    assert result["compatibilityStanding"] == "MISMATCH"
    assert result["compatibilityReasonCode"] == "INTERFACE_ID_MISMATCH"
    assert result["currentnessStanding"] == "POINT_IN_TIME_OBSERVED"
    assert result["evidenceAdmissibility"] == "INADMISSIBLE"
    assert result["admissibilityReasonCode"] == "INTERFACE_MISMATCH"


def test_source_kind_not_accepted_does_not_change_compatibility_fact() -> None:
    observation = direct_observation()
    exp = expectation()
    exp["acceptedSourceKinds"] = ["client-effective-surface"]

    result = evaluate_interface(observation, exp)

    assert result["compatibilityStanding"] == "EXACT_MATCH"
    assert result["currentnessStanding"] == "POINT_IN_TIME_OBSERVED"
    assert result["evidenceAdmissibility"] == "INADMISSIBLE"
    assert result["admissibilityReasonCode"] == "SOURCE_KIND_NOT_ACCEPTED"


def test_retained_projection_currentness_is_orthogonal_to_compatibility() -> None:
    version = _digest("authority-version")

    current = evaluate_interface(
        retained_observation(live=version, projected=version),
        expectation(),
    )
    assert current["compatibilityStanding"] == "EXACT_MATCH"
    assert current["currentnessStanding"] == "CURRENT_DECLARED"
    assert current["evidenceAdmissibility"] == "ADMISSIBLE"
    assert current["admissibilityReasonCode"] == "ACCEPTED_CURRENT_DECLARED"

    stale = evaluate_interface(
        retained_observation(live=_digest("new-authority"), projected=version),
        expectation(),
    )
    assert stale["compatibilityStanding"] == "EXACT_MATCH"
    assert stale["currentnessStanding"] == "HISTORICAL_NOT_CURRENT"
    assert stale["evidenceAdmissibility"] == "INADMISSIBLE"
    assert stale["admissibilityReasonCode"] == "OBSERVATION_HISTORICAL"

    unknown = evaluate_interface(
        retained_observation(live=None, projected=version),
        expectation(),
    )
    assert unknown["compatibilityStanding"] == "EXACT_MATCH"
    assert unknown["currentnessStanding"] == "CURRENTNESS_UNKNOWN"
    assert unknown["evidenceAdmissibility"] == "UNKNOWN"
    assert unknown["admissibilityReasonCode"] == "CURRENTNESS_UNKNOWN"


def test_explicit_compatibility_can_remain_true_while_retained_evidence_is_stale() -> (
    None
):
    version = _digest("authority-version")
    alternate = _digest("compatible-alternate")
    exp = expectation()
    exp["acceptedAlternates"] = [
        {
            "digest": alternate,
            "compatibilityEvidenceRef": "evidence:gateway-backcompat-r2",
        }
    ]

    result = evaluate_interface(
        retained_observation(
            live=_digest("new-authority"),
            projected=version,
            digest=alternate,
        ),
        exp,
    )

    assert result["compatibilityStanding"] == "COMPATIBLE_BY_DECLARATION"
    assert result["currentnessStanding"] == "HISTORICAL_NOT_CURRENT"
    assert result["evidenceAdmissibility"] == "INADMISSIBLE"


def test_observation_and_expectation_for_different_circuits_fail_closed() -> None:
    observation = direct_observation()
    exp = expectation()
    exp["circuitRef"]["digest"] = _digest("different-circuit")

    with pytest.raises(CircuitContractError, match="circuitRef mismatch"):
        evaluate_interface(observation, exp)


def test_git_or_transport_recency_cannot_be_added_as_currentness_authority() -> None:
    version = _digest("authority-version")
    observation = retained_observation(live=version, projected=version)
    observation["gitHead"] = "deadbeef"

    with pytest.raises(CircuitContractError, match="schema violation"):
        evaluate_interface(observation, expectation())


def test_client_effective_surface_is_point_in_time_not_permanently_live() -> None:
    observation = direct_observation()
    observation["sourceKind"] = "client-effective-surface"
    observation["observationId"] = "observation:chatgpt-effective-surface"
    observation["sourceRef"] = "evidence:chatgpt-effective-tools"

    result = evaluate_interface(observation, expectation())

    assert result["currentnessStanding"] == "POINT_IN_TIME_OBSERVED"
    assert result["compatibilityStanding"] == "EXACT_MATCH"
    assert result["evidenceAdmissibility"] == "ADMISSIBLE"


def test_result_does_not_alias_mutable_input_objects() -> None:
    observation = direct_observation()
    exp = expectation()
    original_observed_digest = observation["interfaceRef"]["digest"]
    original_circuit_digest = exp["circuitRef"]["digest"]

    result = evaluate_interface(observation, exp)

    observation["interfaceRef"]["digest"] = _digest("mutated-observation")
    observation["circuitRef"]["digest"] = _digest("mutated-observation-circuit")
    exp["circuitRef"]["digest"] = _digest("mutated-circuit")

    assert result["observedInterfaceRef"]["digest"] == original_observed_digest
    assert result["circuitRef"]["digest"] == original_circuit_digest


def test_result_identity_changes_with_exact_circuit_binding() -> None:
    first_exp = expectation()
    first_observation = direct_observation()
    first = evaluate_interface(first_observation, first_exp)

    second_circuit = {
        "id": first_exp["circuitRef"]["id"],
        "digest": _digest("changed-circuit-manifest"),
    }
    second_exp = expectation()
    second_exp["circuitRef"] = copy.deepcopy(second_circuit)
    second_observation = direct_observation(circuit_ref=second_circuit)
    second = evaluate_interface(second_observation, second_exp)

    assert first["expectationDigest"] != second["expectationDigest"]
    assert first["observationDigest"] != second["observationDigest"]
    assert first["resultDigest"] != second["resultDigest"]
    assert first["circuitRef"] != second["circuitRef"]
