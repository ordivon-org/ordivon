from __future__ import annotations

import base64
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_core.json_validation import load_json
from artifact_trust.trust_policy import SIGSTORE_BUNDLE_V03

INTOTO_DSSE_PAYLOAD_TYPE = "application/vnd.in-toto+json"


def verify_sigstore_vsa_bundle_shape(
    bundle_path: Path,
    statement_path: Path,
    accepted_media_types: Iterable[str],
    signer_mode: str,
) -> dict[str, Any]:
    failures: list[str] = []
    bundle = load_json(bundle_path)
    statement = load_json(statement_path)
    accepted = set(accepted_media_types)
    media_type = bundle.get("mediaType") if isinstance(bundle, dict) else None
    if media_type != SIGSTORE_BUNDLE_V03 or media_type not in accepted:
        failures.append(
            "bundle is not an explicitly accepted standardized Sigstore v0.3 JSON bundle"
        )
    envelope = bundle.get("dsseEnvelope") if isinstance(bundle, dict) else None
    signed_statement: Any = None
    if not isinstance(envelope, dict):
        failures.append("Sigstore bundle does not contain a DSSE envelope")
    else:
        if envelope.get("payloadType") != INTOTO_DSSE_PAYLOAD_TYPE:
            failures.append("DSSE payloadType is not application/vnd.in-toto+json")
        signatures = envelope.get("signatures")
        if not isinstance(signatures, list) or not signatures:
            failures.append("DSSE envelope contains no signature")
        payload = envelope.get("payload")
        if not isinstance(payload, str):
            failures.append("DSSE envelope payload is absent")
        else:
            try:
                decoded = base64.b64decode(payload, validate=True)
                signed_statement = json.loads(decoded)
            except Exception as error:
                failures.append(f"DSSE payload is not valid base64 JSON: {error}")
    if signed_statement is not None and signed_statement != statement:
        failures.append(
            "detached VSA statement does not exactly match the JSON object authenticated by the DSSE bundle"
        )
    verification_material = bundle.get("verificationMaterial") if isinstance(bundle, dict) else None
    tlog_entries: list[Any] = []
    if not isinstance(verification_material, dict):
        failures.append("Sigstore bundle verificationMaterial is absent")
    else:
        raw_entries = verification_material.get("tlogEntries")
        if isinstance(raw_entries, list):
            tlog_entries = raw_entries
        if signer_mode == "public-key" and not isinstance(
            verification_material.get("publicKey"), dict
        ):
            failures.append(
                "public-key signer requires standardized bundle publicKey verification material"
            )
        if signer_mode == "keyless":
            if not isinstance(verification_material.get("certificate"), dict):
                failures.append(
                    "keyless signer requires standardized bundle leaf certificate verification material"
                )
            if isinstance(verification_material.get("publicKey"), dict):
                failures.append(
                    "keyless signer bundle must not substitute raw publicKey verification material"
                )
    return {
        "status": "PASS" if not failures else "FAIL",
        "bundle": file_fact(bundle_path),
        "mediaType": media_type,
        "payloadType": envelope.get("payloadType") if isinstance(envelope, dict) else None,
        "signatureCount": len(envelope.get("signatures", []))
        if isinstance(envelope, dict) and isinstance(envelope.get("signatures"), list)
        else 0,
        "tlogEntryCount": len(tlog_entries),
        "signedStatementMatches": signed_statement == statement
        if signed_statement is not None
        else False,
        "failures": failures,
    }
