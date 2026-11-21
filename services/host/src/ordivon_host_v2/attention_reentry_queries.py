"""Agent cold re-entry: combine one Attention delta page with Topic cursor coordinates."""

from __future__ import annotations

from typing import Any

from .attention_delta_queries import AttentionDeltaQueries
from .attention_reentry import project_reentry, reentry_topic_refs
from .collection_pagination import DEFAULT_COLLECTION_MAX_BYTES, validate_max_bytes
from .topic_cursor_records import list_topic_cursors_in_tx


class AttentionReentryQueries(AttentionDeltaQueries):
    """Explicitly depends on Delta's same-transaction _delta_in_tx contract."""

    def reentry(
        self,
        actor_ref: str,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
        max_bytes: int = DEFAULT_COLLECTION_MAX_BYTES,
    ) -> dict[str, Any]:
        if type(limit) is not int or not 1 <= limit <= 500:
            raise ValueError("limit must be in [1,500]")
        validate_max_bytes(max_bytes)
        if after_sequence is not None and (
            type(after_sequence) is not int or after_sequence < 0
        ):
            raise ValueError("after_sequence must be non-negative integer")
        # Cursor, events, and topic resume cursors come from one MVCC snapshot.
        with self._connect() as conn, conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            self._require_actor(conn, actor_ref)
            if after_sequence is None:
                row = conn.execute(
                    "SELECT cursor FROM attention_cursors WHERE actor_ref=%s", (actor_ref,)
                ).fetchone()
                after_sequence = 0 if row is None else int(row["cursor"])

            # The delta SQL is an expensive multi-source query. Its bounded
            # event page is already ordered. Trimming a prefix for the re-entry
            # response budget must not re-run that query or change snapshots.
            delta = self._delta_in_tx(
                conn, actor_ref, after_sequence=after_sequence,
                limit=limit, max_bytes=max_bytes,
            )
            topic_refs = reentry_topic_refs(delta["events"])
            cursors = list_topic_cursors_in_tx(
                conn, actor_ref=actor_ref, topic_refs=topic_refs
            )
            return project_reentry(
                delta,
                actor_ref=actor_ref,
                after_sequence=after_sequence,
                cursors=cursors,
                max_bytes=max_bytes,
            )
