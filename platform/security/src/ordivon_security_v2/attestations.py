from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
REFERENCE_PREDICATE = "https://in-toto.io/attestation/reference/v0.1"
VSA_PREDICATE = "https://slsa.dev/verification_summary/v1"


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def subject_descriptor(*, name: str, git_commit: str) -> dict[str, Any]:
    if len(git_commit) not in {40, 64} or any(c not in "0123456789abcdef" for c in git_commit):
        raise ValueError("git_commit must be a lowercase hexadecimal Git object digest")
    return {"name": name, "digest": {"gitCommit": git_commit}}


def reference_statement(
    *,
    subject: dict[str, Any],
    attester_id: str,
    reference_path: Path,
) -> dict[str, Any]:
    return {
        "_type": STATEMENT_TYPE,
        "subject": [subject],
        "predicateType": REFERENCE_PREDICATE,
        "predicate": {
            "attester": {"id": attester_id},
            "references": [
                {
                    "downloadLocation": reference_path.resolve().as_uri(),
                    "digest": {"sha256": sha256_file(reference_path)},
                    "mediaType": "application/json",
                }
            ],
        },
    }


def vsa_statement(
    *,
    subject: dict[str, Any],
    verifier_id: str,
    verifier_versions: dict[str, str],
    resource_uri: str,
    policy_uri: str,
    policy_sha256: str,
    input_attestations: list[dict[str, Any]],
    passed: bool,
) -> dict[str, Any]:
    if len(policy_sha256) != 64:
        raise ValueError("policy_sha256 must be a hexadecimal SHA-256 digest")
    return {
        "_type": STATEMENT_TYPE,
        "subject": [subject],
        "predicateType": VSA_PREDICATE,
        "predicate": {
            "verifier": {"id": verifier_id, "version": verifier_versions},
            "resourceUri": resource_uri,
            "policy": {"uri": policy_uri, "digest": {"sha256": policy_sha256}},
            "inputAttestations": input_attestations,
            "verificationResult": "PASSED" if passed else "FAILED",
            "verifiedLevels": ["SECURITY_PRODUCT_POLICY" if passed else "FAILED"],
            "dependencyLevels": {},
            "slsaVersion": "1.2",
        },
    }
