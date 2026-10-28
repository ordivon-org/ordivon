#!/usr/bin/env python3
"""Task-local verification-obligation compilation and verifier-binding resolution.

R1 deliberately compiles only existing Cognitive Circuit composition gates. It does not
invent domain properties, discover verifiers, rank providers, execute verification, grant
authority, or establish domain completion. Caller-authored task-local bindings identify the
verifier/provider that will discharge each obligation through the existing Composition Gate
result contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .cognitive_circuit_r1 import (
    CircuitContractError,
    _finite_json_float,
    _load_json,
    _reject_non_json_constant,
    _single_valued_json_object,
    _validate_schema,
    canonical_digest,
    compile_manifest,
)

ROOT = Path(__file__).resolve().parent
OBLIGATION_SET_SCHEMA = ROOT / "schemas" / "verification-obligation-set-v1.schema.json"
BINDING_SET_SCHEMA = ROOT / "schemas" / "verifier-binding-set-v1.schema.json"
RESOLUTION_SCHEMA = ROOT / "schemas" / "verifier-resolution-v1.schema.json"


def _load_task_local_json_list(path: Path) -> list[Any]:
    """Reject ambiguous proof/unknown-ref input before impact selection.

    This reuses the existing Composition JSON admission primitives; caller
    reports remain untrusted and acquire no execution or proof authority.
    """
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_single_valued_json_object,
        parse_constant=_reject_non_json_constant,
        parse_float=_finite_json_float,
    )
    if not isinstance(value, list):
        raise CircuitContractError("task-local proof input must be a JSON array")
    return value


def _immutable_git_manifest(
    repo: Path, commit: str, path: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    """Read a regular Git blob at an exact commit; never consult the mutable checkout.

    This establishes only SOURCE bytes, not authenticated consumer evidence or
    installed/current verifier proof.
    """
    relative = path.as_posix()
    if (
        path.is_absolute()
        or not relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
        or chr(0) in relative
    ):
        raise CircuitContractError(
            "source-bound impact needs an exact Git cut and canonical relative path"
        )

    def git(*argv: str) -> bytes:
        try:
            # Exact SourceCut addresses Git's original objects, not any
            # mutable refs/replace overlay supplied by the local repository.
            return subprocess.check_output(
                ["git", "--no-replace-objects", "-C", str(repo), *argv],
                stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise CircuitContractError("Git source cut or regular blob unavailable") from exc

    # Git supports both SHA-1 (40) and SHA-256 (64) storage formats.
    # Ask the repository for the actual object format rather than adopting
    # one hash algorithm as an implicit global LEGO/source-cut type.
    storage_format = git("rev-parse", "--show-object-format=storage").strip()
    if storage_format == b"sha1":
        object_id_width = 40
    elif storage_format == b"sha256":
        object_id_width = 64
    else:
        raise CircuitContractError("unsupported Git repository object format")
    if re.fullmatch(rf"[0-9a-f]{{{object_id_width}}}", commit) is None:
        raise CircuitContractError("source-bound impact needs an exact Git commit object ID")
    if git("cat-file", "-t", commit).strip() != b"commit":
        raise CircuitContractError("Git SourceCut must identify an immutable commit")
    # ls-tree rejects gitlinks, symlinks, missing path, and pathspec ambiguity.
    entries = [
        row
        for row in git("ls-tree", "-z", "--full-tree", commit, "--", relative).split(b"\x00")
        if row
    ]
    if len(entries) != 1 or b"\t" not in entries[0]:
        raise CircuitContractError("exact manifest Git path unavailable")
    meta, name = entries[0].split(b"\t", 1)
    if name.decode("utf-8", "surrogateescape") != relative:
        raise CircuitContractError("manifest pathspec did not identify an exact path")
    mode, kind, blob = meta.split()
    if kind != b"blob" or mode not in (b"100644", b"100755"):
        raise CircuitContractError("manifest must be a regular Git file")
    raw = git("cat-file", "blob", commit + ":" + relative)
    return _load_json(path, source_bytes=raw), {
        "commit": commit,
        "objectFormat": storage_format.decode("ascii"),
        "path": relative,
        "blobId": blob.decode("ascii"),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "truthRole": "git-immutable-source-only-not-proof-reuse",
    }


def _unique_by(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row[key]
        if row_id in result:
            raise CircuitContractError(f"duplicate {label}: {row_id}")
        result[row_id] = row
    return result


def _obligation_from_gate(
    *,
    circuit_ref: dict[str, str],
    gate: dict[str, Any],
) -> dict[str, Any]:
    obligation: dict[str, Any] = {
        "gateId": gate["id"],
        "sourceGateDigest": canonical_digest(gate),
        "circuitRef": dict(circuit_ref),
        "producerStageId": gate["producerStageId"],
        "consumerStageId": gate["consumerStageId"],
        "assumption": gate["assumption"],
        "guarantee": gate["guarantee"],
        "verifierOwnerId": gate["verifierOwnerId"],
        "supportScope": gate["supportScope"],
        "required": gate["required"],
        "requiredStanding": "SATISFIED",
        "resultKind": "ordivon.composition-gate-result",
        "nonClaims": [
            "This obligation is a task-local projection of an existing Composition Gate.",
            "Discharging it establishes only the named support scope, not domain acceptance.",
        ],
    }
    obligation["obligationDigest"] = canonical_digest(obligation)
    return obligation


def compile_verification_obligations(manifest: dict[str, Any]) -> dict[str, Any]:
    """Compile R1 Composition Gates into exact task-local verification obligations."""

    compiled = compile_manifest(manifest)
    circuit_ref = {
        "id": manifest["circuitId"],
        "digest": compiled["manifestDigest"],
    }
    obligations = [
        _obligation_from_gate(circuit_ref=circuit_ref, gate=gate)
        for gate in sorted(manifest["gateRequirements"], key=lambda item: item["id"])
    ]
    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.verification-obligation-set",
        "truthRole": "task-local-non-authoritative-verification-obligation-projection",
        "circuitRef": circuit_ref,
        "obligations": obligations,
        "requiredGateIds": sorted(
            obligation["gateId"] for obligation in obligations if obligation["required"]
        ),
        "nonClaims": [
            "This projection does not discover, select, rank, or execute verifiers.",
            "This projection grants no Tool, credential, workflow, retry, or domain authority.",
            "Verification closure does not establish domain acceptance.",
        ],
    }
    projection["obligationSetDigest"] = canonical_digest(projection)
    _validate_schema(projection, OBLIGATION_SET_SCHEMA, "verification obligation set")
    return projection


def validate_obligation_set(value: dict[str, Any]) -> None:
    _validate_schema(value, OBLIGATION_SET_SCHEMA, "verification obligation set")
    obligations = _unique_by(value["obligations"], "gateId", "verification obligation gateId")

    expected_required = sorted(
        obligation["gateId"] for obligation in obligations.values() if obligation["required"]
    )
    if value["requiredGateIds"] != expected_required:
        raise CircuitContractError("verification obligation requiredGateIds mismatch")

    for obligation in obligations.values():
        if obligation["circuitRef"] != value["circuitRef"]:
            raise CircuitContractError(
                f"verification obligation circuitRef mismatch: {obligation['gateId']}"
            )
        embedded = obligation["obligationDigest"]
        base = dict(obligation)
        del base["obligationDigest"]
        if canonical_digest(base) != embedded:
            raise CircuitContractError(
                f"verification obligation digest mismatch: {obligation['gateId']}"
            )

    set_digest = value["obligationSetDigest"]
    base_set = dict(value)
    del base_set["obligationSetDigest"]
    if canonical_digest(base_set) != set_digest:
        raise CircuitContractError("verification obligation set digest mismatch")


def resolve_verifier_bindings(
    obligation_set: dict[str, Any],
    binding_set: dict[str, Any],
) -> dict[str, Any]:
    """Validate exact caller-authored verifier bindings against one obligation set.

    "Resolve" here means deterministic binding validation only. This function performs no
    registry lookup, provider discovery, availability probe, ranking, or verifier execution.
    """

    validate_obligation_set(obligation_set)
    _validate_schema(binding_set, BINDING_SET_SCHEMA, "verifier binding set")

    if binding_set["circuitRef"] != obligation_set["circuitRef"]:
        raise CircuitContractError("verifier binding set circuitRef mismatch")
    if binding_set["obligationSetDigest"] != obligation_set["obligationSetDigest"]:
        raise CircuitContractError("verifier binding set targets a stale/different obligation set")

    obligations = _unique_by(
        obligation_set["obligations"],
        "gateId",
        "verification obligation gateId",
    )
    bindings = _unique_by(binding_set["bindings"], "gateId", "verifier binding gateId")

    unknown = sorted(set(bindings) - set(obligations))
    if unknown:
        raise CircuitContractError(f"verifier bindings reference unknown obligations: {unknown}")

    resolved: list[dict[str, Any]] = []
    for gate_id in sorted(bindings):
        binding = bindings[gate_id]
        obligation = obligations[gate_id]
        if binding["obligationDigest"] != obligation["obligationDigest"]:
            raise CircuitContractError(f"verifier binding obligation digest mismatch: {gate_id}")
        if binding["verifierOwnerId"] != obligation["verifierOwnerId"]:
            raise CircuitContractError(f"verifier binding owner mismatch: {gate_id}")
        if binding["supportScope"] != obligation["supportScope"]:
            raise CircuitContractError(f"verifier binding support scope mismatch: {gate_id}")

        resolved.append(
            {
                "gateId": gate_id,
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": binding["verifierOwnerId"],
                "verifierRef": dict(binding["verifierRef"]),
                "verifierClass": binding["verifierClass"],
                "nativeSpecificationRef": (
                    None
                    if binding["nativeSpecificationRef"] is None
                    else dict(binding["nativeSpecificationRef"])
                ),
                "supportScope": binding["supportScope"],
            }
        )

    missing_required = sorted(
        gate_id
        for gate_id, obligation in obligations.items()
        if obligation["required"] and gate_id not in bindings
    )
    unbound_optional = sorted(
        gate_id
        for gate_id, obligation in obligations.items()
        if not obligation["required"] and gate_id not in bindings
    )
    # An empty set of required gates cannot witness any verified cross-owner
    # contract. Binding completeness is an evidence claim, not vacuous truth.
    required_ids = {gate_id for gate_id, item in obligations.items() if item["required"]}
    mechanical_resolution = bool(required_ids) and not missing_required
    standing = "VERIFIER_BINDINGS_RESOLVED" if mechanical_resolution else "VERIFIER_BINDINGS_OPEN"

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.verifier-resolution",
        "truthRole": "task-local-non-authoritative-verifier-binding-projection",
        "circuitRef": dict(obligation_set["circuitRef"]),
        "obligationSetDigest": obligation_set["obligationSetDigest"],
        "bindingSetDigest": canonical_digest(binding_set),
        "standing": standing,
        "resolvedBindings": resolved,
        "missingRequiredGateIds": missing_required,
        "unboundOptionalGateIds": unbound_optional,
        "mechanicalResolution": mechanical_resolution,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "Resolution means only that every required task-local obligation has an exact "
            "caller-authored verifier binding whose owner, obligation digest, and support "
            "scope match. It does not prove verifier availability, execute verification, "
            "grant authority, discharge a gate, or establish domain acceptance."
        ),
    }
    projection["resolutionDigest"] = canonical_digest(projection)
    _validate_schema(projection, RESOLUTION_SCHEMA, "verifier resolution")
    return projection


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


def select_manifest_gate_impacts(
    *,
    previous_manifest: dict[str, Any],
    current_manifest: dict[str, Any],
    previous_binding_set: dict[str, Any] | None = None,
    current_binding_set: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare exact task-local manifest property inputs through the existing selector.

    This handles only the two supplied, already-validated manifest JSON values.
    It does not certify source provenance, an Owner query/readset, installed
    currentness, or verifier assumptions outside those manifests. Unchanged
    gate proofs therefore remain UNKNOWN, never proof-reuse qualified.
    """
    previous = compile_verification_obligations(previous_manifest)
    current = compile_verification_obligations(current_manifest)
    if previous_manifest["circuitId"] != current_manifest["circuitId"]:
        raise CircuitContractError("cannot compare different circuit identities")

    # Reuse the existing R2.1 source-scope operator. Its bounded upstream
    # closure already understands producer/consumer stages, incoming edges,
    # method/capability bindings and other premises of the same consumer.
    # Computing another all-non-Gate hash would invalidate unrelated branches.
    scoped = compare_gate_source_scopes(previous_manifest, current_manifest)
    all_current = {item["gateId"] for item in current["obligations"]}
    added = scoped["addedGateIds"]
    removed = scoped["removedGateIds"]

    # Actual global context affects every Gate, including negative membership
    # queries. The scoped comparator separately handles all local source inputs.
    def shared_context(manifest: dict[str, Any]) -> str:
        return canonical_digest(
            {
                key: manifest[key]
                for key in (
                    "schemaVersion",
                    "kind",
                    "circuitId",
                    "objectiveRef",
                    "unresolvedAssumptions",
                    "nonClaims",
                )
            }
        )

    # Negative Gate membership is already part of each bounded consumer's
    # upstreamGates readset in compare_gate_source_scopes. Treating any add/
    # remove as a global change would invalidate independent Gate branches.
    shared_changed = shared_context(previous_manifest) != shared_context(current_manifest)
    local_changed = sorted(set(scoped["changedGateIds"]) | set(added))

    if (previous_binding_set is None) != (current_binding_set is None):
        raise CircuitContractError("both previous and current verifier binding sets are required")

    # These exact binding resolutions validate a caller-authored claim; they do
    # not authenticate a verifier installation, execution or proof. Keep the
    # binding change separate from the Gate's source/contract change.
    binding_pair = previous_binding_set is not None and current_binding_set is not None
    changed_verifier_gates: list[str] = []
    previous_resolution = None
    current_resolution = None
    if binding_pair:
        previous_resolution = resolve_verifier_bindings(previous, previous_binding_set)
        current_resolution = resolve_verifier_bindings(current, current_binding_set)

        # Each binding resolver already checks the exact obligation digest for
        # its own SourceCut. That digest also includes the whole manifest and
        # changes for unrelated Gates: it is NOT a verifier-identity delta.
        # Actual Gate proposition changes are handled by source:gate refs.
        def verifier_identity(row: dict[str, Any]) -> dict[str, Any]:
            return {key: value for key, value in row.items() if key != "obligationDigest"}

        old_bindings = {
            row["gateId"]: verifier_identity(row) for row in previous_resolution["resolvedBindings"]
        }
        new_bindings = {
            row["gateId"]: verifier_identity(row) for row in current_resolution["resolvedBindings"]
        }
        changed_verifier_gates = sorted(
            gate_id
            for gate_id in all_current
            if old_bindings.get(gate_id) != new_bindings.get(gate_id)
        )

    shared_ref = "source:manifest-shared"

    def gate_ref(gate_id: str) -> str:
        return f"source:gate:{gate_id}"

    def verifier_ref(gate_id: str) -> str:
        return f"binding:verifier:{gate_id}"

    authority_refs = [shared_ref] + [gate_ref(key) for key in sorted(all_current)]
    if binding_pair:
        authority_refs.extend(verifier_ref(key) for key in sorted(all_current))
    obligations = [
        {
            "id": f"proof:gate:{gate_id}",
            "dependsOn": [shared_ref, gate_ref(gate_id)]
            + ([verifier_ref(gate_id)] if binding_pair else []),
            # A syntactically complete manifest does NOT account for verifier,
            # installed code, authorization, environment or dynamic consumer reads.
            "dependenciesComplete": False,
        }
        for gate_id in sorted(all_current)
    ]
    changed_refs = [gate_ref(gate_id) for gate_id in local_changed]
    changed_refs.extend(verifier_ref(gate_id) for gate_id in changed_verifier_gates)
    if shared_changed:
        changed_refs.append(shared_ref)
    selection = select_impacted_obligations(
        authority_refs=authority_refs,
        obligations=obligations,
        changed_refs=changed_refs,
    )
    projection = {
        "kind": "ordivon.task-local-manifest-gate-impact",
        "truthRole": "source-manifest-projection-not-proof-admission",
        "previousObligationSetDigest": previous["obligationSetDigest"],
        "currentObligationSetDigest": current["obligationSetDigest"],
        "sharedManifestContextChanged": shared_changed,
        "changedLocalGateIds": local_changed,
        "addedGateIds": added,
        "removedGateIds": removed,
        "selection": selection,
        "proofReuseAdmissible": False,
        "nonClaims": [
            "The manifest objects are caller supplied; source query provenance is not certified.",
            "Shared context covers global manifest premises and Gate membership only.",
            "Gate source deltas reuse existing scoped upstream closure.",
            "An unchanged gate with unresolved verifier/environment deps stays UNKNOWN.",
            "Removed gates need separate actual consumer and proof-retirement qualification.",
        ],
    }
    if binding_pair:
        projection.update(
            {
                "changedVerifierBindingGateIds": changed_verifier_gates,
                "previousVerifierResolutionDigest": previous_resolution["resolutionDigest"],
                "currentVerifierResolutionDigest": current_resolution["resolutionDigest"],
                "verifierBindingComparisonQualification": "CALLER_AUTHORED_BINDINGS_ONLY",
            }
        )
        projection["nonClaims"].append(
            "Verifier/artifact/native specification references are caller-authored; "
            "their digest equality or binding resolution is not a verified runtime readset."
        )
    return projection


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile-obligations")
    compile_parser.add_argument("manifest", type=Path)

    resolve_parser = sub.add_parser("resolve-bindings")
    resolve_parser.add_argument("obligation_set", type=Path)
    resolve_parser.add_argument("binding_set", type=Path)

    observed_parser = sub.add_parser("impact-observations")
    observed_parser.add_argument("previous_observations", type=Path)
    observed_parser.add_argument("current_observations", type=Path)
    observed_parser.add_argument("task_local_graph", type=Path)

    impact_parser = sub.add_parser("select-impact")
    impact_parser.add_argument("git_source_delta", type=Path)
    impact_parser.add_argument("obligations", type=Path)
    # A caller-supplied JSON report is not native Git evidence. Verify it
    # against the exact immutable source cuts before using it for scheduling.
    impact_parser.add_argument("--repo", type=Path, required=True)
    impact_parser.add_argument("--unknown-refs", type=Path)

    manifest_parser = sub.add_parser("impact-manifests")
    manifest_parser.add_argument("previous_manifest", type=Path)
    manifest_parser.add_argument("current_manifest", type=Path)
    manifest_parser.add_argument("--previous-bindings", type=Path)
    manifest_parser.add_argument("--current-bindings", type=Path)
    manifest_parser.add_argument("--git-repo", type=Path)
    manifest_parser.add_argument("--previous-sourcecut")
    manifest_parser.add_argument("--current-sourcecut")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "compile-obligations":
            result = compile_verification_obligations(_load_json(args.manifest))
        elif args.command == "resolve-bindings":
            result = resolve_verifier_bindings(
                _load_json(args.obligation_set),
                _load_json(args.binding_set),
            )
        elif args.command == "impact-manifests":
            requested = (
                args.git_repo is not None,
                args.previous_sourcecut is not None,
                args.current_sourcecut is not None,
            )
            if any(requested) and not all(requested):
                raise CircuitContractError(
                    "Git source mode requires repository and both exact commits"
                )
            if all(requested):
                before, before_source = _immutable_git_manifest(
                    args.git_repo, args.previous_sourcecut, args.previous_manifest
                )
                after, after_source = _immutable_git_manifest(
                    args.git_repo, args.current_sourcecut, args.current_manifest
                )
            else:
                before, after = (
                    _load_json(args.previous_manifest),
                    _load_json(args.current_manifest),
                )
            result = select_manifest_gate_impacts(
                previous_manifest=before,
                current_manifest=after,
                previous_binding_set=(
                    None if args.previous_bindings is None else _load_json(args.previous_bindings)
                ),
                current_binding_set=(
                    None if args.current_bindings is None else _load_json(args.current_bindings)
                ),
            )
            if all(requested):
                result["gitSourceCuts"] = {"previous": before_source, "current": after_source}
        elif args.command == "impact-observations":
            # Natural owners still own the observations and physical receipts.
            # This is a task-local, non-executing source-to-proof adapter.
            graph = _load_json(args.task_local_graph)
            if not isinstance(graph, dict) or set(graph) != {"authorityRefs", "obligations"}:
                raise CircuitContractError(
                    "impact-observations requires task-local authorityRefs and obligations"
                )
            observed_before = _load_json(args.previous_observations)
            observed_after = _load_json(args.current_observations)
            if set(observed_before) != {"observations"} or set(observed_after) != {"observations"}:
                raise CircuitContractError(
                    "impact-observations requires exact observations envelopes"
                )
            # The graph supplies the *known finite* dependency scope. Missing
            # in both snapshots must not become a false reuse candidate.
            declared_environment_refs = [
                ref
                for ref in graph["authorityRefs"]
                if isinstance(ref, str)
                and ref.partition(":")[0]
                in {
                    "config",
                    "environment",
                    "installed",
                    "authority",
                    "provider",
                    "external",
                    "effect",
                }
            ]
            delta = classify_observed_environment_delta(
                previous=observed_before["observations"],
                current=observed_after["observations"],
                required_refs=declared_environment_refs,
            )
            selected = select_impacted_obligations(
                authority_refs=graph["authorityRefs"],
                obligations=graph["obligations"],
                changed_refs=delta["changedRefs"],
                unknown_refs=delta["unknownRefs"],
            )
            result = {
                "kind": "ordivon.task-local-environment-effect-impact",
                "truthRole": "caller-supplied-observations-not-owner-certified",
                "observationDelta": delta,
                "selection": selected,
                "proofReuseAdmissible": False,
            }
        elif args.command == "select-impact":
            delta = _load_json(args.git_source_delta)
            # The JSON is caller-supplied, not authenticated proof evidence.
            # Retain both module contracts: source-only owner projection and
            # Composition's non-authoritative task-local selection.
            if (
                not isinstance(delta, dict)
                or delta.get("kind") != "ordivon.git-source-membership-delta"
            ):
                raise CircuitContractError("select-impact needs an exact Git source delta")
            if (
                delta.get("gitSourceQueryComplete") is not True
                or delta.get("proofReuseAdmissible") is not False
            ):
                raise CircuitContractError(
                    "select-impact cannot promote unqualified Git source evidence"
                )
            # Consume the native Git owner's existing query CLI. Composition
            # is a separate Python package: the repository tools package is
            # not guaranteed to be importable from its project-only sys.path.
            # If this checkout-bound executable is unavailable, fail closed.
            try:
                cuts = delta.get("sourceCuts")
                if not isinstance(cuts, dict):
                    raise ValueError("sourceCuts must specify immutable Git commits")
                owner_tool = (
                    Path(__file__).resolve().parents[4] / "tools/repo/source_history_legos.py"
                )
                if not owner_tool.is_file() or owner_tool.is_symlink():
                    raise ValueError("Git owner query entrypoint unavailable")

                def require_qualified_owner_tool() -> None:
                    # This process asks the existing Git Owner query for exact
                    # evidence. Do not execute a mutable checkout implementation
                    # while presenting that answer as source-qualified.
                    # Native source-history directly imports affected_owners.
                    # Exact byte provenance must include both actually executed
                    # local Python producers, not only the entrypoint script.
                    # This is finite SOURCE qualification, not a dynamic import
                    # closure or a proof of installed Python interpreter bytes.
                    for relative in (
                        "tools/repo/source_history_legos.py",
                        "tools/repo/affected_owners.py",
                    ):
                        producer = owner_tool.parents[2] / relative
                        tree_entry = subprocess.run(
                            [
                                "git",
                                "--no-replace-objects",
                                "-C",
                                str(owner_tool.parents[2]),
                                "ls-tree",
                                "-z",
                                "--full-tree",
                                "HEAD",
                                "--",
                                relative,
                            ],
                            capture_output=True,
                            check=False,
                        )
                        expected = (
                            rb"(100644|100755) blob [0-9a-f]{40,64}\t"
                            + re.escape(relative.encode("utf-8"))
                            + rb"\x00"
                        )
                        if (
                            tree_entry.returncode != 0
                            or re.fullmatch(expected, tree_entry.stdout) is None
                        ):
                            raise CircuitContractError(
                                "native Git query producer Git tree mode is not regular: "
                                + relative
                            )
                        committed = subprocess.run(
                            [
                                "git",
                                "--no-replace-objects",
                                "-C",
                                str(owner_tool.parents[2]),
                                "show",
                                "HEAD:" + relative,
                            ],
                            capture_output=True,
                            check=False,
                        )
                        if (
                            committed.returncode != 0
                            or not producer.is_file()
                            or producer.is_symlink()
                            or committed.stdout != producer.read_bytes()
                        ):
                            raise CircuitContractError(
                                "native Git query producer differs from its Git SourceCut: "
                                + relative
                            )

                require_qualified_owner_tool()
                native_query = subprocess.run(
                    [
                        sys.executable,
                        str(owner_tool),
                        "--repo",
                        str(args.repo),
                        "--left",
                        cuts.get("previous"),
                        "--right",
                        cuts.get("current"),
                        "--impact-prefix",
                        delta.get("queryPrefix"),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                require_qualified_owner_tool()
                if native_query.returncode != 0:
                    raise ValueError("native Git source query failed")
                qualified = json.loads(native_query.stdout)
            except CircuitContractError:
                raise
            except (ValueError, OSError, TypeError) as exc:
                raise CircuitContractError(
                    "select-impact requires independently recomputable native Git scope"
                ) from exc
            if qualified != delta:
                raise CircuitContractError(
                    "select-impact Git report differs from exact native source delta"
                )
            roots, changes = qualified["authorityRefs"], qualified["changedRefs"]
            if (
                not isinstance(roots, list)
                or not isinstance(changes, list)
                or any(not isinstance(ref, str) for ref in roots + changes)
                or not set(changes).issubset(set(roots))
            ):
                raise CircuitContractError(
                    "Git impact changed refs must belong to same scoped authority set"
                )
            obligations = _load_task_local_json_list(args.obligations)
            unknown = _load_task_local_json_list(args.unknown_refs) if args.unknown_refs else None
            if not isinstance(obligations, list) or (
                unknown is not None and not isinstance(unknown, list)
            ):
                raise CircuitContractError(
                    "select-impact obligations and unknown refs must be arrays"
                )
            result = select_impacted_obligations(
                authority_refs=roots,
                obligations=obligations,
                changed_refs=changes,
                unknown_refs=unknown,
            )
        else:
            raise CircuitContractError(f"unknown verification command: {args.command}")
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"verification obligation R1 failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
