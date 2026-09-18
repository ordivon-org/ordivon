from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any

from artifact_operations.receipt import expected_file, operation_file_fact
from .common import PreparedOperation

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_PYTHON = Path(
    "/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python"
)
DEFAULT_ARTIFACT_CLI = ROOT / "scripts/artifact_delivery.py"
DEFAULT_ARTIFACT_OCI_CLI = ROOT / "scripts/artifact_oci_package.py"


def _simple_fact(value: dict[str, Any]) -> dict[str, Any]:
    digest = value.get("sha256") or (value.get("digest") or {}).get("sha256")
    return {
        "path": str(Path(value["path"]).resolve()),
        "sha256": digest,
        "name": value.get("name") or Path(value["path"]).name,
        "size": value.get("size"),
    }


class DeliveryCliOperationProvider:
    """Replaceable bridge from stable Artifact operations to the legacy CLI surface.

    CLI vocabulary is intentionally confined here. A later provider can call Python
    owners directly without changing Temporal or receipt semantics.
    """

    def __init__(
        self,
        *,
        artifact_python: Path = DEFAULT_ARTIFACT_PYTHON,
        artifact_cli: Path = DEFAULT_ARTIFACT_CLI,
        artifact_oci_cli: Path = DEFAULT_ARTIFACT_OCI_CLI,
    ) -> None:
        self.artifact_python = artifact_python.absolute()
        self.artifact_cli = artifact_cli.resolve()
        self.artifact_oci_cli = artifact_oci_cli.resolve()
        if not self.artifact_python.is_file():
            raise RuntimeError(
                f"Artifact Delivery Python is absent: {self.artifact_python}"
            )
        if not self.artifact_cli.is_file():
            raise RuntimeError(f"Artifact Delivery CLI is absent: {self.artifact_cli}")
        if not self.artifact_oci_cli.is_file():
            raise RuntimeError(
                f"Artifact OCI Package CLI is absent: {self.artifact_oci_cli}"
            )

    def _run_cli(
        self, args: list[str], *, timeout: int = 300
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.artifact_python), str(self.artifact_cli), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            env=dict(os.environ),
        )

    def _run_oci_cli(
        self, args: list[str], *, timeout: int = 300
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.artifact_python), str(self.artifact_oci_cli), *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            env=dict(os.environ),
        )

    @staticmethod
    def cli_failure_message(
        label: str,
        process: subprocess.CompletedProcess[str],
        report: Path | None = None,
    ) -> str:
        details: list[str] = []
        if report is not None and report.is_file():
            try:
                report_text = report.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeError):
                report_text = ""
            if report_text:
                details.append(f"report={report_text[-4000:]}")
        for stream in ("stdout", "stderr"):
            text = getattr(process, stream, "") or ""
            if text.strip():
                details.append(f"{stream}={text[-4000:]}")
        if not details:
            details.append("no diagnostic output")
        return f"{label} failed (exit={process.returncode}): " + " | ".join(details)

    def validate_trust_material(self, value: dict[str, Any]) -> dict[str, Any]:
        unknown = set(value) - {"trustPolicy", "bundles", "signerIds"}
        if unknown:
            raise RuntimeError(
                f"trust material contains unsupported fields: {sorted(unknown)}"
            )
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
            raise RuntimeError(
                "trust material signerIds must exactly match bundle gates"
            )
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

    def prepare_operation(self, operation: dict[str, Any]) -> PreparedOperation:
        kind = operation["operationKind"]
        inputs = operation["inputs"]
        options = operation["options"]

        if kind in {"prepare", "build"}:
            request_path = expected_file(dict(inputs["request"]), "request")
            exact = {"request": operation_file_fact(request_path)}
            return PreparedOperation(exact, {"requestPath": request_path})

        if kind == "verify":
            profile_path = expected_file(dict(inputs["profile"]), "profile")
            artifact_path = expected_file(dict(inputs["artifact"]), "artifact")
            exact = {
                "profile": operation_file_fact(profile_path),
                "artifact": operation_file_fact(artifact_path),
            }
            return PreparedOperation(
                exact,
                {"profilePath": profile_path, "artifactPath": artifact_path},
            )

        if kind == "verify-trust":
            profile_path = expected_file(dict(inputs["profile"]), "profile")
            artifact_path = expected_file(dict(inputs["artifact"]), "artifact")
            trust = self.validate_trust_material(dict(inputs["trustMaterial"]))
            gate_vsas = dict(inputs["gateVsas"])
            normalized: dict[str, Any] = {}
            for gate, fact in sorted(gate_vsas.items()):
                normalized[gate] = operation_file_fact(
                    expected_file(dict(fact), f"gateVsas.{gate}")
                )
            exact = {
                "profile": operation_file_fact(profile_path),
                "artifact": operation_file_fact(artifact_path),
                "gateVsas": normalized,
                "trustMaterial": trust["commitment"],
            }
            return PreparedOperation(
                exact,
                {
                    "profilePath": profile_path,
                    "artifactPath": artifact_path,
                    "gateVsas": normalized,
                    "trust": trust,
                },
            )

        if kind == "package":
            profile_path = expected_file(dict(inputs["profile"]), "profile")
            artifact_path = expected_file(dict(inputs["artifact"]), "artifact")
            verify_report_path = expected_file(
                dict(inputs["verifyReport"]), "verifyReport"
            )
            local = bool(options.get("allowLocalUnsignedDevelopment", False))
            trust = (
                None
                if local
                else self.validate_trust_material(dict(inputs.get("trustMaterial") or {}))
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

        raise RuntimeError(f"unsupported Artifact operation kind: {kind}")

    def produce(
        self,
        operation_kind: str,
        context: dict[str, Any],
        output_directory: Path,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        if operation_kind == "prepare":
            request_path = context["requestPath"]
            out = output_directory / "derived-plan.json"
            process = self._run_cli(
                ["compile-request", str(request_path), "--output", str(out)]
            )
            if process.returncode or not out.is_file():
                raise RuntimeError(
                    self.cli_failure_message("compile-request", process, out)
                )
            plan = json.loads(out.read_text())
            if plan.get("status") != "PASS":
                raise RuntimeError(
                    f"derived plan did not PASS: {plan.get('failures')}"
                )
            return {"plan": "derived-plan.json"}, {
                "requestId": plan.get("requestId"),
                "profile": _simple_fact(plan["resolvedInputs"]["profile"]),
                "source": _simple_fact(plan["resolvedInputs"]["source"]),
                "requiredGates": plan.get("requiredGates", []),
            }

        if operation_kind == "build":
            request_path = context["requestPath"]
            artifacts = output_directory / "artifacts"
            report = output_directory / "build-stage.json"
            process = self._run_cli(
                [
                    "build-request",
                    str(request_path),
                    "--output-directory",
                    str(artifacts),
                    "--output",
                    str(report),
                ]
            )
            if process.returncode or not report.is_file():
                raise RuntimeError(
                    self.cli_failure_message("build-request", process, report)
                )
            result = json.loads(report.read_text())
            if result.get("status") != "PASS":
                raise RuntimeError(
                    f"build stage did not PASS: {result.get('failures')}"
                )
            artifact_path = Path(result["artifact"]["path"])
            if (
                artifact_path.parent.resolve() != artifacts.resolve()
                or not artifact_path.is_file()
            ):
                raise RuntimeError("build output escaped operation directory")
            return {
                "buildReport": "build-stage.json",
                "artifact": f"artifacts/{artifact_path.name}",
            }, {
                "artifactName": artifact_path.name,
                "adapter": result.get("plan", {}).get("buildAdapter"),
            }

        if operation_kind == "verify":
            profile_path = context["profilePath"]
            artifact_path = context["artifactPath"]
            evidence = output_directory / "evidence"
            report = output_directory / "verify-stage.json"
            process = self._run_cli(
                [
                    "verify-stage",
                    "--profile",
                    str(profile_path),
                    "--artifact",
                    str(artifact_path),
                    "--output-directory",
                    str(evidence),
                    "--output",
                    str(report),
                ]
            )
            if process.returncode or not report.is_file():
                raise RuntimeError(
                    self.cli_failure_message("verify-stage", process, report)
                )
            result = json.loads(report.read_text())
            if result.get("status") != "PASS":
                raise RuntimeError(
                    f"verify stage did not PASS: {result.get('failures')}"
                )
            roles = {"verifyReport": "verify-stage.json"}
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
            return roles, {
                "profileVerificationComplete": bool(
                    result.get("profileVerificationComplete")
                ),
                "gateVsas": gates,
            }

        if operation_kind == "verify-trust":
            profile_path = context["profilePath"]
            artifact_path = context["artifactPath"]
            normalized = context["gateVsas"]
            trust = context["trust"]
            out = output_directory / "trusted-vsa-aggregation.json"
            args = [
                "aggregate-vsa-gates",
                "--profile",
                str(profile_path),
                "--subject",
                str(artifact_path),
            ]
            for gate, fact in sorted(normalized.items()):
                args += ["--gate", f"{gate}={fact['path']}"]
            for gate, fact in sorted(trust["bundles"].items()):
                args += ["--bundle", f"{gate}={fact['path']}"]
            for gate, signer in sorted(trust["signerIds"].items()):
                args += ["--signer", f"{gate}={signer}"]
            args += [
                "--trust-policy",
                trust["trustPolicy"]["path"],
                "--output",
                str(out),
            ]
            process = self._run_cli(args)
            if process.returncode or not out.is_file():
                raise RuntimeError(
                    self.cli_failure_message(
                        "trusted VSA aggregation", process, out
                    )
                )
            result = json.loads(out.read_text())
            if result.get("status") != "PASS":
                raise RuntimeError(
                    f"trusted VSA aggregation did not PASS: {result.get('failures')}"
                )
            return {"trustAggregation": "trusted-vsa-aggregation.json"}, {
                "trustedGates": sorted(result.get("components", {}))
            }

        if operation_kind == "package":
            profile_path = context["profilePath"]
            artifact_path = context["artifactPath"]
            verify_report_path = context["verifyReportPath"]
            local = context["local"]
            trust = context["trust"]
            package = output_directory / "package"
            out = output_directory / "oci-package-stage.json"
            args = [
                "--profile",
                str(profile_path),
                "--primary",
                str(artifact_path),
                "--verify-report",
                str(verify_report_path),
                "--output-directory",
                str(package),
                "--output",
                str(out),
            ]
            if local:
                args.append("--allow-local-unsigned")
            else:
                assert trust is not None
                for gate, fact in sorted(trust["bundles"].items()):
                    args += ["--gate-bundle", f"{gate}={fact['path']}"]
                for gate, signer in sorted(trust["signerIds"].items()):
                    args += ["--gate-signer", f"{gate}={signer}"]
                args += ["--trust-policy", trust["trustPolicy"]["path"]]
            process = self._run_oci_cli(args)
            if process.returncode or not out.is_file():
                raise RuntimeError(
                    self.cli_failure_message("oci-package-stage", process, out)
                )
            result = json.loads(out.read_text())
            if result.get("status") != "PASS":
                raise RuntimeError(
                    f"OCI package stage did not PASS: {result.get('failures')}"
                )
            layout = package / "layout"
            roles = {
                "packageReport": "oci-package-stage.json",
                "ociLayoutIndex": "package/layout/index.json",
                "ociLayoutMarker": "package/layout/oci-layout",
            }
            for blob in sorted((layout / "blobs" / "sha256").glob("*")):
                roles[f"ociBlob:{blob.name}"] = (
                    f"package/layout/blobs/sha256/{blob.name}"
                )
            return roles, {
                "releaseReady": bool(result.get("releaseReady")),
                "trustStanding": result.get("trustStanding"),
                "packageRelativePath": "package/layout",
                "subjectDigest": result.get("oci", {})
                .get("subject", {})
                .get("digest"),
                "referrerCount": len(
                    result.get("oci", {}).get("discover", {}).get("referrers", [])
                ),
            }

        raise RuntimeError(f"unsupported Artifact operation kind: {operation_kind}")
