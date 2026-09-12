#!/usr/bin/env python3
"""Thin OCI packaging adapter for Artifact Build & Delivery v2.

Artifact policy/verification semantics remain in artifact_delivery.py. OCI identity,
layout, manifests and subject/referrer relationships are delegated to ORAS/OCI 1.1.
This module deliberately does not implement a registry, OCI manifest serializer or a
second package-index/release-manifest format.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import artifact_delivery as artifact

DEFAULT_ORAS = Path(os.environ.get("ARTIFACT_ORAS", "/opt/ordivon/external/oras/1.3.4/bin/oras"))
DEFAULT_OPA = Path(os.environ.get("ARTIFACT_OPA", "/opt/ordivon/external/opa/1.20.2/bin/opa"))
DEFAULT_RELEASE_POLICY = Path(os.environ.get("ARTIFACT_RELEASE_POLICY", str(SCRIPT_DIR.parent / "artifact-delivery/policy/release.rego")))
RELEASE_ARTIFACT_TYPE = "application/vnd.ordivon.release.v2"
GATE_ARTIFACT_TYPE = "application/vnd.ordivon.verification.v1+json"
VERIFY_RUN_ARTIFACT_TYPE = "application/vnd.ordivon.verification-run.v1+json"
PROVENANCE_ARTIFACT_TYPE = "application/vnd.in-toto+json"
OCI_REFERENCE = "ordivon.invalid/artifact:release"

FORMAT_MEDIA_TYPES = {
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf": "application/pdf",
    ".html": "text/html",
    ".htm": "text/html",
    ".json": "application/json",
}
FORMAT_SUFFIXES = {
    "pptx": ".pptx",
    "docx": ".docx",
    "xlsx": ".xlsx",
    "html": ".html",
    "pdf": ".pdf",
    "pdf-a-4": ".pdf",
    "pdf-ua-2": ".pdf",
}


def media_type(path: Path) -> str:
    return FORMAT_MEDIA_TYPES.get(path.suffix.casefold(), "application/octet-stream")


def run_oras(args: list[str], *, cwd: Path, timeout: int = 120) -> dict[str, Any]:
    if not DEFAULT_ORAS.is_file() or not os.access(DEFAULT_ORAS, os.X_OK):
        raise RuntimeError(f"ORAS carrier is unavailable: {DEFAULT_ORAS}")
    proc = subprocess.run(
        [str(DEFAULT_ORAS), *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
        env=dict(os.environ),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ORAS command failed ({proc.returncode}): {' '.join(args)}\n"
            f"stdout={proc.stdout[-4000:]}\nstderr={proc.stderr[-4000:]}"
        )
    text = proc.stdout.strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"ORAS returned non-JSON output: {error}: {text[-4000:]}") from error
    if not isinstance(value, dict):
        raise RuntimeError("ORAS JSON output is not an object")
    return value


def evaluate_release_policy(policy_input: dict[str, Any]) -> dict[str, Any]:
    if not DEFAULT_OPA.is_file() or not os.access(DEFAULT_OPA, os.X_OK):
        raise RuntimeError(f"OPA carrier is unavailable: {DEFAULT_OPA}")
    if not DEFAULT_RELEASE_POLICY.is_file():
        raise RuntimeError(f"Artifact release policy is unavailable: {DEFAULT_RELEASE_POLICY}")
    proc = subprocess.run(
        [
            str(DEFAULT_OPA), "eval", "--format", "raw",
            "--data", str(DEFAULT_RELEASE_POLICY), "--stdin-input",
            "data.artifact.release.ready",
        ],
        input=json.dumps(policy_input, separators=(",", ":")),
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False, timeout=30, env=dict(os.environ),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"OPA release policy evaluation failed ({proc.returncode}): {proc.stderr[-4000:]}")
    raw = proc.stdout.strip()
    if raw not in {"true", "false"}:
        raise RuntimeError(f"OPA release policy returned unexpected result: {raw!r}")
    return {
        "status": "PASS",
        "ready": raw == "true",
        "query": "data.artifact.release.ready",
        "input": policy_input,
        "policy": {
            "path": str(DEFAULT_RELEASE_POLICY.resolve()),
            "sha256": artifact.sha256_file(DEFAULT_RELEASE_POLICY),
        },
        "tool": {
            "path": str(DEFAULT_OPA.resolve()),
            "sha256": artifact.sha256_file(DEFAULT_OPA),
            "version": "1.20.2",
        },
    }


def copy_exact(source: Path, destination: Path, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    before = artifact.file_fact(source)
    if expected is not None:
        if expected.get("name") != before.get("name"):
            raise RuntimeError(f"staging source name drift: {source}")
        if expected.get("size") != before.get("size"):
            raise RuntimeError(f"staging source size drift: {source}")
        if expected.get("digest", {}).get("sha256") != before.get("digest", {}).get("sha256"):
            raise RuntimeError(f"staging source digest drift: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    after = artifact.file_fact(source)
    staged = artifact.file_fact(destination)
    if before["digest"]["sha256"] != after["digest"]["sha256"] or before["size"] != after["size"]:
        raise RuntimeError(f"source changed during OCI staging: {source}")
    if staged["digest"]["sha256"] != before["digest"]["sha256"] or staged["size"] != before["size"]:
        raise RuntimeError(f"OCI staging copy mismatch: {source}")
    return staged


def parse_named(values: Iterable[str], label: str, *, paths: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{label} requires name=value")
        name, raw = value.split("=", 1)
        if not name or name in result:
            raise ValueError(f"duplicate/invalid {label} name: {name!r}")
        result[name] = Path(raw) if paths else raw
    return result


def required_companion_failures(profile: dict[str, Any], companions: list[Path]) -> list[str]:
    failures: list[str] = []
    observed = [p.suffix.casefold() for p in companions]
    for item in profile.get("companions", []):
        if not isinstance(item, dict) or item.get("required") is not True:
            continue
        fmt = str(item.get("format", ""))
        suffix = FORMAT_SUFFIXES.get(fmt)
        if suffix is not None and suffix not in observed:
            failures.append(f"required companion format absent: {fmt}")
    return failures


def execute_oci_package_stage(
    profile_path: Path,
    primary: Path,
    verify_report_path: Path,
    output_dir: Path,
    companions: Iterable[Path] = (),
    request_path: Path | None = None,
    provenance_path: Path | None = None,
    allow_local_unsigned: bool = False,
    gate_bundles: dict[str, Path] | None = None,
    trust_policy_path: Path | None = None,
    signer_ids: dict[str, str] | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    profile_result = artifact.validate_profile(profile_path)
    profile = profile_result.get("profile", {})
    if profile_result.get("status") != "PASS":
        failures.append("delivery profile did not PASS validation")
    if not primary.is_file():
        failures.append("primary artifact is absent")
    if not verify_report_path.is_file():
        failures.append("verify report is absent")
    if failures:
        return {"schemaVersion": 1, "kind": "artifact-oci-package-stage", "status": "FAIL", "failures": failures, "packageCreated": False, "releaseReady": False}

    verify_report_fact = artifact.file_fact(verify_report_path)
    verify_report = artifact.load_json(verify_report_path)
    if verify_report.get("kind") != "artifact-delivery-verify-stage":
        failures.append("verify report kind is not artifact-delivery-verify-stage")
    report_artifact = verify_report.get("artifact", {}) if isinstance(verify_report.get("artifact"), dict) else {}
    primary_fact = artifact.file_fact(primary)
    if report_artifact.get("digest", {}).get("sha256") != primary_fact["digest"]["sha256"]:
        failures.append("verify report artifact digest does not bind the primary artifact")
    if report_artifact.get("name") != primary.name:
        failures.append("verify report artifact name does not bind the primary artifact")

    receipts = verify_report.get("receipts", {}) if isinstance(verify_report.get("receipts"), dict) else {}
    raw_paths: dict[str, Path] = {}
    vsa_paths: dict[str, Path] = {}
    raw_facts: dict[str, dict[str, Any]] = {}
    vsa_facts: dict[str, dict[str, Any]] = {}
    receipt_checks: dict[str, Any] = {}
    for gate, receipt in sorted(receipts.items()):
        if not isinstance(receipt, dict):
            failures.append(f"invalid verify receipt object: {gate}")
            continue
        raw_fact = receipt.get("rawEvidence", {}) if isinstance(receipt.get("rawEvidence"), dict) else {}
        vsa_fact = receipt.get("vsa", {}) if isinstance(receipt.get("vsa"), dict) else {}
        raw_check = artifact.verify_file_fact(raw_fact)
        vsa_check = artifact.verify_file_fact(vsa_fact)
        receipt_checks[gate] = {"raw": raw_check, "vsa": vsa_check}
        if raw_check.get("status") != "PASS":
            failures.append(f"raw evidence file fact failed: {gate}")
        else:
            raw_paths[gate] = Path(raw_check["path"])
            raw_facts[gate] = raw_fact
        if vsa_check.get("status") != "PASS":
            failures.append(f"VSA file fact failed: {gate}")
        else:
            vsa_paths[gate] = Path(vsa_check["path"])
            vsa_facts[gate] = vsa_fact

    bundle_paths = gate_bundles or {}
    selected_signers = signer_ids or {}
    gate_aggregation = artifact.aggregate_vsa_gates(
        profile_path,
        primary,
        vsa_paths,
        allow_local_unsigned,
        bundle_paths,
        trust_policy_path,
        selected_signers,
    )
    if gate_aggregation.get("status") != "PASS":
        failures.append("required VSA gate aggregation did not PASS")

    companion_paths = list(companions)
    names = {primary.name}
    for companion in companion_paths:
        if not companion.is_file():
            failures.append(f"companion artifact is absent: {companion}")
            continue
        if companion.name in names:
            failures.append(f"artifact basename collision: {companion.name}")
        names.add(companion.name)
    failures.extend(required_companion_failures(profile, companion_paths))

    generated_provenance: dict[str, Any] | None = None
    provenance_source = provenance_path
    if provenance_source is not None:
        checked = artifact.verify_release_provenance(provenance_source, [primary, *companion_paths])
        if checked.get("status") != "PASS":
            failures.extend(f"release provenance: {item}" for item in checked.get("failures", []))
    elif profile.get("gates", {}).get("releaseProvenance") is True:
        if request_path is None:
            failures.append("release provenance required but neither request nor provenance was supplied")
        else:
            request_validation = artifact.validate_delivery_request(request_path)
            if request_validation.get("status") != "PASS":
                failures.append("delivery request did not PASS validation for provenance generation")
            else:
                request = request_validation["request"]
                profile_ref = request.get("profile", {})
                if profile_ref.get("id") != profile.get("id") or profile_ref.get("sha256") != artifact.sha256_file(profile_path):
                    failures.append("delivery request profile binding does not match package profile")
                else:
                    materials = [Path(request_validation["resolved"]["source"]["path"])]
                    materials.extend(Path(item["path"]) for item in request_validation["resolved"].get("materials", []))
                    generated_provenance = artifact.slsa_statement(
                        [primary, *companion_paths],
                        materials,
                        profile_path,
                        request["builder"]["id"],
                        request["builder"]["buildType"],
                    )

    if failures:
        return {
            "schemaVersion": 1,
            "kind": "artifact-oci-package-stage",
            "status": "FAIL",
            "profileId": profile.get("id"),
            "primary": primary_fact,
            "verifyReport": verify_report_fact,
            "receiptChecks": receipt_checks,
            "gateAggregation": gate_aggregation,
            "packageCreated": False,
            "releaseReady": False,
            "failures": failures,
            "boundary": "OCI package preflight failed before layout creation. Verification/authenticity failures cannot be converted into package PASS.",
        }

    if output_dir.exists() and any(output_dir.iterdir()):
        return {
            "schemaVersion": 1,
            "kind": "artifact-oci-package-stage",
            "status": "FAIL",
            "profileId": profile.get("id"),
            "packageCreated": False,
            "releaseReady": False,
            "failures": ["OCI package output directory already exists and is not empty"],
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    staging = output_dir / ".staging"
    layout = output_dir / "layout"
    staging.mkdir()

    try:
        artifact_stage = staging / "artifacts"
        primary_staged = artifact_stage / primary.name
        copy_exact(primary, primary_staged, report_artifact)
        companion_staged: list[Path] = []
        for companion in companion_paths:
            target = artifact_stage / companion.name
            copy_exact(companion, target)
            companion_staged.append(target)

        provenance_staged: Path | None = None
        if provenance_source is not None:
            provenance_staged = staging / "provenance" / "slsa-provenance.json"
            copy_exact(provenance_source, provenance_staged)
        elif generated_provenance is not None:
            provenance_staged = staging / "provenance" / "slsa-provenance.json"
            artifact.write_json(provenance_staged, generated_provenance)

        gate_staged: dict[str, dict[str, Path]] = {}
        for gate in sorted(vsa_paths):
            gd = staging / "gates" / gate
            raw_target = gd / "raw-evidence.json"
            vsa_target = gd / "verification-summary.json"
            copy_exact(raw_paths[gate], raw_target, raw_facts[gate])
            copy_exact(vsa_paths[gate], vsa_target, vsa_facts[gate])
            gate_staged[gate] = {"raw": raw_target, "vsa": vsa_target}
            if gate in bundle_paths:
                bundle_target = gd / "sigstore-bundle.json"
                expected_bundle = gate_aggregation.get("bundles", {}).get(gate)
                copy_exact(bundle_paths[gate], bundle_target, expected_bundle)
                gate_staged[gate]["bundle"] = bundle_target

        verify_staged = staging / "verify" / "verify-stage.json"
        copy_exact(verify_report_path, verify_staged, verify_report_fact)

        subject_args = [
            "push",
            OCI_REFERENCE,
            "--oci-layout-path",
            str(layout.resolve()),
            "--artifact-type",
            RELEASE_ARTIFACT_TYPE,
            "--annotation",
            f"io.ordivon.profile={profile.get('id')}",
            "--annotation",
            f"io.ordivon.profile.sha256={artifact.sha256_file(profile_path)}",
            "--annotation",
            f"io.ordivon.trust-standing={'LOCAL_UNSIGNED_DEVELOPMENT' if allow_local_unsigned else 'CRYPTOGRAPHICALLY_VERIFIED'}",
            "--format",
            "json",
        ]
        subject_args.extend([f"{primary_staged.name}:{media_type(primary_staged)}"])
        subject_args.extend(f"{p.name}:{media_type(p)}" for p in companion_staged)
        subject = run_oras(subject_args, cwd=artifact_stage)

        gate_referrers: list[dict[str, Any]] = []
        for gate, files in sorted(gate_staged.items()):
            args = [
                "attach",
                OCI_REFERENCE,
                "--oci-layout-path",
                str(layout.resolve()),
                "--artifact-type",
                GATE_ARTIFACT_TYPE,
                "--annotation",
                f"io.ordivon.gate={gate}",
                "--annotation",
                f"io.ordivon.trust-standing={'LOCAL_UNSIGNED_DEVELOPMENT' if allow_local_unsigned else 'CRYPTOGRAPHICALLY_VERIFIED'}",
                "--format",
                "json",
                "raw-evidence.json:application/json",
                "verification-summary.json:application/vnd.in-toto+json",
            ]
            if "bundle" in files:
                args.append("sigstore-bundle.json:application/vnd.dev.sigstore.bundle.v0.3+json")
            gate_referrers.append(run_oras(args, cwd=files["raw"].parent))

        verify_referrer = run_oras(
            [
                "attach",
                OCI_REFERENCE,
                "--oci-layout-path",
                str(layout.resolve()),
                "--artifact-type",
                VERIFY_RUN_ARTIFACT_TYPE,
                "--annotation",
                "io.ordivon.evidence.role=verify-stage",
                "--format",
                "json",
                "verify-stage.json:application/json",
            ],
            cwd=verify_staged.parent,
        )

        provenance_referrer: dict[str, Any] | None = None
        if provenance_staged is not None:
            provenance_referrer = run_oras(
                [
                    "attach",
                    OCI_REFERENCE,
                    "--oci-layout-path",
                    str(layout.resolve()),
                    "--artifact-type",
                    PROVENANCE_ARTIFACT_TYPE,
                    "--annotation",
                    "io.ordivon.evidence.role=slsa-provenance",
                    "--format",
                    "json",
                    "slsa-provenance.json:application/vnd.in-toto+json",
                ],
                cwd=provenance_staged.parent,
            )

        manifest = run_oras(
            ["manifest", "fetch", OCI_REFERENCE, "--oci-layout-path", str(layout.resolve())],
            cwd=staging,
        )
        discover = run_oras(
            ["discover", OCI_REFERENCE, "--oci-layout-path", str(layout.resolve()), "--format", "json"],
            cwd=staging,
        )

        layer_by_title = {
            item.get("annotations", {}).get("org.opencontainers.image.title"): item
            for item in manifest.get("layers", [])
            if isinstance(item, dict)
        }
        expected_release_files = [primary, *companion_paths]
        for source in expected_release_files:
            observed = layer_by_title.get(source.name)
            expected_digest = "sha256:" + artifact.sha256_file(source)
            if not isinstance(observed, dict) or observed.get("digest") != expected_digest or observed.get("size") != source.stat().st_size:
                raise RuntimeError(f"OCI subject layer does not exactly bind release file: {source.name}")

        expected_referrers = len(gate_staged) + 1 + (1 if provenance_referrer is not None else 0)
        refs = discover.get("referrers", []) if isinstance(discover.get("referrers"), list) else []
        if len(refs) != expected_referrers:
            raise RuntimeError(f"OCI referrer count mismatch: expected {expected_referrers}, observed {len(refs)}")

        required_assembly = sorted(set(gate_aggregation.get("assemblyGates", [])))
        satisfied_assembly: list[str] = []
        if "companionPdf" in required_assembly and any(p.suffix.casefold() == ".pdf" for p in companion_paths):
            satisfied_assembly.append("companionPdf")
        if "releaseProvenance" in required_assembly and provenance_staged is not None:
            satisfied_assembly.append("releaseProvenance")
        unresolved_assembly = sorted(set(required_assembly) - set(satisfied_assembly))
        trust_standing = "LOCAL_UNSIGNED_DEVELOPMENT" if allow_local_unsigned else "CRYPTOGRAPHICALLY_VERIFIED"
        verified_gates = sorted(
            gate for gate, component in gate_aggregation.get("components", {}).items()
            if isinstance(component, dict)
            and component.get("status") == "PASS"
            and component.get("authenticity") == "VERIFIED"
        )
        release_policy_input = {
            "package_status": "PASS",
            "local_unsigned": allow_local_unsigned,
            "trust_standing": trust_standing,
            "subject": {"digest": subject.get("digest")},
            "profile": {"id": profile.get("id"), "sha256": artifact.sha256_file(profile_path)},
            "verification": {
                "required_gates": sorted(gate_aggregation.get("requiredGates", [])),
                "passed_gates": verified_gates,
            },
            "assembly": {
                "required_gates": required_assembly,
                "satisfied_gates": sorted(satisfied_assembly),
            },
        }
        release_policy = evaluate_release_policy(release_policy_input)
        release_ready = release_policy["ready"]

        blobs = sorted((layout / "blobs" / "sha256").glob("*"))
        result = {
            "schemaVersion": 1,
            "kind": "artifact-oci-package-stage",
            "status": "PASS",
            "profileId": profile.get("id"),
            "profileSha256": artifact.sha256_file(profile_path),
            "primary": primary_fact,
            "companions": [artifact.file_fact(p) for p in companion_paths],
            "verifyReport": verify_report_fact,
            "receiptChecks": receipt_checks,
            "gateAggregation": gate_aggregation,
            "oras": {
                "path": str(DEFAULT_ORAS.resolve()),
                "sha256": artifact.sha256_file(DEFAULT_ORAS),
                "version": "1.3.4",
            },
            "oci": {
                "layoutPath": str(layout.resolve()),
                "reference": OCI_REFERENCE,
                "subject": subject,
                "manifest": manifest,
                "discover": discover,
                "gateReferrers": gate_referrers,
                "verifyRunReferrer": verify_referrer,
                "provenanceReferrer": provenance_referrer,
                "blobCount": len(blobs),
                "blobDigests": ["sha256:" + p.name for p in blobs],
            },
            "trustStanding": trust_standing,
            "unresolvedAssemblyGates": unresolved_assembly,
            "releasePolicy": release_policy,
            "releaseReady": release_ready,
            "packageCreated": True,
            "failures": [],
            "boundary": "PASS means ORAS created a standards-based OCI 1.1 layout whose release subject exactly binds the release artifact bytes and whose verification/provenance relationships are OCI referrers. Artifact validators/VSA/Sigstore produce evidence; OPA decides releaseReady from verification/trust/assembly facts; OCI identity/relationship mechanics are not reimplemented here.",
        }
        return result
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def emit(value: dict[str, Any], path: Path | None) -> None:
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path is None:
        sys.stdout.write(text)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--verify-report", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--companion", type=Path, action="append", default=[])
    parser.add_argument("--request", type=Path)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--gate-bundle", action="append", default=[], help="gateName=path/to/sigstore-bundle.json")
    parser.add_argument("--gate-signer", action="append", default=[], help="gateName=trusted-signer-id")
    parser.add_argument("--trust-policy", type=Path)
    parser.add_argument("--allow-local-unsigned", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = execute_oci_package_stage(
            args.profile,
            args.primary,
            args.verify_report,
            args.output_directory,
            args.companion,
            args.request,
            args.provenance,
            args.allow_local_unsigned,
            parse_named(args.gate_bundle, "--gate-bundle", paths=True),
            args.trust_policy,
            parse_named(args.gate_signer, "--gate-signer"),
        )
        emit(result, args.output)
        return 0 if result.get("status") == "PASS" else 1
    except Exception as error:
        print(json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
