from __future__ import annotations

import base64
import json
from hashlib import sha256
from pathlib import Path
from typing import Any

VSA_PREDICATE = "https://slsa.dev/verification_summary/v1"
DSSE_PAYLOAD_TYPE = "application/vnd.in-toto+json"


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def decode_bundle_statement(bundle_path: Path) -> tuple[dict[str, Any], bytes]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    envelope = bundle.get("dsseEnvelope")
    if not isinstance(envelope, dict):
        raise ValueError("Sigstore bundle does not contain a DSSE envelope")
    if envelope.get("payloadType") != DSSE_PAYLOAD_TYPE:
        raise ValueError("unexpected DSSE payload type")
    signatures = envelope.get("signatures")
    if not isinstance(signatures, list) or not signatures:
        raise ValueError("DSSE envelope has no signatures")
    payload_text = envelope.get("payload")
    if not isinstance(payload_text, str):
        raise ValueError("DSSE envelope payload is missing")
    try:
        payload = base64.b64decode(payload_text, validate=True)
    except Exception as exc:  # binascii.Error is an implementation detail here.
        raise ValueError("DSSE payload is not valid base64") from exc
    statement = json.loads(payload)
    if not isinstance(statement, dict):
        raise ValueError("DSSE payload is not an in-toto Statement object")
    return statement, payload


def load_trust_mapping(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != 1:
        raise ValueError("unsupported trust-policy schema")
    verifiers = payload.get("verifiers")
    if not isinstance(verifiers, dict):
        raise ValueError("trust policy must contain verifiers")
    mapping: dict[str, str] = {}
    for verifier_id, config in verifiers.items():
        if not isinstance(verifier_id, str) or not isinstance(config, dict):
            raise ValueError("invalid verifier trust entry")
        digest = config.get("publicKeySha256")
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise ValueError("verifier trust entry must bind a public-key SHA-256")
        mapping[verifier_id] = digest
    return mapping


def verify_vsa_semantics(
    *,
    statement: dict[str, Any],
    expected_subject_git_commit: str,
    expected_verifier_id: str,
    expected_level: str,
    public_key_sha256: str,
    trust_mapping: dict[str, str],
    expected_statement_bytes: bytes | None = None,
    signed_payload_bytes: bytes | None = None,
) -> None:
    if statement.get("predicateType") != VSA_PREDICATE:
        raise ValueError("unexpected VSA predicateType")
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or len(subjects) != 1:
        raise ValueError("VSA must bind exactly one subject for this verifier")
    digest = subjects[0].get("digest") if isinstance(subjects[0], dict) else None
    if not isinstance(digest, dict) or digest.get("gitCommit") != expected_subject_git_commit:
        raise ValueError("VSA subject Git commit does not match expected subject")
    predicate = statement.get("predicate")
    if not isinstance(predicate, dict):
        raise ValueError("VSA predicate is missing")
    verifier = predicate.get("verifier")
    if not isinstance(verifier, dict) or verifier.get("id") != expected_verifier_id:
        raise ValueError("VSA verifier identity does not match expected verifier")
    trusted_key = trust_mapping.get(expected_verifier_id)
    if trusted_key is None:
        raise ValueError("VSA verifier is not present in the trust policy")
    if trusted_key != public_key_sha256:
        raise ValueError("VSA verifier is not bound to this public key by the trust policy")
    if predicate.get("verificationResult") != "PASSED":
        raise ValueError("VSA verificationResult is not PASSED")
    levels = predicate.get("verifiedLevels")
    if not isinstance(levels, list) or expected_level not in levels:
        raise ValueError("VSA does not contain the required verified level")
    if expected_statement_bytes is not None:
        if signed_payload_bytes is None or signed_payload_bytes != expected_statement_bytes:
            raise ValueError("signed DSSE payload is not byte-identical to the expected Statement")
