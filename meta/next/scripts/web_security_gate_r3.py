#!/usr/bin/env python3
"""Web <-> Security public-contract seam verifier for Cross-domain R3.

The adapter consumes a task-local seam binding rather than embedding repository
topology. It verifies only the delegated-Agent seam and does not claim production
eligibility, physical human presence, or global Security correctness.
"""

from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path
from typing import Any

try:
    from scripts.cognitive_circuit_r1 import (
        CircuitContractError,
        canonical_digest,
        compile_manifest,
        validate_gate_result,
    )
    from scripts.cross_domain_binding_r3 import resolve_repo_file, validate_binding
except ModuleNotFoundError:
    from cognitive_circuit_r1 import (
        CircuitContractError,
        canonical_digest,
        compile_manifest,
        validate_gate_result,
    )
    from cross_domain_binding_r3 import resolve_repo_file, validate_binding


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _binding_section(binding: dict[str, Any]) -> dict[str, Any]:
    validate_binding(binding)
    section = binding.get("webSecurity")
    if not isinstance(section, dict):
        raise CircuitContractError("binding webSecurity section is required")
    paths = section.get("paths")
    if not isinstance(paths, dict):
        raise CircuitContractError("binding webSecurity paths are required")
    for key in (
        "dependencyContracts",
        "nativeE2e",
        "requestSource",
        "admissionSource",
        "storeSource",
    ):
        if not isinstance(paths.get(key), str) or not paths[key]:
            raise CircuitContractError(f"binding webSecurity path is missing: {key}")
    for key in (
        "requiredSeams",
        "forbiddenSourceFragments",
        "requiredStoreMarkers",
    ):
        if not isinstance(section.get(key), list) or not section[key]:
            raise CircuitContractError(f"binding webSecurity list is missing: {key}")
    for key in ("requestContractImport", "admissionContractImport"):
        if not isinstance(section.get(key), str) or not section[key]:
            raise CircuitContractError(f"binding webSecurity value is missing: {key}")
    matrix = section.get("expectedMatrix")
    if not isinstance(matrix, dict) or not matrix:
        raise CircuitContractError("binding webSecurity expectedMatrix is required")
    return section


def _evidence_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:{canonical_digest(value)}"


def _dependency_contract_ok(
    value: dict[str, Any],
    binding: dict[str, Any],
) -> bool:
    section = _binding_section(binding)
    seams = value.get("seams")
    if not isinstance(seams, list):
        return False
    found: set[tuple[str, str, str]] = set()
    for row in seams:
        if not isinstance(row, dict):
            continue
        found.add(
            (
                str(row.get("source_glob")),
                str(row.get("allowed_fragment")),
                str(row.get("kind")),
            )
        )
    required: set[tuple[str, str, str]] = set()
    for row in section["requiredSeams"]:
        if not isinstance(row, dict):
            return False
        required.add(
            (
                str(row.get("sourceGlob")),
                str(row.get("allowedFragment")),
                str(row.get("kind")),
            )
        )
    return required.issubset(found)


def _source_boundary_ok(
    binding: dict[str, Any],
    request_source: str,
    admission_source: str,
    store_source: str,
) -> bool:
    section = _binding_section(binding)
    combined = "\n".join((request_source, admission_source, store_source))
    forbidden = tuple(str(item) for item in section["forbiddenSourceFragments"])
    if any(token in combined for token in forbidden):
        return False

    required_store_markers = tuple(
        str(item) for item in section["requiredStoreMarkers"]
    )
    return (
        section["requestContractImport"] in request_source
        and section["admissionContractImport"] in admission_source
        and all(marker in store_source for marker in required_store_markers)
    )


def _native_e2e_ok(
    evidence: dict[str, Any],
    binding: dict[str, Any],
) -> bool:
    section = _binding_section(binding)
    source = evidence.get("source")
    matrix = evidence.get("matrix")
    if not isinstance(source, dict) or not isinstance(matrix, dict):
        return False
    expected = section["expectedMatrix"]
    return (
        evidence.get("schemaVersion") == 1
        and evidence.get("kind") == "ordivon-agent-native-website-e2e-r1"
        and source.get("executionDisposition") == "succeeded"
        and all(matrix.get(key) == value for key, value in expected.items())
        and evidence.get("approvalConsumed") is True
        and evidence.get("productionHumanPresenceClaim") is False
        and evidence.get("productionEligible") is False
    )


def build_gate_result(
    manifest: dict[str, Any],
    binding: dict[str, Any],
    dependency_contracts: dict[str, Any],
    native_e2e: dict[str, Any],
    request_source: str,
    admission_source: str,
    store_source: str,
    *,
    gate_id: str = "gate:web-security-agent-authority",
) -> dict[str, Any]:
    _binding_section(binding)
    compiled = compile_manifest(manifest)
    gates = {row["id"]: row for row in manifest["gateRequirements"]}
    gate = gates.get(gate_id)
    if gate is None:
        raise CircuitContractError(f"manifest does not declare {gate_id}")

    checks = (
        _dependency_contract_ok(dependency_contracts, binding),
        _source_boundary_ok(binding, request_source, admission_source, store_source),
        _native_e2e_ok(native_e2e, binding),
    )
    standing = "SATISFIED" if all(checks) else "UNSATISFIED"

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compiled["manifestDigest"],
        "gateId": gate_id,
        "verifierOwnerId": gate["verifierOwnerId"],
        "standing": standing,
        "evidenceRefs": [
            f"r3-binding:{canonical_digest(binding)}",
            _evidence_ref("repo-dependency-contracts", dependency_contracts),
            _evidence_ref("web-security-request-consumer", request_source),
            _evidence_ref("web-security-admission-consumer", admission_source),
            _evidence_ref("web-local-authority-store", store_source),
            _evidence_ref("web-agent-native-e2e", native_e2e),
        ],
        "supportScope": gate["supportScope"],
        "nonClaims": [
            "Security verification does not own Web Grant or effect durable state.",
            "Web effect success does not make Web the OAuth/DPoP protocol authority.",
            "This gate does not establish production eligibility or physical human presence.",
        ],
    }
    validate_gate_result(manifest, compiled, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("binding", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifest = _load_json(args.manifest)
        binding = _load_json(args.binding)
        section = _binding_section(binding)
        paths = section["paths"]
        dependency_path = resolve_repo_file(
            args.repo_root, paths["dependencyContracts"]
        )
        with dependency_path.open("rb") as handle:
            dependencies = tomllib.load(handle)
        result = build_gate_result(
            manifest,
            binding,
            dependencies,
            _load_json(resolve_repo_file(args.repo_root, paths["nativeE2e"])),
            _read(resolve_repo_file(args.repo_root, paths["requestSource"])),
            _read(resolve_repo_file(args.repo_root, paths["admissionSource"])),
            _read(resolve_repo_file(args.repo_root, paths["storeSource"])),
        )
    except (
        OSError,
        KeyError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
        CircuitContractError,
    ) as exc:
        raise SystemExit(f"web-security gate R3 failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
