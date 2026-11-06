from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical_json import canonical_digest
from .command_receipts import claim_command_receipt, record_command_receipt
from .coordination_inputs import CoordinationIntentInput, IntentStanding
from .errors import ConflictError
from .social_errors import MessageNotFound as MessageNotFound
from .social_errors import SpaceNotFound as SpaceNotFound
from .social_errors import TopicNotFound as TopicNotFound


class SocialIntentCommands:
    """PostgreSQL commands through the sole Host SocialStore authority."""

    def declare_intent(
        self, value: CoordinationIntentInput, *, client_request_id: str
    ) -> dict[str, Any]:
        value.validate_window()
        request = {"operation": "intent.declare", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = claim_command_receipt(
                conn, client_request_id, "intent.declare", request_digest
            )
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            if value.work_ref is not None:
                self._require_work(conn, value.work_ref)
            if value.space_ref is not None:
                self._require_space(conn, value.space_ref)
            immutable = (
                value.actor_ref,
                value.subject_ref,
                value.work_ref,
                value.space_ref,
                value.operation,
            )
            # Two observers of an absent intent_ref must not both INSERT.
            # The same natural-key arbiter used by Work/Space is enough.
            inserted = conn.execute(
                "INSERT INTO coordination_intents(intent_ref,actor_ref,subject_ref,work_ref,space_ref,"
                "operation,standing,observed_at_ms,expires_at_ms) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (intent_ref) DO NOTHING RETURNING intent_ref",
                (
                    value.intent_ref,
                    value.actor_ref,
                    value.subject_ref,
                    value.work_ref,
                    value.space_ref,
                    value.operation,
                    value.standing.value,
                    value.observed_at_ms,
                    value.expires_at_ms,
                ),
            ).fetchone()
            if inserted is not None:
                admission = "committed"
            else:
                current = conn.execute(
                    "SELECT * FROM coordination_intents WHERE intent_ref=%s FOR UPDATE",
                    (value.intent_ref,),
                ).fetchone()
                if current is None:
                    raise RuntimeError("intent_ref disappeared after insert conflict")
                existing_immutable = (
                    current["actor_ref"],
                    current["subject_ref"],
                    current["work_ref"],
                    current["space_ref"],
                    current["operation"],
                )
                if existing_immutable != immutable:
                    raise ConflictError(
                        "intent_ref already exists with different immutable semantics"
                    )
                if (
                    current["standing"] == IntentStanding.RELEASED.value
                    and value.standing == IntentStanding.ACTIVE
                ):
                    raise ConflictError("released coordination intent cannot be resurrected")
                conn.execute(
                    "UPDATE coordination_intents SET standing=%s,observed_at_ms=%s,expires_at_ms=%s,"
                    "updated_at=clock_timestamp(),change_sequence=swf_next_change_sequence() "
                    "WHERE intent_ref=%s",
                    (
                        value.standing.value,
                        value.observed_at_ms,
                        value.expires_at_ms,
                        value.intent_ref,
                    ),
                )
                admission = (
                    "existing" if current["standing"] == value.standing.value else "committed"
                )
            row = conn.execute(
                "SELECT * FROM coordination_intents WHERE intent_ref=%s", (value.intent_ref,)
            ).fetchone()
            if row is None:
                raise RuntimeError("coordination intent disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-coordination-intent",
                "admission": admission,
                "intentRef": row["intent_ref"],
                "actorRef": row["actor_ref"],
                "subjectRef": row["subject_ref"],
                "workRef": row["work_ref"],
                "spaceRef": row["space_ref"],
                "operation": row["operation"],
                "standing": row["standing"],
                "observedAtMs": int(row["observed_at_ms"]),
                "expiresAtMs": None if row["expires_at_ms"] is None else int(row["expires_at_ms"]),
                "updatedAt": row["updated_at"].isoformat(),
                "truthBoundary": "coordination intent only; not assignment, reservation, lock, lease, scheduler decision, or EffectAuthority",
            }
            record_command_receipt(
                conn, client_request_id, "intent.declare", request_digest, result
            )
            return result
