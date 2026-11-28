"""Single-transaction Space response projection shared by creation and reads.

Uses the caller's PostgreSQL transaction and exact existing response-byte budget.
Does not own a second write store or a new connection.
"""
from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_bytes
from .collection_pagination import DEFAULT_SPACE_MAX_BYTES, MIN_SPACE_MAX_BYTES, validate_max_bytes
from .errors import InvalidArgumentError
from .social_errors import SpaceNotFound


def read_space_in_tx(
    conn: psycopg.Connection[dict[str, Any]],
    space_ref: str,
    *,
    participant_limit: int = 200,
    topic_limit: int = 200,
    max_bytes: int = DEFAULT_SPACE_MAX_BYTES,
) -> dict[str, Any]:
    validate_max_bytes(max_bytes, minimum=MIN_SPACE_MAX_BYTES)
    space = conn.execute(
        "SELECT space_ref,purpose,created_by_actor_ref,created_at FROM spaces WHERE space_ref=%s",
        (space_ref,),
    ).fetchone()
    if space is None:
        raise SpaceNotFound(space_ref)
    subject_count = int(
        conn.execute(
            "SELECT count(*) AS n FROM space_subjects WHERE space_ref=%s", (space_ref,)
        ).fetchone()["n"]
    )
    participant_count = int(
        conn.execute(
            "SELECT count(*) AS n FROM participations WHERE space_ref=%s", (space_ref,)
        ).fetchone()["n"]
    )
    topic_count = int(
        conn.execute(
            "SELECT count(*) AS n FROM topics WHERE space_ref=%s AND state <> 'archived'",
            (space_ref,),
        ).fetchone()["n"]
    )
    subject_rows = conn.execute(
        "SELECT subject_ref FROM space_subjects WHERE space_ref=%s ORDER BY subject_ref LIMIT 129",
        (space_ref,),
    ).fetchall()
    participant_rows = conn.execute(
        "SELECT actor_ref,standing,updated_at FROM participations WHERE space_ref=%s ORDER BY actor_ref LIMIT %s",
        (space_ref, participant_limit + 1),
    ).fetchall()
    topic_rows = conn.execute(
        "SELECT topic_ref,title,state,created_by_actor_ref,created_at,updated_at FROM topics "
        "WHERE space_ref=%s AND state <> 'archived' ORDER BY topic_ref LIMIT %s",
        (space_ref, topic_limit + 1),
    ).fetchall()
    subjects = [row["subject_ref"] for row in subject_rows[:128]]
    participants = [
        {
            "actorRef": row["actor_ref"],
            "standing": row["standing"],
            "updatedAt": row["updated_at"].isoformat(),
        }
        for row in participant_rows[:participant_limit]
    ]
    topics = [
        {
            "topicRef": row["topic_ref"],
            "title": row["title"],
            "state": row["state"],
            "createdByActorRef": row["created_by_actor_ref"],
            "createdAt": row["created_at"].isoformat(),
            "updatedAt": row["updated_at"].isoformat(),
        }
        for row in topic_rows[:topic_limit]
    ]

    def build() -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.host-space",
            "spaceRef": space["space_ref"],
            "purpose": space["purpose"],
            "createdByActorRef": space["created_by_actor_ref"],
            "createdAt": space["created_at"].isoformat(),
            "subjectRefs": subjects,
            "subjectCount": subject_count,
            "subjectHasMore": len(subjects) < subject_count,
            "participants": participants,
            "participantCount": participant_count,
            "participantHasMore": len(participants) < participant_count,
            "topics": topics,
            "topicCount": topic_count,
            "topicHasMore": len(topics) < topic_count,
            "truthBoundary": "social organization record only; participation does not imply identity, authority, ownership, or assignment",
        }

    result = build()
    while len(canonical_bytes(result)) > max_bytes:
        if topics:
            topics.pop()
        elif participants:
            participants.pop()
        elif subjects:
            subjects.pop()
        else:
            raise InvalidArgumentError("max_bytes cannot fit the Space response envelope")
        result = build()
    return result
