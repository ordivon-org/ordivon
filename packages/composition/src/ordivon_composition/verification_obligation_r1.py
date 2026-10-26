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
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cognitive_circuit_r1 import (
    CircuitContractError,
    _load_json,
    canonical_digest,
    compile_manifest,
)

ROOT = Path(__file__).resolve().parent
OBLIGATION_SET_SCHEMA = ROOT / "schemas" / "verification-obligation-set-v1.schema.json"
BINDING_SET_SCHEMA = ROOT / "schemas" / "verifier-binding-set-v1.schema.json"
RESOLUTION_SCHEMA = ROOT / "schemas" / "verifier-resolution-v1.schema.json"


def _immutable_git_manifest(
    repo: Path, commit: str, path: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    """Read a regular Git blob at an exact commit; never consult the mutable checkout.

    This establishes only SOURCE bytes, not authenticated consumer evidence or
    installed/current verifier proof.
    """
    relative = path.as_posix()
    if (
        re.fullmatch(r"[0-9a-f]{40}", commit) is None
        or path.is_absolute()
        or not relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
        or "\\x00" in relative
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
        "path": relative,
        "blobId": blob.decode("ascii"),
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "truthRole": "git-immutable-source-only-not-proof-reuse",
    }


def _schema(path: Path) -> dict[str, Any]:
    return _load_json(path)


def _validate_schema(value: dict[str, Any], schema_path: Path, label: str) -> None:
    validator = Draft202012Validator(_schema(schema_path))
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise CircuitContractError(f"{label} schema violation at {location}: {first.message}")


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
        from .cognitive_circuit_r1 import _topological_order

        _topological_order(
            [{"id": root, "dependsOn": []} for root in prev_roots]
            + [
                {"id": identity, "dependsOn": sorted(item["dependsOn"])}
                for identity, item in prev_claims.items()
            ]
        )
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

    unindexed = sorted((changed | unknown) - (roots | set(claims)))
    rows = [{"id": root, "dependsOn": []} for root in roots]
    rows += [{"id": identity, "dependsOn": item["dependsOn"]} for identity, item in claims.items()]
    from .cognitive_circuit_r1 import _topological_order

    order = _topological_order(rows)
    statuses: dict[str, str] = {}
    for identity in order:
        if identity in roots:
            statuses[identity] = (
                "RECHECK_REQUIRED"
                if identity in changed
                else "UNKNOWN"
                if identity in unknown or unindexed
                else "REUSE_CANDIDATE"
            )
            continue
        item = claims[identity]
        upstream = [statuses[ref] for ref in item["dependsOn"]]
        if identity in changed or "RECHECK_REQUIRED" in upstream:
            statuses[identity] = "RECHECK_REQUIRED"
        elif (
            identity in unknown
            or unindexed
            or not item["dependenciesComplete"]
            or "UNKNOWN" in upstream
        ):
            statuses[identity] = "UNKNOWN"
        else:
            statuses[identity] = "REUSE_CANDIDATE"

    projection = {
        "kind": "ordivon.task-local-obligation-impact",
        "truthRole": "rebuildable-non-authoritative-selection",
        "standingByObligation": [
            {"id": identity, "standing": statuses[identity]} for identity in sorted(claims)
        ],
        "unindexedChangeRefs": unindexed,
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

    previous_gates = {item["gateId"]: item for item in previous["obligations"]}
    current_gates = {item["gateId"]: item for item in current["obligations"]}
    all_previous = set(previous_gates)
    all_current = set(current_gates)
    added = sorted(all_current - all_previous)
    removed = sorted(all_previous - all_current)

    def shared_context(manifest: dict[str, Any]) -> str:
        # All non-Gate inputs are a shared dependency, including stage bindings,
        # edges, circuit objective, unresolved assumptions and composition metadata.
        # Gate existence/required-set membership is a negative query dependency:
        # new or removed required obligations may affect global closure.
        body = {key: value for key, value in manifest.items() if key != "gateRequirements"}
        gates = manifest["gateRequirements"]
        body["gateMembership"] = sorted(item["id"] for item in gates)
        body["requiredGateMembership"] = sorted(item["id"] for item in gates if item["required"])
        return canonical_digest(body)

    shared_changed = shared_context(previous_manifest) != shared_context(current_manifest)
    local_changed = sorted(
        gate_id
        for gate_id in all_current
        if gate_id not in previous_gates
        or previous_gates[gate_id]["sourceGateDigest"] != current_gates[gate_id]["sourceGateDigest"]
    )

    shared_ref = "source:manifest-shared"

    def gate_ref(gate_id: str) -> str:
        return f"source:gate:{gate_id}"

    authority_refs = [shared_ref] + [gate_ref(key) for key in sorted(all_current)]
    obligations = [
        {
            "id": f"proof:gate:{gate_id}",
            "dependsOn": [shared_ref, gate_ref(gate_id)],
            # A syntactically complete manifest does NOT account for verifier,
            # installed code, authorization, environment or dynamic consumer reads.
            "dependenciesComplete": False,
        }
        for gate_id in sorted(all_current)
    ]
    changed_refs = [gate_ref(gate_id) for gate_id in local_changed]
    if shared_changed:
        changed_refs.append(shared_ref)
    selection = select_impacted_obligations(
        authority_refs=authority_refs,
        obligations=obligations,
        changed_refs=changed_refs,
    )
    return {
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
            "The shared context covers only manifest JSON, not external proof inputs.",
            "An unchanged gate with unresolved verifier/environment deps stays UNKNOWN.",
            "Removed gates need separate actual consumer and proof-retirement qualification.",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile-obligations")
    compile_parser.add_argument("manifest", type=Path)

    resolve_parser = sub.add_parser("resolve-bindings")
    resolve_parser.add_argument("obligation_set", type=Path)
    resolve_parser.add_argument("binding_set", type=Path)

    impact_parser = sub.add_parser("select-impact")
    impact_parser.add_argument("git_source_delta", type=Path)
    impact_parser.add_argument("obligations", type=Path)
    impact_parser.add_argument("--unknown-refs", type=Path)

    manifest_parser = sub.add_parser("impact-manifests")
    manifest_parser.add_argument("previous_manifest", type=Path)
    manifest_parser.add_argument("current_manifest", type=Path)
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
            result = select_manifest_gate_impacts(previous_manifest=before, current_manifest=after)
            if all(requested):
                result["gitSourceCuts"] = {"previous": before_source, "current": after_source}
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
            roots, changes = delta.get("authorityRefs"), delta.get("changedRefs")
            if (
                not isinstance(roots, list)
                or not isinstance(changes, list)
                or any(not isinstance(ref, str) for ref in roots + changes)
                or not set(changes).issubset(set(roots))
            ):
                raise CircuitContractError(
                    "Git impact changed refs must belong to same scoped authority set"
                )
            obligations = json.loads(args.obligations.read_text(encoding="utf-8"))
            unknown = (
                json.loads(args.unknown_refs.read_text(encoding="utf-8"))
                if args.unknown_refs
                else None
            )
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
