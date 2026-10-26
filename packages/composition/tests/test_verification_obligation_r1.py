from __future__ import annotations

import copy

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError, canonical_digest
from ordivon_composition.verification_obligation_r1 import (
    compile_verification_obligations,
    resolve_verifier_bindings,
    select_impacted_obligations,
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


def test_cross_circuit_obligation_is_rejected_even_with_consistent_digests() -> None:
    obligation_set = compile_verification_obligations(_manifest())
    obligation = obligation_set["obligations"][0]
    obligation["circuitRef"] = {
        "id": "circuit:unrelated",
        "digest": _digest("unrelated-circuit"),
    }

    # Both hashes remain self-consistent: integrity is not identity binding.
    obligation_body = dict(obligation)
    del obligation_body["obligationDigest"]
    obligation["obligationDigest"] = canonical_digest(obligation_body)
    set_body = dict(obligation_set)
    del set_body["obligationSetDigest"]
    obligation_set["obligationSetDigest"] = canonical_digest(set_body)

    with pytest.raises(CircuitContractError, match="circuitRef mismatch"):
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


@pytest.mark.parametrize("optional_only", [False, True])
def test_zero_required_gates_cannot_claim_mechanical_verifier_closure(
    optional_only: bool,
) -> None:
    manifest = _manifest(required=False)
    if not optional_only:
        manifest["gateRequirements"] = []
    obligation_set = compile_verification_obligations(manifest)
    binding_set = {
        "schemaVersion": 1,
        "kind": "ordivon.task-local-verifier-binding-set",
        "circuitRef": copy.deepcopy(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindings": [],
        "nonClaims": ["No verification has occurred."],
    }
    result = resolve_verifier_bindings(obligation_set, binding_set)
    assert result["mechanicalResolution"] is False
    assert result["standing"] == "VERIFIER_BINDINGS_OPEN"
    assert result["missingRequiredGateIds"] == []
    assert result["executionAuthorityGranted"] is False
    assert result["domainAcceptanceEstablished"] is False


def test_unbound_optional_obligation_does_not_invent_required_resolution() -> None:
    obligation_set = compile_verification_obligations(_manifest(required=False))
    binding_set = _binding_set(obligation_set)
    binding_set["bindings"] = []

    resolution = resolve_verifier_bindings(obligation_set, binding_set)

    assert resolution["standing"] == "VERIFIER_BINDINGS_OPEN"
    assert resolution["mechanicalResolution"] is False
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


def _impact(*, graph=None, changed=None, unknown=None):
    return select_impacted_obligations(
        authority_refs=["source:runtime", "installed:runtime", "source:host"],
        obligations=graph
        if graph is not None
        else [
            {"id": "proof:runtime", "dependsOn": ["source:runtime"], "dependenciesComplete": True},
            {
                "id": "proof:composite",
                "dependsOn": ["proof:runtime", "installed:runtime"],
                "dependenciesComplete": True,
            },
            {"id": "proof:host", "dependsOn": ["source:host"], "dependenciesComplete": True},
        ],
        changed_refs=changed or [],
        unknown_refs=unknown or [],
    )


def _statuses(projection):
    return {r["id"]: r["standing"] for r in projection["standingByObligation"]}


def test_impact_selective_delta_preserves_independent_proof_candidate():
    result = _impact(changed=["source:runtime"])
    assert _statuses(result) == {
        "proof:runtime": "RECHECK_REQUIRED",
        "proof:composite": "RECHECK_REQUIRED",
        "proof:host": "REUSE_CANDIDATE",
    }
    assert result["basisDigest"] == _impact(changed=["source:runtime"])["basisDigest"]
    assert result["dependencyQualification"] == "CALLER_DECLARED_NOT_OWNER_CERTIFIED"
    assert result["proofReuseAdmissible"] is False
    assert result["proofAcceptanceEstablished"] is False


def test_impact_unknown_currentness_propagates_without_false_recheck():
    result = _impact(unknown=["installed:runtime"])
    assert _statuses(result) == {
        "proof:runtime": "REUSE_CANDIDATE",
        "proof:composite": "UNKNOWN",
        "proof:host": "REUSE_CANDIDATE",
    }


def test_impact_unresolved_dynamic_edges_never_promote_reuse():
    graph = [
        {"id": "proof:dynamic", "dependsOn": ["source:runtime"], "dependenciesComplete": False},
        {"id": "proof:consumer", "dependsOn": ["proof:dynamic"], "dependenciesComplete": True},
    ]
    assert _statuses(_impact(graph=graph)) == {
        "proof:dynamic": "UNKNOWN",
        "proof:consumer": "UNKNOWN",
    }
    assert _statuses(_impact(graph=graph, changed=["source:runtime"])) == {
        "proof:dynamic": "RECHECK_REQUIRED",
        "proof:consumer": "RECHECK_REQUIRED",
    }


def test_impact_unindexed_environment_delta_fails_closed():
    result = _impact(changed=["external:unknown-plugin"])
    assert result["unindexedChangeRefs"] == ["external:unknown-plugin"]
    assert set(_statuses(result).values()) == {"UNKNOWN"}


def test_impact_rejects_graph_cycles_missing_edges_and_fake_completeness():
    base = [{"id": "proof:a", "dependsOn": ["source:runtime"], "dependenciesComplete": True}]
    with pytest.raises(CircuitContractError, match="depends on unknown"):
        _impact(graph=[{**base[0], "dependsOn": ["source:missing"]}])
    with pytest.raises(CircuitContractError, match="dependency cycle"):
        _impact(
            graph=[
                {"id": "proof:a", "dependsOn": ["proof:b"], "dependenciesComplete": True},
                {"id": "proof:b", "dependsOn": ["proof:a"], "dependenciesComplete": True},
            ]
        )
    with pytest.raises(CircuitContractError, match="duplicate"):
        _impact(graph=base + base)
    with pytest.raises(CircuitContractError, match="JSON boolean"):
        _impact(graph=[{**base[0], "dependenciesComplete": "true"}])


def test_impact_bounded_dag_family_matches_independent_forward_oracle():
    from itertools import combinations

    names = ["proof:a", "proof:b", "proof:c"]
    arcs = [(names[a], names[b]) for a in range(3) for b in range(a + 1, 3)]
    roots = ["source:a", "source:b", "source:c"]
    for count in range(4):
        for chosen in combinations(arcs, count):
            rows = []
            for i, identity in enumerate(names):
                deps = [roots[i]] + [parent for parent, target in chosen if target == identity]
                rows.append({"id": identity, "dependsOn": deps, "dependenciesComplete": True})
            for mask in range(8):
                changed = [r for i, r in enumerate(roots) if mask & (1 << i)]
                result = select_impacted_obligations(
                    authority_refs=roots, obligations=rows, changed_refs=changed
                )
                impacted = set(changed)
                for identity in names:
                    item = next(r for r in rows if r["id"] == identity)
                    if any(dep in impacted for dep in item["dependsOn"]):
                        impacted.add(identity)
                assert {
                    identity
                    for identity, status in _statuses(result).items()
                    if status == "RECHECK_REQUIRED"
                } == impacted.intersection(names)


def test_impact_unobserved_source_dependency_exposes_a_non_authoritative_reuse_candidate():
    # Independent review challenge: the *real* readset includes source:runtime,
    # but a caller incorrectly declares a complete empty readset.
    # The pure algorithm cannot discover this missing edge. Its candidate
    # must never become owner-qualified reuse or evidence of a proved property.
    result = _impact(
        graph=[{"id": "proof:misdeclared", "dependsOn": [], "dependenciesComplete": True}],
        changed=["source:runtime"],
    )
    assert _statuses(result)["proof:misdeclared"] == "REUSE_CANDIDATE"
    assert result["proofReuseAdmissible"] is False
    assert result["proofAcceptanceEstablished"] is False


@pytest.mark.parametrize(
    "alias",
    (" source:runtime", "source:runtime ", ":runtime", "source:", "source:\u200dghost"),
)
@pytest.mark.parametrize("position", ("authority", "changed", "unknown", "id", "dependsOn"))
def test_impact_rejects_noncanonical_source_or_proof_identity(alias: str, position: str) -> None:
    # The source change must never bypass propagation through a spelling alias.
    authority = ["source:runtime"]
    changed = ["source:runtime"]
    unknown: list[str] = []
    obligation = {
        "id": "proof:runtime",
        "dependsOn": ["source:runtime"],
        "dependenciesComplete": True,
    }
    if position == "authority":
        authority.append(alias)
    elif position == "changed":
        changed.append(alias)
    elif position == "unknown":
        unknown.append(alias)
    elif position == "id":
        obligation["id"] = alias
    else:
        obligation["dependsOn"] = [alias]
    with pytest.raises(CircuitContractError, match="nonempty typed references"):
        select_impacted_obligations(
            authority_refs=authority,
            obligations=[obligation],
            changed_refs=changed,
            unknown_refs=unknown,
        )
