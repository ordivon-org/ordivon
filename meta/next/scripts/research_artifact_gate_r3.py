#!/usr/bin/env python3
"""Research <-> Artifact publication seam verifier for Cross-domain R3.

The adapter understands a task-local seam binding, not repository topology.
It verifies only that a Research publication composition profile consumes
Artifact-owned carrier mechanics without lifting carrier PASS into scientific
truth, Human perceptual closure, venue authority, or submission completion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.cognitive_circuit_r1 import (
        CircuitContractError,
        canonical_digest,
        compile_manifest,
        validate_gate_result,
    )
except ModuleNotFoundError:
    from cognitive_circuit_r1 import (
        CircuitContractError,
        canonical_digest,
        compile_manifest,
        validate_gate_result,
    )


BINDING_KIND = "ordivon.cross-domain-verification-r3-binding"
BINDING_ROLE = "task-local-acceptance-binding-not-owner-truth"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def _repo_path(repo_root: Path, relative: str) -> Path:
    root = repo_root.resolve()
    candidate = (root / relative).resolve()
    if candidate != root and root not in candidate.parents:
        raise CircuitContractError(f"binding path escapes repository: {relative}")
    return candidate


def _binding_section(binding: dict[str, Any]) -> dict[str, Any]:
    if (
        binding.get("schemaVersion") != 1
        or binding.get("kind") != BINDING_KIND
        or binding.get("truthRole") != BINDING_ROLE
    ):
        raise CircuitContractError("invalid cross-domain R3 binding identity")
    section = binding.get("researchArtifact")
    if not isinstance(section, dict):
        raise CircuitContractError("binding researchArtifact section is required")
    required = (
        "profilePath",
        "dogfoodPath",
        "expectedScientificTruth",
        "expectedCarrierMechanics",
        "expectedDistributionEffect",
    )
    if any(
        not isinstance(section.get(key), str) or not section[key] for key in required
    ):
        raise CircuitContractError("binding researchArtifact section is incomplete")
    return section


def _evidence_ref(prefix: str, value: dict[str, Any]) -> str:
    return f"{prefix}:{canonical_digest(value)}"


def _profile_boundary_ok(
    profile: dict[str, Any],
    binding: dict[str, Any],
) -> bool:
    section = _binding_section(binding)
    bindings = profile.get("ownerBindings")
    if not isinstance(bindings, dict):
        return False
    return (
        profile.get("schemaVersion") == 1
        and profile.get("kind") == "research-publication-closure-composition-profile"
        and profile.get("truthRole") == "composition-profile-not-scientific-truth"
        and profile.get("runtimeOwner") is None
        and bindings.get("scientificTruth") == section["expectedScientificTruth"]
        and bindings.get("carrierMechanics") == section["expectedCarrierMechanics"]
        and bindings.get("distributionEffect") == section["expectedDistributionEffect"]
    )


def _dogfood_boundary_ok(dogfood: dict[str, Any]) -> bool:
    evaluation = dogfood.get("evaluation")
    nonclaims = dogfood.get("nonClaims")
    if not isinstance(evaluation, dict) or not isinstance(nonclaims, list):
        return False
    text = "\n".join(str(item) for item in nonclaims)
    machine_pass = evaluation.get("machineStanding") == "PASS"
    standing = evaluation.get("standing")
    human_gate_consistent = standing in {"PASS", "PENDING_HUMAN"}
    if standing == "PENDING_HUMAN":
        human_gate_consistent = "HUMAN_PERCEPTUAL_SIGNOFF" in evaluation.get(
            "humanGates", []
        )
    return (
        dogfood.get("schemaVersion") == 1
        and dogfood.get("kind") == "research-publication-carrier-dogfood-receipt"
        and machine_pass
        and human_gate_consistent
        and "does not establish scientific correctness" in text
        and "does not satisfy Human perceptual signoff" in text
    )


def build_gate_result(
    manifest: dict[str, Any],
    binding: dict[str, Any],
    profile: dict[str, Any],
    dogfood: dict[str, Any],
    *,
    gate_id: str = "gate:research-artifact-carrier",
) -> dict[str, Any]:
    _binding_section(binding)
    compiled = compile_manifest(manifest)
    gates = {row["id"]: row for row in manifest["gateRequirements"]}
    gate = gates.get(gate_id)
    if gate is None:
        raise CircuitContractError(f"manifest does not declare {gate_id}")

    profile_ok = _profile_boundary_ok(profile, binding)
    dogfood_ok = _dogfood_boundary_ok(dogfood)
    standing = "SATISFIED" if profile_ok and dogfood_ok else "UNSATISFIED"

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
            _evidence_ref("research-profile", profile),
            _evidence_ref("artifact-publication-dogfood", dogfood),
        ],
        "supportScope": gate["supportScope"],
        "nonClaims": [
            "Artifact carrier machine PASS is not scientific correctness.",
            "Artifact carrier machine PASS is not Human perceptual signoff.",
            "Artifact does not become venue-policy or submission authority.",
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
        manifest = _load(args.manifest)
        binding = _load(args.binding)
        section = _binding_section(binding)
        result = build_gate_result(
            manifest,
            binding,
            _load(_repo_path(args.repo_root, section["profilePath"])),
            _load(_repo_path(args.repo_root, section["dogfoodPath"])),
        )
    except (OSError, json.JSONDecodeError, CircuitContractError) as exc:
        raise SystemExit(f"research-artifact gate R3 failed: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
