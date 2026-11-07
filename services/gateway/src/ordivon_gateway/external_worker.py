from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from .external_worker_contracts import (
    ExternalOperation,
    WorkerConflict,
)
from .external_worker_contracts import (
    WorkerAuthError as WorkerAuthError,
)
from .external_worker_contracts import (
    WorkerError as WorkerError,
)
from .worker_identity import WorkerIdentityMethods, _canonical_json, _digest
from .worker_receipts import WorkerReceiptMethods


class ExternalPullWorkerTransport(WorkerIdentityMethods, WorkerReceiptMethods):
    """Durable provider-neutral pull-worker transport.

    This store is Gateway transport mechanics only. It does not establish Task ownership,
    semantic completion, priority, or domain authority.
    """

    def __init__(
        self,
        dsn: str,
        *,
        clock_ms: Callable[[], int] | None = None,
        lease_ms: int = 30_000,
        signature_window_ms: int = 300_000,
        stale_after_ms: int = 120_000,
    ) -> None:
        # libpq accepts an empty DSN and defaults to a local server: forbid that.
        try:
            options = conninfo_to_dict(dsn) if isinstance(dsn, str) and dsn.strip() else {}
        except psycopg.ProgrammingError:
            options = {}
        if not options.get("dbname") or not options.get("host"):
            raise ValueError(
                "external worker requires an explicit PostgreSQL DSN with host and dbname"
            )
        self.dsn = dsn
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self.lease_ms = lease_ms
        self.signature_window_ms = signature_window_ms
        self.stale_after_ms = stale_after_ms
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[psycopg.Connection]:
        # Preserve the transport's single-writer CAS boundary across processes.
        # All identity, lease and receipt reads/writes share this transaction lock.
        with psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=10) as db:
            db.execute("SELECT pg_advisory_xact_lock(71403928561002)")
            db.execute("SET LOCAL search_path TO gateway_external_worker_epoch1, pg_catalog")
            yield db

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE SCHEMA IF NOT EXISTS gateway_external_worker_epoch1;
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    generation BIGINT NOT NULL,
                    public_key_b64 TEXT NOT NULL,
                    admitted_capabilities_json TEXT NOT NULL,
                    capabilities_json TEXT NOT NULL,
                    enrolled_at_ms BIGINT NOT NULL,
                    last_heartbeat_ms BIGINT NOT NULL,
                    revoked BIGINT NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS operations (
                    operation_id TEXT PRIMARY KEY,
                    capability TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    parcel_json TEXT NOT NULL,
                    state TEXT NOT NULL,
                    terminal BIGINT NOT NULL DEFAULT 0,
                    desired_state TEXT NOT NULL DEFAULT 'run',
                    active_attempt_id TEXT,
                    exit_code BIGINT,
                    result_json TEXT,
                    result_digest TEXT,
                    created_at_ms BIGINT NOT NULL,
                    updated_at_ms BIGINT NOT NULL,
                    UNIQUE(capability, request_id)
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY,
                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
                    worker_id TEXT NOT NULL REFERENCES workers(worker_id),
                    generation BIGINT NOT NULL,
                    lease_id TEXT NOT NULL UNIQUE,
                    lease_expires_ms BIGINT NOT NULL,
                    state TEXT NOT NULL,
                    created_at_ms BIGINT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
                    artifact_id TEXT NOT NULL,
                    content BYTEA NOT NULL,
                    digest TEXT NOT NULL,
                    PRIMARY KEY(operation_id, artifact_id)
                );
                CREATE TABLE IF NOT EXISTS nonces (
                    worker_id TEXT NOT NULL REFERENCES workers(worker_id),
                    nonce TEXT NOT NULL,
                    timestamp_ms BIGINT NOT NULL,
                    PRIMARY KEY(worker_id, nonce)
                );
                CREATE TABLE IF NOT EXISTS events (
                    operation_id TEXT NOT NULL REFERENCES operations(operation_id),
                    attempt_id TEXT NOT NULL,
                    sequence BIGINT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at_ms BIGINT NOT NULL,
                    PRIMARY KEY(operation_id, attempt_id, sequence)
                );
                CREATE INDEX IF NOT EXISTS idx_operations_claim
                    ON operations(terminal, desired_state, state, created_at_ms);
                CREATE INDEX IF NOT EXISTS idx_attempts_operation
                    ON attempts(operation_id, created_at_ms);
                """
            )

    def submit(
        self, *, capability: str, request_id: str, parcel: dict[str, Any]
    ) -> ExternalOperation:
        if not capability or not request_id:
            raise WorkerConflict("capability and request_id are required")
        with self._connect() as db:
            now = self._clock_ms()
            existing = db.execute(
                "SELECT * FROM operations WHERE capability=%s AND request_id=%s",
                (capability, request_id),
            ).fetchone()
            if existing is not None:
                if existing["parcel_json"] != _canonical_json(parcel):
                    raise WorkerConflict("request replay differs from admitted parcel")
                return self._operation_from_row(db, existing)
            operation_id = "xop-" + uuid.uuid4().hex
            db.execute(
                """
                INSERT INTO operations(
                    operation_id, capability, request_id, parcel_json, state, terminal,
                    desired_state, created_at_ms, updated_at_ms
                ) VALUES(%s,%s,%s,%s, 'queued',0,'run',%s,%s)
                """,
                (operation_id, capability, request_id, _canonical_json(parcel), now, now),
            )
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
            ).fetchone()
            if row is None:
                raise WorkerConflict("persisted operation is missing")
            return self._operation_from_row(db, row)

    def resolve(self, capability: str, request_id: str) -> ExternalOperation | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM operations WHERE capability=%s AND request_id=%s",
                (capability, request_id),
            ).fetchone()
            return self._operation_from_row(db, row) if row is not None else None

    def _reap_expired(self, db: psycopg.Connection, now: int) -> None:
        # The caller holds the transaction advisory lock. Preserve the claimed/started safety
        # boundary with a fixed number of set-based PostgreSQL transitions.
        db.execute(
            """
            UPDATE operations
            SET state='queued', active_attempt_id=NULL, updated_at_ms=%s
            WHERE terminal=0 AND desired_state='run'
              AND (operation_id, active_attempt_id) IN (
                SELECT operation_id, attempt_id FROM attempts
                WHERE state='claimed' AND lease_expires_ms < %s
              )
            """,
            (now, now),
        )
        # Started attempts can have external effects. Never make them claimable.
        db.execute(
            """
            UPDATE operations
            SET state='reconcile_required', updated_at_ms=%s
            WHERE terminal=0 AND desired_state='run'
              AND (operation_id, active_attempt_id) IN (
                SELECT operation_id, attempt_id FROM attempts
                WHERE state='started' AND lease_expires_ms < %s
              )
            """,
            (now, now),
        )
        db.execute(
            """
            UPDATE attempts SET state='expired_unstarted'
            WHERE state='claimed' AND lease_expires_ms < %s
            """,
            (now,),
        )
        db.execute(
            """
            UPDATE attempts SET state='reconcile_required'
            WHERE state='started' AND lease_expires_ms < %s
            """,
            (now,),
        )

    def claim(self, worker_id: str, *, generation: int) -> dict[str, Any] | None:
        with self._connect() as db:
            now = self._clock_ms()
            worker = self._worker(db, worker_id, generation)
            self._reap_expired(db, now)
            capabilities = json.loads(worker["capabilities_json"])
            if not capabilities:
                return None
            placeholders = ",".join("%s" for _ in capabilities)
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
                return None
            attempt_id = "xatt-" + uuid.uuid4().hex
            lease_id = "xlease-" + uuid.uuid4().hex
            expires = now + self.lease_ms
            db.execute(
                """
                INSERT INTO attempts(
                    attempt_id, operation_id, worker_id, generation, lease_id,
                    lease_expires_ms, state, created_at_ms
                ) VALUES(%s,%s,%s,%s,%s,%s, 'claimed',%s)
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
                SET state='claimed', active_attempt_id=%s, updated_at_ms=%s
                WHERE operation_id=%s
                """,
                (attempt_id, now, row["operation_id"]),
            )
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
        db: psycopg.Connection,
        *,
        worker_id: str,
        generation: int,
        operation_id: str,
        attempt_id: str,
        lease_id: str,
        allow_expired_started: bool = False,
        allow_terminal_replay: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        self._worker(db, worker_id, generation)
        operation = db.execute(
            "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
        ).fetchone()
        attempt = db.execute("SELECT * FROM attempts WHERE attempt_id=%s", (attempt_id,)).fetchone()
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
            committed_replay = (
                allow_terminal_replay
                and bool(operation["terminal"])
                and attempt["state"] in {"completed", "failed"}
            )
            if not late_started_result and not committed_replay:
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
        with self._connect() as db:
            now = self._clock_ms()
            operation, attempt = self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            if bool(operation["terminal"]):
                return
            if attempt["state"] not in {"claimed", "started"}:
                raise WorkerConflict("attempt cannot start from current state")
            db.execute("UPDATE attempts SET state='started' WHERE attempt_id=%s", (attempt_id,))
            db.execute(
                "UPDATE operations SET state='started', updated_at_ms=%s WHERE operation_id=%s",
                (now, operation_id),
            )

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
        with self._connect() as db:
            now = self._clock_ms()
            operation = db.execute(
                "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
            ).fetchone()
            if operation is None:
                raise WorkerConflict("unknown operation")
            # Authenticate exact Worker/Attempt/Lease even for terminal retries.
            operation, _ = self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
                allow_expired_started=True,
                allow_terminal_replay=True,
            )
            if bool(operation["terminal"]):
                if operation["result_digest"] != terminal_digest:
                    raise WorkerConflict("terminal result differs from committed result")
                return self._operation_from_row(db, operation)

            for item, projection in zip(artifacts, artifact_projection, strict=True):
                db.execute(
                    """
                    INSERT INTO artifacts(operation_id, artifact_id, content, digest)
                    VALUES(%s,%s,%s,%s)
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
                "UPDATE attempts SET state=%s WHERE attempt_id=%s",
                (state, attempt_id),
            )
            db.execute(
                """
                UPDATE operations
                SET state=%s, terminal=1, exit_code=%s, result_json=%s, result_digest=%s,
                    updated_at_ms=%s
                WHERE operation_id=%s
                """,
                (state, exit_code, _canonical_json(result), terminal_digest, now, operation_id),
            )
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
            ).fetchone()
            if row is None:
                raise WorkerConflict("persisted operation is missing")
            return self._operation_from_row(db, row)

    def cancellation_requests(self, worker_id: str, *, generation: int) -> list[str]:
        with self._connect() as db:
            self._worker(db, worker_id, generation)
            rows = db.execute(
                """
                SELECT o.operation_id
                FROM operations o JOIN attempts a ON o.active_attempt_id=a.attempt_id
                WHERE a.worker_id=%s AND a.generation=%s AND o.terminal=0
                  AND o.desired_state='cancel'
                ORDER BY o.operation_id
                """,
                (worker_id, generation),
            ).fetchall()
        return [str(row["operation_id"]) for row in rows]

    def cancel(self, operation_id: str) -> ExternalOperation:
        with self._connect() as db:
            now = self._clock_ms()
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
            ).fetchone()
            if row is None:
                raise WorkerConflict("unknown operation")
            if bool(row["terminal"]):
                return self._operation_from_row(db, row)
            if row["state"] == "queued":
                db.execute(
                    """
                    UPDATE operations
                    SET desired_state='cancel', state='cancelled', terminal=1, updated_at_ms=%s
                    WHERE operation_id=%s
                    """,
                    (now, operation_id),
                )
            else:
                db.execute(
                    """
                    UPDATE operations
                    SET desired_state='cancel', state='cancel_requested', updated_at_ms=%s
                    WHERE operation_id=%s
                    """,
                    (now, operation_id),
                )
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
            ).fetchone()
            if row is None:
                raise WorkerConflict("persisted operation is missing")
            return self._operation_from_row(db, row)

    def get(self, operation_id: str) -> ExternalOperation:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM operations WHERE operation_id=%s", (operation_id,)
            ).fetchone()
            if row is None:
                raise WorkerConflict("unknown operation")
            return self._operation_from_row(db, row)

    def _operation_from_row(self, db: psycopg.Connection, row: dict[str, Any]) -> ExternalOperation:
        artifacts = [
            str(item["artifact_id"])
            for item in db.execute(
                "SELECT artifact_id FROM artifacts WHERE operation_id=%s ORDER BY artifact_id",
                (row["operation_id"],),
            ).fetchall()
        ]
        parcel = json.loads(row["parcel_json"])
        workspace_id = parcel.get("workspace_id") if isinstance(parcel, dict) else None
        if not isinstance(workspace_id, str) or not workspace_id.strip():
            workspace_id = None
        return ExternalOperation(
            workspace_id=workspace_id,
            operation_id=str(row["operation_id"]),
            capability=str(row["capability"]),
            request_id=str(row["request_id"]),
            state=str(row["state"]),
            terminal=bool(row["terminal"]),
            desired_state=str(row["desired_state"]),
            exit_code=int(row["exit_code"]) if row["exit_code"] is not None else None,
            artifact_ids=artifacts,
        )
