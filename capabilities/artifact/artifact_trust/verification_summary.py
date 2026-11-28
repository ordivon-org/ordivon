"""Structural in-toto/SLSA Verification Summary encoding and verification.

A valid unsigned statement is NOT proof of authenticated source or trust.
Cryptographic Cosign/Sigstore effects remain in the sibling VSA owner module.
"""

from __future__ import annotations

import base64
import hashlib
import urllib.parse
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact, sha256_file
from artifact_core.json_validation import load_json
from artifact_trust.provenance import IN_TOTO_STATEMENT_V1, utc_now

SLSA_VERIFICATION_SUMMARY_V1 = "https://slsa.dev/verification_summary/v1"
SLSA_VERSION = "1.2"

def _require_uri(value: str, field: str) -> str:
    if not urllib.parse.urlparse(value).scheme:
        raise RuntimeError(f"{field} must be a URI")
    return value


def ni_sha256_uri(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).digest()
    value = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"ni:///sha-256;{value}"


def verification_summary_statement(
    subject: Path,
    profile_path: Path,
    verifier_id: str,
    verifier_versions: dict[str, str],
    passed: bool,
) -> dict[str, Any]:
    verifier_id = _require_uri(verifier_id, "verifier-id")
    profile_uri = profile_path.resolve().as_uri()
    subject_uri = ni_sha256_uri(subject)
    return {
        "_type": IN_TOTO_STATEMENT_V1,
        "subject": [{"name": subject.name, "digest": {"sha256": sha256_file(subject)}}],
        "predicateType": SLSA_VERIFICATION_SUMMARY_V1,
        "predicate": {
            "verifier": {"id": verifier_id, "version": dict(sorted(verifier_versions.items()))},
            "timeVerified": utc_now(),
            "resourceUri": subject_uri,
            "policy": {
                "uri": profile_uri,
                "digest": {"sha256": sha256_file(profile_path)},
            },
            "verificationResult": "PASSED" if passed else "FAILED",
            "verifiedLevels": ["SLSA_BUILD_LEVEL_UNEVALUATED" if passed else "FAILED"],
            "slsaVersion": SLSA_VERSION,
        },
    }


def verify_verification_summary(
    statement_path: Path,
    subject: Path,
    profile_path: Path,
    allowed_verifiers: Iterable[str] = (),
) -> dict[str, Any]:
    value = load_json(statement_path)
    failures: list[str] = []
    expected_subject = {subject.name: sha256_file(subject)}
    observed_subject: dict[str, str] = {}
    if value.get("_type") != IN_TOTO_STATEMENT_V1:
        failures.append("verification summary is not an in-toto Statement v1")
    if value.get("predicateType") != SLSA_VERIFICATION_SUMMARY_V1:
        failures.append("predicateType is not SLSA Verification Summary v1")
    for item in value.get("subject", []) if isinstance(value.get("subject"), list) else []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            digest = item.get("digest", {}).get("sha256") if isinstance(item.get("digest"), dict) else None
            if isinstance(digest, str):
                observed_subject[item["name"]] = digest
    if observed_subject != expected_subject:
        failures.append("verification summary subject does not exactly bind the artifact")
    predicate = value.get("predicate", {}) if isinstance(value.get("predicate"), dict) else {}
    verifier = predicate.get("verifier", {}) if isinstance(predicate.get("verifier"), dict) else {}
    verifier_id = verifier.get("id")
    if not isinstance(verifier_id, str) or not urllib.parse.urlparse(verifier_id).scheme:
        failures.append("verification summary verifier.id is absent or not a URI")
    allowed = set(allowed_verifiers)
    if allowed and verifier_id not in allowed:
        failures.append("verification summary verifier.id is not allowed for this gate")
    policy = predicate.get("policy", {}) if isinstance(predicate.get("policy"), dict) else {}
    if policy.get("uri") != profile_path.resolve().as_uri():
        failures.append("verification summary policy URI does not bind the selected delivery profile")
    if policy.get("digest", {}).get("sha256") != sha256_file(profile_path):
        failures.append("verification summary policy digest does not bind the selected delivery profile")
    if predicate.get("resourceUri") != ni_sha256_uri(subject):
        failures.append("verification summary resourceUri does not bind the artifact content via RFC 6920 ni URI")
    input_attestations = predicate.get("inputAttestations")
    if input_attestations not in (None, []):
        failures.append("local v1 verification summaries must not misuse inputAttestations for raw validator output")

    verification_result = predicate.get("verificationResult")
    if verification_result not in {"PASSED", "FAILED"}:
        failures.append("verificationResult must be PASSED or FAILED")
    levels = predicate.get("verifiedLevels")
    if not isinstance(levels, list) or not levels:
        failures.append("verifiedLevels is absent or empty")
    elif verification_result == "PASSED" and "SLSA_BUILD_LEVEL_UNEVALUATED" not in levels:
        failures.append("PASSED non-SLSA policy verification must remain BUILD_LEVEL_UNEVALUATED")
    if predicate.get("slsaVersion") != SLSA_VERSION:
        failures.append(f"unexpected slsaVersion; expected {SLSA_VERSION}")
    return {
        "status": "PASS" if not failures else "FAIL",
        "statement": file_fact(statement_path),
        "subject": file_fact(subject),
        "profile": file_fact(profile_path),
        "verifier": verifier,
        "verificationResult": verification_result,
        "inputAttestations": input_attestations,
        "authenticity": "NOT_VERIFIED",
        "failures": failures,
        "boundary": "This validates unsigned in-toto/SLSA VSA structure and exact local digest bindings. External trust still requires signature/root-of-trust verification; do not treat this result as cryptographic authenticity.",
    }
