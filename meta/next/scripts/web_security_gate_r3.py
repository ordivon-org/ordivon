#!/usr/bin/env python3
"""Web <-> Security public-contract seam verifier for Cross-domain R3.

This adapter verifies only the current delegated-Agent seam: Web consumes the two
Security-owned public contracts, avoids Security internal policy/lab imports, keeps
local replay/Grant/effect state in WebStore, and has owner-native E2E evidence for
the expected fail-closed and replay semantics. It does not claim production
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
except ModuleNotFoundError:
    from cognitive_circuit_r1 import (
        CircuitContractError,
        canonical_digest,
        compile_manifest,
        validate_gate_result,
    )


REQUEST_SOURCE = "apps/web/src/security-agent-verifier.ts"
ADMISSION_SOURCE = "apps/web/src/agent-authority.ts"
STORE_SOURCE = "apps/web/src/store.ts"

REQUIRED_SEAMS = {
    (
        REQUEST_SOURCE,
        "platform/security/contracts/agent-request-verifier-v1/",
        "PUBLIC_SOURCE_CONTRACT",
    ),
    (
        ADMISSION_SOURCE,
        "platform/security/contracts/agent-admission-v1/",
        "PUBLIC_SOURCE_CONTRACT",
    ),
}

EXPECTED_MATRIX = {
    "noProof": 401,
    "wrongKey": 401,
    "firstCreate": 201,
    "proofReplay": 401,
    "exactReplay": 200,
    "conflict": 409,
    "publishStepUp": 428,
    "approval": 201,
    "publishApproved": 200,
    "revoke": 200,
    "newEffectAfterRevoke": 403,
    "historicalReplayAfterRevoke": 200,
}


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _evidence_ref(prefix: str, value: Any) -> str:
    return f"{prefix}:{canonical_digest(value)}"


def _dependency_contract_ok(value: dict[str, Any]) -> bool:
    seams = value.get("seams")
    if not isinstance(seams, list):
        return False
    found: set[tuple[str, str, str]] = set()
    for row in seams:
        if not isinstance(row, dict):
            continue
        if row.get("from_owner") != "web" or row.get("to_owner") != "security":
            continue
        found.add(
            (
                str(row.get("source_glob")),
                str(row.get("allowed_fragment")),
                str(row.get("kind")),
            )
        )
    return REQUIRED_SEAMS.issubset(found)


def _source_boundary_ok(
    request_source: str,
    admission_source: str,
    store_source: str,
) -> bool:
    forbidden = (
        "platform/security/policies/",
        "platform/security/labs/",
        "agent_admission.rego",
        "effect_admission.rego",
    )
    if any(token in request_source or token in admission_source for token in forbidden):
        return False

    request_contract = (
        "../../../platform/security/contracts/agent-request-verifier-v1/src/index.ts"
    )
    admission_contract = (
        "../../../platform/security/contracts/agent-admission-v1/evaluate.py"
    )
    required_store_markers = (
        "CREATE TABLE IF NOT EXISTS agent_grants",
        "CREATE TABLE IF NOT EXISTS dpop_proofs",
        "consumeDpopProof(",
        "createAgentGrant(",
        "revokeAgentGrant(",
        "requirePendingEffectApproval(",
        "putEffectApproval(",
    )
    return (
        request_contract in request_source
        and admission_contract in admission_source
        and all(marker in store_source for marker in required_store_markers)
    )


def _native_e2e_ok(evidence: dict[str, Any]) -> bool:
    source = evidence.get("source")
    matrix = evidence.get("matrix")
    if not isinstance(source, dict) or not isinstance(matrix, dict):
        return False
    return (
        evidence.get("schemaVersion") == 1
        and evidence.get("kind") == "ordivon-agent-native-website-e2e-r1"
        and source.get("executionDisposition") == "succeeded"
        and all(matrix.get(key) == value for key, value in EXPECTED_MATRIX.items())
        and evidence.get("approvalConsumed") is True
        and evidence.get("productionHumanPresenceClaim") is False
        and evidence.get("productionEligible") is False
    )


def build_gate_result(
    manifest: dict[str, Any],
    dependency_contracts: dict[str, Any],
    native_e2e: dict[str, Any],
    request_source: str,
    admission_source: str,
    store_source: str,
    *,
    gate_id: str = "gate:web-security-agent-authority",
) -> dict[str, Any]:
    compiled = compile_manifest(manifest)
    gates = {row["id"]: row for row in manifest["gateRequirements"]}
    gate = gates.get(gate_id)
    if gate is None:
        raise CircuitContractError(f"manifest does not declare {gate_id}")

    checks = (
        _dependency_contract_ok(dependency_contracts),
        _source_boundary_ok(request_source, admission_source, store_source),
        _native_e2e_ok(native_e2e),
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
    parser.add_argument("dependency_contracts", type=Path)
    parser.add_argument("native_e2e", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()

    try:
        manifest = _load_json(args.manifest)
        with args.dependency_contracts.open("rb") as handle:
            dependencies = tomllib.load(handle)
        result = build_gate_result(
            manifest,
            dependencies,
            _load_json(args.native_e2e),
            _read(args.repo_root / REQUEST_SOURCE),
            _read(args.repo_root / ADMISSION_SOURCE),
            _read(args.repo_root / STORE_SOURCE),
        )
    except (
        OSError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
        CircuitContractError,
    ) as exc:
        raise SystemExit(f"web-security gate R3 failed: {exc}") from exc

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
