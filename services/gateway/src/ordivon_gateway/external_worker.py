from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class WorkerError(RuntimeError):
    pass


class WorkerAuthError(WorkerError):
    pass


class WorkerConflict(WorkerError):
    pass


@dataclass(frozen=True)
class ExternalOperation:
    operation_id: str
    capability: str
    request_id: str
    state: str
    terminal: bool
    desired_state: str
    exit_code: int | None
    artifact_ids: list[str]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


class ExternalPullWorkerTransport:
    """Durable provider-neutral pull-worker transport.

    This store is Gateway transport mechanics only. It does not establish Task ownership,
    semantic completion, priority, or domain authority.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        clock_ms: Callable[[], int] | None = None,
        lease_ms: int = 30_000,
        signature_window_ms: int = 300_000,
        stale_after_ms: int = 120_000,
    ) -> None:
        self.path = str(path)
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self.lease_ms = lease_ms
        self.signature_window_ms = signature_window_ms
        self.stale_after_ms = stale_after_ms
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    public_key_b64 TEXT NOT NULL,
                    admitted_capabilities_json TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    enrolled_at_ms INTEGER NOT NULL,
                    last_heartbeat_ms INTEGER NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS operations (
                    operation_id TEXT PRIMARY KEY,
                    capability TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    parcel_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    terminal INTEGER NOT NULL DEFAULT 0,
                    desired_state TEXT NOT NULL DEFAULT 'run',
                    active_attempt_id TEXT,
                    exit_code INTEGER,
                    result_json TEXT,
                    result_digest TEXT,
                    created_at_ms INTEGER NOT NULL,
                    updated_at_ms INTEGER NOT NULL,
                    UNIQUE(capability, request_id)
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY,
                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
                    worker_id TEXT NOT NULL REFERENCES workers(worker_id),
                    generation INTEGER NOT NULL,
                    lease_id TEXT NOT NULL UNIQUE,
                    lease_expires_ms INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
                    artifact_id TEXT NOT NULL,
                    content BLOB NOT NULL,
                    digest TEXT NOT NULL,
                    PRIMARY KEY(operation_id, artifact_id)
                );
                CREATE TABLE IF NOT EXISTS nonces (
                    worker_id TEXT NOT NULL REFERENCES workers(worker_id),
                    nonce TEXT NOT NULL,
                    timestamp_ms INTEGER NOT NULL,
                    PRIMARY KEY(worker_id, nonce)
                );
                CREATE TABLE IF NOT EXISTS events (
                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
                    attempt_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(operation_id, attempt_id, sequence)
                );
                CREATE INDEX IF NOT EXISTS idx_operations_claim
                    ON operations(terminal, desired_state, state, created_at_ms);
                CREATE INDEX IF NOT EXISTS idx_attempts_operation
                    ON attempts(operation_id, created_at_ms);
                """
            )
            worker_columns = {
                str(row["name"]) for row in db.execute("PRAGMA table_info(workers)").fetchall()
            }
            if "admitted_capabilities_json" not in worker_columns:
                db.execute("ALTER TABLE workers ADD COLUMN admitted_capabilities_json TEXT")
                db.execute(
                    "UPDATE workers SET admitted_capabilities_json=capabilities_json "
                    "WHERE admitted_capabilities_json IS NULL"
                )

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
        now = self._clock_ms()
        capabilities_json = _canonical_json(sorted(set(capabilities)))
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM workers WHERE worker_id=?", (worker_id,)
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
                    db.execute("COMMIT")
                    return
                if generation <= int(existing["generation"]):
                    db.execute("ROLLBACK")
                    raise WorkerConflict("worker generation must increase for replacement")
                db.execute(
                    """
                    UPDATE workers
                    SET provider_id=?, generation=?, public_key_b64=?,
                        admitted_capabilities_json=?, capabilities_json=?,
                        enrolled_at_ms=?, last_heartbeat_ms=?, revoked=0
                    WHERE worker_id=?
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
                    ) VALUES(?,?,?,?,?,?,?,?,0)
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
            db.execute("COMMIT")

    def revoke(self, worker_id: str) -> None:
        with self._connect() as db:
            changed = db.execute(
                "UPDATE workers SET revoked=1 WHERE worker_id=?", (worker_id,)
            ).rowcount
            if changed != 1:
                raise WorkerConflict("unknown worker")

    def _worker(self, db: sqlite3.Connection, worker_id: str, generation: int) -> sqlite3.Row:
        row = db.execute("SELECT * FROM workers WHERE worker_id=?", (worker_id,)).fetchone()
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
        now = self._clock_ms()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._worker(db, worker_id, generation)
            capabilities_json = row["capabilities_json"]
            if capabilities is not None:
                if not capabilities or any(
                    not isinstance(item, str) or not item for item in capabilities
                ):
                    db.execute("ROLLBACK")
                    raise WorkerConflict("heartbeat capabilities are invalid")
                admitted = set(json.loads(row["admitted_capabilities_json"]))
                advertised = set(capabilities)
                if not advertised.issubset(admitted):
                    db.execute("ROLLBACK")
                    raise WorkerAuthError("worker capability exceeds operator-admitted ceiling")
                capabilities_json = _canonical_json(sorted(advertised))
            db.execute(
                "UPDATE workers SET last_heartbeat_ms=?, capabilities_json=? WHERE worker_id=?",
                (now, capabilities_json, worker_id),
            )
            # A live worker heartbeat renews only leases that are still valid at the
            # serialization point. It never resurrects an already-expired attempt.
            db.execute(
                """
                UPDATE attempts
                SET lease_expires_ms=?
                WHERE worker_id=? AND generation=?
                  AND state IN ('claimed','started') AND lease_expires_ms>=?
                """,
                (now + self.lease_ms, worker_id, generation, now),
            )
            db.execute("COMMIT")

    def capability_projection(self) -> dict[str, list[str]]:
        now = self._clock_ms()
        result: dict[str, list[str]] = {}
        with self._connect() as db:
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

    def submit(
        self, *, capability: str, request_id: str, parcel: dict[str, Any]
    ) -> ExternalOperation:
        if not capability or not request_id:
            raise WorkerConflict("capability and request_id are required")
        now = self._clock_ms()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM operations WHERE capability=? AND request_id=?",
                (capability, request_id),
            ).fetchone()
            if existing is not None:
                if existing["parcel_json"] != _canonical_json(parcel):
                    db.execute("ROLLBACK")
                    raise WorkerConflict("request replay differs from admitted parcel")
                db.execute("COMMIT")
                return self._operation_from_row(db, existing)
            operation_id = "xop-" + uuid.uuid4().hex
            db.execute(
                """
                INSERT INTO operations(
                    operation_id, capability, request_id, parcel_json, state, terminal,
                    desired_state, created_at_ms, updated_at_ms
                ) VALUES(?,?,?,?, 'queued',0,'run',?,?)
                """,
                (operation_id, capability, request_id, _canonical_json(parcel), now, now),
            )
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            db.execute("COMMIT")
            assert row is not None
            return self._operation_from_row(db, row)

    def resolve(self, capability: str, request_id: str) -> ExternalOperation | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM operations WHERE capability=? AND request_id=?",
                (capability, request_id),
            ).fetchone()
            return self._operation_from_row(db, row) if row is not None else None

    def _reap_expired(self, db: sqlite3.Connection, now: int) -> None:
        expired = db.execute(
            """
            SELECT attempt_id, operation_id, state FROM attempts
            WHERE state IN ('claimed','started') AND lease_expires_ms < ?
            """,
            (now,),
        ).fetchall()
        for row in expired:
            if row["state"] == "claimed":
                # No started acknowledgement exists, so the transport may safely
                # make the parcel claimable again. Workers must acknowledge started
                # before performing external effects.
                db.execute(
                    "UPDATE attempts SET state='expired_unstarted' WHERE attempt_id=?",
                    (row["attempt_id"],),
                )
                db.execute(
                    """
                    UPDATE operations
                    SET state='queued', active_attempt_id=NULL, updated_at_ms=?
                    WHERE operation_id=? AND terminal=0 AND desired_state='run'
                      AND active_attempt_id=?
                    """,
                    (now, row["operation_id"], row["attempt_id"]),
                )
                continue

            # A started attempt may already have produced external side effects.
            # Lease loss therefore means execution truth is unknown, not that the
            # operation is safe to duplicate. Fence new attempts until the same
            # execution is reconciled or returns a terminal result.
            db.execute(
                "UPDATE attempts SET state='reconcile_required' WHERE attempt_id=?",
                (row["attempt_id"],),
            )
            db.execute(
                """
                UPDATE operations
                SET state='reconcile_required', updated_at_ms=?
                WHERE operation_id=? AND terminal=0 AND desired_state='run'
                  AND active_attempt_id=?
                """,
                (now, row["operation_id"], row["attempt_id"]),
            )

    def claim(self, worker_id: str, *, generation: int) -> dict[str, Any] | None:
        now = self._clock_ms()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            worker = self._worker(db, worker_id, generation)
            self._reap_expired(db, now)
            capabilities = json.loads(worker["capabilities_json"])
            if not capabilities:
                db.execute("COMMIT")
                return None
            placeholders = ",".join("?" for _ in capabilities)
            row = db.execute(
                f"""
                SELECT * FROM operations
                WHERE terminal=0 AND desired_state='run' AND state='queued'
                  AND capability IN ({placeholders})
                ORDER BY created_at_ms, operation_id
                LIMIT 1
                """,
                tuple(capabilities),
            ).fetchone()
            if row is None:
                db.execute("COMMIT")
                return None
            attempt_id = "xatt-" + uuid.uuid4().hex
            lease_id = "xlease-" + uuid.uuid4().hex
            expires = now + self.lease_ms
            db.execute(
                """
                INSERT INTO attempts(
                    attempt_id, operation_id, worker_id, generation, lease_id,
                    lease_expires_ms, state, created_at_ms
                ) VALUES(?,?,?,?,?,?, 'claimed',?)
                """,
                (
                    attempt_id,
                    row["operation_id"],
                    worker_id,
                    generation,
                    lease_id,
                    expires,
                    now,
                ),
            )
            db.execute(
                """
                UPDATE operations
                SET state='claimed', active_attempt_id=?, updated_at_ms=?
                WHERE operation_id=?
                """,
                (attempt_id, now, row["operation_id"]),
            )
            db.execute("COMMIT")
            return {
                "operation_id": row["operation_id"],
                "attempt_id": attempt_id,
                "lease_id": lease_id,
                "lease_expires_at_ms": expires,
                "capability": row["capability"],
                "parcel": json.loads(row["parcel_json"]),
            }

    def _active_attempt(
        self,
        db: sqlite3.Connection,
        *,
        worker_id: str,
        generation: int,
        operation_id: str,
        attempt_id: str,
        lease_id: str,
        allow_expired_started: bool = False,
    ) -> tuple[sqlite3.Row, sqlite3.Row]:
        self._worker(db, worker_id, generation)
        operation = db.execute(
            "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
        ).fetchone()
        attempt = db.execute("SELECT * FROM attempts WHERE attempt_id=?", (attempt_id,)).fetchone()
        if operation is None or attempt is None:
            raise WorkerConflict("unknown operation or attempt")
        if (
            attempt["operation_id"] != operation_id
            or attempt["worker_id"] != worker_id
            or int(attempt["generation"]) != generation
            or attempt["lease_id"] != lease_id
            or operation["active_attempt_id"] != attempt_id
        ):
            raise WorkerConflict("stale attempt cannot commit")
        if int(attempt["lease_expires_ms"]) < self._clock_ms():
            late_started_result = (
                allow_expired_started
                and attempt["state"] in {"started", "reconcile_required"}
                and operation["state"] in {"started", "reconcile_required"}
            )
            if not late_started_result:
                raise WorkerConflict("stale attempt lease expired")
        return operation, attempt

    def started(
        self,
        *,
        worker_id: str,
        generation: int,
        operation_id: str,
        attempt_id: str,
        lease_id: str,
    ) -> None:
        now = self._clock_ms()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            operation, attempt = self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            if bool(operation["terminal"]):
                db.execute("COMMIT")
                return
            if attempt["state"] not in {"claimed", "started"}:
                db.execute("ROLLBACK")
                raise WorkerConflict("attempt cannot start from current state")
            db.execute("UPDATE attempts SET state='started' WHERE attempt_id=?", (attempt_id,))
            db.execute(
                "UPDATE operations SET state='started', updated_at_ms=? WHERE operation_id=?",
                (now, operation_id),
            )
            db.execute("COMMIT")

    def complete(
        self,
        *,
        worker_id: str,
        generation: int,
        operation_id: str,
        attempt_id: str,
        lease_id: str,
        exit_code: int,
        result: dict[str, Any],
        artifacts: list[dict[str, str]],
    ) -> ExternalOperation:
        artifact_projection = [
            {
                "artifact_id": item["artifact_id"],
                "digest": "sha256:" + hashlib.sha256(item["content"].encode("utf-8")).hexdigest(),
            }
            for item in artifacts
        ]
        terminal_digest = _digest(
            {"exit_code": exit_code, "result": result, "artifacts": artifact_projection}
        )
        now = self._clock_ms()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            operation = db.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if operation is None:
                db.execute("ROLLBACK")
                raise WorkerConflict("unknown operation")
            if bool(operation["terminal"]):
                if operation["result_digest"] != terminal_digest:
                    db.execute("ROLLBACK")
                    raise WorkerConflict("terminal result differs from committed result")
                db.execute("COMMIT")
                return self._operation_from_row(db, operation)

            operation, _ = self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
                allow_expired_started=True,
            )
            for item, projection in zip(artifacts, artifact_projection, strict=True):
                db.execute(
                    """
                    INSERT INTO artifacts(operation_id, artifact_id, content, digest)
                    VALUES(?,?,?,?)
                    """,
                    (
                        operation_id,
                        item["artifact_id"],
                        item["content"].encode("utf-8"),
                        projection["digest"],
                    ),
                )
            state = "completed" if exit_code == 0 else "failed"
            db.execute(
                "UPDATE attempts SET state=? WHERE attempt_id=?",
                (state, attempt_id),
            )
            db.execute(
                """
                UPDATE operations
                SET state=?, terminal=1, exit_code=?, result_json=?, result_digest=?,
                    updated_at_ms=?
                WHERE operation_id=?
                """,
                (state, exit_code, _canonical_json(result), terminal_digest, now, operation_id),
            )
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            db.execute("COMMIT")
            assert row is not None
            return self._operation_from_row(db, row)

    def record_event(
        self,
        *,
        worker_id: str,
        generation: int,
        operation_id: str,
        attempt_id: str,
        lease_id: str,
        sequence: int,
        event: dict[str, Any],
    ) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            try:
                db.execute(
                    """
                    INSERT INTO events(operation_id, attempt_id, sequence, payload_json, created_at_ms)
                    VALUES(?,?,?,?,?)
                    """,
                    (operation_id, attempt_id, sequence, _canonical_json(event), self._clock_ms()),
                )
            except sqlite3.IntegrityError:
                existing = db.execute(
                    """
                    SELECT payload_json FROM events
                    WHERE operation_id=? AND attempt_id=? AND sequence=?
                    """,
                    (operation_id, attempt_id, sequence),
                ).fetchone()
                if existing is None or existing["payload_json"] != _canonical_json(event):
                    db.execute("ROLLBACK")
                    raise WorkerConflict("event replay differs from committed event")
            db.execute("COMMIT")

    def put_artifact(
        self,
        *,
        worker_id: str,
        generation: int,
        operation_id: str,
        attempt_id: str,
        lease_id: str,
        artifact_id: str,
        content: str,
    ) -> None:
        digest = "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            existing = db.execute(
                "SELECT digest FROM artifacts WHERE operation_id=? AND artifact_id=?",
                (operation_id, artifact_id),
            ).fetchone()
            if existing is not None:
                if existing["digest"] != digest:
                    db.execute("ROLLBACK")
                    raise WorkerConflict("artifact replay differs from committed artifact")
                db.execute("COMMIT")
                return
            db.execute(
                """
                INSERT INTO artifacts(operation_id, artifact_id, content, digest)
                VALUES(?,?,?,?)
                """,
                (operation_id, artifact_id, content.encode("utf-8"), digest),
            )
            db.execute("COMMIT")

    def cancellation_requests(self, worker_id: str, *, generation: int) -> list[str]:
        with self._connect() as db:
            self._worker(db, worker_id, generation)
            rows = db.execute(
                """
                SELECT o.operation_id
                FROM operations o JOIN attempts a ON o.active_attempt_id=a.attempt_id
                WHERE a.worker_id=? AND a.generation=? AND o.terminal=0
                  AND o.desired_state='cancel'
                ORDER BY o.operation_id
                """,
                (worker_id, generation),
            ).fetchall()
        return [str(row["operation_id"]) for row in rows]

    def cancel(self, operation_id: str) -> ExternalOperation:
        now = self._clock_ms()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise WorkerConflict("unknown operation")
            if bool(row["terminal"]):
                db.execute("COMMIT")
                return self._operation_from_row(db, row)
            if row["state"] == "queued":
                db.execute(
                    """
                    UPDATE operations
                    SET desired_state='cancel', state='cancelled', terminal=1, updated_at_ms=?
                    WHERE operation_id=?
                    """,
                    (now, operation_id),
                )
            else:
                db.execute(
                    """
                    UPDATE operations
                    SET desired_state='cancel', state='cancel_requested', updated_at_ms=?
                    WHERE operation_id=?
                    """,
                    (now, operation_id),
                )
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            db.execute("COMMIT")
            assert row is not None
            return self._operation_from_row(db, row)

    def get(self, operation_id: str) -> ExternalOperation:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is None:
                raise WorkerConflict("unknown operation")
            return self._operation_from_row(db, row)

    def read_artifact(
        self, operation_id: str, artifact_id: str, *, offset: int, max_bytes: int
    ) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT content, digest FROM artifacts
                WHERE operation_id=? AND artifact_id=?
                """,
                (operation_id, artifact_id),
            ).fetchone()
            if row is None:
                raise WorkerConflict("unknown artifact")
            content = bytes(row["content"])
        chunk = content[offset : offset + max_bytes]
        return {
            "offset": offset,
            "next_offset": offset + len(chunk),
            "eof": offset + len(chunk) >= len(content),
            "digest": row["digest"],
            "content": chunk.decode("utf-8"),
        }

    def verify_signed_request(
        self,
        *,
        method: str,
        path: str,
        body: dict[str, Any],
        headers: Mapping[str, str],
    ) -> tuple[str, int]:
        normalized = {key.lower(): value for key, value in headers.items()}
        try:
            worker_id = normalized["x-ordivon-worker"]
            generation = int(normalized["x-ordivon-generation"])
            timestamp_ms = int(normalized["x-ordivon-timestamp-ms"])
            nonce = normalized["x-ordivon-nonce"]
            signature_b64 = normalized["x-ordivon-signature"]
        except (KeyError, ValueError) as exc:
            raise WorkerAuthError("missing or invalid worker signature headers") from exc
        now = self._clock_ms()
        if abs(now - timestamp_ms) > self.signature_window_ms:
            raise WorkerAuthError("worker signature timestamp outside allowed window")
        with self._connect() as db:
            worker = self._worker(db, worker_id, generation)
            digest = _digest(body)
            canonical = "\n".join(
                [
                    worker_id,
                    str(generation),
                    str(timestamp_ms),
                    nonce,
                    method.upper(),
                    path,
                    digest,
                ]
            ).encode("utf-8")
            try:
                public = Ed25519PublicKey.from_public_bytes(
                    base64.b64decode(worker["public_key_b64"], validate=True)
                )
                public.verify(base64.b64decode(signature_b64, validate=True), canonical)
            except (InvalidSignature, ValueError) as exc:
                raise WorkerAuthError("invalid worker request signature") from exc
            try:
                db.execute(
                    "INSERT INTO nonces(worker_id, nonce, timestamp_ms) VALUES(?,?,?)",
                    (worker_id, nonce, timestamp_ms),
                )
            except sqlite3.IntegrityError as exc:
                raise WorkerAuthError("worker request replay detected") from exc
            db.execute(
                "DELETE FROM nonces WHERE timestamp_ms < ?",
                (now - self.signature_window_ms * 2,),
            )
        return worker_id, generation

    def _operation_from_row(self, db: sqlite3.Connection, row: sqlite3.Row) -> ExternalOperation:
        artifacts = [
            str(item["artifact_id"])
            for item in db.execute(
                "SELECT artifact_id FROM artifacts WHERE operation_id=? ORDER BY artifact_id",
                (row["operation_id"],),
            ).fetchall()
        ]
        return ExternalOperation(
            operation_id=str(row["operation_id"]),
            capability=str(row["capability"]),
            request_id=str(row["request_id"]),
            state=str(row["state"]),
            terminal=bool(row["terminal"]),
            desired_state=str(row["desired_state"]),
            exit_code=int(row["exit_code"]) if row["exit_code"] is not None else None,
            artifact_ids=artifacts,
        )
