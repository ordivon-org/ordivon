"""Qualify an observed native receipt against an independently selected plan.

This is a consumer of local retained bytes, not a Runtime witness, signer,
scheduler or semantic verifier.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .agent_processing import required_source_paths
from .assets import UnstableBlobError, hash_file
from .processing_plan_identity import canonical_relative_path, is_digest, validate_selected_closure
from .strict_json import decode_object

_PREFIX = "ordivon.media.v2."
# Fixed carrier identities from the four existing native adapters.
_CONTRACTS = {
    "av": ("external-qc-evidence", "artifact", "technicalQc", "profile-assertions", {
        "rawProbeDigest": "raw/ffprobe.json",
    }),
    "audio": ("external-audio-qc-evidence", "artifact", "technicalQc", "audio-profile-assertions", {
        "rawProbeDigest": "raw/ffprobe.json",
        "rawLoudnormStderrDigest": "raw/ffmpeg-loudnorm.stderr",
        "rawLoudnormJsonDigest": "raw/ffmpeg-loudnorm.json",
    }),
    "otio": ("external-otio-evidence", "input", "editorialGate", "otio-assertions", {
        "inspectionDigest": "raw/otio-inspection.json",
    }),
    "timed-text": ("external-timed-text-evidence", "input", "mechanicalDelivery", "timed-text-assertions", {
        "normalizedVttDigest": "raw/normalized.vtt",
        "packetEvidenceDigest": "raw/ffprobe-subtitle-packets.json",
    }),
}


def _bytes_digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"invalid {field} object")
    return value


def _path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("expected nonempty selected path")
    return (root / value).resolve()


def _carrier(directory: Path, relative: str) -> Path:
    path = directory / relative
    if path.resolve() != path:
        raise ValueError(f"noncanonical evidence carrier: {relative}")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _bound_object(path: Path, expected: object) -> dict[str, Any]:
    raw = path.read_bytes()
    if not is_digest(expected) or _bytes_digest(raw) != expected:
        raise ValueError(f"selected evidence digest mismatch: {path.name}")
    return decode_object(raw)


def qualify_processing_receipt(
    root: Path, *, plan: dict[str, Any], exit_code: int | None, expected_receipt_digest: str,
) -> dict[str, Any]:
    """Check retained evidence against the exact caller-observed receipt identity.

    Caller supplies its independently selected plan and observed exit/digest.
    Missing observation remains UNKNOWN. A coherent native negative is not a
    successful mechanical gate. Raw observations are hashed, not re-executed.
    """
    result: dict[str, Any] = {
        "schemaVersion": 1, "kind": "ordivon.studio-processing-receipt-qualification",
        "standing": "UNKNOWN", "mechanicalOk": None, "verifiedFiles": [],
        "scope": "caller-selected-plan-and-local-retained-bytes",
        "runtimeWitness": "not-verified", "semanticQuality": "not-evaluated",
        "publicationStanding": "not-evaluated",
    }
    if exit_code is None:
        result["reason"] = "exit-unobserved"
        return result
    if type(exit_code) is not int:
        raise ValueError("exit code must be an observed integer")
    if exit_code not in (0, 2):
        result["reason"] = "native-exit-outside-receipt-contract"
        return result
    if not is_digest(expected_receipt_digest):
        raise ValueError("expected receipt digest must be SHA-256")
    if type(plan.get("schemaVersion")) is not int or plan["schemaVersion"] != 1 or (
        plan.get("kind") != "ordivon.studio-native-processing-probe-plan"
    ):
        raise ValueError("unsupported processing plan")
    execution = _object(plan.get("execution"), "execution")
    binding = _object(plan.get("inputByteBinding"), "input binding")
    closure = _object(plan.get("sourceClosureBinding"), "source closure")
    args = execution.get("args")
    if (
        execution.get("executionTarget") != "local_linux"
        or execution.get("executable") != "/usr/bin/bash"
        or execution.get("cwdRelative") != "capabilities/media"
        or not isinstance(args, list) or len(args) != 4
        or closure.get("status") != "caller-selected"
        or not is_digest(closure.get("digest"))
        or not is_digest(binding.get("expectedDigest"))
        or not is_digest(plan.get("profileDigest"))
    ):
        raise ValueError("fully selected local processing plan required")
    kind = next((key for key in _CONTRACTS if args[0] == f"processing/bin/probe-{key}.sh"), None)
    if kind is None:
        raise ValueError("unsupported selected native adapter")
    selected_profile = canonical_relative_path(args[2])
    if not selected_profile.startswith("processing/profiles/"):
        raise ValueError("invalid selected profile location")
    validate_selected_closure(
        root, plan, profile_path=selected_profile, adapter_path=args[0],
        required_paths=required_source_paths(_PREFIX + kind + "-profile"),
    )
    receipt_kind, input_key, gate_key, assertions_kind, raw_files = _CONTRACTS[kind]
    input_path = _path(root, args[1])
    profile_path = _path(root, args[2])
    directory = _path(root, args[3])
    if args[1] != binding.get("inputPath") or str(input_path) != args[1] or (
        _path(root, plan.get("expectedReceipt")) != directory / "evidence.json"
    ):
        raise ValueError("selected plan path mismatch")
    try:
        receipt = _bound_object(_carrier(directory, "evidence.json"), expected_receipt_digest)
        if type(receipt.get("schemaVersion")) is not int or receipt["schemaVersion"] != 1 or (
            receipt.get("kind") != _PREFIX + receipt_kind
            or receipt.get("evidenceDirectory") != str(directory)
        ):
            raise ValueError("receipt envelope or attempt directory mismatch")
        observed = _object(receipt.get(input_key), "observed input")
        profile = _object(receipt.get("profile"), "profile")
        if (observed.get("path") != str(input_path) or observed.get("digest") != binding["expectedDigest"]
                or type(observed.get("sizeBytes")) is not int or observed["sizeBytes"] < 0):
            raise ValueError("selected input identity mismatch")
        if (profile.get("path") != str(profile_path) or profile.get("digest") != plan["profileDigest"]
                or profile.get("snapshotPath") != "profile.json"):
            raise ValueError("selected profile identity mismatch")
        profile_snapshot = _bound_object(_carrier(directory, "profile.json"), plan["profileDigest"])
        if (type(profile_snapshot.get("schemaVersion")) is not int or profile_snapshot["schemaVersion"] != 1
                or profile_snapshot.get("id") != plan.get("profileId")
                or profile_snapshot.get("kind") != _PREFIX + kind + "-profile"):
            raise ValueError("profile snapshot identity mismatch")
        evidence = _object(receipt.get("evidence"), "evidence")
        if kind == "otio" and evidence.get("inspectionPath") != raw_files["inspectionDigest"]:
            raise ValueError("OTIO inspection carrier mismatch")
        assertions = _bound_object(_carrier(directory, "assertions.json"), evidence.get("assertionsDigest"))
        checks = assertions.get("checks")
        verdict = _object(receipt.get(gate_key), "mechanical gate").get("ok")
        if (type(assertions.get("schemaVersion")) is not int or assertions["schemaVersion"] != 1
                or assertions.get("kind") != _PREFIX + assertions_kind
                or assertions.get("profileId") != plan.get("profileId")
                or not isinstance(checks, list) or not checks
                or any(not isinstance(check, dict) or type(check.get("ok")) is not bool for check in checks)
                or type(assertions.get("ok")) is not bool or type(verdict) is not bool
                or verdict != assertions["ok"] or verdict != all(check["ok"] for check in checks)
                or verdict != (exit_code == 0)):
            raise ValueError("assertion, native verdict or exit mismatch")
        verified = [
            {"path": "evidence.json", "digest": expected_receipt_digest},
            {"path": "profile.json", "digest": plan["profileDigest"]},
            {"path": "assertions.json", "digest": evidence["assertionsDigest"]},
        ]
        for field, relative in raw_files.items():
            actual = hash_file(_carrier(directory, relative)).digest
            if not is_digest(evidence.get(field)) or actual != evidence[field]:
                raise ValueError(f"raw evidence digest mismatch: {relative}")
            verified.append({"path": relative, "digest": actual})
        result.update(standing="QUALIFIED", mechanicalOk=verdict, verifiedFiles=verified)
    except (FileNotFoundError, UnstableBlobError) as exc:
        result["reason"] = f"evidence-unobserved: {exc}"
    return result
