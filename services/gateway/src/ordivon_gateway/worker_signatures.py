"""Pure worker signature wire-format parsing and Ed25519 verification.

The caller owns worker admission, generation, clock policy, nonce uniqueness,
and the storage transaction. This module never opens or writes a database.
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


@dataclass(frozen=True)
class SignedWorkerHeaders:
    worker_id: str
    generation: int
    timestamp_ms: int
    nonce: str
    signature_b64: str


def parse_signed_worker_headers(headers: Mapping[str, str]) -> SignedWorkerHeaders:
    normalized = {key.lower(): value for key, value in headers.items()}
    return SignedWorkerHeaders(
        worker_id=normalized["x-ordivon-worker"],
        generation=int(normalized["x-ordivon-generation"]),
        timestamp_ms=int(normalized["x-ordivon-timestamp-ms"]),
        nonce=normalized["x-ordivon-nonce"],
        signature_b64=normalized["x-ordivon-signature"],
    )


def verify_worker_signature(
    *,
    headers: SignedWorkerHeaders,
    method: str,
    path: str,
    body_digest: str,
    public_key_b64: str,
) -> None:
    canonical = "\n".join(
        [
            headers.worker_id,
            str(headers.generation),
            str(headers.timestamp_ms),
            headers.nonce,
            method.upper(),
            path,
            body_digest,
        ]
    ).encode("utf-8")
    public = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64, validate=True))
    public.verify(base64.b64decode(headers.signature_b64, validate=True), canonical)
