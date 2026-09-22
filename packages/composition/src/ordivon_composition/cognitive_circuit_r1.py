#!/usr/bin/env python3
"""Task-local Cognitive Circuit R1 mechanical compiler and gate evaluator.

This module deliberately does not plan work, select methods, discover capabilities,
grant authority, schedule execution, retry effects, or decide domain completion.
It validates/binds an already-authored composition and evaluates verifier-owned
composition-gate records against that exact manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
MANIFEST_SCHEMA = ROOT / "schemas" / "cognitive-circuit-manifest-v1.schema.json"
GATE_SCHEMA = ROOT / "schemas" / "composition-gate-result-v1.schema.json"


class CircuitContractError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def _schema(path: Path) -> dict[str, Any]:
    return _load_json(path)


def _validate_schema(value: dict[str, Any], schema_path: Path, label: str) -> None:
    validator = Draft202012Validator(_schema(schema_path))
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise CircuitContractError(f"{label} schema violation at {location}: {first.message}")


def _unique_index(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = row["id"]
        if row_id in result:
            raise CircuitContractError(f"duplicate {label} id: {row_id}")
        result[row_id] = row
    return result


def _check_dag(stages: dict[str, dict[str, Any]]) -> None:
    known = set(stages)
    for stage_id, stage in stages.items():
        unknown = sorted(set(stage["dependsOn"]) - known)
        if unknown:
            raise CircuitContractError(f"stage {stage_id} depends on unknown stages: {unknown}")
        if stage_id in stage["dependsOn"]:
            raise CircuitContractError(f"stage {stage_id} cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage_id: str) -> None:
        if stage_id in visited:
            return
        if stage_id in visiting:
            raise CircuitContractError(f"stage dependency cycle includes {stage_id}")
        visiting.add(stage_id)
        for dependency in stages[stage_id]["dependsOn"]:
            visit(dependency)
        visiting.remove(stage_id)
        visited.add(stage_id)

    for stage_id in sorted(stages):
        visit(stage_id)


def validate_manifest(value: dict[str, Any]) -> None:
    _validate_schema(value, MANIFEST_SCHEMA, "cognitive circuit manifest")

    methods = _unique_index(value["methodBindings"], "method binding")
    capabilities = _unique_index(value["capabilityBindings"], "capability binding")
    stages = _unique_index(value["stages"], "stage")
    edges = _unique_index(value["edges"], "edge")
    gates = _unique_index(value["gateRequirements"], "gate requirement")
    del edges  # uniqueness is the only direct edge-index property needed below.

    _check_dag(stages)

    method_ids = set(methods)
    capability_ids = set(capabilities)
    for stage_id, stage in stages.items():
        missing_methods = sorted(set(stage["methodBindings"]) - method_ids)
        if missing_methods:
            raise CircuitContractError(
                f"stage {stage_id} references unknown method bindings: {missing_methods}"
            )
        missing_capabilities = sorted(set(stage["capabilityBindings"]) - capability_ids)
        if missing_capabilities:
            raise CircuitContractError(
                f"stage {stage_id} references unknown capability bindings: {missing_capabilities}"
            )

    for edge in value["edges"]:
        source = edge["from"]
        target = edge["to"]
        source_stage = stages.get(source["stageId"])
        target_stage = stages.get(target["stageId"])
        if source_stage is None or target_stage is None:
            raise CircuitContractError(f"edge {edge['id']} references unknown stage")
        if source["port"] not in source_stage["outputs"]:
            raise CircuitContractError(
                f"edge {edge['id']} source port is not declared by "
                f"{source['stageId']}: {source['port']}"
            )
        if target["port"] not in target_stage["inputs"]:
            raise CircuitContractError(
                f"edge {edge['id']} target port is not declared by "
                f"{target['stageId']}: {target['port']}"
            )
        if source["stageId"] == target["stageId"]:
            raise CircuitContractError(f"edge {edge['id']} cannot self-connect a stage")
        if source["stageId"] not in target_stage["dependsOn"]:
            raise CircuitContractError(
                f"edge {edge['id']} requires {target['stageId']} to depend on {source['stageId']}"
            )

    for gate_id, gate in gates.items():
        producer = stages.get(gate["producerStageId"])
        consumer = stages.get(gate["consumerStageId"])
        if producer is None or consumer is None:
            raise CircuitContractError(
                f"gate {gate_id} references an unknown producer or consumer stage"
            )
        if gate["producerStageId"] == gate["consumerStageId"]:
            raise CircuitContractError(f"gate {gate_id} must cross a stage boundary")
        if producer["ownerId"] == consumer["ownerId"]:
            raise CircuitContractError(f"gate {gate_id} must cross an owner boundary in R1")
        if gate["producerStageId"] not in consumer["dependsOn"]:
            raise CircuitContractError(
                f"gate {gate_id} producer must be a dependency of its consumer stage"
            )


def compile_manifest(value: dict[str, Any]) -> dict[str, Any]:
    validate_manifest(value)
    manifest_digest = canonical_digest(value)
    required_gate_ids = sorted(gate["id"] for gate in value["gateRequirements"] if gate["required"])
    compiled: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-compiled",
        "truthRole": "task-local-non-authoritative-composition-projection",
        "circuitId": value["circuitId"],
        "manifestDigest": manifest_digest,
        "objectiveRef": value["objectiveRef"],
        "methodBindingIds": sorted(item["id"] for item in value["methodBindings"]),
        "capabilityBindingIds": sorted(item["id"] for item in value["capabilityBindings"]),
        "stageOrder": _topological_order(value["stages"]),
        "requiredGateIds": required_gate_ids,
        "unresolvedAssumptions": sorted(value["unresolvedAssumptions"]),
        "authorityBoundary": (
            "This compiled projection grants no Tool, credential, execution, network, "
            "retry, workflow, domain-verdict, or semantic-completion authority."
        ),
    }
    compiled["compiledDigest"] = canonical_digest(compiled)
    return compiled


def _topological_order(rows: list[dict[str, Any]]) -> list[str]:
    stages = {row["id"]: row for row in rows}
    indegree = {stage_id: 0 for stage_id in stages}
    children: dict[str, list[str]] = {stage_id: [] for stage_id in stages}
    for stage_id, stage in stages.items():
        for dependency in stage["dependsOn"]:
            indegree[stage_id] += 1
            children[dependency].append(stage_id)

    ready = sorted(stage_id for stage_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(order) != len(stages):
        raise CircuitContractError("stage dependency graph is not acyclic")
    return order


def validate_gate_result(
    manifest: dict[str, Any],
    compiled: dict[str, Any],
    result: dict[str, Any],
) -> None:
    _validate_schema(result, GATE_SCHEMA, "composition gate result")
    if result["circuitId"] != manifest["circuitId"]:
        raise CircuitContractError(f"gate {result['gateId']} binds a different circuitId")
    if result["manifestDigest"] != compiled["manifestDigest"]:
        raise CircuitContractError(
            f"gate {result['gateId']} binds a stale/different manifest digest"
        )
    gates = {gate["id"]: gate for gate in manifest["gateRequirements"]}
    gate = gates.get(result["gateId"])
    if gate is None:
        raise CircuitContractError(f"unknown composition gate result: {result['gateId']}")
    if result["verifierOwnerId"] != gate["verifierOwnerId"]:
        raise CircuitContractError(f"gate {result['gateId']} verifier owner mismatch")
    if result["supportScope"] != gate["supportScope"]:
        raise CircuitContractError(f"gate {result['gateId']} support scope mismatch")


def evaluate_gate_results(
    manifest: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    compiled = compile_manifest(manifest)
    by_gate: dict[str, dict[str, Any]] = {}
    for result in results:
        validate_gate_result(manifest, compiled, result)
        gate_id = result["gateId"]
        if gate_id in by_gate:
            raise CircuitContractError(f"duplicate composition gate result: {gate_id}")
        by_gate[gate_id] = result

    required = {gate["id"]: gate for gate in manifest["gateRequirements"] if gate["required"]}
    missing = sorted(set(required) - set(by_gate))
    unsatisfied = sorted(
        gate_id
        for gate_id in required
        if gate_id in by_gate and by_gate[gate_id]["standing"] == "UNSATISFIED"
    )
    unknown = sorted(
        gate_id
        for gate_id in required
        if gate_id in by_gate and by_gate[gate_id]["standing"] == "UNKNOWN"
    )
    satisfied = sorted(
        gate_id
        for gate_id in required
        if gate_id in by_gate and by_gate[gate_id]["standing"] == "SATISFIED"
    )
    unresolved = sorted(manifest["unresolvedAssumptions"])

    if unsatisfied:
        standing = "COMPOSITION_GATES_UNSATISFIED"
    elif missing or unknown or unresolved:
        standing = "COMPOSITION_GATES_OPEN"
    else:
        standing = "COMPOSITION_GATES_SATISFIED"

    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-gate-projection",
        "truthRole": "bounded-composition-gate-projection-not-domain-verdict",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compiled["manifestDigest"],
        "standing": standing,
        "requiredGateIds": sorted(required),
        "satisfiedGateIds": satisfied,
        "unsatisfiedGateIds": unsatisfied,
        "unknownGateIds": unknown,
        "missingGateIds": missing,
        "unresolvedAssumptions": unresolved,
        "mechanicalClosure": standing == "COMPOSITION_GATES_SATISFIED",
        "domainAcceptanceEstablished": False,
        "claimBoundary": (
            "Mechanical closure means only that all required task-local composition "
            "obligations have verifier-owned SATISFIED records and no unresolved "
            "manifest assumptions remain. It does not establish domain success."
        ),
    }
    projection["projectionDigest"] = canonical_digest(projection)
    return projection


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    compile_parser = sub.add_parser("compile")
    compile_parser.add_argument("manifest", type=Path)

    verify_parser = sub.add_parser("verify-gates")
    verify_parser.add_argument("manifest", type=Path)
    verify_parser.add_argument("results", nargs="*", type=Path)

    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        manifest = _load_json(args.manifest)
        if args.command == "compile":
            output = compile_manifest(manifest)
        else:
            results = [_load_json(path) for path in args.results]
            output = evaluate_gate_results(manifest, results)
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"cognitive circuit R1 failed: {exc}") from exc
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
