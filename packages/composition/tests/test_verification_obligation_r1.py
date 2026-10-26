from __future__ import annotations

import copy

import pytest

from ordivon_composition.cognitive_circuit_r1 import CircuitContractError, canonical_digest
from ordivon_composition.verification_obligation_r1 import (
    compare_gate_source_scopes,
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
    assert "source:runtime" in deleted["unindexedChangeRefs"]
    assert set(_statuses(deleted).values()) == {"UNKNOWN"}


def test_impact_rejects_malformed_or_cyclic_previous_graph():
    obligation = {"id": "proof:a", "dependsOn": ["source:a"], "dependenciesComplete": True}
    args = {"authority_refs": ["source:a"], "obligations": [obligation], "changed_refs": []}
    invalids = [
        {"authorityRefs": ["source:a"], "obligations": [obligation, obligation]},
        {
            "authorityRefs": ["source:a"],
            "obligations": [
                {"id": "proof:b", "dependsOn": ["proof:b"], "dependenciesComplete": True}
            ],
        },
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
        return subprocess.check_output(
            ["git", "-C", str(tmp_path), *args], text=True
        ).strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Ordivon Contract Test")
    git("config", "user.email", "contract@example.invalid")
    source_cut = "6e3b5e7205108662d3a0fa6cae23aa53411fce3c"
    cas = "services/runtime/crates/ordivon-runtime-core/src/runtime/registry/lifecycle.rs"
    model = "services/runtime/formal/RuntimeDispatchR1.tla"
    other = "services/runtime/formal/README.md"
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
    prefix = "services/runtime/"

    def inspect(old: str, new: str, *, unknown: list[str] | None = None):
        delta = source_membership_delta(tmp_path, old, new, prefix)
        scoped = delta["sourceScopeRef"]
        claims = [
            {"id": "proof:CAS-implementation",
             "dependsOn": [scoped + ":path:" + cas], "dependenciesComplete": True},
            {"id": "proof:RuntimeDispatch-TLA-model",
             "dependsOn": [scoped + ":path:" + model], "dependenciesComplete": True},
            {"id": "proof:all-runtime-members",
             "dependsOn": [delta["membershipRef"]], "dependenciesComplete": True},
            {"id": "proof:unrelated-doc",
             "dependsOn": [scoped + ":path:" + other], "dependenciesComplete": True},
        ]
        result = select_impacted_obligations(
            authority_refs=delta["authorityRefs"], obligations=claims,
            changed_refs=delta["changedRefs"], unknown_refs=unknown
        )
        return delta, result, {
            row["id"]: row["standing"] for row in result["standingByObligation"]
        }

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

    extra = tmp_path / "services/runtime/providers/new.rs"
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
