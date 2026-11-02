"""Pure source, evidence and proof-impact selection for Composition R1.

This is a source-only, task-local calculation; it does not run verifiers, reuse
proofs, grant authority or read an installed owner. The obligation compiler
retains the supported public/CLI entrypoints and imports this module.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_from_bytes

from .cognitive_circuit_r1 import CircuitContractError, canonical_digest, compile_manifest


def _gate_scoped_source_digest(manifest: dict[str, Any], gate_id: str) -> str:
    """Project a bounded Gate *source* readset; never qualify verifier evidence.

    Include all upstream stage responsibilities and their declared method/tool
    bindings, incoming typed edges, and the Gates that constrain that upstream
    closure. This intentionally overapproximates proof dependencies: ambient
    effects, outside-owner identities and dynamic reads remain unqualified.
    """
    stage_by_id = {stage["id"]: stage for stage in manifest["stages"]}
    gate_by_id = {gate["id"]: gate for gate in manifest["gateRequirements"]}
    gate = gate_by_id[gate_id]
    included: set[str] = set()
    frontier = [gate["producerStageId"], gate["consumerStageId"]]
    while frontier:
        stage_id = frontier.pop()
        if stage_id in included:
            continue
        included.add(stage_id)
        frontier.extend(stage_by_id[stage_id]["dependsOn"])
    stage_rows = [stage_by_id[key] for key in sorted(included)]
    method_ids = {method for stage in stage_rows for method in stage["methodBindings"]}
    capability_ids = {cap for stage in stage_rows for cap in stage["capabilityBindings"]}
    scoped: dict[str, Any] = {
        "schemaVersion": manifest["schemaVersion"],
        "kind": manifest["kind"],
        "circuitId": manifest["circuitId"],
        "objectiveRef": manifest["objectiveRef"],
        "unresolvedAssumptions": sorted(manifest["unresolvedAssumptions"]),
        "nonClaims": manifest["nonClaims"],
        "stages": stage_rows,
        "methodBindings": sorted(
            (row for row in manifest["methodBindings"] if row["id"] in method_ids),
            key=lambda row: row["id"],
        ),
        "capabilityBindings": sorted(
            (row for row in manifest["capabilityBindings"] if row["id"] in capability_ids),
            key=lambda row: row["id"],
        ),
        "incomingEdges": sorted(
            (edge for edge in manifest["edges"] if edge["to"]["stageId"] in included),
            key=lambda edge: edge["id"],
        ),
        "upstreamGates": sorted(
            (item for item in manifest["gateRequirements"] if item["consumerStageId"] in included),
            key=lambda item: item["id"],
        ),
    }
    return canonical_digest(scoped)


def compare_gate_source_scopes(
    previous_manifest: dict[str, Any],
    current_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Select changed task-local source Gate IDs from two valid Circuit cuts.

    Feed changedGateIds into the existing obligation impact selector. This
    comparison *cannot* reuse any verifier PASS: its input is caller-provided
    manifests, not certified owner query footprints or installed binaries.
    """
    previous = compile_manifest(previous_manifest)
    current = compile_manifest(current_manifest)
    if previous_manifest["circuitId"] != current_manifest["circuitId"]:
        raise CircuitContractError("gate source comparison requires the same circuitId")
    old_gates = {item["id"] for item in previous_manifest["gateRequirements"]}
    new_gates = {item["id"] for item in current_manifest["gateRequirements"]}
    common = old_gates & new_gates
    previous_digests = {
        identity: _gate_scoped_source_digest(previous_manifest, identity)
        for identity in sorted(common)
    }
    current_digests = {
        identity: _gate_scoped_source_digest(current_manifest, identity)
        for identity in sorted(common)
    }
    changed = sorted(
        identity for identity in common if previous_digests[identity] != current_digests[identity]
    )
    unchanged = sorted(common - set(changed))
    added = sorted(new_gates - old_gates)
    removed = sorted(old_gates - new_gates)
    return {
        "kind": "ordivon.task-local-gate-source-delta",
        "previousManifestDigest": previous["manifestDigest"],
        "currentManifestDigest": current["manifestDigest"],
        "changedGateIds": changed,
        "unchangedGateIds": unchanged,
        "addedGateIds": added,
        "removedGateIds": removed,
        "proofReuseAdmissible": False,
        "dependencyQualification": "SCOPED_CALLER_MANIFEST_SOURCE_ONLY",
        "nonClaims": [
            "Source Gate scope is an explicit overapproximation, not a complete proof readset.",
            "Verifier outcomes and global Circuit manifest-bound gate results remain unchanged.",
            "Outside-Owner runtime, environment, dynamic reads and admission are not certified.",
        ],
    }


def _cyclic_proof_members(rows: list[dict[str, Any]]) -> set[str]:
    """Find exactly the recursive proof members in O(nodes + edges).

    Kosaraju's iterative strongly-connected-component traversal avoids the
    prior per-node reachability scan and Python recursion depth. Recursive
    proof assumptions remain UNKNOWN, including self-loops; their downstream
    consumers are handled by the existing impact worklist.
    """
    graph = {row["id"]: set(row["dependsOn"]) for row in rows}
    if len(graph) != len(rows):
        raise CircuitContractError("duplicate proof graph identity")
    identities = set(graph)  # Materialize once, not once per dependency row.
    reverse: dict[str, set[str]] = {identity: set() for identity in graph}
    for identity, deps in graph.items():
        missing = deps - identities
        if missing:
            raise CircuitContractError(
                f"proof {identity} depends on unknown references: {sorted(missing)}"
            )
        for dependency in deps:
            reverse[dependency].add(identity)

    # First DFS pass: postorder in the declared dependency direction.
    visited: set[str] = set()
    finish: list[str] = []
    for root in graph:
        if root in visited:
            continue
        visited.add(root)
        stack = [(root, iter(graph[root]))]
        while stack:
            node, neighbors = stack[-1]
            dependency = next(neighbors, None)
            if dependency is None:
                finish.append(node)
                stack.pop()
            elif dependency not in visited:
                visited.add(dependency)
                stack.append((dependency, iter(graph[dependency])))

    # Second pass over reversed edges: every component is maximal.
    assigned: set[str] = set()
    cyclic: set[str] = set()
    for root in reversed(finish):
        if root in assigned:
            continue
        component: set[str] = {root}
        assigned.add(root)
        pending = [root]
        while pending:
            node = pending.pop()
            for consumer in reverse[node]:
                if consumer not in assigned:
                    assigned.add(consumer)
                    component.add(consumer)
                    pending.append(consumer)
        if len(component) > 1 or root in graph[root]:
            cyclic.update(component)
    return cyclic


def select_source_readset_impacts(
    *,
    git_source_delta: dict[str, Any],
    source_readset_evidence: dict[str, Any],
) -> dict[str, Any]:
    """Compose natural-owner source readsets with the existing impact selector.

    Git owns immutable path/member truth. The source owner supplies positive
    read edges. Composition only maps those paths to exact Git authority refs
    and reuses select_impacted_obligations; it does not create a second impact
    algorithm or promote a readset candidate into proof acceptance.
    """

    if (
        not isinstance(git_source_delta, dict)
        or git_source_delta.get("kind") != "ordivon.git-source-membership-delta"
        or git_source_delta.get("gitSourceQueryComplete") is not True
        or git_source_delta.get("proofReuseAdmissible") is not False
    ):
        raise CircuitContractError("source-readset impact needs qualified Git source delta")
    cuts = git_source_delta.get("sourceCuts")
    if (
        not isinstance(cuts, dict)
        or not isinstance(cuts.get("current"), str)
        or not isinstance(git_source_delta.get("sourceScopeRef"), str)
        or not isinstance(git_source_delta.get("queryPrefix"), str)
        or not isinstance(git_source_delta.get("authorityRefs"), list)
        or not isinstance(git_source_delta.get("changedRefs"), list)
        or any(not isinstance(ref, str) for ref in git_source_delta["authorityRefs"])
    ):
        raise CircuitContractError("Git source delta lacks exact authority projection")

    evidence = source_readset_evidence
    if (
        not isinstance(evidence, dict)
        or evidence.get("kind") != "ordivon.source-readset-evidence"
        or evidence.get("proofReuseAdmissible") is not False
        or evidence.get("sourceCut") != cuts["current"]
        or evidence.get("scopePrefix") != git_source_delta["queryPrefix"]
        or not isinstance(evidence.get("items"), list)
        or not isinstance(evidence.get("dependencyQualification"), str)
    ):
        raise CircuitContractError("source readset evidence must bind the exact current Git scope")

    authority = set(git_source_delta["authorityRefs"])
    obligations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in evidence["items"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"id", "sourcePaths", "dependenciesComplete"}
            or not isinstance(item["id"], str)
            or ":" not in item["id"]
            or not isinstance(item["sourcePaths"], list)
            or type(item["dependenciesComplete"]) is not bool
        ):
            raise CircuitContractError("source readset item has invalid contract")
        if item["id"] in seen_ids:
            raise CircuitContractError("source readset evidence has duplicate proof identity")
        seen_ids.add(item["id"])
        paths = item["sourcePaths"]
        if any(not isinstance(path, str) for path in paths):
            raise CircuitContractError("source readset paths must be strings")
        if len(paths) != len(set(paths)):
            raise CircuitContractError("source readset has duplicate source paths")
        refs: list[str] = []
        for path in paths:
            if (
                not isinstance(path, str)
                or not path.startswith(evidence["scopePrefix"])
                or path.startswith("/")
                or "\\" in path
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                raise CircuitContractError("source readset path escapes qualified Git scope")
            encoded = quote_from_bytes(path.encode("utf-8", "surrogateescape"), safe="/")
            ref = f"{git_source_delta['sourceScopeRef']}:path:{encoded}"
            if ref not in authority:
                raise CircuitContractError(
                    "source readset path is absent from exact Git authority refs"
                )
            refs.append(ref)
        obligations.append(
            {
                "id": item["id"],
                "dependsOn": sorted(refs),
                "dependenciesComplete": item["dependenciesComplete"],
            }
        )

    selection = select_impacted_obligations(
        authority_refs=git_source_delta["authorityRefs"],
        obligations=obligations,
        changed_refs=git_source_delta["changedRefs"],
    )
    result = {
        "kind": "ordivon.task-local-source-readset-impact",
        "truthRole": "rebuildable-non-authoritative-owner-readset-selection",
        "sourceCut": cuts["current"],
        "sourceScopeRef": git_source_delta["sourceScopeRef"],
        "queryPrefix": git_source_delta["queryPrefix"],
        "readsetDependencyQualification": evidence["dependencyQualification"],
        "selection": selection,
        "proofReuseAdmissible": False,
        "proofAcceptanceEstablished": False,
        "nonClaims": [
            "Owner readset evidence supplies positive dependency edges, not proof of complete dynamic/build/environment closure.",
            "REUSE_CANDIDATE remains a scheduling candidate and is never verifier PASS.",
            "No implementation refinement, installed currentness, effect authority, or domain acceptance is established.",
        ],
    }
    result["projectionDigest"] = canonical_digest(result)
    return result


def classify_observed_environment_delta(
    *,
    previous: list[dict[str, Any]],
    current: list[dict[str, Any]],
    required_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Task-local, non-authoritative bridge: scoped observations -> proof impact.

    This is NOT an environment inventory or a new truth store. Real environment
    and effect witnesses must come from their natural Runtime/Security/Domain
    authorities. The bridge qualifies the *shape* of caller-supplied evidence,
    NOT its issuer, time-continuity, hidden readsets or physical truth.
    Outputs feed the existing select_impacted_obligations changed/unknown refs.

    Exact observed content equality can be considered a bounded config-source
    candidate. Equality of installed state, live environment, credentials,
    external provider or effects does NOT prove temporal continuity, and stays
    UNKNOWN even when two point-in-time digests match.
    """
    classes = frozenset(
        {
            "config",
            "environment",
            "installed",
            "authority",
            "provider",
            "external",
            "effect",
        }
    )

    def validate(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
        if not isinstance(rows, list):
            raise CircuitContractError(f"{label} observations must be a list")
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            if not isinstance(row, dict) or set(row) != {
                "ref",
                "standing",
                "valueDigest",
                "witnessRef",
            }:
                raise CircuitContractError(f"{label} requires exact observation fields")
            ref, standing = row["ref"], row["standing"]
            if (
                not isinstance(ref, str)
                or ref != ref.strip()
                or not ref.isprintable()
                or ":" not in ref
                or not ref.split(":", 1)[1]
                or ref.split(":", 1)[0] not in classes
            ):
                raise CircuitContractError(f"{label} observation needs typed environment ref")
            if ref in result:
                raise CircuitContractError(f"duplicate {label} observation: {ref}")
            digest, witness = row["valueDigest"], row["witnessRef"]
            if standing == "OBSERVED":
                if (
                    not isinstance(digest, str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is None
                    or not isinstance(witness, str)
                    or witness != witness.strip()
                    or ":" not in witness
                    or not all(witness.split(":", 1))
                    or not witness.isprintable()
                ):
                    raise CircuitContractError(f"{label} needs observed digest and witnessRef")
            elif standing == "UNKNOWN":
                if digest is not None or witness is not None:
                    raise CircuitContractError(f"{label} UNKNOWN must not invent a witness")
            else:
                raise CircuitContractError(f"{label} observation standing unsupported")
            result[ref] = row
        return result

    before = validate(previous, "previous")
    after = validate(current, "current")
    if required_refs is not None:
        if (
            not isinstance(required_refs, list)
            or not all(isinstance(ref, str) for ref in required_refs)
            or len(required_refs) != len(set(required_refs))
            or any(
                not ref.isprintable()
                or ref != ref.strip()
                or ":" not in ref
                or not all(ref.split(":", 1))
                or ref.split(":", 1)[0] not in classes
                for ref in required_refs
            )
        ):
            raise CircuitContractError("required environment refs need distinct typed identities")
    required = set(required_refs or [])
    unobserved = sorted(required - (before.keys() | after.keys()))
    changed: list[str] = []
    unknown: list[str] = list(unobserved)
    equal_config: list[str] = []
    for ref in sorted(before.keys() | after.keys()):
        old, new = before.get(ref), after.get(ref)
        if (
            old is None
            or new is None
            or old["standing"] != "OBSERVED"
            or new["standing"] != "OBSERVED"
        ):
            # Absent from a snapshot is NOT proof that the provider was removed.
            unknown.append(ref)
        elif old["valueDigest"] != new["valueDigest"]:
            changed.append(ref)
        elif ref.startswith("config:") and old["witnessRef"] != new["witnessRef"]:
            # Two distinct *claimed* observations are necessary even for
            # a configuration candidate. Replaying the exact same receipt
            # cannot establish that the later state was observed at all.
            # Authenticity and actual observation time remain owner duties.
            equal_config.append(ref)
        else:
            # Point-in-time equality is insufficient for live, temporal
            # authorities; credential revocation and effects may be unobserved.
            unknown.append(ref)
    return {
        "kind": "ordivon.task-local-environment-observation-delta",
        "truthRole": "caller-supplied-observation-bridge-not-authoritative-currentness",
        "changedRefs": changed,
        "unknownRefs": sorted(unknown),
        "equalConfigurationRefs": equal_config,
        "unobservedRequiredRefs": unobserved,
        "requiredScopeQualification": (
            "CALLER_DECLARED_GRAPH_ONLY" if required_refs is not None else "NOT_BOUND_TO_GRAPH"
        ),
        "proofReuseAdmissible": False,
        "nonClaims": [
            "A witnessRef names supplied evidence; this bridge does not authenticate it.",
            "No exhaustive dynamic dependency discovery or temporal continuity.",
            "Equal config digests are scoped candidates, not formal proof or live authorization.",
            "An unindexed changed/unknown ref must reach the existing conservative selector.",
            "External effects and authorization require native owner receipts and reconciliation.",
        ],
    }


def select_impacted_obligations(
    *,
    authority_refs: list[str],
    obligations: list[dict[str, Any]],
    changed_refs: list[str],
    unknown_refs: list[str] | None = None,
    previous_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Task-local conservative proof impact projection, never verifier authority.

    Caller-reported dependency completeness is an explicit assumption, not
    proof of graph closure. When prior/current graphs are both supplied, their
    *declared* relation and optional owner-obligation-digest delta is derived
    mechanically, not confused with a source-file delta.
    Prior snapshot provenance and readset completeness
    remain the caller's independent qualification obligations.
    REUSE_CANDIDATE is not PASS/current acceptance.
    """

    def require_refs(values: list[str], label: str) -> set[str]:
        if not isinstance(values, list) or any(
            not isinstance(ref, str)
            or ":" not in ref
            or ref != ref.strip()
            or not ref.isprintable()
            or not all(ref.split(":", 1))
            for ref in values
        ):
            raise CircuitContractError(f"{label} needs nonempty typed references")
        if len(values) != len(set(values)):
            raise CircuitContractError(f"{label} has duplicate references")
        return set(values)

    def validate_impact_claim(item: Any, label: str) -> None:
        required = {"id", "dependsOn", "dependenciesComplete"}
        if not isinstance(item, dict) or not (
            required <= set(item) <= required | {"obligationDigest"}
        ):
            raise CircuitContractError(f"{label} requires id, dependsOn, dependenciesComplete")
        if "obligationDigest" in item:
            digest = item["obligationDigest"]
            if (
                not isinstance(digest, str)
                or not digest.startswith("sha256:")
                or len(digest) != 71
                or any(ch not in "0123456789abcdef" for ch in digest[7:])
            ):
                raise CircuitContractError(f"{label} obligationDigest must be canonical sha256")

    roots = require_refs(authority_refs, "authorityRefs")
    changed = require_refs(changed_refs, "changedRefs")
    unknown = require_refs(unknown_refs if unknown_refs is not None else [], "unknownRefs")
    # Shared R2.1 proof-graph ingress for C06, environment and Git-impact
    # consumers. A malformed JSON top-level obligation collection must never
    # escape as an unhandled Python TypeError or mimic an empty proof graph.
    if not isinstance(obligations, list):
        raise CircuitContractError("obligations must be a JSON array")
    claims: dict[str, dict[str, Any]] = {}
    for item in obligations:
        validate_impact_claim(item, "obligation")
        identity = item["id"]
        require_refs([identity], "obligation id")
        require_refs(item["dependsOn"], "dependsOn")
        if type(item["dependenciesComplete"]) is not bool:
            raise CircuitContractError("dependenciesComplete must be JSON boolean")
        if identity in claims or identity in roots:
            raise CircuitContractError(f"duplicate obligation/source identity: {identity}")
        claims[identity] = dict(item)

    derived_relation_changes: set[str] = set()
    derived_contract_changes: set[str] = set()
    retired_known_refs: set[str] = set()
    if previous_graph is not None:
        if (
            not isinstance(previous_graph, dict)
            or set(previous_graph) != {"authorityRefs", "obligations"}
            or not isinstance(previous_graph["obligations"], list)
        ):
            raise CircuitContractError("previousGraph needs authorityRefs and obligations")
        prev_roots = require_refs(previous_graph["authorityRefs"], "previous authorityRefs")
        prev_claims: dict[str, dict[str, Any]] = {}
        for item in previous_graph["obligations"]:
            validate_impact_claim(item, "previous obligation")
            identity = item["id"]
            require_refs([identity], "previous obligation id")
            deps = require_refs(item["dependsOn"], "previous dependsOn")
            if type(item["dependenciesComplete"]) is not bool:
                raise CircuitContractError("previous dependenciesComplete must be JSON boolean")
            if identity in prev_claims or identity in prev_roots:
                raise CircuitContractError(
                    f"duplicate previous obligation/source identity: {identity}"
                )
            prev_claims[identity] = {
                "dependsOn": deps,
                "dependenciesComplete": item["dependenciesComplete"],
                "obligationDigest": item.get("obligationDigest"),
            }
        _cyclic_proof_members(
            [{"id": root, "dependsOn": []} for root in prev_roots]
            + [
                {"id": identity, "dependsOn": sorted(item["dependsOn"])}
                for identity, item in prev_claims.items()
            ]
        )
        # A prior-only proof identity is *known historical provenance*, not
        # a missing external source. If no current claim references it, its
        # retirement cannot be an unindexed dependency of all current proofs.
        # Actual current consumers must declare a new DAG relation, and their
        # changed contracts are still rechecked through the loop below.
        # A previous-only Source root or proof node is a known historical
        # retirement, not an unindexed present-day dependency. Keep the delta
        # visible, but do not spread its uncertainty to unrelated consumers.
        # Explicit unknownRefs and changed surviving contracts still flow.
        retired_known_refs = (prev_roots - roots) | (set(prev_claims) - set(claims))
        derived_relation_changes = roots ^ prev_roots
        for identity in set(claims) | set(prev_claims):
            item = claims.get(identity)
            current = (
                None
                if item is None
                else {
                    "dependsOn": set(item["dependsOn"]),
                    "dependenciesComplete": item["dependenciesComplete"],
                    "obligationDigest": item.get("obligationDigest"),
                }
            )
            previous = prev_claims.get(identity)
            if (
                current is None
                or previous is None
                or current["dependsOn"] != previous["dependsOn"]
                or current["dependenciesComplete"] != previous["dependenciesComplete"]
            ):
                derived_relation_changes.add(identity)
            # A semantic contract change is different from a relation change;
            # both invalidate the proof, but should remain distinguishable.
            if (current or {}).get("obligationDigest") != (previous or {}).get("obligationDigest"):
                derived_contract_changes.add(identity)
        changed |= derived_relation_changes | derived_contract_changes

    # Explicit UNKNOWN must never be silenced by an earlier provenance
    # witness: it is a new unresolved fact, unlike a known historical Delta.
    unindexed = sorted(((changed - retired_known_refs) | unknown) - (roots | set(claims)))
    rows = [{"id": root, "dependsOn": []} for root in roots]
    rows += [{"id": identity, "dependsOn": item["dependsOn"]} for identity, item in claims.items()]
    cyclic = _cyclic_proof_members(rows)
    # Conservative least-fixed-point propagation on the three-element lattice
    # REUSE_CANDIDATE < UNKNOWN < RECHECK_REQUIRED. A recursive assumption is
    # UNKNOWN until independently discharged by a separate joint proof; the
    # caller's dependenciesComplete boolean can never supply that proof.
    rank = {"REUSE_CANDIDATE": 0, "UNKNOWN": 1, "RECHECK_REQUIRED": 2}
    statuses: dict[str, str] = {}
    for identity in sorted(roots | set(claims)):
        if identity in changed:
            status = "RECHECK_REQUIRED"
        elif identity in unknown or unindexed:
            status = "UNKNOWN"
        elif identity in cyclic or (
            identity in claims and not claims[identity]["dependenciesComplete"]
        ):
            status = "UNKNOWN"
        else:
            status = "REUSE_CANDIDATE"
        statuses[identity] = status
    # Standard monotone worklist over the existing declared dependency graph.
    # Each node can be raised at most twice in the three-element lattice, so
    # unrelated proof nodes are not repeatedly rescanned on every change.
    from collections import deque

    dependents: dict[str, set[str]] = {identity: set() for identity in statuses}
    for identity, claim in claims.items():
        for dependency in claim["dependsOn"]:
            dependents[dependency].add(identity)

    pending = deque(sorted(identity for identity, status in statuses.items() if rank[status] > 0))
    while pending:
        dependency = pending.popleft()
        for consumer in sorted(dependents[dependency]):
            if rank[statuses[dependency]] > rank[statuses[consumer]]:
                statuses[consumer] = statuses[dependency]
                pending.append(consumer)

    projection = {
        "kind": "ordivon.task-local-obligation-impact",
        "truthRole": "rebuildable-non-authoritative-selection",
        "standingByObligation": [
            {"id": identity, "standing": statuses[identity]} for identity in sorted(claims)
        ],
        "unindexedChangeRefs": unindexed,
        "cyclicObligationIds": sorted(cyclic),
        "derivedRelationChangedRefs": sorted(derived_relation_changes),
        "derivedContractChangedRefs": sorted(derived_contract_changes),
        "derivedChangedRefs": sorted(derived_relation_changes | derived_contract_changes),
        "relationComparisonQualification": (
            "CALLER_SUPPLIED_PRIOR_AND_CURRENT_NOT_OWNER_CERTIFIED"
            if previous_graph is not None
            else "NOT_REQUESTED"
        ),
        "dependencyQualification": "CALLER_DECLARED_NOT_OWNER_CERTIFIED",
        "proofReuseAdmissible": False,
        "proofAcceptanceEstablished": False,
        "basisDigest": canonical_digest(
            {
                "authorityRefs": sorted(roots),
                # dependsOn is a graph prerequisite SET, not an ordered program.
                # Canonicalize its members so equivalent read-sets share identity.
                "obligations": [
                    {**item, "dependsOn": sorted(item["dependsOn"])}
                    for item in sorted(claims.values(), key=lambda x: x["id"])
                ],
                "changedRefs": sorted(changed),
                "unknownRefs": sorted(unknown),
                # Historical retirement can change whether a ref is indexed,
                # even when the caller's current graph and changes match.
                "unindexedChangeRefs": unindexed,
            }
        ),
        "nonClaims": [
            "REUSE_CANDIDATE never claims verifier PASS or current correctness.",
            "dependenciesComplete is an unproven caller-supplied assertion.",
            "Unresolved dynamic/foreign dependencies must remain UNKNOWN.",
            "Prior/current graph source authority and completeness are not certified.",
            "Optional obligationDigest is caller-supplied, not owner-authenticated.",
            "No verifier execution, effect permission, or domain acceptance.",
        ],
    }
    # basisDigest identifies only the effective selection inputs; equal
    # selection bases must remain reusable despite different historical
    # comparison provenance. projectionDigest distinguishes those claims.
    projection["projectionDigest"] = canonical_digest(projection)
    return projection
