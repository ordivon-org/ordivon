from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row

from .canonical_json import canonical_digest
from .collaboration_inputs import (
    ParticipationStanding,
    SpaceInput,
)
from .command_receipts import claim_command_receipt, record_command_receipt
from .errors import ConflictError
from .social_errors import MessageNotFound as MessageNotFound
from .social_errors import SpaceNotFound as SpaceNotFound
from .social_errors import TopicNotFound as TopicNotFound


class SocialSpaceCommands:
    """PostgreSQL commands through the sole Host SocialStore authority."""

    def create_space(self, value: SpaceInput, *, client_request_id: str) -> dict[str, Any]:
        request = {"operation": "space.create", **value.model_dump(mode="json")}
        request_digest = canonical_digest(request)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            replay = claim_command_receipt(conn, client_request_id, "space.create", request_digest)
            if replay is not None:
                return replay
            self._require_actor(conn, value.actor_ref)
            # The unique space_ref constraint linearizes parallel first creates.
            # SELECT-before-INSERT allows multiple writers to observe absence.
            inserted = conn.execute(
                "INSERT INTO spaces(space_ref,purpose,created_by_actor_ref) VALUES (%s,%s,%s) "
                "ON CONFLICT (space_ref) DO NOTHING RETURNING space_ref",
                (value.space_ref, value.purpose, value.actor_ref),
            ).fetchone()
            admission = "committed"
            if inserted is not None:
                for subject_ref in sorted(value.subject_refs):
                    conn.execute(
                        "INSERT INTO space_subjects(space_ref,subject_ref) VALUES (%s,%s)",
                        (value.space_ref, subject_ref),
                    )
            else:
                # Conflict arbitration waits for the complete original
                # transaction, including its subject rows, to commit.
                current = conn.execute(
                    "SELECT space_ref,purpose,created_by_actor_ref,created_at FROM spaces "
                    "WHERE space_ref=%s FOR UPDATE",
                    (value.space_ref,),
                ).fetchone()
                if current is None:
                    raise RuntimeError("space_ref disappeared after insert conflict")
                subjects = [
                    row["subject_ref"]
                    for row in conn.execute(
                        "SELECT subject_ref FROM space_subjects WHERE space_ref=%s "
                        "ORDER BY subject_ref",
                        (value.space_ref,),
                    ).fetchall()
                ]
                if (
                    current["purpose"] != value.purpose
                    or current["created_by_actor_ref"] != value.actor_ref
                    or subjects != sorted(value.subject_refs)
                ):
                    raise ConflictError("space_ref already exists with different initial semantics")
                admission = "existing"
            result = self._get_space_in_tx(conn, value.space_ref)
            result["admission"] = admission
            record_command_receipt(conn, client_request_id, "space.create", request_digest, result)
            return result

    def set_participation(
        self,
        *,
        space_ref: str,
        actor_ref: str,
        standing: ParticipationStanding,
        client_request_id: str,
    ) -> dict[str, Any]:
        # Desired-state command: the (space, actor) natural key plus standing owns
        # idempotency. Historical request receipts must not block joined→left→joined.
        _ = client_request_id
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn, conn.transaction():
            self._require_space(conn, space_ref)
            self._require_actor(conn, actor_ref)
            row = conn.execute(
                "INSERT INTO participations(space_ref,actor_ref,standing) VALUES (%s,%s,%s) "
                "ON CONFLICT (space_ref,actor_ref) DO UPDATE SET standing=EXCLUDED.standing,"
                "updated_at=clock_timestamp(),change_sequence=swf_next_change_sequence() "
                "WHERE participations.standing IS DISTINCT FROM EXCLUDED.standing "
                "RETURNING space_ref,actor_ref,standing,updated_at",
                (space_ref, actor_ref, standing.value),
            ).fetchone()
            if row is None:
                row = conn.execute(
                    "SELECT space_ref,actor_ref,standing,updated_at FROM participations "
                    "WHERE space_ref=%s AND actor_ref=%s",
                    (space_ref, actor_ref),
                ).fetchone()
            if row is None:
                raise RuntimeError("participation update disappeared")
            result = {
                "schemaVersion": 1,
                "kind": "ordivon.host-participation",
                "spaceRef": row["space_ref"],
                "actorRef": row["actor_ref"],
                "standing": row["standing"],
                "updatedAt": row["updated_at"].isoformat(),
                "truthBoundary": "social participation only; not ownership, authentication, authorization, assignment, or EffectAuthority",
            }
            return result
