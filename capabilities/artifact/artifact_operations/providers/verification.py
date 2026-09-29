from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from artifact_core.bindings import CapabilityBindingRegistry
from artifact_core.profiles import ProfileRegistry
from artifact_operations.receipt import expected_file, operation_file_fact
from artifact_verification import (
    build_production_v1_evaluation_request,
    build_registered_v2_evaluation_request,
    project_production_v1_result,
    project_registered_v2_result,
    resolve_verifier_plugin,
    validate_evaluation_projection,
)

from .common import PreparedOperation

ProductionVerify = Callable[[Path, Path, Path, Path | None], dict[str, Any]]


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Artifact profile must be a JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class VerifyOperationHandler:
    """Route one canonical Artifact verify operation to a replaceable verifier provider.

    Current production-v1 profiles retain their existing verify-stage implementation.
    Native-v2 family profiles resolve one explicit CapabilityBinding/VerifierPlugin.
    Both registered routes project into the same EvaluationProjection waist. Unknown
    legacy v1 profiles retain the historical stage path without pretending that a
    canonical-v2 compatibility mapping exists.
    """

    def __init__(
        self,
        artifact_root: Path,
        *,
        production_verify: ProductionVerify,
    ) -> None:
        self.artifact_root = artifact_root.resolve()
        self.repo_root = self.artifact_root.parent
        self.production_verify = production_verify
        self.profiles = ProfileRegistry(self.artifact_root)
        self.bindings = CapabilityBindingRegistry(self.artifact_root)

    def prepare(self, operation: dict[str, Any]) -> PreparedOperation:
        inputs = operation["inputs"]
        unknown = set(inputs) - {"profile", "artifact", "objectContract"}
        if unknown:
            raise RuntimeError(
                f"verify inputs contain unsupported fields: {sorted(unknown)}"
            )
        if "profile" not in inputs or "artifact" not in inputs:
            raise RuntimeError("verify requires profile and artifact inputs")
        profile_path = expected_file(dict(inputs["profile"]), "profile")
        artifact_path = expected_file(dict(inputs["artifact"]), "artifact")
        object_contract_path = (
            expected_file(dict(inputs["objectContract"]), "objectContract")
            if inputs.get("objectContract") is not None
            else None
        )
        raw = _load_json(profile_path)
        profile_id = raw.get("id")
        version = raw.get("profileVersion")
        if not isinstance(profile_id, str) or not profile_id:
            raise RuntimeError("verify profile id is absent")

        mode: str
        binding = None
        record = None
        if version == 1:
            try:
                record = self.profiles.resolve(profile_id)
            except KeyError:
                record = None
            if (
                record is not None
                and record.source_kind == "production-v1-adapted"
                and profile_path.resolve() == record.source_path.resolve()
            ):
                mode = "production-v1-registered"
            else:
                # Preserve the historical DirectPython ability to verify bounded
                # ephemeral v1 profiles without manufacturing canonical-v2 semantics.
                mode = "production-v1-legacy-unregistered"
            if object_contract_path is not None:
                raise RuntimeError("production-v1 verify does not accept objectContract")
        elif version == 2:
            try:
                record = self.profiles.resolve(profile_id)
            except KeyError as error:
                raise RuntimeError(str(error)) from error
            if record.source_kind != "native-v2-shadow":
                raise RuntimeError(
                    "production-v1 profile must verify through its production source bytes"
                )
            if profile_path.resolve() != record.canonical_path.resolve():
                raise RuntimeError("v2 verify profile path is not canonical authority")
            binding = self.bindings.resolve(profile_id, "verify")
            if binding.object_contract_required and object_contract_path is None:
                raise RuntimeError(
                    f"Artifact profile requires an object contract: {profile_id}"
                )
            mode = "registered-v2-family"
        else:
            raise RuntimeError(f"unsupported verify profileVersion: {version!r}")

        exact: dict[str, Any] = {
            "profile": operation_file_fact(profile_path),
            "artifact": operation_file_fact(artifact_path),
        }
        if object_contract_path is not None:
            exact["objectContract"] = operation_file_fact(object_contract_path)
        context = {
            "operationId": operation["operationId"],
            "evaluationRequestId": operation.get("options", {}).get(
                "evaluationRequestId", operation["operationId"]
            ),
            "verificationMode": mode,
            "profileId": profile_id,
            "profilePath": profile_path,
            "artifactPath": artifact_path,
            "objectContractPath": object_contract_path,
            "profileRecord": record,
            "binding": binding,
        }
        return PreparedOperation(exact, context)

    def produce(
        self,
        context: dict[str, Any],
        output_directory: Path,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        evidence = output_directory / "evidence"
        evidence.mkdir(parents=True, exist_ok=True)
        mode = context["verificationMode"]
        profile_path: Path = context["profilePath"]
        artifact_path: Path = context["artifactPath"]
        object_contract_path: Path | None = context["objectContractPath"]
        evaluation_projection: dict[str, Any] | None = None

        if mode in {"production-v1-registered", "production-v1-legacy-unregistered"}:
            result = self.production_verify(
                profile_path,
                artifact_path,
                evidence,
                None,
            )
            report_name = "verify-stage.json"
            if mode == "production-v1-registered":
                record = context["profileRecord"]
                request = build_production_v1_evaluation_request(
                    record.source_path,
                    record.canonical_path,
                    artifact_path,
                    request_id=str(context["evaluationRequestId"]),
                )
                evaluation_projection = project_production_v1_result(request, result)
        elif mode == "registered-v2-family":
            binding = context["binding"]
            record = context["profileRecord"]
            plugin = resolve_verifier_plugin(binding, artifact_root=self.repo_root)
            result = plugin.verify(
                artifact_path,
                evidence,
                object_contract=object_contract_path,
            )
            report_name = "family-verification.json"
            request = build_registered_v2_evaluation_request(
                record,
                binding,
                artifact_path,
                object_contract_path=object_contract_path,
                request_id=str(context["evaluationRequestId"]),
            )
            evaluation_projection = project_registered_v2_result(request, result)
        else:
            raise RuntimeError(f"unsupported verificationMode: {mode!r}")

        report = output_directory / report_name
        _write_json(report, result)
        roles: dict[str, str] = {"verifyReport": report_name}
        if evaluation_projection is not None:
            validate_evaluation_projection(evaluation_projection)
            projection_path = output_directory / "evaluation-projection.json"
            _write_json(projection_path, evaluation_projection)
            roles["evaluationProjection"] = "evaluation-projection.json"

        if result.get("status") != "PASS":
            raise RuntimeError(
                f"verify stage did not PASS: {result.get('failures')}"
            )

        gates: list[str] = []
        for path in sorted(evidence.glob("*.json")):
            relative = f"evidence/{path.name}"
            if path.name.endswith(".vsa.json"):
                gate = path.name[:-9]
                roles[f"gateVsa:{gate}"] = relative
                gates.append(gate)
            elif path.name.endswith(".raw.json"):
                gate = path.name[:-9]
                roles[f"rawEvidence:{gate}"] = relative

        if evaluation_projection is not None:
            vector = evaluation_projection["standingDecision"]["standingVector"]
            complete = (
                vector["verificationStatus"] == "PASS"
                and vector["evidenceCompleteness"] == "COMPLETE"
            )
        else:
            complete = bool(result.get("profileVerificationComplete"))
        return roles, {
            "verificationMode": mode,
            "profileId": context["profileId"],
            "profileVerificationComplete": complete,
            "gateVsas": gates,
            "evaluationProjection": evaluation_projection is not None,
        }
