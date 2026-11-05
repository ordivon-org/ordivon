"""Native PostgreSQL append-only R6 experiment event ledger.

SQL transactions and per-search advisory locking remain provider-native.
No local SQLite writable ledger, shadow journal or generic state registry.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import psycopg

from .grounded_contracts import canonical_digest
from .trial_registration import _strict_text

EVENT_TYPES = (
    "trial.proposed",
    "trial.duplicate",
    "trial.rejected",
    "trial.failed",
    "trial.evaluated",
    "trial.selected",
    "trial.holdout_revealed",
)



class TrialLedger:
    """PostgreSQL append-only experiment history, one serialized hash chain per search.

    SQL storage and transactional lock are natural database capabilities, not a
    second orchestration service. A source string must be a PostgreSQL DSN.
    """

    def __init__(self, dsn: str, *, search_id: str):
        if not isinstance(dsn, str) or not dsn.startswith(("postgresql://", "postgres://")):
            raise ValueError("TrialLedger requires a PostgreSQL DSN, not a SQLite path")
        self.search_id = _strict_text(search_id, "search_id")
        self.db = psycopg.connect(dsn, autocommit=True)
        try:
            self._create_schema()
        except BaseException:
            self.db.close()
            raise

    def _create_schema(self) -> None:
        with self.db.transaction():
            # PostgreSQL CREATE SCHEMA IF NOT EXISTS is not a concurrency gate.
            # Serialize first-time Owner schema admission across connections.
            schema_key = int.from_bytes(
                hashlib.sha256(b"ordivon:media-trial:schema:v1").digest()[:8],
                "big", signed=True,
            )
            self.db.execute("SELECT pg_advisory_xact_lock(%s)", (schema_key,))
            self.db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_media_trial")
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS ordivon_media_trial.trial_events (
                  seq BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                  event_id TEXT NOT NULL UNIQUE,
                  search_id TEXT NOT NULL,
                  attempt_id TEXT NOT NULL,
                  candidate_id TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  prev_hash TEXT,
                  event_hash TEXT NOT NULL UNIQUE
                )
            """)
            self.db.execute(
                "CREATE INDEX IF NOT EXISTS trial_events_search_idx "
                "ON ordivon_media_trial.trial_events(search_id,seq)"
            )
            self.db.execute("""
                CREATE OR REPLACE FUNCTION ordivon_media_trial.reject_trial_mutation()
                RETURNS trigger LANGUAGE plpgsql AS $function$
                BEGIN
                    RAISE EXCEPTION 'trial events are append-only' USING ERRCODE = '55000';
                END;
                $function$
            """)
            self.db.execute("""
                DO $block$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger
                    WHERE tgrelid = 'ordivon_media_trial.trial_events'::regclass
                      AND tgname = 'trial_events_no_mutation'
                      AND NOT tgisinternal
                  ) THEN
                    CREATE TRIGGER trial_events_no_mutation
                    BEFORE UPDATE OR DELETE ON ordivon_media_trial.trial_events
                    FOR EACH ROW EXECUTE FUNCTION ordivon_media_trial.reject_trial_mutation();
                  END IF;
                END $block$
            """)
            # CREATE ... IF NOT EXISTS is not evidence that a pre-existing
            # database object has the required PostgreSQL semantics.
            self._verify_schema()

    def _verify_schema(self) -> None:
        """Admit a real PostgreSQL append-only ledger, not a namesake relation.

        This checks PostgreSQL catalog identity and immutable-data fences at
        owner connection admission; it is not a substitute for a trusted DB
        administrator or proof that privileged actors cannot later mutate DDL.
        """
        relation = self.db.execute(
            """
            SELECT c.relkind, c.relpersistence
            FROM pg_class c
            JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='ordivon_media_trial' AND c.relname='trial_events'
            """
        ).fetchone()
        if relation != ("r", "p"):
            raise ValueError("PostgreSQL trial ledger must be one permanent base table")

        columns = self.db.execute(
            """
            SELECT a.attname, format_type(a.atttypid,a.atttypmod),
                   a.attnotnull, a.attidentity
            FROM pg_attribute a
            WHERE a.attrelid='ordivon_media_trial.trial_events'::regclass
              AND a.attnum>0 AND NOT a.attisdropped
            ORDER BY a.attnum
            """
        ).fetchall()
        expected_columns = (
            ("seq", "bigint", True, "a"),
            ("event_id", "text", True, ""),
            ("search_id", "text", True, ""),
            ("attempt_id", "text", True, ""),
            ("candidate_id", "text", True, ""),
            ("event_type", "text", True, ""),
            ("payload_json", "text", True, ""),
            ("prev_hash", "text", False, ""),
            ("event_hash", "text", True, ""),
        )
        if tuple(columns) != expected_columns:
            raise ValueError("PostgreSQL trial ledger column/identity contract mismatch")

        rows = self.db.execute(
            """
            SELECT con.conname, con.contype,
                   ARRAY(
                       SELECT attr.attname
                       FROM unnest(con.conkey) WITH ORDINALITY AS key(attnum, position)
                       JOIN pg_attribute attr
                         ON attr.attrelid=con.conrelid AND attr.attnum=key.attnum
                       ORDER BY key.position
                   )
            FROM pg_constraint con
            WHERE con.conrelid='ordivon_media_trial.trial_events'::regclass
              AND con.contype IN ('p', 'u')
            """
        ).fetchall()
        constraints = {(name, kind, tuple(keys)) for name, kind, keys in rows}
        required = {
            ("trial_events_pkey", "p", ("seq",)),
            ("trial_events_event_id_key", "u", ("event_id",)),
            ("trial_events_event_hash_key", "u", ("event_hash",)),
        }
        if constraints != required:
            raise ValueError("PostgreSQL trial ledger event uniqueness/primary-key contract mismatch")

        # tgtype bits: ROW=1, BEFORE=2, DELETE=8, UPDATE=16. Disabled or
        # differently scoped triggers must never qualify as append-only.
        trigger = self.db.execute(
            """
            SELECT t.tgtype, t.tgenabled, t.tgisinternal,
                   t.tgfoid='ordivon_media_trial.reject_trial_mutation()'::regprocedure,
                   t.tgqual IS NULL, t.tgnargs, t.tgconstraint=0
            FROM pg_trigger t
            WHERE t.tgrelid='ordivon_media_trial.trial_events'::regclass
              AND t.tgname='trial_events_no_mutation'
            """
        ).fetchone()
        if trigger != (27, "O", False, True, True, 0, True):
            raise ValueError("PostgreSQL trial ledger append-only trigger is absent or counterfeit")

    def close(self) -> None:
        self.db.close()

    def _last_hash(self) -> str | None:
        row = self.db.execute(
            "SELECT event_hash FROM ordivon_media_trial.trial_events "
            "WHERE search_id=%s ORDER BY seq DESC LIMIT 1", (self.search_id,)
        ).fetchone()
        return str(row[0]) if row else None

    @contextmanager
    def search_transaction(self) -> Iterator[None]:
        """Use the same native per-search lock for verification and append."""
        key = int.from_bytes(
            hashlib.sha256(self.search_id.encode("utf-8")).digest()[:8],
            "big", signed=True,
        )
        with self.db.transaction():
            self.db.execute("SELECT pg_advisory_xact_lock(%s)", (key,))
            yield

    def append(self, attempt_id: str, candidate_id: str, event_type: str, payload: Mapping[str, Any]) -> str:
        _strict_text(attempt_id, "attempt_id")
        _strict_text(candidate_id, "candidate_id")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported trial event type: {event_type}")
        with self.search_transaction():
            # Serialized per search, including independent concurrent connections.
            previous = self._last_hash()
            semantic = {
                "searchId": self.search_id,
                "attemptId": attempt_id,
                "candidateId": candidate_id,
                "eventType": event_type,
                "payload": dict(payload),
                "prevHash": previous,
            }
            event_hash = canonical_digest(semantic)
            event_id = "trial-event://" + event_hash.removeprefix("sha256:")
            self.db.execute(
                "INSERT INTO ordivon_media_trial.trial_events "
                "(event_id,search_id,attempt_id,candidate_id,event_type,payload_json,prev_hash,event_hash) "
                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    event_id, self.search_id, attempt_id, candidate_id, event_type,
                    json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    previous, event_hash,
                ),
            )
        return event_id

    def verify(self) -> bool:
        previous: str | None = None
        rows = self.db.execute(
            "SELECT attempt_id,candidate_id,event_type,payload_json,prev_hash,event_hash "
            "FROM ordivon_media_trial.trial_events WHERE search_id=%s ORDER BY seq",
            (self.search_id,),
        )
        for attempt_id, candidate_id, event_type, payload_json, observed_prev, observed_hash in rows:
            if observed_prev != previous:
                return False
            semantic = {
                "searchId": self.search_id,
                "attemptId": attempt_id,
                "candidateId": candidate_id,
                "eventType": event_type,
                "payload": json.loads(payload_json),
                "prevHash": previous,
            }
            if canonical_digest(semantic) != observed_hash:
                return False
            previous = observed_hash
        return True

    def summary(self) -> dict[str, Any]:
        event_counts = {
            str(row[0]): int(row[1])
            for row in self.db.execute(
                "SELECT event_type,count(*) FROM ordivon_media_trial.trial_events "
                "WHERE search_id=%s GROUP BY event_type", (self.search_id,)
            )
        }
        attempts = int(
            self.db.execute(
                "SELECT count(DISTINCT attempt_id) FROM ordivon_media_trial.trial_events WHERE search_id=%s",
                (self.search_id,),
            ).fetchone()[0]
        )
        candidates = int(
            self.db.execute(
                "SELECT count(DISTINCT candidate_id) FROM ordivon_media_trial.trial_events "
                "WHERE search_id=%s AND event_type='trial.proposed'",
                (self.search_id,),
            ).fetchone()[0]
        )
        return {
            "searchId": self.search_id,
            "attemptCount": attempts,
            "uniqueCandidateCount": candidates,
            "eventCounts": event_counts,
            "eventChainValid": self.verify(),
        }
