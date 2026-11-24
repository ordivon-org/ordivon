"""Shared conn-scoped Message row integrity, not a second Social query/store.

Both immutable reads and write-command readbacks use the same PostgreSQL row
fields, canonical digest, and explicit current transaction connection.
"""

from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_digest
from .social_errors import MessageNotFound


def verify_message_content_digest(row: dict[str, Any]) -> None:
    # Digest is a claim about all immutable message fields, not an
    # authoritative pointer by itself. Every consumer-visible read must
    # bind the stored claim to the actual PostgreSQL row bytes/values.
    actual = canonical_digest(
        {
            "messageRef": row["message_ref"],
            "spaceRef": row["space_ref"],
            "topicRef": row["topic_ref"],
            "authorActorRef": row["author_actor_ref"],
            "messageKind": row["message_kind"],
            "body": row["body"],
            "recordedAtMs": row["recorded_at_ms"],
        }
    )
    if actual != row["message_digest"]:
        raise RuntimeError("Host message content digest differs from stored claim")


def require_message(conn: psycopg.Connection[dict[str, Any]], message_ref: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT message_ref,sequence,space_ref,topic_ref,author_actor_ref "
        "FROM messages WHERE message_ref=%s",
        (message_ref,),
    ).fetchone()
    if row is None:
        raise MessageNotFound(message_ref)
    return row
