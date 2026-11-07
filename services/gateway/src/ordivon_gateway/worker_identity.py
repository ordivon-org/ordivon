"""Worker enrollment and signed-request identity, subordinate to Gateway transport."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from typing import Any

import psycopg
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .external_worker_contracts import WorkerAuthError, WorkerConflict
from .worker_signatures import parse_signed_worker_headers, verify_worker_signature


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class WorkerIdentityMethods:
    """Enrollment, liveness and request attestation; no independent worker store."""

    def enroll(
        self,
        *,
        worker_id: str,
        provider_id: str,
        generation: int,
        public_key_b64: str,
        capabilities: list[str],
    ) -> None:
        if not worker_id or not provider_id or generation < 1:
            raise WorkerConflict("invalid worker enrollment identity")
        if not capabilities or any(not isinstance(item, str) or not item for item in capabilities):
            raise WorkerConflict("worker must advertise non-empty string capabilities")
        try:
            raw = base64.b64decode(public_key_b64, validate=True)
            Ed25519PublicKey.from_public_bytes(raw)
        except Exception as exc:
            raise WorkerConflict("invalid Ed25519 public key") from exc
        capabilities_json = _canonical_json(sorted(set(capabilities)))
        with self._connect() as db:
            now = self._clock_ms()
            existing = db.execute(
                "SELECT * FROM workers WHERE worker_id=%s", (worker_id,)
            ).fetchone()
            if existing is not None:
                same = (
                    existing["provider_id"] == provider_id
                    and int(existing["generation"]) == generation
                    and existing["public_key_b64"] == public_key_b64
                    and existing["admitted_capabilities_json"] == capabilities_json
                    and existing["capabilities_json"] == capabilities_json
                    and not bool(existing["revoked"])
                )
                if same:
                    return
                if generation <= int(existing["generation"]):
                    raise WorkerConflict("worker generation must increase for replacement")
                db.execute(
                    """
                    UPDATE workers
                    SET provider_id=%s, generation=%s, public_key_b64=%s,
                        admitted_capabilities_json=%s, capabilities_json=%s,
                        enrolled_at_ms=%s, last_heartbeat_ms=%s, revoked=0
                    WHERE worker_id=%s
                    """,
                    (
                        provider_id,
                        generation,
                        public_key_b64,
                        capabilities_json,
                        capabilities_json,
                        now,
                        now,
                        worker_id,
                    ),
                )
            else:
                db.execute(
                    """
                    INSERT INTO workers(
                        worker_id, provider_id, generation, public_key_b64,
                        admitted_capabilities_json, capabilities_json,
                        enrolled_at_ms, last_heartbeat_ms, revoked
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,0)
                    """,
                    (
                        worker_id,
                        provider_id,
                        generation,
                        public_key_b64,
                        capabilities_json,
                        capabilities_json,
                        now,
                        now,
                    ),
                )

    def revoke(self, worker_id: str) -> None:
        with self._connect() as db:
            changed = db.execute(
                "UPDATE workers SET revoked=1 WHERE worker_id=%s", (worker_id,)
            ).rowcount
            if changed != 1:
                raise WorkerConflict("unknown worker")

    def _worker(self, db: psycopg.Connection, worker_id: str, generation: int) -> dict[str, Any]:
        row = db.execute("SELECT * FROM workers WHERE worker_id=%s", (worker_id,)).fetchone()
        if row is None:
            raise WorkerAuthError("unknown worker")
        if bool(row["revoked"]):
            raise WorkerAuthError("worker is revoked")
        if int(row["generation"]) != generation:
            raise WorkerAuthError("worker generation is stale")
        return row

    def heartbeat(
        self, worker_id: str, *, generation: int, capabilities: list[str] | None = None
    ) -> None:
        with self._connect() as db:
            now = self._clock_ms()
            row = self._worker(db, worker_id, generation)
            capabilities_json = row["capabilities_json"]
            if capabilities is not None:
                if not capabilities or any(
                    not isinstance(item, str) or not item for item in capabilities
                ):
                    raise WorkerConflict("heartbeat capabilities are invalid")
                admitted = set(json.loads(row["admitted_capabilities_json"]))
                advertised = set(capabilities)
                if not advertised.issubset(admitted):
                    raise WorkerAuthError("worker capability exceeds operator-admitted ceiling")
                capabilities_json = _canonical_json(sorted(advertised))
            db.execute(
                "UPDATE workers SET last_heartbeat_ms=%s, capabilities_json=%s WHERE worker_id=%s",
                (now, capabilities_json, worker_id),
            )
            # A live worker heartbeat renews only leases that are still valid at the
            # serialization point. It never resurrects an already-expired attempt.
            db.execute(
                """
                UPDATE attempts
                SET lease_expires_ms=%s
                WHERE worker_id=%s AND generation=%s
                  AND state IN ('claimed','started') AND lease_expires_ms>=%s
                """,
                (now + self.lease_ms, worker_id, generation, now),
            )

    def capability_projection(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        with self._connect() as db:
            now = self._clock_ms()
            rows = db.execute(
                """
                SELECT worker_id, capabilities_json, last_heartbeat_ms
                FROM workers WHERE revoked=0
                """
            ).fetchall()
        for row in rows:
            if now - int(row["last_heartbeat_ms"]) > self.stale_after_ms:
                continue
            for capability in json.loads(row["capabilities_json"]):
                result.setdefault(str(capability), []).append(str(row["worker_id"]))
        return {key: sorted(set(value)) for key, value in sorted(result.items())}

    def verify_signed_request(
        self,
        *,
        method: str,
        path: str,
        body: dict[str, Any],
        headers: Mapping[str, str],
    ) -> tuple[str, int]:
        try:
            signature = parse_signed_worker_headers(headers)
        except (KeyError, ValueError) as exc:
            raise WorkerAuthError("missing or invalid worker signature headers") from exc
        with self._connect() as db:
            now = self._clock_ms()
            if abs(now - signature.timestamp_ms) > self.signature_window_ms:
                raise WorkerAuthError("worker signature timestamp outside allowed window")
            worker = self._worker(db, signature.worker_id, signature.generation)
            try:
                verify_worker_signature(
                    headers=signature,
                    method=method,
                    path=path,
                    body_digest=_digest(body),
                    public_key_b64=worker["public_key_b64"],
                )
            except (InvalidSignature, ValueError) as exc:
                raise WorkerAuthError("invalid worker request signature") from exc
            try:
                db.execute(
                    "INSERT INTO nonces(worker_id, nonce, timestamp_ms) VALUES(%s,%s,%s)",
                    (signature.worker_id, signature.nonce, signature.timestamp_ms),
                )
            except psycopg.errors.UniqueViolation as exc:
                raise WorkerAuthError("worker request replay detected") from exc
            db.execute(
                "DELETE FROM nonces WHERE timestamp_ms < %s",
                (now - self.signature_window_ms * 2,),
            )
        return signature.worker_id, signature.generation
