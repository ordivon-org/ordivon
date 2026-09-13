from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical import canonical_digest
from .errors import ConflictError, TaskNotFound


class ExtensionStore:
    """Opaque owner state retained at one exact Host task revision."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def put(
        self, *, task_id: str, namespace: str, expected_task_revision: int, payload: dict[str, Any]
    ) -> dict[str, Any]:
        if not namespace or namespace != namespace.strip() or len(namespace) > 128:
            raise ValueError("namespace is invalid")
        digest = canonical_digest(payload)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            task = conn.execute(
                "SELECT revision FROM tasks WHERE task_id=%s FOR UPDATE", (task_id,)
            ).fetchone()
            if task is None:
                raise TaskNotFound(task_id)
            if int(task["revision"]) != expected_task_revision:
                raise ConflictError("extension task revision is stale")
            existing = conn.execute(
                "SELECT payload_digest FROM extension_history "
                "WHERE task_id=%s AND namespace=%s AND task_revision=%s",
                (task_id, namespace, expected_task_revision),
            ).fetchone()
            if existing is not None and existing["payload_digest"] != digest:
                raise ConflictError(
                    "extension history at this task revision is already bound to different content"
                )
            if existing is None:
                conn.execute(
                    "INSERT INTO extension_history(task_id,namespace,task_revision,payload_digest,payload) "
                    "VALUES (%s,%s,%s,%s,%s::jsonb)",
                    (
                        task_id,
                        namespace,
                        expected_task_revision,
                        digest,
                        psycopg.types.json.Jsonb(payload),
                    ),
                )
            conn.execute(
                "INSERT INTO extension_states(task_id,namespace,task_revision,payload_digest,payload) VALUES (%s,%s,%s,%s,%s::jsonb) "
                "ON CONFLICT (task_id,namespace) DO UPDATE SET task_revision=EXCLUDED.task_revision,payload_digest=EXCLUDED.payload_digest,payload=EXCLUDED.payload,updated_at=clock_timestamp()",
                (
                    task_id,
                    namespace,
                    expected_task_revision,
                    digest,
                    psycopg.types.json.Jsonb(payload),
                ),
            )
            return {
                "taskId": task_id,
                "namespace": namespace,
                "taskRevision": expected_task_revision,
                "payloadDigest": digest,
            }

    def get(
        self, *, task_id: str, namespace: str, at_revision: int | None = None
    ) -> dict[str, Any] | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            if at_revision is None:
                row = conn.execute(
                    "SELECT * FROM extension_states WHERE task_id=%s AND namespace=%s",
                    (task_id, namespace),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM extension_history WHERE task_id=%s AND namespace=%s AND task_revision<=%s ORDER BY task_revision DESC LIMIT 1",
                    (task_id, namespace, at_revision),
                ).fetchone()
            if row is None:
                return None
            return {
                "taskId": row["task_id"],
                "namespace": row["namespace"],
                "taskRevision": int(row["task_revision"]),
                "payloadDigest": row["payload_digest"],
                "payload": dict(row["payload"]),
                "truthBoundary": "opaque owner bytes retained by Host; not owner currentness, health, authority, or success",
            }
