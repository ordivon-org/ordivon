"""Shared conn-scoped Message row integrity, not a second Social query/store.

Both immutable reads and write-command readbacks use the same PostgreSQL row
fields, canonical digest, and explicit current transaction connection.
"""

from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_digest
from .social_errors import MessageNotFound


def message_content(
    *,
    message_ref: str,
    space_ref: str,
    topic_ref: str,
    author_actor_ref: str,
    message_kind: str,
    body: str,
    recorded_at_ms: int,
) -> dict[str, Any]:
    """Immutable digest preimage shared by command and read consumers."""
    return {
        "messageRef": message_ref,
        "spaceRef": space_ref,
        "topicRef": topic_ref,
        "authorActorRef": author_actor_ref,
        "messageKind": message_kind,
        "body": body,
        "recordedAtMs": recorded_at_ms,
    }


def _verified_content(row: dict[str, Any]) -> dict[str, Any]:
    content = message_content(
        message_ref=row["message_ref"],
        space_ref=row["space_ref"],
        topic_ref=row["topic_ref"],
        author_actor_ref=row["author_actor_ref"],
        message_kind=row["message_kind"],
        body=row["body"],
        recorded_at_ms=row["recorded_at_ms"],
    )
    if canonical_digest(content) != row["message_digest"]:
        raise RuntimeError("Host message content digest differs from stored claim")
    return content


def verified_message_wire(
    row: dict[str, Any],
    *,
    include_scope: bool = True,
) -> dict[str, Any]:
    """Verify all immutable fields before emitting full or topic-scoped wire data."""
    content = _verified_content(row)
    if not include_scope:
        del content["spaceRef"]
        del content["topicRef"]
    return {
        "sequence": int(row["sequence"]),
        **content,
        "messageDigest": row["message_digest"],
        "recordedAtMs": int(row["recorded_at_ms"]),
        "createdAt": row["created_at"].isoformat(),
    }


def require_message(conn: psycopg.Connection[dict[str, Any]], message_ref: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT message_ref,sequence,space_ref,topic_ref,author_actor_ref "
        "FROM messages WHERE message_ref=%s",
        (message_ref,),
    ).fetchone()
    if row is None:
        raise MessageNotFound(message_ref)
    return row
