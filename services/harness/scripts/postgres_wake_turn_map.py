#!/usr/bin/env python3
"""PostgreSQL-native, effect-free wake intent identity owner.

This owner is selected only by an explicit PG cutover configuration; it never
silently creates a fresh identity to stand in for an existing SQLite wake.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

import psycopg
from psycopg.rows import dict_row

try:
    from sqlite_wake_turn_map import SQLiteWakeTurnMap, WakeTurnConflict, _digest, _text
    from standard_identifiers import require_uuid7
except ModuleNotFoundError:
    from scripts.sqlite_wake_turn_map import SQLiteWakeTurnMap, WakeTurnConflict, _digest, _text
    from scripts.standard_identifiers import require_uuid7


class PostgresWakeTurnMap:
    def __init__(
        self,
        dsn: str,
        *,
        uuid7_factory: Callable[[], str] = lambda: str(uuid.uuid7()),
        now_ms: Callable[[], int] = lambda: int(time.time() * 1000),
    ) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("PostgreSQL wake owner requires an explicit DSN")
        self.dsn = dsn
        self._uuid7_factory = uuid7_factory
        self._now_ms = now_ms
        with psycopg.connect(self.dsn) as db:
            # PostgreSQL IF NOT EXISTS does not serialize concurrent first
            # admissions. The native transaction lock protects schema+table.
            schema_lock = int.from_bytes(
                hashlib.sha256(b"ordivon:harness:wake-turn-pg-schema:v1").digest()[:8],
                "big", signed=True,
            )
            db.execute("SELECT pg_advisory_xact_lock(%s)", (schema_lock,))
            db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_harness")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS ordivon_harness.wake_turn_map(
                    wake_intent_id TEXT PRIMARY KEY,
                    campaign_ref TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    prompt_digest TEXT NOT NULL,
                    turn_request_id TEXT NOT NULL UNIQUE,
                    created_at_ms BIGINT NOT NULL CHECK (created_at_ms >= 0)
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS ordivon_harness.wake_cutover(
                    cutover_id TEXT PRIMARY KEY CHECK (cutover_id = 'legacy'),
                    state TEXT NOT NULL CHECK (state IN ('PENDING','ACTIVE'))
                )
                """
            )

    # Shared admission locks allow parallel wake writes; only the one-time
    # migration's exclusive lock blocks writers while a cutover fence is set.
    _CUTOVER_ADVISORY_KEY = 57163519194018

    @classmethod
    def _admit_cutover_state(cls, db: psycopg.Connection) -> None:
        db.execute("SELECT pg_advisory_xact_lock_shared(%s)", (cls._CUTOVER_ADVISORY_KEY,))
        row = db.execute(
            "SELECT state FROM ordivon_harness.wake_cutover "
            "WHERE cutover_id='legacy'"
        ).fetchone()
        if row is not None:
            state = row["state"] if isinstance(row, dict) else row[0]
            if state != "ACTIVE":
                raise WakeTurnConflict("PostgreSQL wake cutover pending; writer not certified")

    def _mark_pending_before_legacy_freeze(self) -> None:
        with psycopg.connect(self.dsn) as pg:
            with pg.transaction():
                pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                pg.execute(
                    "SELECT pg_advisory_xact_lock(%s)", (self._CUTOVER_ADVISORY_KEY,)
                )
                row = pg.execute(
                    "SELECT state FROM ordivon_harness.wake_cutover "
                    "WHERE cutover_id='legacy'"
                ).fetchone()
                if row is not None:  # PENDING resume or ACTIVE identity audit
                    return
                if pg.execute(
                    "SELECT 1 FROM ordivon_harness.wake_turn_map LIMIT 1"
                ).fetchone():
                    raise WakeTurnConflict(
                        "divergent PostgreSQL wake identities: destination already writable"
                    )
                pg.execute(
                    "INSERT INTO ordivon_harness.wake_cutover "
                    "(cutover_id,state) VALUES('legacy','PENDING')"
                )

    def _certify_cutover_after_source_commit(self) -> None:
        with psycopg.connect(self.dsn) as pg:
            with pg.transaction():
                pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                pg.execute(
                    "SELECT pg_advisory_xact_lock(%s)", (self._CUTOVER_ADVISORY_KEY,)
                )
                row = pg.execute(
                    "SELECT state FROM ordivon_harness.wake_cutover "
                    "WHERE cutover_id='legacy' FOR UPDATE"
                ).fetchone()
                if row is None:
                    raise WakeTurnConflict("PostgreSQL wake cutover marker disappeared")
                pg.execute(
                    "UPDATE ordivon_harness.wake_cutover SET state='ACTIVE' "
                    "WHERE cutover_id='legacy'"
                )

    @staticmethod
    def _receipt(row: dict[str, Any], disposition: str) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.wake-turn-mapping",
            "disposition": disposition,
            "wakeIntentId": row["wake_intent_id"],
            "campaignRef": row["campaign_ref"],
            "agentId": row["agent_id"],
            "promptDigest": row["prompt_digest"],
            "turnRequestId": row["turn_request_id"],
            "createdAtMs": int(row["created_at_ms"]),
            "providerEffectAttempted": False,
        }

    @staticmethod
    def _canonical_rows(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
        names = (
            "wake_intent_id", "campaign_ref", "agent_id", "prompt_digest",
            "turn_request_id", "created_at_ms",
        )
        result = []
        for row in rows:
            _text(row["wake_intent_id"], "wakeIntentId")
            _digest(row["campaign_ref"], "campaignRef")
            _text(row["agent_id"], "agentId", max_bytes=128)
            _digest(row["prompt_digest"], "promptDigest")
            require_uuid7(row["turn_request_id"], "turnRequestId")
            timestamp = int(row["created_at_ms"])
            if timestamp < 0:
                raise WakeTurnConflict("legacy wake timestamp cannot be negative")
            result.append(tuple(row[k] for k in names[:-1]) + (timestamp,))
        return sorted(result)

    @staticmethod
    def _legacy_rows(path: Path, *, write: bool = False) -> tuple[sqlite3.Connection, list[dict]]:
        if not path.is_file():
            raise WakeTurnConflict("legacy wake source missing")
        # Reuse the already-qualified SQLite source owner; adding a second
        # direct SQLite connection site violates PG-first source debt bounds.
        legacy = object.__new__(SQLiteWakeTurnMap)
        legacy.path = path
        db = legacy._connect(read_only=not write)
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")  # Freeze source writers through PG commit.
            rows = [dict(r) for r in db.execute("SELECT * FROM wake_turn_map")]
            return db, rows
        except Exception:
            db.close()
            raise

    def _postgres_rows(self, db: psycopg.Connection) -> list[dict]:
        return db.execute(
            "SELECT * FROM ordivon_harness.wake_turn_map ORDER BY wake_intent_id"
        ).fetchall()

    def retire_legacy_and_import(self, source: Path) -> dict[str, Any]:
        """Explicit quiesced cutover: PG import + SQLite writer-retirement triggers.

        Caller must have stopped external/old Browserless workers before this
        command, and must atomically roll out the PG-configured consumer afterward.
        This method never contacts a Provider or performs its effects.
        """
        source = Path(source)
        if not source.is_file():
            raise WakeTurnConflict("legacy wake source missing")
        # This PostgreSQL commit is the admission fence. It precedes any copy
        # and prevents new PG allocations until source retirement is committed.
        self._mark_pending_before_legacy_freeze()
        db, rows = self._legacy_rows(source, write=True)
        with closing(db):
            source_committed = False
            try:
                original = self._canonical_rows(rows)
                with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
                    with pg.transaction():
                        pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        for row in original:
                            pg.execute(
                                "INSERT INTO ordivon_harness.wake_turn_map "
                                "(wake_intent_id,campaign_ref,agent_id,prompt_digest,"
                                "turn_request_id,created_at_ms) VALUES(%s,%s,%s,%s,%s,%s) "
                                "ON CONFLICT (wake_intent_id) DO NOTHING",
                                row,
                            )
                        observed = self._canonical_rows(self._postgres_rows(pg))
                        if observed != original:
                            raise WakeTurnConflict(
                                "PG migration has missing, divergent, or additional wake identities"
                            )
                        # Install a durable SQLite fail-closed fence while its
                        # single writer lock is still held.
                        for operation in ("INSERT", "UPDATE", "DELETE"):
                            name = f"wake_turn_pg_retired_{operation.lower()}"
                            sql = (
                                f"CREATE TRIGGER {name} "
                                f"BEFORE {operation} ON wake_turn_map BEGIN "
                                "SELECT RAISE(ABORT,'wake mapping retired to PostgreSQL'); END"
                            )
                            existing = db.execute(
                                "SELECT sql FROM sqlite_master "
                                "WHERE type='trigger' AND name=?", (name,)
                            ).fetchone()
                            if existing is not None and existing["sql"] != sql:
                                raise WakeTurnConflict("legacy wake retirement trigger has drifted")
                            if existing is None:
                                db.execute(sql)
                db.execute("COMMIT")
                source_committed = True
                # A PostgreSQL copy is not authority until the legacy source
                # has sealed durably and the source/PG identity readback agrees.
                self.assert_legacy_sealed(source)
                self._certify_cutover_after_source_commit()
                digest = "sha256:" + hashlib.sha256(
                    json.dumps(original, ensure_ascii=False, separators=(",", ":")).encode()
                ).hexdigest()
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.wake-turn-pg-cutover",
                    "migrationStanding": "source-sealed",
                    "sourceRows": len(original),
                    "postgresRows": len(observed),
                    "identityDigest": digest,
                }
            except Exception:
                if not source_committed:
                    db.execute("ROLLBACK")
                raise

    def assert_legacy_sealed(self, source: Path, *, fresh_bootstrap: bool = False) -> None:
        """Check source identity continuity, not merely presence of a cutover flag.

        PostgreSQL may contain new rows after cutover. All frozen source
        identities must remain identical and the retired source may never
        permit new INSERT/UPDATE/DELETE traffic.
        """
        source = Path(source)
        if not source.exists():
            if fresh_bootstrap:
                return  # Explicitly qualified new install with no legacy source.
            raise WakeTurnConflict("legacy wake source is absent; fresh PG bootstrap not qualified")
        db, rows = self._legacy_rows(source)
        with closing(db):
            actual = {
                row[0]: row[1] for row in db.execute(
                    "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
                )
            }
            for operation in ("INSERT", "UPDATE", "DELETE"):
                name = f"wake_turn_pg_retired_{operation.lower()}"
                sql = (
                    f"CREATE TRIGGER {name} "
                    f"BEFORE {operation} ON wake_turn_map BEGIN "
                    "SELECT RAISE(ABORT,'wake mapping retired to PostgreSQL'); END"
                )
                if actual.get(name) != sql:
                    raise WakeTurnConflict("legacy wake writer retirement fence is missing or altered")
        canonical = self._canonical_rows(rows)
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            by_id = {x["wake_intent_id"]: x for x in self._postgres_rows(pg)}
        for old in canonical:
            pg_row = by_id.get(old[0])
            if pg_row is None or self._canonical_rows([pg_row]) != [old]:
                raise WakeTurnConflict("legacy wake identity differs from PostgreSQL")

    def get(self, wake_intent_id: str) -> dict[str, Any] | None:
        wake_intent_id = _text(wake_intent_id, "wakeIntentId")
        with psycopg.connect(self.dsn, row_factory=dict_row) as db:
            self._admit_cutover_state(db)
            row = db.execute(
                "SELECT * FROM ordivon_harness.wake_turn_map WHERE wake_intent_id=%s",
                (wake_intent_id,),
            ).fetchone()
            if row is None:
                return None
            try:
                require_uuid7(row["turn_request_id"], "turnRequestId")
            except (ValueError, TypeError) as error:
                raise WakeTurnConflict("PostgreSQL wake receipt identity invalid") from error
            return self._receipt(row, "existing")

    def allocate(
        self,
        *,
        campaign_ref: str,
        agent_id: str,
        wake_intent_id: str,
        prompt_digest: str,
    ) -> dict[str, Any]:
        campaign_ref = _digest(campaign_ref, "campaignRef")
        agent_id = _text(agent_id, "agentId", max_bytes=128)
        wake_intent_id = _text(wake_intent_id, "wakeIntentId")
        prompt_digest = _digest(prompt_digest, "promptDigest")
        semantic = (campaign_ref, agent_id, prompt_digest)
        for attempt in range(4):
            try:
                with psycopg.connect(self.dsn, row_factory=dict_row) as db:
                    with db.transaction():
                        db.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        self._admit_cutover_state(db)
                        existing = db.execute(
                            "SELECT * FROM ordivon_harness.wake_turn_map "
                            "WHERE wake_intent_id=%s",
                            (wake_intent_id,),
                        ).fetchone()
                        if existing is not None:
                            observed = tuple(
                                existing[k] for k in ("campaign_ref", "agent_id", "prompt_digest")
                            )
                            if observed != semantic:
                                raise WakeTurnConflict("wake intent identity changed semantics")
                            try:
                                require_uuid7(existing["turn_request_id"], "turnRequestId")
                            except (TypeError, ValueError) as error:
                                raise WakeTurnConflict("wake turn replay receipt invalid") from error
                            return self._receipt(existing, "existing")
                        turn_request_id = require_uuid7(self._uuid7_factory(), "turnRequestId")
                        now = int(self._now_ms())
                        db.execute(
                            "INSERT INTO ordivon_harness.wake_turn_map "
                            "(wake_intent_id,campaign_ref,agent_id,prompt_digest,"
                            "turn_request_id,created_at_ms) VALUES(%s,%s,%s,%s,%s,%s) "
                            "ON CONFLICT (wake_intent_id) DO NOTHING",
                            (wake_intent_id, *semantic, turn_request_id, now),
                        )
                        row = db.execute(
                            "SELECT * FROM ordivon_harness.wake_turn_map "
                            "WHERE wake_intent_id=%s",
                            (wake_intent_id,),
                        ).fetchone()
                        if row is None:
                            raise WakeTurnConflict("PostgreSQL wake durable receipt missing")
                        observed = tuple(row[k] for k in ("campaign_ref", "agent_id", "prompt_digest"))
                        if observed != semantic:
                            raise WakeTurnConflict("wake intent identity changed semantics")
                        try:
                            require_uuid7(row["turn_request_id"], "turnRequestId")
                        except (ValueError, TypeError) as error:
                            raise WakeTurnConflict("PostgreSQL wake durable receipt invalid") from error
                        disposition = "created" if row["turn_request_id"] == turn_request_id else "existing"
                        if disposition == "created" and row["created_at_ms"] != now:
                            raise WakeTurnConflict("PostgreSQL wake receipt time changed")
                        return self._receipt(row, disposition)
            except psycopg.errors.SerializationFailure as error:
                if attempt == 3:
                    raise WakeTurnConflict("PostgreSQL wake serializable retry exhausted") from error
            except psycopg.errors.UniqueViolation as error:
                raise WakeTurnConflict("PostgreSQL wake turn identity collision") from error
        raise AssertionError("unreachable")
