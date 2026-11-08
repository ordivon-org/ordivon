from __future__ import annotations

from typing import Any

import psycopg

from .canonical_json import canonical_digest
from .collaboration_inputs import (
    MessageInput,
    MessageRelationInput,
    MessageRelationKind,
)
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ConflictError
from .social_errors import MessageNotFound as MessageNotFound
from .social_errors import SpaceNotFound as SpaceNotFound
from .social_errors import TopicNotFound as TopicNotFound


def _reply_target_precedes_source(source_sequence: int, target_sequence: int) -> bool:
    """Strictly earlier reply target, using exact PostgreSQL signed bigint order.

    pre: -(2**63) <= source_sequence <= 2**63 - 1
    pre: -(2**63) <= target_sequence <= 2**63 - 1
    post: __return__ == (target_sequence < source_sequence)
    post: __return__ == (not (target_sequence >= source_sequence))
    """
    return not (target_sequence >= source_sequence)


class SocialMessageCommands:
    """PostgreSQL commands through the sole Host SocialStore authority."""

    def post_message(self, value: MessageInput) -> dict[str, Any]:
        request = {"operation": "message.post", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        message_digest = canonical_digest(
            {
                "messageRef": value.message_ref,
                "spaceRef": value.space_ref,
                "topicRef": value.topic_ref,
                "authorActorRef": value.author_actor_ref,
                "messageKind": value.message_kind.value,
                "body": value.body,
                "recordedAtMs": value.recorded_at_ms,
            }
        )
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(
                conn, value.client_request_id, "message.post", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.author_actor_ref)
            self._require_space(conn, value.space_ref)
            # The same-topic row fence precedes the IDENTITY default so a
            # later visible sequence cannot overtake a pending older one.
            # NO KEY UPDATE remains compatible with FK KEY SHARE on topics.
            topic = self._require_topic(conn, value.topic_ref, for_no_key_update=True)
            if topic["space_ref"] != value.space_ref:
                raise ConflictError("topic does not belong to the supplied space")
            if topic["state"] != "open":
                raise ConflictError("closed topic does not accept new messages")
            row = conn.execute(
                "INSERT INTO messages(message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,"
                "message_kind,body,message_digest,recorded_at_ms) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (message_ref) DO NOTHING RETURNING sequence,message_ref,space_ref,topic_ref,"
                "author_actor_ref,message_kind,body,message_digest,recorded_at_ms,created_at",
                (
                    value.message_ref,
                    value.client_request_id,
                    value.space_ref,
                    value.topic_ref,
                    value.author_actor_ref,
                    value.message_kind.value,
                    value.body,
                    message_digest,
                    value.recorded_at_ms,
                ),
            ).fetchone()
            admission = "committed"
            if row is None:
                row = conn.execute(
                    "SELECT sequence,message_ref,client_request_id,space_ref,topic_ref,author_actor_ref,"
                    "message_kind,body,message_digest,recorded_at_ms,created_at FROM messages "
                    "WHERE message_ref=%s",
                    (value.message_ref,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("message declaration disappeared")
                if row["message_digest"] != message_digest:
                    raise ConflictError("message_ref already exists with different content")
                admission = "existing"
            self._verify_message_content_digest(row)
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-message",
                "admission": admission,
                "sequence": int(row["sequence"]),
                "messageRef": row["message_ref"],
                "spaceRef": row["space_ref"],
                "topicRef": row["topic_ref"],
                "authorActorRef": row["author_actor_ref"],
                "messageKind": row["message_kind"],
                "body": row["body"],
                "messageDigest": row["message_digest"],
                "recordedAtMs": int(row["recorded_at_ms"]),
                "createdAt": row["created_at"].isoformat(),
                "truthBoundary": "durable collaboration message only; participation is not authorization and message content is not Work/domain truth",
            }
            record_command_receipt(
                conn, value.client_request_id, "message.post", request_digest, result
            )
            return result

    def add_message_relation(
        self, value: MessageRelationInput, *, client_request_id: str
    ) -> dict[str, Any]:
        request = {"operation": "message.relation.add", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with self._connect() as conn, conn.transaction():
            replay = claim_command_receipt(
                conn, client_request_id, "message.relation.add", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            source = self._require_message(conn, value.source_message_ref)
            self._validate_relation_target(conn, source, value)
            row = conn.execute(
                "INSERT INTO message_relations(source_message_ref,relation,target_ref,created_by_actor_ref) "
                "VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING created_at",
                (
                    value.source_message_ref,
                    value.relation.value,
                    value.target_ref,
                    value.actor_ref,
                ),
            ).fetchone()
            admission = "committed" if row is not None else "existing"
            existing = conn.execute(
                "SELECT source_message_ref,relation,target_ref,created_by_actor_ref,created_at "
                "FROM message_relations WHERE source_message_ref=%s AND relation=%s AND target_ref=%s",
                (value.source_message_ref, value.relation.value, value.target_ref),
            ).fetchone()
            if existing is None:
                raise RuntimeError("message relation disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-message-relation",
                "admission": admission,
                "sourceMessageRef": existing["source_message_ref"],
                "relation": existing["relation"],
                "targetRef": existing["target_ref"],
                "createdByActorRef": existing["created_by_actor_ref"],
                "createdAt": existing["created_at"].isoformat(),
                "truthBoundary": "collaboration relation only; acknowledgement is not vote/acceptance and mention is not assignment",
            }
            record_command_receipt(
                conn, client_request_id, "message.relation.add", request_digest, result
            )
            return result

    def _validate_relation_target(
        self,
        conn: psycopg.Connection[dict[str, Any]],
        source: dict[str, Any],
        value: MessageRelationInput,
    ) -> None:
        if value.relation in {
            MessageRelationKind.REPLY_TO,
            MessageRelationKind.ACKNOWLEDGES,
            MessageRelationKind.SUPERSEDES,
        }:
            target = self._require_message(conn, value.target_ref)
            if target["space_ref"] != source["space_ref"]:
                raise ConflictError(f"{value.relation.value} cannot cross spaces")
            if (
                value.relation == MessageRelationKind.REPLY_TO
                and target["topic_ref"] != source["topic_ref"]
            ):
                raise ConflictError("reply_to cannot cross topics")
            if value.relation == MessageRelationKind.REPLY_TO and not _reply_target_precedes_source(
                source["sequence"], target["sequence"]
            ):
                # Immutable identity ordinals form a strict descending rank
                # for every reply edge, so its transitive closure is acyclic.
                # Lean: OrdivonR21.CausalReply.qualified_reply_graph_acyclic.
                raise ConflictError("reply_to must target an earlier message")
            if (
                value.relation == MessageRelationKind.SUPERSEDES
                and value.target_ref == value.source_message_ref
            ):
                raise ConflictError("message cannot supersede itself")
        elif value.relation == MessageRelationKind.MENTIONS:
            self._require_actor(conn, value.target_ref)
        # references/about intentionally accept opaque external refs; presence is not existence proof.
