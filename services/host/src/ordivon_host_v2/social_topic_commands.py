from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Literal

import psycopg

from .canonical_json import canonical_digest
from .collaboration_inputs import (
    TopicInput,
)
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ConflictError, InvalidArgumentError
from .postgres_bounds import HOST_WIRE_INT_MAX
from .references.actor_refs import ActorReferenceLookup
from .references.record_refs import RecordReferenceLookup
from .social_errors import MessageNotFound as MessageNotFound
from .social_errors import SpaceNotFound as SpaceNotFound
from .social_errors import TopicNotFound as TopicNotFound
from .topic_cursor_records import ack_topic_cursor_in_tx


class SocialTopicCommands:
    """PostgreSQL commands through the sole Host SocialStore authority."""

    def __init__(
        self, connect: Callable[[], AbstractContextManager[psycopg.Connection[dict[str, Any]]]]
    ) -> None:
        self._connect = connect

    def create_topic(self, value: TopicInput, *, client_request_id: str) -> dict[str, Any]:
        request = {"operation": "topic.create", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "topic.create", request_digest)
            if replay is not None:
                return replay
            RecordReferenceLookup._require_space(conn, value.space_ref)
            ActorReferenceLookup._require_actor(conn, value.actor_ref)
            row = conn.execute(
                "INSERT INTO topics(topic_ref,space_ref,title,state,created_by_actor_ref) "
                "VALUES (%s,%s,%s,'open',%s) ON CONFLICT (topic_ref) DO NOTHING "
                "RETURNING topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at",
                (value.topic_ref, value.space_ref, value.title, value.actor_ref),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT topic_ref,space_ref,title,state,created_by_actor_ref,created_at,updated_at "
                    "FROM topics WHERE topic_ref=%s",
                    (value.topic_ref,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("topic declaration disappeared")
                if (
                    row["space_ref"] != value.space_ref
                    or row["title"] != value.title
                    or row["created_by_actor_ref"] != value.actor_ref
                ):
                    raise ConflictError("topic_ref already exists with different initial semantics")
                admission = "existing"
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic",
                "admission": admission,
                "topicRef": row["topic_ref"],
                "spaceRef": row["space_ref"],
                "title": row["title"],
                "state": row["state"],
                "createdByActorRef": row["created_by_actor_ref"],
                "createdAt": row["created_at"].isoformat(),
                "updatedAt": row["updated_at"].isoformat(),
                "truthBoundary": "named asynchronous conversation axis only; not Work lifecycle or authority",
            }
            record_command_receipt(conn, client_request_id, "topic.create", request_digest, result)
            return result

    def set_topic_state(
        self,
        *,
        topic_ref: str,
        actor_ref: str,
        state: Literal["open", "closed", "archived"],
        expected_state: Literal["open", "closed", "archived"],
        expected_high_sequence: int,
        client_request_id: str,
    ) -> dict[str, Any]:
        """CAS for open, closed and logical archive; never deletes message bytes.

        The same row lock fences message posting. Archive requires a closed
        topic; restoring to writeable requires two explicit transitions.
        """
        if state not in ("open", "closed", "archived") or expected_state not in (
            "open",
            "closed",
            "archived",
        ):
            raise InvalidArgumentError("topic state must be open, closed, or archived")
        if (
            type(expected_high_sequence) is not int
            or not 0 <= expected_high_sequence <= HOST_WIRE_INT_MAX
        ):
            raise InvalidArgumentError(
                "expected_high_sequence must be a non-negative integer within JSON safe integer range"
            )
        request = {
            "operation": "topic.state.set",
            "topicRef": topic_ref,
            "actorRef": actor_ref,
            "state": state,
            "expectedState": expected_state,
            "expectedHighSequence": expected_high_sequence,
        }
        digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "topic.state.set", digest)
            if replay is not None:
                return replay
            ActorReferenceLookup._require_actor(conn, actor_ref)
            topic = RecordReferenceLookup._require_topic(conn, topic_ref, for_no_key_update=True)
            high = int(
                conn.execute(
                    "SELECT COALESCE(MAX(sequence),0) AS high FROM messages WHERE topic_ref=%s",
                    (topic_ref,),
                ).fetchone()["high"]
            )
            if topic["state"] != expected_state:
                raise ConflictError("topic state changed since expected state")
            if high != expected_high_sequence:
                raise ConflictError("topic messages changed since expected high sequence")
            if state == "archived" and topic["state"] == "open":
                raise ConflictError("topic must be closed before archiving")
            if state == "open" and topic["state"] == "archived":
                raise ConflictError("restore archived topic to closed before reopening")
            admission = "existing" if state == topic["state"] else "committed"
            if admission == "committed":
                topic = conn.execute(
                    "UPDATE topics SET state=%s,updated_at=clock_timestamp(),"
                    "change_sequence=swf_next_change_sequence() WHERE topic_ref=%s "
                    "RETURNING topic_ref,space_ref,title,state,created_by_actor_ref,"
                    "created_at,updated_at",
                    (state, topic_ref),
                ).fetchone()
                if topic is None:
                    raise RuntimeError("topic state update disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-topic",
                "admission": admission,
                "topicRef": topic["topic_ref"],
                "spaceRef": topic["space_ref"],
                "title": topic["title"],
                "state": topic["state"],
                "createdByActorRef": topic["created_by_actor_ref"],
                "createdAt": topic["created_at"].isoformat(),
                "updatedAt": topic["updated_at"].isoformat(),
                "truthBoundary": "topic openness only; no message deletion, consumer-release proof, or authority transfer",
            }
            record_command_receipt(conn, client_request_id, "topic.state.set", digest, result)
            return result

    def ack_topic_cursor(
        self,
        *,
        actor_ref: str,
        topic_ref: str,
        cursor: int,
        client_request_id: str,
    ) -> dict[str, Any]:
        if type(cursor) is not int or not 0 <= cursor <= HOST_WIRE_INT_MAX:
            raise InvalidArgumentError("cursor must be non-negative within JSON safe integer range")
        request = {
            "operation": "topic.cursor.ack",
            "actorRef": actor_ref,
            "topicRef": topic_ref,
            "cursor": cursor,
        }
        request_digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(
                conn, client_request_id, "topic.cursor.ack", request_digest
            )
            if replay is not None:
                return replay
            ActorReferenceLookup._require_actor(conn, actor_ref)
            RecordReferenceLookup._require_topic(conn, topic_ref)
            result = ack_topic_cursor_in_tx(
                conn, actor_ref=actor_ref, topic_ref=topic_ref, cursor=cursor
            )
            record_command_receipt(
                conn, client_request_id, "topic.cursor.ack", request_digest, result
            )
            return result
