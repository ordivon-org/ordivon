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
import json
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
                raise CircuitContractError(f"duplicate previous obligation/source identity: {identity}")
            prev_claims[identity] = {
                "dependsOn": deps,
                "dependenciesComplete": item["dependenciesComplete"],
                "obligationDigest": item.get("obligationDigest"),
            }
        from .cognitive_circuit_r1 import _topological_order

        _topological_order(
            [{"id": root, "dependsOn": []} for root in prev_roots]
            + [{"id": identity, "dependsOn": sorted(item["dependsOn"])}
               for identity, item in prev_claims.items()]
        )
        derived_relation_changes = roots ^ prev_roots
        for identity in set(claims) | set(prev_claims):
            item = claims.get(identity)
            current = (
                None if item is None else {
                    "dependsOn": set(item["dependsOn"]),
                    "dependenciesComplete": item["dependenciesComplete"],
                    "obligationDigest": item.get("obligationDigest"),
                }
            )
            if current != prev_claims.get(identity):
                derived_relation_changes.add(identity)
        changed |= derived_relation_changes

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

    return {
        "kind": "ordivon.task-local-obligation-impact",
        "truthRole": "rebuildable-non-authoritative-selection",
        "standingByObligation": [
            {"id": identity, "standing": statuses[identity]} for identity in sorted(claims)
        ],
        "unindexedChangeRefs": unindexed,
        "derivedRelationChangedRefs": sorted(derived_relation_changes),
        "relationComparisonQualification": (
            "CALLER_SUPPLIED_PRIOR_AND_CURRENT_NOT_OWNER_CERTIFIED"
            if previous_graph is not None else "NOT_REQUESTED"
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile-obligations")
    compile_parser.add_argument("manifest", type=Path)

    resolve_parser = sub.add_parser("resolve-bindings")
    resolve_parser.add_argument("obligation_set", type=Path)
    resolve_parser.add_argument("binding_set", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "compile-obligations":
            result = compile_verification_obligations(_load_json(args.manifest))
        else:
            result = resolve_verifier_bindings(
                _load_json(args.obligation_set),
                _load_json(args.binding_set),
            )
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"verification obligation R1 failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
