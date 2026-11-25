"""Relocatable Artifact file + contract + canonical Profile + native evidence.

This is a thin consumer adapter over the existing verification service, not
an alternative Profile authority, Artifact registry, transfer or trust system.
Use as a module CLI: python -m artifact_operations.portable_bundle build|verify.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from scripts import artifact_verify


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("portable Artifact JSON must be an object")
    return value


def _entry(path: str, raw: bytes) -> dict[str, str]:
    return {"path": path, "sha256": _sha(raw)}


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()


def _safe_archive_members(archive: zipfile.ZipFile) -> set[str]:
    names: set[str] = set()
    for item in archive.infolist():
        name = item.filename
        parts = PurePosixPath(name).parts
        if (
            not name or name.startswith("/") or "\\" in name
            or not parts or any(part in {".", ".."} for part in parts)
            or item.is_dir() or stat.S_ISLNK(item.external_attr >> 16)
            or name in names
        ):
            raise ValueError(f"unsafe or duplicate portable Artifact member: {name}")
        names.add(name)
    return names


def build_bundle(request_path: Path, destination: Path) -> dict[str, Any]:
    """Reverify existing inputs; then write a self-contained *evidence* archive.

    Native verifiers and the installed Artifact Profile authority remain
    external tools. A prior PASS report cannot authorize packaging stale bytes.
    """
    request_path = Path(request_path).resolve()
    destination = Path(destination).resolve()
    request_raw = request_path.read_bytes()
    original = _json(request_raw)
    failures = artifact_verify.validate_request(original)
    if failures:
        raise ValueError(f"invalid verification request: {failures}")
    if destination.exists():
        raise FileExistsError(f"portable Artifact destination already exists: {destination}")

    with tempfile.TemporaryDirectory(prefix="artifact-portable-build-") as temp:
        scratch = Path(temp)
        fresh = dict(original)
        fresh["evidenceDirectory"] = str(scratch / "evidence")
        fresh_path = scratch / "verification-request.json"
        fresh_path.write_bytes(_json_bytes(fresh))
        observed = artifact_verify.verify_request(fresh_path)
        if observed.get("status") != "PASS" or observed.get("profileVerificationComplete") is not True:
            raise ValueError(
                f"source not fully qualified by current native verification: "
                f"{observed.get('failures', [])}"
            )

        subject_path = artifact_verify.resolve_request_path(original["subject"]["path"])
        subject_raw = subject_path.read_bytes()
        subject = _entry(f"subject/{subject_path.name}", subject_raw)
        if subject["sha256"] != original["subject"]["sha256"]:
            raise ValueError("subject changed after native verification")

        profile_ref = original["profile"]
        profile = artifact_verify.PROFILE_REGISTRY.resolve(profile_ref["id"])
        profile_raw = profile.canonical_path.read_bytes()
        if _sha(profile_raw) != profile_ref["sha256"]:
            raise ValueError("canonical Profile differs from verification request")

        payloads: dict[str, bytes] = {
            subject["path"]: subject_raw,
            "profile/profile.json": profile_raw,
            "provenance/original-request.json": request_raw,
        }
        manifest: dict[str, Any] = {
            "schemaVersion": 1,
            "kind": "artifact-portable-verification-bundle",
            "subject": subject,
            "profile": {"id": profile_ref["id"], **_entry("profile/profile.json", profile_raw)},
            "originalRequest": _entry("provenance/original-request.json", request_raw),
            "boundary": (
                "Native Profile authority and verifier tooling must be installed at the "
                "consumer. This archive is relocatable evidence, not independent "
                "provider installation, final-target delivery or domain acceptance."
            ),
        }
        if original.get("objectContract"):
            contract_path = artifact_verify.resolve_request_path(
                original["objectContract"]["path"]
            )
            contract_raw = contract_path.read_bytes()
            contract = _entry("contract/object-contract.json", contract_raw)
            if contract["sha256"] != original["objectContract"]["sha256"]:
                raise ValueError("object contract changed after native verification")
            manifest["objectContract"] = contract
            payloads[contract["path"]] = contract_raw

        evidence_root = scratch / "evidence"
        for path in sorted(evidence_root.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"native evidence includes a symlink: {path}")
            if path.is_file():
                payloads["evidence/" + path.relative_to(evidence_root).as_posix()] = (
                    path.read_bytes()
                )
        service_report = payloads.get("evidence/service-result.json")
        if service_report is None:
            raise ValueError("native verification did not produce service-result.json")
        manifest["verificationReport"] = _entry(
            "evidence/service-result.json", service_report
        )
        payloads["bundle.json"] = _json_bytes(manifest)
        _safe_archive_members_from_paths(payloads)
        with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, raw in sorted(payloads.items()):
                archive.writestr(name, raw)
    return {
        "status": "PASS", "profileVerificationComplete": True,
        "bundlePath": str(destination), "bundleSha256": _sha(destination.read_bytes()),
        "fileCount": len(payloads), "subject": subject,
        "boundary": "Fresh native verification and bundle construction only; target consumption not claimed.",
    }


def _safe_archive_members_from_paths(payloads: dict[str, bytes]) -> None:
    for name in payloads:
        parts = PurePosixPath(name).parts
        if (
            not name or name.startswith("/") or "\\" in name
            or not parts or any(part in {".", ".."} for part in parts)
        ):
            raise ValueError(f"unsafe Artifact bundle member: {name}")


def verify_bundle(bundle_path: Path) -> dict[str, Any]:
    """Independently reverify a relocated archive through current native tooling.

    Original request paths are historical evidence only. Extract exactly the
    subject and contract needed for the new consumer verification invocation.
    """
    try:
        with zipfile.ZipFile(bundle_path) as archive:
            names = _safe_archive_members(archive)
            if "bundle.json" not in names:
                raise ValueError("bundle.json is absent")
            manifest = _json(archive.read("bundle.json"))
            if (
                manifest.get("schemaVersion") != 1
                or manifest.get("kind") != "artifact-portable-verification-bundle"
            ):
                raise ValueError("portable Artifact manifest identity/version invalid")

            def checked_bytes(ref: dict[str, str]) -> bytes:
                name = ref["path"]
                if name not in names:
                    raise ValueError(f"required portable member absent: {name}")
                raw = archive.read(name)
                if _sha(raw) != ref["sha256"]:
                    raise ValueError(f"portable member changed: {name}")
                return raw

            subject_ref = manifest["subject"]
            profile_ref = manifest["profile"]
            subject_raw = checked_bytes(subject_ref)
            profile_raw = checked_bytes(profile_ref)
            original_raw = checked_bytes(manifest["originalRequest"])
            old_report = _json(checked_bytes(manifest["verificationReport"]))
            if (
                old_report.get("status") != "PASS"
                or old_report.get("profileVerificationComplete") is not True
            ):
                raise ValueError("original native verification does not claim complete PASS")
            original_request = _json(original_raw)
            if artifact_verify.validate_request(original_request):
                raise ValueError("original request shape invalid")
            # Retain the source proof's precise subject, contract and Profile
            # identity; provenance text cannot be relabeled to a different
            # bundle even when the receiving machine can verify its bytes.
            if not all(isinstance(old_report.get(key), dict) for key in ("subject", "profile")):
                raise ValueError("portable verification report identity is malformed")
            if (
                original_request["profile"]["id"] != profile_ref["id"]
                or original_request["profile"]["sha256"] != profile_ref["sha256"]
                or original_request["subject"]["sha256"] != subject_ref["sha256"]
                or old_report.get("kind") != "artifact-verification-result"
                or old_report.get("schemaVersion") != 1
                or old_report.get("requestId") != original_request["requestId"]
                or old_report.get("subject", {}).get("sha256") != subject_ref["sha256"]
                or old_report.get("subject", {}).get("size") != len(subject_raw)
                or old_report.get("profile", {}).get("id") != profile_ref["id"]
                or old_report.get("profile", {}).get("sha256") != profile_ref["sha256"]
                or old_report.get("consumer") != original_request.get("consumer")
            ):
                raise ValueError("portable bundle identity differs from original verification")
            contract_ref = manifest.get("objectContract")
            original_contract = original_request.get("objectContract")
            report_contract = old_report.get("objectContract")
            if (
                (contract_ref is None) != (original_contract is None)
                or (contract_ref is None) != (report_contract is None)
                or (report_contract is not None and not isinstance(report_contract, dict))
                or (
                    contract_ref is not None
                    and (
                        contract_ref["sha256"] != original_contract["sha256"]
                        or contract_ref["sha256"] != report_contract["sha256"]
                    )
                )
            ):
                raise ValueError("portable bundle object contract differs from provenance")

            canonical = artifact_verify.PROFILE_REGISTRY.resolve(profile_ref["id"])
            if (
                _sha(profile_raw) != canonical.canonical_sha256
                or _sha(canonical.canonical_path.read_bytes()) != _sha(profile_raw)
                or _json(profile_raw).get("id") != profile_ref["id"]
            ):
                raise ValueError("embedded Profile is not current canonical authority")

            with tempfile.TemporaryDirectory(prefix="artifact-portable-consumer-") as temp:
                scratch = Path(temp)
                subject_path = scratch / "subject" / Path(subject_ref["path"]).name
                subject_path.parent.mkdir()
                subject_path.write_bytes(subject_raw)
                request: dict[str, Any] = {
                    "schemaVersion": 1,
                    "kind": "artifact-verification-request",
                    "requestId": original_request["requestId"] + "-portable-consumer",
                    "profile": {
                        "id": profile_ref["id"],
                        "path": str(canonical.canonical_path),
                        "sha256": profile_ref["sha256"],
                    },
                    "subject": {"path": str(subject_path), "sha256": subject_ref["sha256"]},
                    "evidenceDirectory": str(scratch / "fresh-evidence"),
                }
                if "consumer" in original_request:
                    request["consumer"] = original_request["consumer"]
                if "objectContract" in manifest:
                    contract_ref = manifest["objectContract"]
                    contract_path = scratch / "contract.json"
                    contract_path.write_bytes(checked_bytes(contract_ref))
                    request["objectContract"] = {
                        "path": str(contract_path),
                        "sha256": contract_ref["sha256"],
                    }
                fresh_path = scratch / "verification-request.json"
                fresh_path.write_bytes(_json_bytes(request))
                result = artifact_verify.verify_request(fresh_path)
                return {
                    "status": result.get("status", "FAIL"),
                    "profileVerificationComplete": result.get(
                        "profileVerificationComplete", False
                    ),
                    "consumer": result.get("consumer"),
                    "subject": subject_ref,
                    "requiredEvidenceAssessment": result.get("requiredEvidenceAssessment"),
                    "failures": result.get("failures", []),
                    "boundary": (
                        "Verified this relocated archive against locally installed "
                        "canonical Profile and current native verifier; not remote "
                        "delivery or target-domain acceptance."
                    ),
                }
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        return {
            "status": "FAIL", "profileVerificationComplete": False,
            "failures": [str(error)],
            "boundary": "Portable archive admission failed; no native or target PASS claimed.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("build", help="Reverify source and create portable archive")
    build.add_argument("request", type=Path)
    build.add_argument("--output", type=Path, required=True)
    verify = sub.add_parser("verify", help="Reverify archive in current environment")
    verify.add_argument("bundle", type=Path)
    args = parser.parse_args()
    if args.action == "build":
        try:
            outcome = build_bundle(args.request, args.output)
        except (ValueError, OSError) as error:
            outcome = {"status": "FAIL", "failures": [str(error)]}
    else:
        outcome = verify_bundle(args.bundle)
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return 0 if outcome["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
