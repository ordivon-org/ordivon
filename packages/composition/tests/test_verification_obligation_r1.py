from __future__ import annotations

import copy

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError, canonical_digest
from ordivon_composition.verification_obligation_r1 import (
    classify_observed_environment_delta,
    compare_gate_source_scopes,
    compile_verification_obligations,
    resolve_verifier_bindings,
    select_impacted_obligations,
    select_manifest_gate_impacts,
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


def _env_observation(ref, value, *, known=True, epoch="baseline"):
    return {
        "ref": ref,
        "standing": "OBSERVED" if known else "UNKNOWN",
        "valueDigest": ("sha256:" + value * 64) if known else None,
        "witnessRef": f"runtime:observation:{ref}:{epoch}" if known else None,
    }


def test_environment_observation_bridge_scoped_change_and_unknown_do_not_fan_out():
    old = [
        _env_observation("config:network-proxy", "a"),
        _env_observation("installed:postgres-writer", "b"),
        _env_observation("config:media-renderer", "c"),
    ]
    now = [
        _env_observation("config:network-proxy", "d", epoch="current"),
        _env_observation("installed:postgres-writer", "b", epoch="current"),
        _env_observation("config:media-renderer", "c", epoch="current"),
    ]
    delta = classify_observed_environment_delta(previous=old, current=now)
    assert delta["changedRefs"] == ["config:network-proxy"]
    assert delta["unknownRefs"] == ["installed:postgres-writer"]
    assert delta["equalConfigurationRefs"] == ["config:media-renderer"]
    impact = select_impacted_obligations(
        authority_refs=[
            "config:network-proxy",
            "installed:postgres-writer",
            "config:media-renderer",
        ],
        obligations=[
            {
                "id": "proof:network",
                "dependsOn": ["config:network-proxy"],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:writer",
                "dependsOn": ["installed:postgres-writer"],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:media",
                "dependsOn": ["config:media-renderer"],
                "dependenciesComplete": True,
            },
            {"id": "proof:client", "dependsOn": ["proof:network"], "dependenciesComplete": True},
        ],
        changed_refs=delta["changedRefs"],
        unknown_refs=delta["unknownRefs"],
    )
    assert _statuses(impact) == {
        "proof:network": "RECHECK_REQUIRED",
        "proof:client": "RECHECK_REQUIRED",
        "proof:writer": "UNKNOWN",
        "proof:media": "REUSE_CANDIDATE",
    }
    assert impact["proofReuseAdmissible"] is False
    assert delta["proofReuseAdmissible"] is False


def test_observation_bridge_declared_env_absent_in_both_is_locally_unknown():
    # An omitted environment ref present in NEITHER observation envelope
    # cannot be mistaken for an unchanged qualified environment.
    delta = classify_observed_environment_delta(
        previous=[], current=[], required_refs=["installed:pg-writer"]
    )
    assert delta["unobservedRequiredRefs"] == ["installed:pg-writer"]
    assert delta["unknownRefs"] == ["installed:pg-writer"]
    result = select_impacted_obligations(
        authority_refs=["installed:pg-writer", "source:independent"],
        obligations=[
            {"id": "proof:pg", "dependsOn": ["installed:pg-writer"], "dependenciesComplete": True},
            {
                "id": "proof:other",
                "dependsOn": ["source:independent"],
                "dependenciesComplete": True,
            },
        ],
        changed_refs=delta["changedRefs"],
        unknown_refs=delta["unknownRefs"],
    )
    assert _statuses(result) == {
        "proof:pg": "UNKNOWN",
        "proof:other": "REUSE_CANDIDATE",
    }
    assert result["proofReuseAdmissible"] is False


def test_observation_bridge_declared_env_duplicate_and_forged_unknown_scope_reject():
    with pytest.raises(CircuitContractError, match="required environment refs"):
        classify_observed_environment_delta(
            previous=[], current=[], required_refs=["installed:pg-writer", "installed:pg-writer"]
        )
    with pytest.raises(CircuitContractError, match="required environment refs"):
        classify_observed_environment_delta(
            previous=[], current=[], required_refs=["source:cannot-pretend-this-is-observed-env"]
        )


def test_observation_bridge_rejects_effect_same_digest_as_continuity_proof():
    receipt = _env_observation("effect:remote-publish", "f")
    revoked = _env_observation("authority:provider-grant", "d")
    result = classify_observed_environment_delta(
        previous=[receipt, revoked],
        current=[receipt, revoked],
    )
    assert result["changedRefs"] == []
    assert result["unknownRefs"] == ["authority:provider-grant", "effect:remote-publish"]
    assert result["proofReuseAdmissible"] is False
    changed = classify_observed_environment_delta(
        previous=[receipt],
        current=[_env_observation("effect:remote-publish", "e")],
    )
    assert changed["changedRefs"] == ["effect:remote-publish"]
    assert changed["unknownRefs"] == []


def test_repeated_same_configuration_receipt_is_unknown_not_fresh_observation():
    same = _env_observation("config:proxy", "a")
    stale = classify_observed_environment_delta(previous=[same], current=[same])
    assert stale["unknownRefs"] == ["config:proxy"]
    assert stale["equalConfigurationRefs"] == []
    # Reusing one receipt at two snapshot labels is not a continuity witness.
    newer = classify_observed_environment_delta(
        previous=[same],
        current=[_env_observation("config:proxy", "a", epoch="new")],
    )
    assert newer["equalConfigurationRefs"] == ["config:proxy"]
    assert newer["proofReuseAdmissible"] is False


def test_environment_observation_missing_or_unindexed_fails_closed():
    old = [_env_observation("external:plugin-provider", "a")]
    missing = classify_observed_environment_delta(previous=old, current=[])
    assert missing["unknownRefs"] == ["external:plugin-provider"]
    # Actual graph has no declared edge for this provider, therefore the
    # existing projection cannot exclude any proof; no false narrow impact.
    result = select_impacted_obligations(
        authority_refs=["config:media-renderer"],
        obligations=[
            {
                "id": "proof:media",
                "dependsOn": ["config:media-renderer"],
                "dependenciesComplete": True,
            }
        ],
        changed_refs=[],
        unknown_refs=missing["unknownRefs"],
    )
    assert _statuses(result) == {"proof:media": "UNKNOWN"}
    assert result["unindexedChangeRefs"] == ["external:plugin-provider"]
    assert result["proofReuseAdmissible"] is False


def test_environment_observation_rejects_forged_digest_duplicate_and_unknown_witness():
    valid = _env_observation("config:network-proxy", "a")
    corrupt = [
        [{**valid, "valueDigest": "sha256:deadbeef"}],
        [valid, valid],
        [{**valid, "ref": "not-environment"}],
        [{**valid, "standing": "UNKNOWN"}],
    ]
    for rows in corrupt:
        with pytest.raises(CircuitContractError):
            classify_observed_environment_delta(previous=rows, current=[valid])
    assert classify_observed_environment_delta(
        previous=[_env_observation("authority:grant", "a", known=False)],
        current=[_env_observation("authority:grant", "a", known=True)],
    )["unknownRefs"] == ["authority:grant"]


def test_impact_basis_digest_is_invariant_under_dependency_set_permutation():
    # A proof's DAG prerequisites are a set, not an ordered execution sequence.
    def select(depends_on):
        return select_impacted_obligations(
            authority_refs=["source:a", "source:b"],
            obligations=[
                {
                    "id": "proof:combined",
                    "dependsOn": depends_on,
                    "dependenciesComplete": True,
                }
            ],
            changed_refs=["source:a"],
        )

    first = select(["source:a", "source:b"])
    swapped = select(["source:b", "source:a"])
    changed_graph = select(["source:a"])
    assert first["standingByObligation"] == swapped["standingByObligation"]
    assert first["basisDigest"] == swapped["basisDigest"]
    assert first["basisDigest"] != changed_graph["basisDigest"]
    assert first["proofReuseAdmissible"] is False


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
    # Cyclic proof dependencies are representable, but cannot bootstrap
    # themselves into verified reuse through caller completeness assertions.
    recursive = _impact(
        graph=[
            {"id": "proof:a", "dependsOn": ["proof:b"], "dependenciesComplete": True},
            {"id": "proof:b", "dependsOn": ["proof:a"], "dependenciesComplete": True},
        ]
    )
    assert _statuses(recursive) == {"proof:a": "UNKNOWN", "proof:b": "UNKNOWN"}
    assert recursive["cyclicObligationIds"] == ["proof:a", "proof:b"]
    assert recursive["proofReuseAdmissible"] is False
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


def test_impact_derives_changed_dependency_edges_without_caller_changed_refs():
    old = [
        {"id": "proof:p", "dependsOn": ["source:runtime"], "dependenciesComplete": True},
        {"id": "proof:q", "dependsOn": ["proof:p"], "dependenciesComplete": True},
        {"id": "proof:host", "dependsOn": ["source:host"], "dependenciesComplete": True},
    ]
    new = [dict(row) for row in old]
    new[0]["dependsOn"] = ["source:runtime", "source:host"]
    result = select_impacted_obligations(
        authority_refs=["source:runtime", "source:host"],
        obligations=new,
        changed_refs=[],
        previous_graph={"authorityRefs": ["source:runtime", "source:host"], "obligations": old},
    )
    assert result["derivedRelationChangedRefs"] == ["proof:p"]
    assert _statuses(result) == {
        "proof:p": "RECHECK_REQUIRED",
        "proof:q": "RECHECK_REQUIRED",
        "proof:host": "REUSE_CANDIDATE",
    }
    assert result["relationComparisonQualification"].startswith("CALLER_SUPPLIED")
    assert result["proofReuseAdmissible"] is False


def test_impact_relation_permutation_does_not_create_false_change():
    old = [
        {
            "id": "proof:p",
            "dependsOn": ["source:runtime", "source:host"],
            "dependenciesComplete": True,
        }
    ]
    current = [dict(old[0], dependsOn=["source:host", "source:runtime"])]
    args = {
        "authority_refs": ["source:host", "source:runtime"],
        "obligations": current,
        "changed_refs": [],
    }
    a = select_impacted_obligations(**args)
    b = select_impacted_obligations(
        **args,
        previous_graph={"authorityRefs": ["source:runtime", "source:host"], "obligations": old},
    )
    assert b["derivedRelationChangedRefs"] == []
    assert b["basisDigest"] == a["basisDigest"]
    assert _statuses(b)["proof:p"] == "REUSE_CANDIDATE"


def test_impact_dependency_completeness_change_and_deleted_relation_fail_closed():
    old = [{"id": "proof:p", "dependsOn": ["source:runtime"], "dependenciesComplete": True}]
    current = [dict(old[0], dependenciesComplete=False)]
    args = {
        "authority_refs": ["source:runtime"],
        "changed_refs": [],
        "previous_graph": {"authorityRefs": ["source:runtime"], "obligations": old},
    }
    result = select_impacted_obligations(obligations=current, **args)
    assert result["derivedRelationChangedRefs"] == ["proof:p"]
    assert _statuses(result)["proof:p"] == "RECHECK_REQUIRED"

    # A deleted source root cannot disappear silently from a previous-graph witness.
    deleted = select_impacted_obligations(
        authority_refs=["source:host"],
        obligations=[{"id": "proof:p", "dependsOn": ["source:host"], "dependenciesComplete": True}],
        changed_refs=[],
        previous_graph={
            "authorityRefs": ["source:runtime", "source:host"],
            "obligations": [
                {"id": "proof:p", "dependsOn": ["source:host"], "dependenciesComplete": True}
            ],
        },
    )
    assert "source:runtime" in deleted["derivedRelationChangedRefs"]
    assert deleted["unindexedChangeRefs"] == []
    assert _statuses(deleted) == {"proof:p": "REUSE_CANDIDATE"}
    assert deleted["proofReuseAdmissible"] is False


def test_retired_known_unconsumed_obligation_cannot_globally_poison_proof_impact():
    """A deleted historical leaf is indexed in the prior graph, not UNKNOWN.

    This is *only* task-local candidate selection. Neither completeness nor
    proof reuse is admitted from caller-authored graphs. A genuinely missing
    external ref must still fail closed.
    """
    kept = {
        "id": "proof:live",
        "dependsOn": ["source:active"],
        "dependenciesComplete": True,
    }
    retired = {
        "id": "proof:retired",
        "dependsOn": ["source:other"],
        "dependenciesComplete": True,
        "obligationDigest": _digest("retired-historical-proof"),
    }
    roots = ["source:active", "source:other"]
    prior = {"authorityRefs": roots, "obligations": [kept, retired]}
    params = {"authority_refs": roots, "obligations": [kept], "changed_refs": []}

    outcome = select_impacted_obligations(**params, previous_graph=prior)
    assert outcome["derivedRelationChangedRefs"] == ["proof:retired"]
    assert outcome["derivedContractChangedRefs"] == ["proof:retired"]
    assert outcome["unindexedChangeRefs"] == []
    assert _statuses(outcome) == {"proof:live": "REUSE_CANDIDATE"}
    assert not outcome["proofReuseAdmissible"]

    # If the retired proof was actually a prerequisite of the surviving one,
    # the current contract change itself must remain RECHECK_REQUIRED.
    previous_consumer = dict(kept, dependsOn=["proof:retired"])
    consumed = select_impacted_obligations(
        **params,
        previous_graph={
            "authorityRefs": roots,
            "obligations": [previous_consumer, retired],
        },
    )
    assert "proof:live" in consumed["derivedRelationChangedRefs"]
    assert _statuses(consumed) == {"proof:live": "RECHECK_REQUIRED"}

    # A foreign source missing from *both* graphs is still unindexed and
    # correctly contaminates all current reuse candidates with UNKNOWN.
    unresolved = select_impacted_obligations(
        **params,
        previous_graph=prior,
        unknown_refs=["external:unresolved-runtime-consumer"],
    )
    assert unresolved["unindexedChangeRefs"] == ["external:unresolved-runtime-consumer"]
    assert _statuses(unresolved) == {"proof:live": "UNKNOWN"}
    assert not unresolved["proofReuseAdmissible"]


def test_historical_source_root_retirement_does_not_poison_independent_proof():
    """A previously indexed, unconsumed root is not an unindexed runtime edge."""
    independent = {
        "id": "proof:independent",
        "dependsOn": ["source:live"],
        "dependenciesComplete": True,
    }
    current = {
        "authority_refs": ["source:live"],
        "obligations": [independent],
        "changed_refs": [],
    }
    previous = {
        "authorityRefs": ["source:retired", "source:live"],
        "obligations": [independent],
    }
    benign = select_impacted_obligations(**current, previous_graph=previous)
    assert benign["derivedRelationChangedRefs"] == ["source:retired"]
    assert benign["unindexedChangeRefs"] == []
    assert _statuses(benign) == {"proof:independent": "REUSE_CANDIDATE"}
    assert benign["proofReuseAdmissible"] is False

    # If an actual consumer dropped that root, its relation must be RECHECK.
    former = dict(independent, dependsOn=["source:retired", "source:live"])
    changed = select_impacted_obligations(
        **current, previous_graph={**previous, "obligations": [former]}
    )
    assert "proof:independent" in changed["derivedRelationChangedRefs"]
    assert _statuses(changed) == {"proof:independent": "RECHECK_REQUIRED"}

    # A caller's explicit unresolved reference is stronger than the mere
    # historical retirement; never suppress it as a known old-only node.
    unknown = select_impacted_obligations(
        **current, previous_graph=previous, unknown_refs=["source:retired"]
    )
    assert unknown["unindexedChangeRefs"] == ["source:retired"]
    assert _statuses(unknown) == {"proof:independent": "UNKNOWN"}
    assert unknown["proofReuseAdmissible"] is False


def test_impact_basis_digest_distinguishes_known_retirement_from_missing_dependency():
    """A selection cache key must distinguish UNKNOWN from a valid reuse candidate."""
    live = {
        "id": "proof:live",
        "dependsOn": ["source:live"],
        "dependenciesComplete": True,
    }
    retired = {
        "id": "proof:retired",
        "dependsOn": ["source:live"],
        "dependenciesComplete": True,
    }
    common = {
        "authority_refs": ["source:live"],
        "obligations": [live],
        "changed_refs": ["proof:retired"],
    }
    unresolved = select_impacted_obligations(**common)
    known_retirement = select_impacted_obligations(
        **common,
        previous_graph={"authorityRefs": ["source:live"], "obligations": [live, retired]},
    )
    assert _statuses(unresolved) == {"proof:live": "UNKNOWN"}
    assert _statuses(known_retirement) == {"proof:live": "REUSE_CANDIDATE"}
    assert unresolved["unindexedChangeRefs"] == ["proof:retired"]
    assert known_retirement["unindexedChangeRefs"] == []
    assert unresolved["basisDigest"] != known_retirement["basisDigest"]
    assert not unresolved["proofReuseAdmissible"]
    assert not known_retirement["proofReuseAdmissible"]


def test_explicit_unknown_retired_proof_is_not_suppressed_by_provenance():
    live = {"id": "proof:live", "dependsOn": ["source:live"], "dependenciesComplete": True}
    gone = {"id": "proof:retired", "dependsOn": ["source:live"], "dependenciesComplete": True}
    args = {"authority_refs": ["source:live"], "obligations": [live], "changed_refs": []}
    prev = {"authorityRefs": ["source:live"], "obligations": [live, gone]}
    result = select_impacted_obligations(
        **args, previous_graph=prev, unknown_refs=["proof:retired"]
    )
    assert result["derivedRelationChangedRefs"] == ["proof:retired"]
    assert result["unindexedChangeRefs"] == ["proof:retired"]
    assert _statuses(result) == {"proof:live": "UNKNOWN"}
    assert result["proofReuseAdmissible"] is False


def test_impact_rejects_malformed_previous_graph_but_refines_prior_cycle():

    obligation = {"id": "proof:a", "dependsOn": ["source:a"], "dependenciesComplete": True}
    args = {"authority_refs": ["source:a"], "obligations": [obligation], "changed_refs": []}
    invalids = [
        {"authorityRefs": ["source:a"], "obligations": [obligation, obligation]},
        {
            "authorityRefs": ["source:a"],
            "obligations": [
                {"id": "proof:b", "dependsOn": ["source:a"], "dependenciesComplete": "yes"}
            ],
        },
    ]
    for invalid in invalids:
        with pytest.raises(CircuitContractError):
            select_impacted_obligations(**args, previous_graph=invalid)

    # A historical cycle was a valid declared dependency pattern, not proof
    # that the old graph was discharged. A new acyclic graph must recheck the
    # changed relation instead of skipping it or accepting the old cycle.
    prior_cycle = {
        "authorityRefs": ["source:a"],
        "obligations": [{"id": "proof:a", "dependsOn": ["proof:a"], "dependenciesComplete": True}],
    }
    result = select_impacted_obligations(**args, previous_graph=prior_cycle)
    assert result["derivedRelationChangedRefs"] == ["proof:a"]
    assert _statuses(result) == {"proof:a": "RECHECK_REQUIRED"}
    assert result["cyclicObligationIds"] == []
    assert result["proofReuseAdmissible"] is False


def test_impact_relation_delta_matches_independent_full_graph_closure_randomized():
    from random import Random

    rng = Random(841842)
    roots = ["source:a", "source:b", "source:c"]
    proof_ids = ["proof:a", "proof:b", "proof:c"]

    def graph():
        result = []
        for i, identity in enumerate(proof_ids):
            possible = roots + proof_ids[:i]
            deps = [p for p in possible if rng.choice([False, True])]
            rng.shuffle(deps)
            result.append(
                {
                    "id": identity,
                    "dependsOn": deps,
                    "dependenciesComplete": rng.choice([False, True]),
                }
            )
        return result

    for _ in range(1200):
        old = graph()
        current = graph()
        projection = select_impacted_obligations(
            authority_refs=roots,
            obligations=current,
            changed_refs=[],
            previous_graph={"authorityRefs": list(reversed(roots)), "obligations": old},
        )
        old_index = {row["id"]: row for row in old}
        changed_proofs = {
            row["id"]
            for row in current
            if (
                set(row["dependsOn"]) != set(old_index[row["id"]]["dependsOn"])
                or row["dependenciesComplete"] != old_index[row["id"]]["dependenciesComplete"]
            )
        }
        impacted = set(changed_proofs)
        while True:
            next_impact = impacted | {
                row["id"] for row in current if any(d in impacted for d in row["dependsOn"])
            }
            if next_impact == impacted:
                break
            impacted = next_impact
        actual = {
            ref for ref, status in _statuses(projection).items() if status == "RECHECK_REQUIRED"
        }
        assert actual == impacted
        assert set(projection["derivedRelationChangedRefs"]) == changed_proofs
        assert projection["proofReuseAdmissible"] is False


def test_impact_real_compiler_guarantee_digest_delta_rechecks_downstream_without_edge_delta():
    before = compile_verification_obligations(_manifest())
    weaker = _manifest()
    weaker["gateRequirements"][0]["guarantee"] = (
        "Producer may emit a candidate not bound to the required contract."
    )
    after = compile_verification_obligations(weaker)
    original_digest = before["obligations"][0]["obligationDigest"]
    new_digest = after["obligations"][0]["obligationDigest"]
    assert original_digest != new_digest
    assert before["obligations"][0]["gateId"] == after["obligations"][0]["gateId"]

    def graph(digest):
        return [
            {
                "id": "proof:contract",
                "dependsOn": ["source:producer"],
                "dependenciesComplete": True,
                "obligationDigest": digest,
            },
            {"id": "proof:consumer", "dependsOn": ["proof:contract"], "dependenciesComplete": True},
            {"id": "proof:independent", "dependsOn": ["source:host"], "dependenciesComplete": True},
        ]

    old = graph(original_digest)
    current = graph(new_digest)
    result = select_impacted_obligations(
        authority_refs=["source:producer", "source:host"],
        obligations=current,
        changed_refs=[],
        previous_graph={"authorityRefs": ["source:host", "source:producer"], "obligations": old},
    )
    assert result["derivedRelationChangedRefs"] == []
    assert result["derivedContractChangedRefs"] == ["proof:contract"]
    assert result["derivedChangedRefs"] == ["proof:contract"]
    assert _statuses(result) == {
        "proof:contract": "RECHECK_REQUIRED",
        "proof:consumer": "RECHECK_REQUIRED",
        "proof:independent": "REUSE_CANDIDATE",
    }
    assert result["proofReuseAdmissible"] is False
    # Identical exact owner obligation digests yield no false relation change.
    same = select_impacted_obligations(
        authority_refs=["source:producer", "source:host"],
        obligations=current,
        changed_refs=[],
        previous_graph={
            "authorityRefs": ["source:producer", "source:host"],
            "obligations": graph(new_digest),
        },
    )
    assert same["derivedRelationChangedRefs"] == []
    assert same["derivedContractChangedRefs"] == []


def test_impact_contract_digest_input_downgrade_or_invalid_identity_fails_closed():
    digest = compile_verification_obligations(_manifest())["obligations"][0]["obligationDigest"]
    roots = ["source:a"]
    row = {
        "id": "proof:a",
        "dependsOn": roots,
        "dependenciesComplete": True,
        "obligationDigest": digest,
    }
    args = {"authority_refs": roots, "changed_refs": []}
    # Removing a previously known content identity is itself a semantic change.
    downgrade = select_impacted_obligations(
        **args,
        obligations=[{k: v for k, v in row.items() if k != "obligationDigest"}],
        previous_graph={"authorityRefs": roots, "obligations": [row]},
    )
    assert downgrade["derivedRelationChangedRefs"] == []
    assert downgrade["derivedContractChangedRefs"] == ["proof:a"]
    assert _statuses(downgrade)["proof:a"] == "RECHECK_REQUIRED"
    assert downgrade["proofReuseAdmissible"] is False

    for bad in ("0" * 64, "sha256:Z" * 9, "sha256:" + "0" * 63, "sha256:" + "0" * 63 + "G"):
        with pytest.raises(CircuitContractError, match="canonical sha256"):
            select_impacted_obligations(**args, obligations=[{**row, "obligationDigest": bad}])
        with pytest.raises(CircuitContractError, match="canonical sha256"):
            select_impacted_obligations(
                **args,
                obligations=[row],
                previous_graph={
                    "authorityRefs": roots,
                    "obligations": [{**row, "obligationDigest": bad}],
                },
            )


def test_impact_projection_digest_distinguishes_prior_graph_qualification():
    # Same effective impact is not the same evidence qualification.
    claim = {"id": "proof:a", "dependsOn": ["source:a"], "dependenciesComplete": True}
    args = {"authority_refs": ["source:a"], "obligations": [claim], "changed_refs": []}
    without = select_impacted_obligations(**args)
    with_equal_prior = select_impacted_obligations(
        **args, previous_graph={"authorityRefs": ["source:a"], "obligations": [claim]}
    )
    assert without["standingByObligation"] == with_equal_prior["standingByObligation"]
    assert (
        without["relationComparisonQualification"]
        != with_equal_prior["relationComparisonQualification"]
    )
    assert without["basisDigest"] == with_equal_prior["basisDigest"]
    assert without["projectionDigest"] != with_equal_prior["projectionDigest"]
    assert not without["proofReuseAdmissible"] and not with_equal_prior["proofReuseAdmissible"]


def test_impact_projection_digest_distinguishes_derived_vs_caller_declared_delta():
    claim = {"id": "proof:a", "dependsOn": ["source:a"], "dependenciesComplete": True}
    prior = {"id": "proof:a", "dependsOn": [], "dependenciesComplete": True}
    args = {"authority_refs": ["source:a"], "obligations": [claim]}
    caller = select_impacted_obligations(**args, changed_refs=["proof:a"])
    derived = select_impacted_obligations(
        **args,
        changed_refs=[],
        previous_graph={"authorityRefs": ["source:a"], "obligations": [prior]},
    )
    assert caller["standingByObligation"] == derived["standingByObligation"]
    assert caller["derivedRelationChangedRefs"] != derived["derivedRelationChangedRefs"]
    assert caller["basisDigest"] == derived["basisDigest"]
    assert caller["projectionDigest"] != derived["projectionDigest"]
    assert not caller["proofReuseAdmissible"] and not derived["proofReuseAdmissible"]


def test_impact_projection_digest_is_order_insensitive_for_equivalent_readsets():
    claim = {"id": "proof:a", "dependsOn": ["source:a", "source:b"], "dependenciesComplete": True}
    a = select_impacted_obligations(
        authority_refs=["source:a", "source:b"],
        obligations=[claim],
        changed_refs=[],
        previous_graph={
            "authorityRefs": ["source:a", "source:b"],
            "obligations": [claim],
        },
    )
    b = select_impacted_obligations(
        authority_refs=["source:b", "source:a"],
        obligations=[dict(claim, dependsOn=["source:b", "source:a"])],
        changed_refs=[],
        previous_graph={
            "authorityRefs": ["source:b", "source:a"],
            "obligations": [dict(claim, dependsOn=["source:b", "source:a"])],
        },
    )
    assert a["basisDigest"] == b["basisDigest"]
    assert a["projectionDigest"] == b["projectionDigest"]
    assert a["derivedRelationChangedRefs"] == b["derivedRelationChangedRefs"] == []


def test_gate_source_delta_preserves_independent_parallel_branch() -> None:
    before = _manifest()
    before["stages"].append(
        {
            "id": "stage:parallel",
            "ownerId": "parallel",
            "responsibility": "Independent branch.",
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": ["parallel-output"],
        }
    )
    after = copy.deepcopy(before)
    after["stages"][-1]["responsibility"] = "Independent branch v2."
    before_set = compile_verification_obligations(before)
    after_set = compile_verification_obligations(after)
    # Existing obligationDigest includes the whole manifest, so the old
    # admission receipt still correctly becomes stale.
    assert (
        before_set["obligations"][0]["obligationDigest"]
        != after_set["obligations"][0]["obligationDigest"]
    )
    delta = compare_gate_source_scopes(before, after)
    assert delta["unchangedGateIds"] == ["gate:candidate-contract"]
    assert delta["changedGateIds"] == []
    assert delta["previousManifestDigest"] != delta["currentManifestDigest"]
    assert delta["proofReuseAdmissible"] is False


@pytest.mark.parametrize(
    "mutation", ["gate", "producer", "consumer", "global_assumption", "incoming_edge"]
)
def test_gate_source_delta_detects_every_known_upstream_contract_change(mutation: str) -> None:
    before = _manifest()
    after = copy.deepcopy(before)
    if mutation == "gate":
        after["gateRequirements"][0]["guarantee"] = "Completely different guarantee."
    elif mutation == "producer":
        after["stages"][0]["responsibility"] = "Different producer responsibility."
    elif mutation == "consumer":
        after["stages"][1]["responsibility"] = "Different consumer responsibility."
    elif mutation == "global_assumption":
        after["unresolvedAssumptions"].append("Network is unavailable.")
    elif mutation == "incoming_edge":
        after["edges"][0]["contractRef"] = "contract:candidate-v2"
    delta = compare_gate_source_scopes(before, after)
    assert delta["changedGateIds"] == ["gate:candidate-contract"]
    assert delta["unchangedGateIds"] == []
    assert delta["proofReuseAdmissible"] is False


def test_gate_source_delta_normalizes_independent_order_without_unsafe_acceptance() -> None:
    before = _manifest()
    before["stages"].append(
        {
            "id": "stage:parallel",
            "ownerId": "parallel",
            "responsibility": "Independent.",
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": ["parallel"],
        }
    )
    after = copy.deepcopy(before)
    after["stages"].reverse()
    delta = compare_gate_source_scopes(before, after)
    assert delta["changedGateIds"] == []
    assert delta["unchangedGateIds"] == ["gate:candidate-contract"]
    assert delta["proofReuseAdmissible"] is False


def test_gate_source_delta_rejects_invalid_or_different_circuit() -> None:
    before = _manifest()
    after = copy.deepcopy(before)
    after["circuitId"] = "circuit:different"
    with pytest.raises(CircuitContractError, match="same circuitId"):
        compare_gate_source_scopes(before, after)
    after = copy.deepcopy(before)
    after["edges"][0]["to"]["port"] = "missing"
    with pytest.raises(CircuitContractError, match="target port is not declared"):
        compare_gate_source_scopes(before, after)


def test_gate_source_delta_can_feed_existing_impact_selector_without_verdict() -> None:
    before = _manifest()
    after = copy.deepcopy(before)
    after["gateRequirements"][0]["guarantee"] = "Changed."
    delta = compare_gate_source_scopes(before, after)
    impact = select_impacted_obligations(
        authority_refs=["source:runtime"],
        obligations=[
            {
                "id": "gate:candidate-contract",
                "dependsOn": ["source:runtime"],
                "dependenciesComplete": True,
            }
        ],
        changed_refs=delta["changedGateIds"],
    )
    assert _statuses(impact)["gate:candidate-contract"] == "RECHECK_REQUIRED"
    assert impact["proofReuseAdmissible"] is False


def test_gate_source_delta_detects_new_incoming_proof_requirement() -> None:
    before = _manifest()
    after = copy.deepcopy(before)
    extra = dict(after["gateRequirements"][0])
    extra["id"] = "gate:additional-consumer-premise"
    extra["guarantee"] = "Additional exact bound on the same consumer."
    after["gateRequirements"].append(extra)
    delta = compare_gate_source_scopes(before, after)
    assert delta["addedGateIds"] == ["gate:additional-consumer-premise"]
    assert delta["changedGateIds"] == ["gate:candidate-contract"]
    assert delta["proofReuseAdmissible"] is False


def test_gate_source_delta_retains_independent_local_source_when_parallel_gate_added() -> None:
    before = _manifest()
    before["stages"] += [
        {
            "id": "stage:parallel-producer",
            "ownerId": "another-producer",
            "responsibility": "Unrelated producer.",
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": ["parallel-port"],
        },
        {
            "id": "stage:parallel-consumer",
            "ownerId": "another-consumer",
            "responsibility": "Unrelated consumer.",
            "dependsOn": ["stage:parallel-producer"],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": ["parallel-port"],
            "outputs": ["parallel-result"],
        },
    ]
    after = copy.deepcopy(before)
    after["gateRequirements"].append(
        {
            **after["gateRequirements"][0],
            "id": "gate:parallel",
            "producerStageId": "stage:parallel-producer",
            "consumerStageId": "stage:parallel-consumer",
            "guarantee": "Independent parallel guarantee.",
        }
    )
    delta = compare_gate_source_scopes(before, after)
    assert delta["addedGateIds"] == ["gate:parallel"]
    assert delta["unchangedGateIds"] == ["gate:candidate-contract"]
    assert delta["changedGateIds"] == []
    assert delta["proofReuseAdmissible"] is False


def test_native_git_source_delta_selects_cas_without_rechecking_tla(tmp_path, monkeypatch):
    """Real Git and existing Composition selector: red CAS != model-source delta.

    The Git reader owns only SOURCE facts. No acceptance or installed property
    follows from a REUSE_CANDIDATE returned by this task-local selector.
    """
    import subprocess
    from pathlib import Path

    source_repo = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(source_repo))
    from tools.repo.source_history_legos import source_membership_delta

    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Ordivon Contract Test")
    git("config", "user.email", "contract@example.invalid")
    source_cut = "6e3b5e7205108662d3a0fa6cae23aa53411fce3c"
    # Consume the existing Runtime owner-facing formal trace manifest,
    # rather than embedding a second set of owner source paths in Composition.
    manifest_path = "services/runtime/formal/RuntimeDispatchR1.trace-r1.json"
    import json

    manifest = json.loads(
        subprocess.check_output(
            ["git", "-C", str(source_repo), "show", f"{source_cut}:{manifest_path}"],
        )
    )
    prefix = Path(manifest_path).parents[1].as_posix() + "/"
    cas = prefix + next(
        item["path"] for item in manifest["contractSeams"] if item["id"] == "Registry.dispatchCAS"
    )
    model = prefix + manifest["formalSpecification"]["modulePath"]
    other = prefix + "formal/README.md"
    for item in [cas, model]:
        output = subprocess.check_output(
            ["git", "-C", str(source_repo), "show", f"{source_cut}:{item}"]
        )
        location = tmp_path / item
        location.parent.mkdir(parents=True, exist_ok=True)
        location.write_bytes(output)
    (tmp_path / other).write_text("Unrelated Runtime documentation.")
    (tmp_path / "README.md").write_text("Outside scoped Git source.")
    git("add", ".")
    git("commit", "-qm", "frozen runtime source")
    baseline = git("rev-parse", "HEAD")

    def inspect(old: str, new: str, *, unknown: list[str] | None = None):
        delta = source_membership_delta(tmp_path, old, new, prefix)
        scoped = delta["sourceScopeRef"]
        claims = [
            {
                "id": "proof:CAS-implementation",
                "dependsOn": [scoped + ":path:" + cas],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:RuntimeDispatch-TLA-model",
                "dependsOn": [scoped + ":path:" + model],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:all-runtime-members",
                "dependsOn": [delta["membershipRef"]],
                "dependenciesComplete": True,
            },
            {
                "id": "proof:unrelated-doc",
                "dependsOn": [scoped + ":path:" + other],
                "dependenciesComplete": True,
            },
        ]
        result = select_impacted_obligations(
            authority_refs=delta["authorityRefs"],
            obligations=claims,
            changed_refs=delta["changedRefs"],
            unknown_refs=unknown,
        )
        return delta, result, {row["id"]: row["standing"] for row in result["standingByObligation"]}

    (tmp_path / "README.md").write_text("Unrelated Git change.")
    git("add", ".")
    git("commit", "-qm", "unrelated change")
    unrelated = git("rev-parse", "HEAD")
    _, baseline_selection, baseline_standing = inspect(baseline, unrelated)
    assert all(v == "REUSE_CANDIDATE" for v in baseline_standing.values())
    assert not baseline_selection["proofReuseAdmissible"]

    path = tmp_path / cas
    rust = path.read_bytes()
    start = rust.index(b"pub(super) fn mark_dispatch_issued(")
    end = rust.index(b"pub(crate) fn dispatch_issued_at_ms", start)
    method = rust[start:end]
    state_guard = (
        b"if attempt.state != AttemptState::Accepted\\n"
        b"            || attempt.row_version != expected_row_version\\n"
        b"            || attempt.bundle_digest.is_none()"
    ).replace(b"\\n", b"\n")
    sql_guard = b"AND state='accepted' AND row_version=?2 AND bundle_digest IS NOT NULL"
    assert method.count(state_guard) == 1 and method.count(sql_guard) == 1
    red = method.replace(state_guard, b"if attempt.bundle_digest.is_none()")
    red = red.replace(sql_guard, b"AND (?2 >= 0) AND bundle_digest IS NOT NULL")
    path.write_bytes(rust[:start] + red + rust[end:])
    git("add", ".")
    git("commit", "-qm", "red mutant on exact CAS implementation")
    red_cut = git("rev-parse", "HEAD")
    delta, selected, status = inspect(unrelated, red_cut)
    assert delta["changedValuePaths"] == [cas]
    assert delta["membershipChanged"] is False
    assert status["proof:CAS-implementation"] == "RECHECK_REQUIRED"
    assert status["proof:RuntimeDispatch-TLA-model"] == "REUSE_CANDIDATE"
    assert status["proof:all-runtime-members"] == "REUSE_CANDIDATE"
    assert status["proof:unrelated-doc"] == "REUSE_CANDIDATE"
    assert selected["proofReuseAdmissible"] is False

    # Agent-native path: existing repo CLI emits the scoped, immutable Git
    # delta; existing Composition CLI consumes it without inventing authority.
    import json
    import os
    import sys

    delta_output = subprocess.check_output(
        [
            sys.executable,
            str(source_repo / "tools/repo/source_history_legos.py"),
            "--repo",
            str(tmp_path),
            "--left",
            unrelated,
            "--right",
            red_cut,
            "--impact-prefix",
            prefix,
        ],
        text=True,
    )
    cli_delta = json.loads(delta_output)
    assert cli_delta == delta
    delta_file = tmp_path / "git-delta.json"
    claims_file = tmp_path / "claims.json"
    delta_file.write_text(delta_output, encoding="utf8")
    scope = delta["sourceScopeRef"]
    claims_file.write_text(
        json.dumps(
            [
                {
                    "id": "proof:CAS-implementation",
                    "dependsOn": [scope + ":path:" + cas],
                    "dependenciesComplete": True,
                },
                {
                    "id": "proof:RuntimeDispatch-TLA-model",
                    "dependsOn": [scope + ":path:" + model],
                    "dependenciesComplete": True,
                },
            ]
        ),
        encoding="utf8",
    )
    cli_status = json.loads(
        subprocess.check_output(
            [
                sys.executable,
                "-m",
                "ordivon_composition.verification_obligation_r1",
                "select-impact",
                str(delta_file),
                str(claims_file),
                "--repo",
                str(tmp_path),
            ],
            text=True,
        )
    )
    assert {row["id"]: row["standing"] for row in cli_status["standingByObligation"]} == {
        "proof:CAS-implementation": "RECHECK_REQUIRED",
        "proof:RuntimeDispatch-TLA-model": "REUSE_CANDIDATE",
    }
    assert cli_status["proofReuseAdmissible"] is False

    # Package-only invocation matches CI: Composition is separately installed
    # and its subprocess does not inherit the monorepo root on sys.path.
    composition_root = Path(__file__).resolve().parents[1]
    restricted_env = dict(os.environ, PYTHONPATH=str(composition_root / "src"))
    package_only = json.loads(
        subprocess.check_output(
            [
                sys.executable,
                "-m",
                "ordivon_composition.verification_obligation_r1",
                "select-impact",
                str(delta_file),
                str(claims_file),
                "--repo",
                str(tmp_path),
            ],
            cwd=composition_root,
            env=restricted_env,
            text=True,
        )
    )
    assert package_only == cli_status

    # A caller-supplied fake "owner certificate" cannot be promoted by CLI.
    untrusted = dict(cli_delta)
    untrusted["proofReuseAdmissible"] = True
    delta_file.write_text(json.dumps(untrusted), encoding="utf8")
    denied = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_composition.verification_obligation_r1",
            "select-impact",
            str(delta_file),
            str(claims_file),
            "--repo",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert denied.returncode != 0
    assert "cannot promote unqualified" in denied.stderr
    delta_file.write_text(delta_output, encoding="utf8")
    # A plausible report with correct cuts but missing an actual changed path
    # cannot be trusted for scheduling merely because proof grants are false.
    forged_changes = dict(cli_delta)
    forged_changes["changedRefs"] = []
    delta_file.write_text(json.dumps(forged_changes), encoding="utf8")
    omitted = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_composition.verification_obligation_r1",
            "select-impact",
            str(delta_file),
            str(claims_file),
            "--repo",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert omitted.returncode != 0
    assert "differs from exact native source delta" in omitted.stderr
    delta_file.write_text(delta_output, encoding="utf8")
    unknown_file = tmp_path / "unresolved-runtime-edges.json"
    unknown_file.write_text(json.dumps(["runtime:unindexed"]), encoding="utf8")
    bounded_unknown = json.loads(
        subprocess.check_output(
            [
                sys.executable,
                "-m",
                "ordivon_composition.verification_obligation_r1",
                "select-impact",
                str(delta_file),
                str(claims_file),
                "--repo",
                str(tmp_path),
                "--unknown-refs",
                str(unknown_file),
            ],
            text=True,
        )
    )
    assert all(
        row["standing"] in {"RECHECK_REQUIRED", "UNKNOWN"}
        for row in bounded_unknown["standingByObligation"]
    )
    assert bounded_unknown["proofReuseAdmissible"] is False

    extra = tmp_path / (prefix + "providers/new.rs")
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("fn new_provider() {}")
    git("add", ".")
    git("commit", "-qm", "new runtime provider appears")
    added_cut = git("rev-parse", "HEAD")
    delta, selected, status = inspect(red_cut, added_cut)
    assert delta["membershipChanged"]
    assert status["proof:all-runtime-members"] == "RECHECK_REQUIRED"
    assert status["proof:CAS-implementation"] == "REUSE_CANDIDATE"
    assert status["proof:RuntimeDispatch-TLA-model"] == "REUSE_CANDIDATE"
    assert not selected["proofReuseAdmissible"]

    # When a non-Git environmental dependency cannot be enumerated, the
    # existing selector fails closed instead of laundering stale evidence.
    _, selected, status = inspect(red_cut, added_cut, unknown=["runtime:ambient-unresolved"])
    assert all(v == "UNKNOWN" or v == "RECHECK_REQUIRED" for v in status.values())
    assert selected["proofReuseAdmissible"] is False


def _two_gate_manifest() -> dict:
    manifest = _manifest()
    other = copy.deepcopy(manifest["gateRequirements"][0])
    other["id"] = "gate:unrelated-property"
    other["assumption"] = "Separate independent premise."
    other["guarantee"] = "Separate independent guarantee."
    # Independent source/consumer chain; a second Gate on the SAME consumer
    # would not be independent and must be invalidated by #851 scope semantics.
    producer = copy.deepcopy(manifest["stages"][0])
    producer.update(
        id="stage:unrelated-producer",
        ownerId="unrelated-producer",
        responsibility="Produce independent candidate",
        outputs=["independent-candidate"],
    )
    consumer = copy.deepcopy(manifest["stages"][1])
    consumer.update(
        id="stage:unrelated-consumer",
        ownerId="unrelated-consumer",
        responsibility="Consume independent candidate",
        dependsOn=["stage:unrelated-producer"],
        inputs=["independent-candidate"],
    )
    manifest["stages"].extend([producer, consumer])
    edge = copy.deepcopy(manifest["edges"][0])
    edge.update(id="edge:unrelated")
    edge["from"] = {"stageId": producer["id"], "port": "independent-candidate"}
    edge["to"] = {"stageId": consumer["id"], "port": "independent-candidate"}
    manifest["edges"].append(edge)
    other["producerStageId"] = producer["id"]
    other["consumerStageId"] = consumer["id"]
    manifest["gateRequirements"].append(other)
    return manifest


def _gate_impact_statuses(result: dict) -> dict[str, str]:
    assert result["selection"]["proofReuseAdmissible"] is False
    assert result["proofReuseAdmissible"] is False
    return {row["id"]: row["standing"] for row in result["selection"]["standingByObligation"]}


def test_manifest_gate_impact_property_delta_is_automatically_recheck() -> None:
    previous = _two_gate_manifest()
    current = copy.deepcopy(previous)
    current["gateRequirements"][0]["guarantee"] = "Relaxed guarantee"
    result = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert result["sharedManifestContextChanged"] is False
    assert result["changedLocalGateIds"] == ["gate:candidate-contract"]
    assert result["addedGateIds"] == []
    assert result["removedGateIds"] == []
    assert _gate_impact_statuses(result) == {
        "proof:gate:gate:candidate-contract": "RECHECK_REQUIRED",
        "proof:gate:gate:unrelated-property": "UNKNOWN",
    }


def test_manifest_gate_impact_unqualified_unchanged_stays_unknown() -> None:
    previous = _two_gate_manifest()
    result = select_manifest_gate_impacts(
        previous_manifest=previous, current_manifest=copy.deepcopy(previous)
    )
    assert not result["changedLocalGateIds"]
    assert not result["sharedManifestContextChanged"]
    assert set(_gate_impact_statuses(result).values()) == {"UNKNOWN"}


def test_manifest_gate_impact_shared_context_delta_rechecks_all() -> None:
    previous = _two_gate_manifest()
    current = copy.deepcopy(previous)
    current["unresolvedAssumptions"].append("Changed global environmental assumption")
    result = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert result["sharedManifestContextChanged"]
    assert set(result["changedLocalGateIds"]) == {
        "gate:candidate-contract",
        "gate:unrelated-property",
    }
    assert set(_gate_impact_statuses(result).values()) == {"RECHECK_REQUIRED"}


def test_manifest_gate_impact_gate_membership_add_retire_invalidates_closure() -> None:
    previous = _manifest()
    current = copy.deepcopy(previous)
    more = copy.deepcopy(previous["gateRequirements"][0])
    more["id"] = "gate:new"
    current["gateRequirements"].append(more)
    added = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert added["addedGateIds"] == ["gate:new"]
    assert added["sharedManifestContextChanged"] is False
    assert set(_gate_impact_statuses(added).values()) == {"RECHECK_REQUIRED"}

    retired = select_manifest_gate_impacts(previous_manifest=current, current_manifest=previous)
    assert retired["removedGateIds"] == ["gate:new"]
    assert retired["sharedManifestContextChanged"] is False
    assert set(_gate_impact_statuses(retired).values()) == {"RECHECK_REQUIRED"}


def test_manifest_gate_impact_semantic_gate_reorder_is_stable() -> None:
    previous = _two_gate_manifest()
    current = copy.deepcopy(previous)
    current["gateRequirements"].reverse()
    result = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert not result["sharedManifestContextChanged"]
    assert not result["changedLocalGateIds"]
    assert set(_gate_impact_statuses(result).values()) == {"UNKNOWN"}


def test_manifest_gate_impact_rejects_incompatible_circuit_identity() -> None:
    previous = _manifest()
    current = copy.deepcopy(previous)
    current["circuitId"] = "circuit:different-contract"
    with pytest.raises(CircuitContractError, match="different circuit identities"):
        select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)


def test_manifest_gate_impact_reuses_existing_cli_command_surface(tmp_path) -> None:
    import json
    import subprocess
    import sys

    previous = _two_gate_manifest()
    current = copy.deepcopy(previous)
    current["gateRequirements"][0]["guarantee"] = "Revised guarantee"
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(previous), encoding="utf-8")
    after.write_text(json.dumps(current), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_composition.verification_obligation_r1",
            "impact-manifests",
            str(before),
            str(after),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    projection = json.loads(completed.stdout)
    assert projection["changedLocalGateIds"] == ["gate:candidate-contract"]
    assert _gate_impact_statuses(projection) == {
        "proof:gate:gate:candidate-contract": "RECHECK_REQUIRED",
        "proof:gate:gate:unrelated-property": "UNKNOWN",
    }


def test_manifest_gate_impact_does_not_recheck_on_parallel_stage_change() -> None:
    previous = _manifest()
    previous["stages"].append(
        {
            "id": "stage:parallel",
            "ownerId": "parallel",
            "responsibility": "Independent external branch",
            "dependsOn": [],
            "methodBindings": [],
            "capabilityBindings": [],
            "inputs": [],
            "outputs": ["unrelated"],
        }
    )
    current = copy.deepcopy(previous)
    current["stages"][-1]["responsibility"] = "Independent branch changed"
    scoped = compare_gate_source_scopes(previous, current)
    assert scoped["changedGateIds"] == []
    result = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert result["sharedManifestContextChanged"] is False
    assert result["changedLocalGateIds"] == []
    assert _gate_impact_statuses(result) == {"proof:gate:gate:candidate-contract": "UNKNOWN"}


def test_manifest_gate_impact_rechecks_true_scoped_producer_change() -> None:
    previous = _manifest()
    current = copy.deepcopy(previous)
    current["stages"][0]["responsibility"] = "Producer changed"
    scoped = compare_gate_source_scopes(previous, current)
    assert scoped["changedGateIds"] == ["gate:candidate-contract"]
    result = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert result["sharedManifestContextChanged"] is False
    assert result["changedLocalGateIds"] == ["gate:candidate-contract"]
    assert _gate_impact_statuses(result) == {
        "proof:gate:gate:candidate-contract": "RECHECK_REQUIRED"
    }


def test_manifest_independent_gate_membership_keeps_unrelated_unknown() -> None:
    # An independent producer/consumer circuit already exists, but it has no Gate
    # at the older SourceCut. Registering a new Gate on that unrelated chain
    # must not invalidate every other Gate's source proof obligation.
    current = _two_gate_manifest()
    previous = copy.deepcopy(current)
    previous["gateRequirements"] = previous["gateRequirements"][:1]

    scoped = compare_gate_source_scopes(previous, current)
    assert scoped["changedGateIds"] == []
    assert scoped["addedGateIds"] == ["gate:unrelated-property"]
    selected = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert selected["sharedManifestContextChanged"] is False
    assert selected["changedLocalGateIds"] == ["gate:unrelated-property"]
    assert _gate_impact_statuses(selected) == {
        "proof:gate:gate:candidate-contract": "UNKNOWN",
        "proof:gate:gate:unrelated-property": "RECHECK_REQUIRED",
    }

    retired = select_manifest_gate_impacts(previous_manifest=current, current_manifest=previous)
    assert retired["removedGateIds"] == ["gate:unrelated-property"]
    assert retired["sharedManifestContextChanged"] is False
    assert _gate_impact_statuses(retired) == {"proof:gate:gate:candidate-contract": "UNKNOWN"}


def test_manifest_gate_membership_same_consumer_rechecks_existing_proof() -> None:
    previous = _manifest()
    current = copy.deepcopy(previous)
    added = copy.deepcopy(previous["gateRequirements"][0])
    added["id"] = "gate:new-consumer-premise"
    current["gateRequirements"].append(added)
    scoped = compare_gate_source_scopes(previous, current)
    assert scoped["changedGateIds"] == ["gate:candidate-contract"]
    out = select_manifest_gate_impacts(previous_manifest=previous, current_manifest=current)
    assert out["changedLocalGateIds"] == [
        "gate:candidate-contract",
        "gate:new-consumer-premise",
    ]
    assert out["sharedManifestContextChanged"] is False
    assert set(_gate_impact_statuses(out).values()) == {"RECHECK_REQUIRED"}


@pytest.mark.parametrize(
    ("before_mask", "after_mask"),
    [(before, after) for before in range(4) for after in range(4)],
)
def test_manifest_independent_gate_membership_subsets_are_local(
    before_mask: int, after_mask: int
) -> None:
    # A bounded differential oracle: four combinations of two independent
    # consumer-Gate registrations on each side of the SourceCut.
    complete = _two_gate_manifest()
    ids = [gate["id"] for gate in complete["gateRequirements"]]
    before = copy.deepcopy(complete)
    after = copy.deepcopy(complete)
    before["gateRequirements"] = [
        gate for i, gate in enumerate(complete["gateRequirements"]) if before_mask & (1 << i)
    ]
    after["gateRequirements"] = [
        gate for i, gate in enumerate(complete["gateRequirements"]) if after_mask & (1 << i)
    ]
    selected = select_manifest_gate_impacts(previous_manifest=before, current_manifest=after)
    added = [
        identity
        for i, identity in enumerate(ids)
        if after_mask & (1 << i) and not before_mask & (1 << i)
    ]
    removed = [
        identity
        for i, identity in enumerate(ids)
        if before_mask & (1 << i) and not after_mask & (1 << i)
    ]
    assert selected["addedGateIds"] == added
    assert selected["removedGateIds"] == removed
    assert selected["changedLocalGateIds"] == added
    assert selected["sharedManifestContextChanged"] is False
    expected = {
        f"proof:gate:{identity}": ("RECHECK_REQUIRED" if identity in added else "UNKNOWN")
        for i, identity in enumerate(ids)
        if after_mask & (1 << i)
    }
    assert _gate_impact_statuses(selected) == expected


def test_manifest_impact_binding_verifier_fingerprint_drift_rechecks_without_source_edit() -> None:
    before_manifest = _manifest()
    after_manifest = copy.deepcopy(before_manifest)
    obligation = compile_verification_obligations(before_manifest)
    before_binding = _binding_set(obligation, native=True)
    after_binding = copy.deepcopy(before_binding)
    after_binding["bindings"][0]["verifierRef"]["digest"] = _digest("different-verifier-artifact")
    result = select_manifest_gate_impacts(
        previous_manifest=before_manifest,
        current_manifest=after_manifest,
        previous_binding_set=before_binding,
        current_binding_set=after_binding,
    )
    assert result["changedLocalGateIds"] == []
    assert result["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert result["proofReuseAdmissible"] is False
    assert result["verifierBindingComparisonQualification"] == "CALLER_AUTHORED_BINDINGS_ONLY"
    assert {r["id"]: r["standing"] for r in result["selection"]["standingByObligation"]} == {
        "proof:gate:gate:candidate-contract": "RECHECK_REQUIRED"
    }


def test_manifest_impact_binding_native_spec_changes_force_recheck() -> None:
    manifest = _manifest()
    obligation = compile_verification_obligations(manifest)
    before = _binding_set(obligation, native=True)
    after = copy.deepcopy(before)
    after["bindings"][0]["nativeSpecificationRef"]["digest"] = _digest("new-target-psi")
    result = select_manifest_gate_impacts(
        previous_manifest=manifest,
        current_manifest=copy.deepcopy(manifest),
        previous_binding_set=before,
        current_binding_set=after,
    )
    assert result["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert result["selection"]["standingByObligation"][0]["standing"] == "RECHECK_REQUIRED"


def test_manifest_impact_binding_nonsemantic_annotations_do_not_force_recheck() -> None:
    manifest = _manifest()
    obligation = compile_verification_obligations(manifest)
    before = _binding_set(obligation, native=True)
    after = copy.deepcopy(before)
    after["nonClaims"].append("Extra task-local audit annotation.")
    after["bindings"][0]["nonClaims"].append("Another explanatory annotation.")
    result = select_manifest_gate_impacts(
        previous_manifest=manifest,
        current_manifest=copy.deepcopy(manifest),
        previous_binding_set=before,
        current_binding_set=after,
    )
    assert result["changedVerifierBindingGateIds"] == []
    assert result["selection"]["standingByObligation"][0]["standing"] == "UNKNOWN"


def test_manifest_impact_binding_pair_required_not_one_sided() -> None:
    manifest = _manifest()
    obligation = compile_verification_obligations(manifest)
    with pytest.raises(CircuitContractError, match="both"):
        select_manifest_gate_impacts(
            previous_manifest=manifest,
            current_manifest=copy.deepcopy(manifest),
            previous_binding_set=_binding_set(obligation),
        )


def test_manifest_impact_binding_removal_rechecks_optional_gate() -> None:
    manifest = _manifest(required=False)
    obligation = compile_verification_obligations(manifest)
    before = _binding_set(obligation, native=True)
    after = copy.deepcopy(before)
    after["bindings"] = []
    result = select_manifest_gate_impacts(
        previous_manifest=manifest,
        current_manifest=copy.deepcopy(manifest),
        previous_binding_set=before,
        current_binding_set=after,
    )
    assert result["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert result["selection"]["standingByObligation"][0]["standing"] == "RECHECK_REQUIRED"


def test_manifest_impact_binding_drift_is_local_to_named_gate() -> None:
    manifest = _two_gate_manifest()
    obligation_set = compile_verification_obligations(manifest)
    by_gate = {row["gateId"]: row for row in obligation_set["obligations"]}
    first = _binding_set(obligation_set, native=True)
    unrelated = copy.deepcopy(first["bindings"][0])
    unrelated["gateId"] = "gate:unrelated-property"
    unrelated["obligationDigest"] = by_gate["gate:unrelated-property"]["obligationDigest"]
    unrelated["verifierOwnerId"] = by_gate["gate:unrelated-property"]["verifierOwnerId"]
    unrelated["supportScope"] = by_gate["gate:unrelated-property"]["supportScope"]
    unrelated["verifierRef"]["id"] = "verifier:unrelated"
    first["bindings"].append(unrelated)

    second = copy.deepcopy(first)
    second["bindings"][0]["verifierClass"] = "changed-provider"
    selected = select_manifest_gate_impacts(
        previous_manifest=manifest,
        current_manifest=copy.deepcopy(manifest),
        previous_binding_set=first,
        current_binding_set=second,
    )
    assert selected["changedLocalGateIds"] == []
    assert selected["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert {
        row["id"]: row["standing"] for row in selected["selection"]["standingByObligation"]
    } == {
        "proof:gate:gate:candidate-contract": "RECHECK_REQUIRED",
        "proof:gate:gate:unrelated-property": "UNKNOWN",
    }


def test_manifest_impact_binding_order_is_a_set_not_a_transition() -> None:
    manifest = _two_gate_manifest()
    obligations = compile_verification_obligations(manifest)
    by_gate = {row["gateId"]: row for row in obligations["obligations"]}
    before = _binding_set(obligations, native=True)
    new = copy.deepcopy(before["bindings"][0])
    new["gateId"] = "gate:unrelated-property"
    new["obligationDigest"] = by_gate["gate:unrelated-property"]["obligationDigest"]
    new["verifierOwnerId"] = by_gate["gate:unrelated-property"]["verifierOwnerId"]
    new["supportScope"] = by_gate["gate:unrelated-property"]["supportScope"]
    before["bindings"].append(new)
    after = copy.deepcopy(before)
    after["bindings"].reverse()
    result = select_manifest_gate_impacts(
        previous_manifest=manifest,
        current_manifest=copy.deepcopy(manifest),
        previous_binding_set=before,
        current_binding_set=after,
    )
    assert result["changedVerifierBindingGateIds"] == []
    assert set(row["standing"] for row in result["selection"]["standingByObligation"]) == {
        "UNKNOWN"
    }


def test_manifest_impact_binding_mismatched_proposition_rejected() -> None:
    manifest = _manifest()
    obligations = compile_verification_obligations(manifest)
    before = _binding_set(obligations, native=True)
    after = copy.deepcopy(before)
    after["bindings"][0]["obligationDigest"] = _digest("bogus-proved-proposition")
    with pytest.raises(CircuitContractError, match="obligation digest mismatch"):
        select_manifest_gate_impacts(
            previous_manifest=manifest,
            current_manifest=copy.deepcopy(manifest),
            previous_binding_set=before,
            current_binding_set=after,
        )


def test_manifest_impact_bindings_existing_cli_subprocess(tmp_path) -> None:
    import json
    import subprocess
    import sys

    manifest = _manifest()
    obligations = compile_verification_obligations(manifest)
    before = _binding_set(obligations, native=True)
    after = copy.deepcopy(before)
    after["bindings"][0]["nativeSpecificationRef"]["digest"] = _digest("native-spec-change")
    files = {}
    for name, value in (
        ("old-manifest", manifest),
        ("new-manifest", manifest),
        ("old-bindings", before),
        ("new-bindings", after),
    ):
        p = tmp_path / (name + ".json")
        p.write_text(json.dumps(value), encoding="utf-8")
        files[name] = str(p)
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_composition.verification_obligation_r1",
            "impact-manifests",
            files["old-manifest"],
            files["new-manifest"],
            "--previous-bindings",
            files["old-bindings"],
            "--current-bindings",
            files["new-bindings"],
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    result = json.loads(process.stdout)
    assert result["changedLocalGateIds"] == []
    assert result["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert result["selection"]["standingByObligation"][0]["standing"] == "RECHECK_REQUIRED"


def test_manifest_sourcecut_and_verifier_bindings_compose_without_promoting_authority(
    tmp_path,
) -> None:
    """The existing one CLI must preserve both independent P0 source/readset fences."""
    import hashlib
    import json
    import subprocess
    import sys

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", "-c", "maintenance.auto=false", "-C", str(repo), *args],
            text=True,
        ).strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Ordivon P0 Test")
    git("config", "user.email", "ordivon-test@example.invalid")
    manifest = _manifest()
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    (repo / "manifest.json").write_bytes(manifest_bytes)
    git("add", ".")
    git("commit", "-qm", "exact manifest source")
    source_cut = git("rev-parse", "HEAD")

    proof_set = compile_verification_obligations(manifest)
    before_bind = _binding_set(proof_set, native=True)
    after_bind = copy.deepcopy(before_bind)
    after_bind["bindings"][0]["nativeSpecificationRef"]["digest"] = _digest(
        "changed-build-qualification"
    )
    before_path = tmp_path / "prior-bindings.json"
    after_path = tmp_path / "current-bindings.json"
    before_path.write_text(json.dumps(before_bind), encoding="utf-8")
    after_path.write_text(json.dumps(after_bind), encoding="utf-8")
    # A current worktree edit MUST NOT change the two pinned Git source inputs.
    (repo / "manifest.json").write_text("{unparseable local worktree mutation", encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "ordivon_composition.verification_obligation_r1",
        "impact-manifests",
        "manifest.json",
        "manifest.json",
        "--git-repo",
        str(repo),
        "--previous-sourcecut",
        source_cut,
        "--current-sourcecut",
        source_cut,
        "--previous-bindings",
        str(before_path),
        "--current-bindings",
        str(after_path),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    selected = json.loads(result.stdout)
    assert selected["gitSourceCuts"]["previous"]["sha256"] == (
        "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()
    )
    assert selected["gitSourceCuts"]["current"]["sha256"] == (
        "sha256:" + hashlib.sha256(manifest_bytes).hexdigest()
    )
    assert selected["changedLocalGateIds"] == []
    assert selected["changedVerifierBindingGateIds"] == ["gate:candidate-contract"]
    assert selected["selection"]["standingByObligation"][0]["standing"] == "RECHECK_REQUIRED"
    assert selected["proofReuseAdmissible"] is False
    # One-sided caller-authored verifier binding cannot be read as a proof delta.
    one_sided = subprocess.run(
        command[:-2],
        text=True,
        capture_output=True,
    )
    assert one_sided.returncode != 0


def test_manifest_impact_verifier_identity_unaffected_by_other_gate_manifest_digest() -> None:
    manifest = _two_gate_manifest()
    successor = copy.deepcopy(manifest)
    successor["gateRequirements"][0]["guarantee"] = "New producer guarantee."
    old_proofs = compile_verification_obligations(manifest)
    new_proofs = compile_verification_obligations(successor)

    def all_bindings(proofs: dict) -> dict:
        by_gate = {row["gateId"]: row for row in proofs["obligations"]}
        bundle = _binding_set(proofs, native=True)
        other = copy.deepcopy(bundle["bindings"][0])
        other["gateId"] = "gate:unrelated-property"
        other["obligationDigest"] = by_gate[other["gateId"]]["obligationDigest"]
        other["verifierOwnerId"] = by_gate[other["gateId"]]["verifierOwnerId"]
        other["supportScope"] = by_gate[other["gateId"]]["supportScope"]
        other["verifierRef"]["id"] = "verifier:independent-stable"
        bundle["bindings"].append(other)
        return bundle

    before = all_bindings(old_proofs)
    after = all_bindings(new_proofs)
    assert old_proofs["obligationSetDigest"] != new_proofs["obligationSetDigest"]
    assert (
        old_proofs["obligations"][1]["obligationDigest"]
        != new_proofs["obligations"][1]["obligationDigest"]
    )
    result = select_manifest_gate_impacts(
        previous_manifest=manifest,
        current_manifest=successor,
        previous_binding_set=before,
        current_binding_set=after,
    )
    assert result["changedLocalGateIds"] == ["gate:candidate-contract"]
    assert result["changedVerifierBindingGateIds"] == []
    assert {row["id"]: row["standing"] for row in result["selection"]["standingByObligation"]} == {
        "proof:gate:gate:candidate-contract": "RECHECK_REQUIRED",
        "proof:gate:gate:unrelated-property": "UNKNOWN",
    }


def test_recursive_proof_cycle_change_propagates_without_blocking_independent_branch():
    graph = [
        {"id": "proof:a", "dependsOn": ["proof:b"], "dependenciesComplete": True},
        {"id": "proof:b", "dependsOn": ["proof:a"], "dependenciesComplete": True},
        {"id": "proof:consumer", "dependsOn": ["proof:b"], "dependenciesComplete": True},
        {"id": "proof:independent", "dependsOn": ["source:host"], "dependenciesComplete": True},
    ]
    result = _impact(graph=graph)
    assert _statuses(result) == {
        "proof:a": "UNKNOWN",
        "proof:b": "UNKNOWN",
        "proof:consumer": "UNKNOWN",
        "proof:independent": "REUSE_CANDIDATE",
    }
    assert result["cyclicObligationIds"] == ["proof:a", "proof:b"]
    assert _statuses(_impact(graph=graph, changed=["proof:a"])) == {
        "proof:a": "RECHECK_REQUIRED",
        "proof:b": "RECHECK_REQUIRED",
        "proof:consumer": "RECHECK_REQUIRED",
        "proof:independent": "REUSE_CANDIDATE",
    }


def test_recursive_proof_cycle_current_vs_prior_relation_change_is_not_forgotten():
    old = [
        {"id": "proof:a", "dependsOn": ["proof:b"], "dependenciesComplete": True},
        {"id": "proof:b", "dependsOn": ["proof:a"], "dependenciesComplete": True},
    ]
    new = [
        {"id": "proof:a", "dependsOn": ["source:runtime"], "dependenciesComplete": True},
        {"id": "proof:b", "dependsOn": ["proof:a"], "dependenciesComplete": True},
    ]
    result = select_impacted_obligations(
        authority_refs=["source:runtime"],
        obligations=new,
        changed_refs=[],
        previous_graph={"authorityRefs": ["source:runtime"], "obligations": old},
    )
    assert result["cyclicObligationIds"] == []
    assert result["derivedRelationChangedRefs"] == ["proof:a"]
    assert dict((x["id"], x["standing"]) for x in result["standingByObligation"]) == {
        "proof:a": "RECHECK_REQUIRED",
        "proof:b": "RECHECK_REQUIRED",
    }
    assert result["proofReuseAdmissible"] is False


def test_recursive_proof_self_cycle_and_missing_edge_are_not_vacuous():
    self_cycle = _impact(
        graph=[{"id": "proof:self", "dependsOn": ["proof:self"], "dependenciesComplete": True}]
    )
    assert _statuses(self_cycle) == {"proof:self": "UNKNOWN"}
    assert self_cycle["cyclicObligationIds"] == ["proof:self"]
    with pytest.raises(CircuitContractError, match="depends on unknown"):
        _impact(
            graph=[
                {"id": "proof:self", "dependsOn": ["proof:missing"], "dependenciesComplete": True}
            ]
        )


def test_cyclic_proof_selector_matches_independent_finite_reachability_oracle():
    # Exhaust all 2**12 declared dependency relations for three proof nodes
    # over the same three proofs plus one real authority root. Compare the
    # implementation's monotone lattice fixed point with an independent
    # reachability-based mathematical oracle.
    from itertools import product

    root = "source:r"
    proof_ids = ("proof:a", "proof:b", "proof:c")
    all_nodes = (root, *proof_ids)
    for bits in product((False, True), repeat=12):
        graph = {}
        for index, identity in enumerate(proof_ids):
            graph[identity] = tuple(
                candidate
                for used, candidate in zip(bits[index * 4 : (index + 1) * 4], all_nodes)
                if used
            )

        def ancestors(identity):
            seen = set()
            queue = list(graph.get(identity, ()))
            while queue:
                candidate = queue.pop()
                if candidate in seen:
                    continue
                seen.add(candidate)
                queue.extend(graph.get(candidate, ()))
            return seen

        cyclic = sorted(identity for identity in proof_ids if identity in ancestors(identity))
        for changed, unknown in (
            ({root}, set()),
            ({"proof:b"}, set()),
            (set(), {"proof:c"}),
            (set(), set()),
        ):
            observed = select_impacted_obligations(
                authority_refs=[root],
                obligations=[
                    {
                        "id": identity,
                        "dependsOn": list(graph[identity]),
                        "dependenciesComplete": True,
                    }
                    for identity in proof_ids
                ],
                changed_refs=sorted(changed),
                unknown_refs=sorted(unknown),
            )
            result = {item["id"]: item["standing"] for item in observed["standingByObligation"]}
            expected = {}
            for identity in proof_ids:
                visited = ancestors(identity) | {identity}
                if visited & changed:
                    expected[identity] = "RECHECK_REQUIRED"
                elif visited & (unknown | set(cyclic)):
                    expected[identity] = "UNKNOWN"
                else:
                    expected[identity] = "REUSE_CANDIDATE"
            assert result == expected, (bits, changed, unknown, expected, result)
            assert observed["cyclicObligationIds"] == cyclic
            assert observed["proofReuseAdmissible"] is False


def test_manifest_git_sourcecuts_bind_exact_prior_current_bytes(tmp_path) -> None:
    import hashlib
    import json
    import subprocess
    import sys

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*argv: str) -> str:
        return subprocess.check_output(["git", "-C", str(repo), *argv], text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Ordivon Test")
    git("config", "user.email", "ordivon-test@example.invalid")
    previous = _two_gate_manifest()
    path = repo / "manifest.json"
    original = json.dumps(previous).encode()
    path.write_bytes(original)
    git("add", ".")
    git("commit", "-qm", "original")
    old = git("rev-parse", "HEAD")
    current = copy.deepcopy(previous)
    current["gateRequirements"][0]["guarantee"] += " improved"
    updated = json.dumps(current).encode()
    path.write_bytes(updated)
    git("add", ".")
    git("commit", "-qm", "updated")
    new = git("rev-parse", "HEAD")
    # A mutable checkout is not source truth. It now contradicts both cuts.
    path.write_text("{invalid JSON but never read by the Git source mode")
    command = [
        sys.executable,
        "-m",
        "ordivon_composition.verification_obligation_r1",
        "impact-manifests",
        "manifest.json",
        "manifest.json",
        "--git-repo",
        str(repo),
        "--previous-sourcecut",
        old,
        "--current-sourcecut",
        new,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["changedLocalGateIds"] == ["gate:candidate-contract"]
    assert data["sharedManifestContextChanged"] is False
    assert (
        data["gitSourceCuts"]["previous"]["sha256"]
        == "sha256:" + hashlib.sha256(original).hexdigest()
    )
    assert (
        data["gitSourceCuts"]["current"]["sha256"]
        == "sha256:" + hashlib.sha256(updated).hexdigest()
    )
    assert data["proofReuseAdmissible"] is False
    # Immutable source read produces byte-identical projection on replay.
    replay = subprocess.run(command, capture_output=True, text=True, check=True)
    assert replay.stdout == result.stdout

    for invalid in (
        command[:-1],  # missing current cut
        [*command[:-1], new[:8]],  # abbreviated mutable rev
        [*command[:4], "../manifest.json", *command[5:]],  # traversal
        [*command[:4], "missing.json", *command[5:]],  # absent source
    ):
        rejected = subprocess.run(invalid, capture_output=True, text=True)
        assert rejected.returncode != 0


def test_manifest_git_sourcecut_rejects_symlinks(tmp_path) -> None:
    import json
    import subprocess

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Ordivon Test"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "ordivon-test@example.invalid"], check=True
    )
    (repo / "manifest.json").write_text(json.dumps(_two_gate_manifest()))
    (repo / "link.json").symlink_to("manifest.json")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "commit"], check=True)
    cut = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    from ordivon_composition.verification_obligation_r1 import _immutable_git_manifest

    with pytest.raises(CircuitContractError, match="regular Git file"):
        _immutable_git_manifest(repo, cut, __import__("pathlib").Path("link.json"))


def test_immutable_manifest_sourcecut_ignores_native_git_replace_refs(tmp_path) -> None:
    """An exact commit ID must not silently alias another commit via Git replace."""
    import json
    import subprocess
    from pathlib import Path

    from ordivon_composition.verification_obligation_r1 import _immutable_git_manifest

    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    original = _two_gate_manifest()
    path = repo / "manifest.json"
    path.write_text(json.dumps(original), encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "initial")
    initial_cut = git("rev-parse", "HEAD")

    mutated = copy.deepcopy(original)
    mutated["gateRequirements"][0]["guarantee"] += " MUTATED"
    path.write_text(json.dumps(mutated), encoding="utf-8")
    git("add", ".")
    git("commit", "-qm", "later")
    replacement_cut = git("rev-parse", "HEAD")
    git("replace", initial_cut, replacement_cut)

    # Under Git's default view this is already falsified: show old commit => new blob.
    substituted = git("show", initial_cut + ":manifest.json")
    assert json.loads(substituted) == mutated

    restored, evidence = _immutable_git_manifest(repo, initial_cut, Path("manifest.json"))
    assert evidence["commit"] == initial_cut
    assert restored == original


def test_git_manifest_sourcecut_uses_repository_object_format(tmp_path) -> None:
    """Git's storage object format—not a universal 40-digit SHA-1 assumption—sets the cut width."""
    import json
    import subprocess
    from pathlib import Path

    from ordivon_composition.verification_obligation_r1 import _immutable_git_manifest

    for object_format, width in (("sha1", 40), ("sha256", 64)):
        repo = tmp_path / object_format
        repo.mkdir()

        def git(*args: str) -> str:
            return subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(repo), *args],
                text=True,
            ).strip()

        subprocess.run(
            ["git", "-C", str(repo), "init", "-q", f"--object-format={object_format}"],
            check=True,
        )
        git("config", "user.name", "Ordivon Source Test")
        git("config", "user.email", "source@example.invalid")
        original = _two_gate_manifest()
        (repo / "manifest.json").write_text(json.dumps(original))
        git("add", ".")
        git("commit", "-qm", "initial")
        old = git("rev-parse", "HEAD")
        assert len(old) == width
        read, evidence = _immutable_git_manifest(repo, old, Path("manifest.json"))
        assert read == original
        assert evidence["commit"] == old
        assert evidence["objectFormat"] == object_format
        with pytest.raises(CircuitContractError, match="exact Git"):
            _immutable_git_manifest(repo, old[:8], Path("manifest.json"))
        with pytest.raises(CircuitContractError, match="exact Git"):
            _immutable_git_manifest(
                repo, old + "0" * (64 if width == 40 else 40), Path("manifest.json")
            )

        newer = copy.deepcopy(original)
        newer["gateRequirements"][0]["guarantee"] += " object-format-independent"
        (repo / "manifest.json").write_text(json.dumps(newer))
        git("add", ".")
        git("commit", "-qm", "newer")
        new = git("rev-parse", "HEAD")
        git("replace", old, new)
        restored, receipt = _immutable_git_manifest(repo, old, Path("manifest.json"))
        assert restored == original  # SHA256/SHA1 both ignore mutable replacement refs
        assert receipt["commit"] == old
        # Verify the public CLI path as consumed by Agents, not just this helper.
        import sys

        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "ordivon_composition.verification_obligation_r1",
                "impact-manifests",
                "manifest.json",
                "manifest.json",
                "--git-repo",
                str(repo),
                "--previous-sourcecut",
                old,
                "--current-sourcecut",
                new,
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        result = json.loads(process.stdout)
        assert result["changedLocalGateIds"] == ["gate:candidate-contract"]
        assert result["gitSourceCuts"]["previous"]["commit"] == old
        assert result["gitSourceCuts"]["current"]["commit"] == new
        assert result["gitSourceCuts"]["previous"]["objectFormat"] == object_format
        assert result["gitSourceCuts"]["current"]["objectFormat"] == object_format
        assert result["proofReuseAdmissible"] is False


def test_agent_cli_impact_observations_reuses_native_selector_without_new_registry(
    tmp_path,
):
    import json
    import subprocess
    import sys

    previous = tmp_path / "previous.json"
    current = tmp_path / "current.json"
    graph = tmp_path / "graph.json"
    previous.write_text(
        json.dumps(
            {
                "observations": [
                    _env_observation("config:network-proxy", "a"),
                    _env_observation("installed:writer", "b"),
                ]
            }
        )
    )
    current.write_text(
        json.dumps(
            {
                "observations": [
                    _env_observation("config:network-proxy", "b", epoch="current"),
                    _env_observation("installed:writer", "b", epoch="current"),
                ]
            }
        )
    )
    graph.write_text(
        json.dumps(
            {
                "authorityRefs": ["config:network-proxy", "installed:writer"],
                "obligations": [
                    {
                        "id": "proof:network",
                        "dependsOn": ["config:network-proxy"],
                        "dependenciesComplete": True,
                    },
                    {
                        "id": "proof:writer",
                        "dependsOn": ["installed:writer"],
                        "dependenciesComplete": True,
                    },
                ],
            }
        )
    )
    cmd = [
        sys.executable,
        "-m",
        "ordivon_composition.verification_obligation_r1",
        "impact-observations",
        str(previous),
        str(current),
        str(graph),
    ]
    observed = subprocess.run(cmd, text=True, capture_output=True, check=True)
    result = json.loads(observed.stdout)
    assert result["kind"] == "ordivon.task-local-environment-effect-impact"
    assert result["proofReuseAdmissible"] is False
    assert result["observationDelta"]["changedRefs"] == ["config:network-proxy"]
    assert result["observationDelta"]["unknownRefs"] == ["installed:writer"]
    assert _statuses(result["selection"]) == {
        "proof:network": "RECHECK_REQUIRED",
        "proof:writer": "UNKNOWN",
    }
    # Even if every observation envelope entirely omits a declared required
    # environment root, the CLI must report scoped UNKNOWN, not false reuse.
    previous.write_text(json.dumps({"observations": []}))
    current.write_text(json.dumps({"observations": []}))
    missing = subprocess.run(cmd, text=True, capture_output=True, check=True)
    missing_out = json.loads(missing.stdout)
    assert missing_out["observationDelta"]["unobservedRequiredRefs"] == [
        "config:network-proxy",
        "installed:writer",
    ]
    assert _statuses(missing_out["selection"]) == {
        "proof:network": "UNKNOWN",
        "proof:writer": "UNKNOWN",
    }
    assert missing_out["proofReuseAdmissible"] is False
    graph.write_text(json.dumps({"authorityRefs": []}))
    bad = subprocess.run(cmd, text=True, capture_output=True, check=False)
    assert bad.returncode != 0
    assert "task-local authorityRefs and obligations" in bad.stderr


def test_selector_three_level_priority_matches_independent_bounded_path_oracle() -> None:
    """Finite falsifier for the Lean least-closed-demand semantics.

    This exhausts 4,608 bounded directed acyclic consumer graphs/input masks;
    it is NOT a proof that the dynamic implementation has a complete readset.
    The oracle uses topological path evaluation, NOT the selector's worklist.
    """
    from itertools import product

    roots = ["source:network", "installed:postgres"]
    proofs = ["proof:gateway", "proof:runtime", "proof:consumer"]
    optional_edges = [(0, 1), (0, 2), (1, 2)]
    standing = ("REUSE_CANDIDATE", "UNKNOWN", "RECHECK_REQUIRED")
    cases = 0

    for arc_bits in range(1 << len(optional_edges)):
        edges = [
            (low, high)
            for index, (low, high) in enumerate(optional_edges)
            if arc_bits & (1 << index)
        ]
        for source_binding in product(range(2), repeat=3):
            for root_priority in product(range(3), repeat=2):
                old_changed = [roots[i] for i, rank in enumerate(root_priority) if rank == 2]
                old_unknown = [roots[i] for i, rank in enumerate(root_priority) if rank == 1]
                for completeness_bits in range(8):
                    rows = []
                    oracle = {root: root_priority[index] for index, root in enumerate(roots)}
                    for index, name in enumerate(proofs):
                        is_complete = not bool(completeness_bits & (1 << index))
                        incoming = [proofs[low] for low, high in edges if high == index]
                        dependencies = [roots[source_binding[index]], *incoming]
                        rows.append(
                            {
                                "id": name,
                                "dependsOn": dependencies,
                                "dependenciesComplete": is_complete,
                            }
                        )
                        oracle[name] = max(
                            [0 if is_complete else 1] + [oracle[d] for d in dependencies]
                        )
                    selected = select_impacted_obligations(
                        authority_refs=roots,
                        obligations=rows,
                        changed_refs=old_changed,
                        unknown_refs=old_unknown,
                    )
                    observed = {
                        row["id"]: row["standing"] for row in selected["standingByObligation"]
                    }
                    assert observed == {name: standing[oracle[name]] for name in proofs}, (
                        edges,
                        source_binding,
                        root_priority,
                        completeness_bits,
                        observed,
                        oracle,
                    )
                    assert selected["proofReuseAdmissible"] is False
                    assert selected["proofAcceptanceEstablished"] is False
                    cases += 1

    assert cases == 4608


def test_recursive_proof_detection_scales_to_long_acyclic_and_cyclic_chains() -> None:
    """A large task-local graph must not require recursive or quadratic walks."""
    from ordivon_composition.verification_obligation_r1 import _cyclic_proof_members

    count = 6000
    chain = [
        {
            "id": f"proof:chain:{index}",
            "dependsOn": [] if index == 0 else [f"proof:chain:{index - 1}"],
        }
        for index in range(count)
    ]
    assert _cyclic_proof_members(chain) == set()

    # The back-edge closes exactly the chain segment [1500..5999].
    # The earlier prefix is a prerequisite, not part of the cycle.
    chain[1500]["dependsOn"].append(f"proof:chain:{count - 1}")
    expected = {f"proof:chain:{index}" for index in range(1500, count)}
    assert _cyclic_proof_members(chain) == expected
    # A self-loop is recursive even without a second member.
    assert _cyclic_proof_members([{"id": "proof:self", "dependsOn": ["proof:self"]}]) == {
        "proof:self"
    }
