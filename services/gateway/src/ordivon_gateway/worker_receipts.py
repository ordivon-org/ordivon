"""Worker event and Artifact receipt operations over the existing transport store."""

from __future__ import annotations

import hashlib
from typing import Any

from .external_worker_contracts import WorkerConflict
from .worker_identity import _canonical_json


class WorkerReceiptMethods:
    """Receipt persistence and readback; caller transport owns transaction handles."""

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
            self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            db.execute(
                """
                INSERT INTO events(operation_id, attempt_id, sequence, payload_json, created_at_ms)
                VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
                """,
                (operation_id, attempt_id, sequence, _canonical_json(event), self._clock_ms()),
            )
            existing = db.execute(
                """SELECT payload_json FROM events
                WHERE operation_id=%s AND attempt_id=%s AND sequence=%s""",
                (operation_id, attempt_id, sequence),
            ).fetchone()
            if existing is None or existing["payload_json"] != _canonical_json(event):
                raise WorkerConflict("event replay differs from committed event")

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
            self._active_attempt(
                db,
                worker_id=worker_id,
                generation=generation,
                operation_id=operation_id,
                attempt_id=attempt_id,
                lease_id=lease_id,
            )
            existing = db.execute(
                "SELECT digest FROM artifacts WHERE operation_id=%s AND artifact_id=%s",
                (operation_id, artifact_id),
            ).fetchone()
            if existing is not None:
                if existing["digest"] != digest:
                    raise WorkerConflict("artifact replay differs from committed artifact")
                return
            db.execute(
                """
                INSERT INTO artifacts(operation_id, artifact_id, content, digest)
                VALUES(%s,%s,%s,%s)
                """,
                (operation_id, artifact_id, content.encode("utf-8"), digest),
            )

    def read_artifact(
        self, operation_id: str, artifact_id: str, *, offset: int, max_bytes: int
    ) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT content, digest FROM artifacts
                WHERE operation_id=%s AND artifact_id=%s
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
