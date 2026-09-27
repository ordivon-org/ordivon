from __future__ import annotations

from pathlib import Path
from typing import Any

from artifact_operations.receipt import expected_file, operation_file_fact
from artifact_trust import vsa as trust_vsa

from .common import PreparedOperation, write_json


def validate_trust_material(value: dict[str, Any]) -> dict[str, Any]:
    unknown = set(value) - {"trustPolicy", "bundles", "signerIds"}
    if unknown:
        raise RuntimeError(f"trust material contains unsupported fields: {sorted(unknown)}")
    if set(value) != {"trustPolicy", "bundles", "signerIds"}:
        raise RuntimeError(
            "trust material requires exactly trustPolicy, bundles and signerIds"
        )
    trust_policy = operation_file_fact(
        expected_file(dict(value["trustPolicy"]), "trustPolicy")
    )
    bundles_value = value["bundles"]
    signers = value["signerIds"]
    if not isinstance(bundles_value, dict) or not bundles_value:
        raise RuntimeError("trust material bundles must be non-empty")
    if not isinstance(signers, dict) or set(signers) != set(bundles_value):
        raise RuntimeError("trust material signerIds must exactly match bundle gates")
    bundles: dict[str, Any] = {}
    for gate, fact in sorted(bundles_value.items()):
        bundles[gate] = operation_file_fact(
            expected_file(dict(fact), f"bundles.{gate}")
        )
        if not isinstance(signers[gate], str) or not signers[gate]:
            raise RuntimeError(f"signerIds.{gate} must be non-empty")
    commitment = {
        "trustPolicy": trust_policy,
        "bundles": bundles,
        "signerIds": dict(sorted(signers.items())),
    }
    return {
        "trustPolicy": trust_policy,
        "bundles": bundles,
        "signerIds": dict(sorted(signers.items())),
        "commitment": commitment,
    }


class TrustOperationHandler:
    def prepare(self, operation: dict[str, Any]) -> PreparedOperation:
        inputs = operation["inputs"]
        profile_path = expected_file(dict(inputs["profile"]), "profile")
        artifact_path = expected_file(dict(inputs["artifact"]), "artifact")
        trust = validate_trust_material(dict(inputs["trustMaterial"]))
        gate_vsas = dict(inputs["gateVsas"])
        normalized: dict[str, Any] = {}
        for gate, fact in sorted(gate_vsas.items()):
            normalized[gate] = operation_file_fact(
                expected_file(dict(fact), f"gateVsas.{gate}")
            )
        return PreparedOperation(
            {
                "profile": operation_file_fact(profile_path),
                "artifact": operation_file_fact(artifact_path),
                "gateVsas": normalized,
                "trustMaterial": trust["commitment"],
            },
            {
                "profilePath": profile_path,
                "artifactPath": artifact_path,
                "gateVsas": normalized,
                "trust": trust,
            },
        )

    def produce(
        self, context: dict[str, Any], output_directory: Path
    ) -> tuple[dict[str, str], dict[str, Any]]:
        normalized = context["gateVsas"]
        trust = context["trust"]
        gate_paths = {gate: Path(fact["path"]) for gate, fact in normalized.items()}
        bundles = {gate: Path(fact["path"]) for gate, fact in trust["bundles"].items()}
        result = trust_vsa.aggregate_vsa_gates(
            context["profilePath"],
            context["artifactPath"],
            gate_paths,
            allow_local_unsigned=False,
            bundles=bundles,
            trust_policy_path=Path(trust["trustPolicy"]["path"]),
            signer_ids=trust["signerIds"],
            toolchain=trust_vsa.default_trust_toolchain_config(),
        )
        out = output_directory / "trusted-vsa-aggregation.json"
        write_json(out, result)
        if result.get("status") != "PASS":
            raise RuntimeError(
                f"trusted VSA aggregation did not PASS: {result.get('failures')}"
            )
        return {"trustAggregation": "trusted-vsa-aggregation.json"}, {
            "trustedGates": sorted(result.get("components", {}))
        }
