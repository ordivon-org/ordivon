from __future__ import annotations

from pathlib import Path
from typing import Any

from artifact_operations.receipt import expected_file, operation_file_fact
from scripts.artifact_oci_package import execute_oci_package_stage

from .common import PreparedOperation, write_json
from .trust import validate_trust_material


class PackageOperationHandler:
    def prepare(self, operation: dict[str, Any]) -> PreparedOperation:
        inputs = operation["inputs"]
        options = operation["options"]
        profile_path = expected_file(dict(inputs["profile"]), "profile")
        artifact_path = expected_file(dict(inputs["artifact"]), "artifact")
        verify_report_path = expected_file(dict(inputs["verifyReport"]), "verifyReport")
        local = bool(options.get("allowLocalUnsignedDevelopment", False))
        trust = (
            None
            if local
            else validate_trust_material(dict(inputs.get("trustMaterial") or {}))
        )
        exact: dict[str, Any] = {
            "profile": operation_file_fact(profile_path),
            "artifact": operation_file_fact(artifact_path),
            "verifyReport": operation_file_fact(verify_report_path),
            "allowLocalUnsignedDevelopment": local,
        }
        if trust is not None:
            exact["trustMaterial"] = trust["commitment"]
        return PreparedOperation(
            exact,
            {
                "profilePath": profile_path,
                "artifactPath": artifact_path,
                "verifyReportPath": verify_report_path,
                "local": local,
                "trust": trust,
            },
        )

    def produce(
        self, context: dict[str, Any], output_directory: Path
    ) -> tuple[dict[str, str], dict[str, Any]]:
        package = output_directory / "package"
        trust = context["trust"]
        bundles = (
            None
            if trust is None
            else {gate: Path(fact["path"]) for gate, fact in trust["bundles"].items()}
        )
        result = execute_oci_package_stage(
            context["profilePath"],
            context["artifactPath"],
            context["verifyReportPath"],
            package,
            allow_local_unsigned=context["local"],
            gate_bundles=bundles,
            trust_policy_path=(
                None if trust is None else Path(trust["trustPolicy"]["path"])
            ),
            signer_ids=None if trust is None else trust["signerIds"],
        )
        out = output_directory / "oci-package-stage.json"
        write_json(out, result)
        if result.get("status") != "PASS":
            raise RuntimeError(f"OCI package stage did not PASS: {result.get('failures')}")
        layout = package / "layout"
        roles = {
            "packageReport": "oci-package-stage.json",
            "ociLayoutIndex": "package/layout/index.json",
            "ociLayoutMarker": "package/layout/oci-layout",
        }
        for blob in sorted((layout / "blobs" / "sha256").glob("*")):
            roles[f"ociBlob:{blob.name}"] = f"package/layout/blobs/sha256/{blob.name}"
        return roles, {
            "releaseReady": bool(result.get("releaseReady")),
            "trustStanding": result.get("trustStanding"),
            "packageRelativePath": "package/layout",
            "subjectDigest": result.get("oci", {}).get("subject", {}).get("digest"),
            "referrerCount": len(result.get("oci", {}).get("discover", {}).get("referrers", [])),
        }
