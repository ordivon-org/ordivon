#!/usr/bin/env python3
"""Thin verification-service adapter for already-existing Artifact bytes.

R1 intentionally does not define artifact content semantics, transport, workflow, or
publication state. It validates an exact request envelope, exact byte/profile/contract
bindings, requires an already LOCAL_LIVE_PROVEN capability binding, and delegates the
actual claim to the existing family-specific verifier.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from artifact_core.bindings import CapabilityBindingRegistry
from artifact_core.contracts import FileCommitment
from artifact_core.input_snapshot import stage_verified_input
from artifact_core.json_validation import load_json
from artifact_core.profiles import ProfileRegistry
from artifact_verification.claim_coverage import assess_required_evidence
from artifact_verification.native_identity import assess_native_identity

ART = ROOT / "artifact-delivery"
REQUEST_SCHEMA = ART / "verification/request-v1.schema.json"
PROFILE_ROOT = ART / "shadow-v2/examples"
PROFILE_REGISTRY = ProfileRegistry(ART)
BINDING_REGISTRY = CapabilityBindingRegistry(ART)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def request_fail(request_id: str | None, failures: list[str], *, request_digest: str | None = None) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "artifact-verification-result",
        "requestId": request_id,
        "requestDigest": request_digest,
        "status": "FAIL",
        "failures": failures,
        "boundary": "Request admission failure; no family-specific Artifact verification PASS is claimed."
    }


def validate_request(value: Any) -> list[str]:
    schema = load_json(REQUEST_SCHEMA)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [e.message for e in sorted(validator.iter_errors(value), key=lambda e: list(e.path))]


def resolve_request_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def load_function(relative: str, name: str) -> tuple[Callable[..., dict[str, Any]], str]:
    """Execute exactly the entrypoint source bytes identified in the receipt.

    This is only entrypoint-source identity, not an import closure, interpreter
    attestation, or a digest of external FFmpeg/Office/native tools.
    """
    candidate = Path(relative)
    if (
        candidate.is_absolute()
        or not candidate.parts
        or candidate.parts[0] != "scripts"
        or ".." in candidate.parts
        or candidate.suffix != ".py"
    ):
        raise ValueError(f"invalid Artifact verifier entrypoint path: {relative}")
    scripts_root = (ROOT / "scripts").resolve(strict=True)
    path = (ROOT / candidate).resolve(strict=True)
    if scripts_root not in path.parents or not path.is_file():
        raise ValueError(f"Artifact verifier entrypoint escapes scripts authority: {relative}")

    # Importlib's ordinary source loader may re-open the file or load a pyc.
    # Compile and execute the *same captured bytes* used for the SHA-256 fact.
    # If the source path changes during module execution, the returned digest
    # still identifies what was compiled, not what later occupied that path.
    source = path.read_bytes()
    source_sha256 = hashlib.sha256(source).hexdigest()
    spec = importlib.util.spec_from_file_location("artifact_verify_delegate_" + path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load verifier module: {relative}")
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, str(path), "exec", dont_inherit=True), module.__dict__)
    fn = getattr(module, name, None)
    if not callable(fn):
        raise RuntimeError(f"verifier function missing: {relative}:{name}")
    return fn, source_sha256


def verify_request(request_path: Path) -> dict[str, Any]:
    try:
        request = load_json(request_path)
    except Exception as error:
        return request_fail(None, [f"request JSON unreadable: {error}"])
    request_id = request.get("requestId") if isinstance(request, dict) else None
    failures = validate_request(request)
    request_digest = canonical_sha256(request) if isinstance(request, dict) else None
    if failures:
        return request_fail(request_id, [f"request schema invalid: {x}" for x in failures], request_digest=request_digest)

    profile_ref = request["profile"]
    profile_id = profile_ref["id"]
    try:
        binding = BINDING_REGISTRY.resolve(profile_id, "verify")
    except KeyError:
        return request_fail(request_id, [f"profile is not on the Artifact verification R1 service surface: {profile_id}"], request_digest=request_digest)
    except (RuntimeError, ValueError, OSError) as error:
        return request_fail(request_id, [f"profile capability binding unavailable: {error}"], request_digest=request_digest)

    try:
        profile_record = PROFILE_REGISTRY.resolve(profile_id)
    except (KeyError, RuntimeError, ValueError, OSError) as error:
        return request_fail(request_id, [f"registered profile unavailable: {error}"], request_digest=request_digest)

    with tempfile.TemporaryDirectory(prefix="artifact-verify-input-") as temporary:
        scratch = Path(temporary)
        profile_path = resolve_request_path(profile_ref["path"])
        expected_profile_root = PROFILE_ROOT.resolve()
        if expected_profile_root not in profile_path.parents:
            return request_fail(request_id, ["profile path is outside the normalized Artifact profile authority"], request_digest=request_digest)
        if not profile_path.is_file():
            return request_fail(request_id, ["profile file is unavailable"], request_digest=request_digest)
        try:
            profile_input = stage_verified_input(
                profile_path, profile_ref["sha256"], scratch, role="profile"
            )
        except (OSError, ValueError) as error:
            return request_fail(request_id, [str(error)], request_digest=request_digest)
        # A request commitment alone is not Profile authority: the Registry
        # may have indexed different bytes before this invocation staged them.
        # Compare the bytes we will actually evaluate with the immutable
        # canonical authority digest captured at Registry indexing.
        if profile_input.sha256 != profile_record.canonical_sha256:
            return request_fail(
                request_id,
                ["profile bytes differ from indexed canonical Profile authority"],
                request_digest=request_digest,
            )
        profile = load_json(profile_input.path)
        if profile.get("profileVersion") != 2 or profile.get("id") != profile_id:
            return request_fail(request_id, ["profile identity/version differs from request"], request_digest=request_digest)
        if profile_path != profile_record.canonical_path:
            return request_fail(request_id, ["profile path does not match the registered canonical profile"], request_digest=request_digest)

        subject_path = resolve_request_path(request["subject"]["path"])
        if not subject_path.is_file():
            return request_fail(request_id, ["subject is not a regular file"], request_digest=request_digest)
        # Snapshot qualification and claim-level completeness are distinct.
        # Parquet is a self-contained file despite lacking qualified v2 claim
        # results; sidecar-bearing formats remain on legacy path admission.
        pinned = binding.require_claim_results or binding.snapshot_inputs
        if pinned:
            try:
                subject_input = stage_verified_input(
                    subject_path, request["subject"]["sha256"], scratch, role="subject"
                )
            except (OSError, ValueError) as error:
                return request_fail(request_id, [str(error)], request_digest=request_digest)
            subject_sha = subject_input.sha256
            subject_size = subject_input.size
            delegated_subject = subject_input.path
        else:
            subject_fact = FileCommitment.from_path(subject_path)
            subject_sha = subject_fact.sha256
            subject_size = subject_fact.size
            delegated_subject = subject_path
            if subject_sha != request["subject"]["sha256"]:
                return request_fail(request_id, ["subject bytes differ from request digest"], request_digest=request_digest)

        contract_path: Path | None = None
        contract_fact: dict[str, Any] | None = None
        if request.get("objectContract"):
            contract_path = resolve_request_path(request["objectContract"]["path"])
            if not contract_path.is_file():
                return request_fail(request_id, ["object contract is not a regular file"], request_digest=request_digest)
            if pinned:
                try:
                    contract_input = stage_verified_input(
                        contract_path, request["objectContract"]["sha256"],
                        scratch, role="contract"
                    )
                except (OSError, ValueError) as error:
                    label = str(error).replace("contract bytes", "object contract bytes")
                    return request_fail(request_id, [label], request_digest=request_digest)
                contract_sha = contract_input.sha256
                delegated_contract = contract_input.path
            else:
                contract_sha = FileCommitment.from_path(contract_path).sha256
                delegated_contract = contract_path
                if contract_sha != request["objectContract"]["sha256"]:
                    return request_fail(request_id, ["object contract bytes differ from request digest"], request_digest=request_digest)
            contract_fact = {"path": str(contract_path), "sha256": contract_sha}
        elif binding.object_contract_required:
            return request_fail(request_id, [f"profile requires an object contract: {profile_id}"], request_digest=request_digest)

        evidence_dir = resolve_request_path(request["evidenceDirectory"])
        evidence_dir.mkdir(parents=True, exist_ok=True)
        verifier_relative = binding.entrypoint.module
        verifier_name = binding.entrypoint.callable
        try:
            verifier, verifier_sha = load_function(verifier_relative, verifier_name)
            if binding.object_contract_required:
                assert contract_path is not None
                delegated = verifier(delegated_subject, delegated_contract, evidence_dir)
            else:
                delegated = verifier(delegated_subject, evidence_dir)
        except Exception as error:
            return request_fail(
                request_id,
                [f"native verifier execution failed: {type(error).__name__}: {error}"],
                request_digest=request_digest,
            )
        if not isinstance(delegated, dict):
            return request_fail(
                request_id,
                ["native verifier did not return an evidence object"],
                request_digest=request_digest,
            )

        delegated_status = delegated.get("status")
        assessment = assess_required_evidence(profile, delegated)
        claim_failure = binding.require_claim_results and not assessment["complete"]
        native_identity = assess_native_identity(
            delegated,
            profile_id=profile_id,
            subject_sha256=subject_sha,
            subject_size=subject_size,
            contract_sha256=contract_fact["sha256"] if contract_fact else None,
            require_complete=binding.require_claim_results,
        )
        verified = (
            delegated_status == "PASS"
            and not claim_failure
            and not native_identity["rejected"]
        )
        service_failures = list(delegated.get("failures") or [])
        if native_identity["rejected"]:
            service_failures.extend(native_identity["mismatches"])
            service_failures.extend(
                f"native evidence identity not evaluated: {field}"
                for field in native_identity["notEvaluated"]
            )
        if claim_failure:
            service_failures.append(
                "profile requiredEvidence is not fully verified by explicit native claimResults"
            )
            service_failures.extend(assessment["issues"])
        result = {
            "schemaVersion": 1,
            "kind": "artifact-verification-result",
            "requestId": request_id,
            "requestDigest": request_digest,
            "status": "PASS" if verified else "FAIL",
            "profile": {"id": profile_id, "path": str(profile_path), "sha256": profile_ref["sha256"], "standing": "SHADOW_PROFILE_LIVE_VERIFIER"},
            "subject": {"path": str(subject_path), "sha256": subject_sha, "size": subject_size},
            "objectContract": contract_fact,
            "capabilityBinding": {"path": str(binding.standing_path), "sha256": binding.standing_sha256, "standing": binding.standing},
            "verifier": {
                "path": verifier_relative,
                "sha256": verifier_sha,
                "function": verifier_name,
                "capabilityId": binding.capability_id,
                "sourceIdentityScope": "EXECUTED_ENTRYPOINT_SOURCE_BYTES",
                "dependencyClosure": "NOT_ATTESTED",
            },
            "consumer": request.get("consumer"),
            "verification": delegated,
            "inputIdentity": {
                "profile": "EXACT_BYTES_SNAPSHOT",
                "subject": "EXACT_BYTES_SNAPSHOT" if pinned else "ADMISSION_DIGEST_ONLY",
                "objectContract": (
                    "EXACT_BYTES_SNAPSHOT" if pinned else "ADMISSION_DIGEST_ONLY"
                ) if contract_path is not None else "NOT_APPLICABLE",
                "snapshotLifetime": "this verification invocation only",
                "sourcePathContinuity": "NOT_CLAIMED",
            },
            "requiredEvidenceAssessment": assessment,
            "nativeIdentityAssessment": native_identity,
            "profileVerificationComplete": bool(
                assessment["complete"] and native_identity["complete"] and verified
            ),
            "failures": service_failures,
            "boundary": (
                "For requireClaimResults bindings, service PASS requires every required "
                "Profile claim to be independently present, PASS, and linked to a "
                "matching native-status evidence node. Other bindings retain legacy "
                "native-verifier PASS without claiming complete Profile evidence. "
                "For explicitly snapshot-qualified self-contained bindings, "
                "native tools verify private input bytes bound to the request; "
                "the original source path can change after admission. Legacy "
                "formats retain admission-time identity only. Native reports "
                "with contradictory Profile/subject/contract identity are "
                "never promoted; missing fields are NOT_EVALUATED on legacy "
                "bindings. The verifier source digest binds exactly the executed "
                "entrypoint source bytes, not imported modules, interpreter, "
                "native tools, or complete execution environment. "
                "No service result establishes consuming-application "
                "acceptance, publication, "
                "deployment, or Profile-v2 production promotion."
            ),
        }
        (evidence_dir / "service-result.json").write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("request", type=Path)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    result = verify_request(args.request.resolve())
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
