#!/usr/bin/env python3
"""PostgreSQL-native Harness conversation binding, with explicit legacy retirement.

Never silently switch an extant SQLite consumer to an empty PostgreSQL store.
This module does not call a Provider, browser or external effect.
"""
from __future__ import annotations

import hashlib
import json
import time
from contextlib import closing
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

try:
    from sqlite_conversation_binding import (
        SQLiteConversationBindingStore, ConversationBindingConflict, _canonical_digest, _text,
    )
except ModuleNotFoundError:
    from scripts.sqlite_conversation_binding import (
        SQLiteConversationBindingStore, ConversationBindingConflict, _canonical_digest, _text,
    )

_TABLE = "ordivon_harness.conversation_bindings"
_NAMES = (
    "campaign_ref", "agent_id", "provider_resource", "session_id",
    "evidence_digest", "request_id", "binding_digest", "created_at_ms",
)
_RETIRE_OPERATIONS = ("INSERT", "UPDATE", "DELETE")


def _fence_statement(operation: str) -> tuple[str, str]:
    name = f"conversation_pg_retired_{operation.lower()}"
    return name, (
        f"CREATE TRIGGER {name} BEFORE {operation} ON conversation_bindings BEGIN "
        "SELECT RAISE(ABORT,'conversation binding retired to PostgreSQL'); END"
    )


class PostgresConversationBindingStore:
    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("PostgreSQL conversation owner requires explicit DSN")
        self.dsn = dsn
        with psycopg.connect(self.dsn) as db:
            # One PG schema bootstrap serialization key is shared with the
            # existing PostgresWakeTurnMap; concurrent first owners must not
            # race CREATE SCHEMA even when their TABLE names differ.
            schema_lock = int.from_bytes(
                hashlib.sha256(b"ordivon:harness:wake-turn-pg-schema:v1").digest()[:8],
                "big", signed=True,
            )
            db.execute("SELECT pg_advisory_xact_lock(%s)", (schema_lock,))
            db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_harness")
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS ordivon_harness.conversation_bindings (
                    campaign_ref TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    provider_resource TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    evidence_digest TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    binding_digest TEXT NOT NULL,
                    created_at_ms BIGINT NOT NULL CHECK (created_at_ms >= 0),
                    PRIMARY KEY(campaign_ref,agent_id),
                    CONSTRAINT conversation_binding_source_digest CHECK (
                        campaign_ref ~ '^sha256:[0-9a-f]{64}$'
                        AND evidence_digest ~ '^sha256:[0-9a-f]{64}$'
                        AND binding_digest ~ '^sha256:[0-9a-f]{64}$'
                    ),
                    CONSTRAINT conversation_binding_session_v7 CHECK (
                        session_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                    )
                )
                """
            )
            # CREATE TABLE IF NOT EXISTS is not a certificate of table shape.
            # Reject pre-existing lookalikes before any consumer writes.
            physical = db.execute(
                "SELECT column_name,data_type,is_nullable FROM information_schema.columns "
                "WHERE table_schema='ordivon_harness' AND table_name='conversation_bindings' "
                "ORDER BY ordinal_position"
            ).fetchall()
            expected = [
                (name, "bigint" if name == "created_at_ms" else "text", "NO")
                for name in _NAMES
            ]
            if physical != expected:
                raise ConversationBindingConflict("PostgreSQL conversation table shape differs")
            constraints = db.execute(
                "SELECT contype,pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid='ordivon_harness.conversation_bindings'::regclass"
            ).fetchall()
            if not (
                any(t == "p" and "(campaign_ref, agent_id)" in body for t, body in constraints)
                and any(t == "u" and "(request_id)" in body for t, body in constraints)
                and any(t == "c" and "created_at_ms" in body for t, body in constraints)
                and any(t == "c" and "conversation" not in body and "sha256:" in body
                        for t, body in constraints)
                and any(t == "c" and "session_id" in body for t, body in constraints)
            ):
                raise ConversationBindingConflict("PostgreSQL conversation unique/check contract missing")

    @staticmethod
    def _record(row: dict[str, Any]) -> dict[str, Any]:
        """Validate all persisted identity fields, not merely the stored digest."""
        try:
            payload = SQLiteConversationBindingStore._validated_payload(
                campaign_ref=row["campaign_ref"],
                agent_id=row["agent_id"],
                provider_resource=row["provider_resource"],
                session_id=row["session_id"],
                evidence_digest=row["evidence_digest"],
                request_id=row["request_id"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ConversationBindingConflict("PostgreSQL stored binding identity invalid") from error
        if _canonical_digest(payload) != row["binding_digest"]:
            raise ConversationBindingConflict("PostgreSQL conversation binding digest mismatch")
        if type(row["created_at_ms"]) is not int or not 0 <= row["created_at_ms"] <= 2**63 - 1:
            raise ConversationBindingConflict("PostgreSQL binding timestamp outside BIGINT")
        return SQLiteConversationBindingStore._receipt(row)

    @classmethod
    def _tuple(cls, row: dict[str, Any]) -> tuple:
        cls._record(row)
        return tuple(row[x] for x in _NAMES)

    @classmethod
    def _canonical(cls, rows: list[dict[str, Any]]) -> list[tuple]:
        return sorted(cls._tuple(x) for x in rows)

    def _all_rows(self, db: psycopg.Connection) -> list[dict[str, Any]]:
        return db.execute(f"SELECT * FROM {_TABLE} ORDER BY campaign_ref,agent_id").fetchall()

    def adopt_binding(
        self, *, campaign_ref: str, agent_id: str, provider_resource: str,
        session_id: str, evidence_digest: str, request_id: str,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        payload = SQLiteConversationBindingStore._validated_payload(
            campaign_ref=campaign_ref, agent_id=agent_id, provider_resource=provider_resource,
            session_id=session_id, evidence_digest=evidence_digest, request_id=request_id,
        )
        digest = _canonical_digest(payload)
        now = int(time.time() * 1000) if now_ms is None else now_ms
        if type(now) is not int or not 0 <= now <= 2**63 - 1:
            raise ValueError("createdAtMs outside PostgreSQL BIGINT")
        expected = (
            payload["campaignRef"], payload["agentId"], payload["providerResource"],
            payload["sessionId"], payload["evidenceDigest"], payload["requestId"], digest, now,
        )
        for attempt in range(6):
            try:
                with psycopg.connect(self.dsn, row_factory=dict_row) as db:
                    with db.transaction():
                        db.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        # Native unique arbiters, NOT SELECT-then-insert as an authority.
                        inserted = db.execute(
                            f"INSERT INTO {_TABLE} ({','.join(_NAMES)}) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) "
                            "ON CONFLICT DO NOTHING RETURNING request_id",
                            expected,
                        ).fetchone()
                        row = db.execute(
                            f"SELECT * FROM {_TABLE} WHERE request_id=%s",
                            (payload["requestId"],),
                        ).fetchone()
                        if row is None:
                            other = db.execute(
                                f"SELECT request_id FROM {_TABLE} WHERE campaign_ref=%s "
                                "AND agent_id=%s", (payload["campaignRef"], payload["agentId"]),
                            ).fetchone()
                            if other is not None:
                                raise ConversationBindingConflict(
                                    "campaign role already has an exact conversation binding"
                                )
                            raise ConversationBindingConflict(
                                "PostgreSQL conversation binding receipt missing"
                            )
                        actual = self._record(row)
                        if row["request_id"] != expected[5]:
                            raise ConversationBindingConflict("conversation binding request mismatch")
                        if tuple(row[x] for x in _NAMES[:7]) != expected[:7]:
                            raise ConversationBindingConflict(
                                "same adoption request identity changed conversation binding"
                            )
                        # Only a newly inserted row must reproduce the entire
                        # request including timestamp. Historical replay retains
                        # its old timestamp and is never silently updated.
                        if inserted is not None and tuple(row[x] for x in _NAMES) != expected:
                            raise ConversationBindingConflict(
                                "PostgreSQL newly written receipt differs before commit"
                            )
                        return actual
            except (psycopg.errors.SerializationFailure, psycopg.errors.DeadlockDetected):
                if attempt == 5:
                    raise
                time.sleep(0.007 * (attempt + 1))
        raise AssertionError("unreachable")

    def get_binding(self, campaign_ref: str, agent_id: str) -> dict[str, Any] | None:
        campaign_ref = _text(campaign_ref, "campaignRef")
        agent_id = _text(agent_id, "agentId", max_bytes=128)
        with psycopg.connect(self.dsn, row_factory=dict_row) as db:
            row = db.execute(
                f"SELECT * FROM {_TABLE} WHERE campaign_ref=%s AND agent_id=%s",
                (campaign_ref, agent_id),
            ).fetchone()
        return None if row is None else self._record(row)

    def resolve_binding(self, campaign_ref: str, agent_id: str) -> dict[str, Any] | None:
        return self.get_binding(campaign_ref, agent_id)

    @staticmethod
    def _legacy(path: Path, *, writable: bool):
        source = Path(path)
        if not source.is_file():
            raise ConversationBindingConflict("legacy conversation source absent")
        owner = object.__new__(SQLiteConversationBindingStore)
        owner.path = source
        db = owner._connect(read_only=not writable)
        try:
            if writable:
                db.execute("BEGIN IMMEDIATE")
            rows = [dict(row) for row in db.execute("SELECT * FROM conversation_bindings")]
            return db, rows
        except Exception:
            db.close()
            raise

    def retire_legacy_and_import(self, source: Path) -> dict[str, Any]:
        """Two-store migration under legacy writer lock. Requires externally quiesced workers.

        Commit PG first, then retire old writers before releasing source lock. If
        retirement commit fails after PG commit the outcome is UNKNOWN: rerun
        source qualification, never infer cutover just from PG row presence.
        """
        db, original_rows = self._legacy(source, writable=True)
        with closing(db):
            try:
                original = self._canonical(original_rows)
                with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
                    with pg.transaction():
                        pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        for row in original:
                            pg.execute(
                                f"INSERT INTO {_TABLE} ({','.join(_NAMES)}) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                                row,
                            )
                        observed = self._canonical(self._all_rows(pg))
                        if observed != original:
                            raise ConversationBindingConflict(
                                "PostgreSQL import has missing, divergent or extra binding identities"
                            )
                        for op in _RETIRE_OPERATIONS:
                            name, sql = _fence_statement(op)
                            old = db.execute(
                                "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
                                (name,),
                            ).fetchone()
                            if old is not None and old["sql"] != sql:
                                raise ConversationBindingConflict("legacy retirement fence drift")
                            if old is None:
                                db.execute(sql)
                db.execute("COMMIT")
                digest = hashlib.sha256(
                    json.dumps(original, separators=(",", ":"), ensure_ascii=False).encode()
                ).hexdigest()
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.conversation-pg-cutover",
                    "migrationStanding": "source-sealed",
                    "sourceRows": len(original),
                    "postgresRows": len(observed),
                    "identityDigest": "sha256:" + digest,
                }
            except Exception:
                try:
                    db.execute("ROLLBACK")
                except Exception:
                    pass
                raise

    def assert_legacy_sealed(self, source: Path, *, fresh_bootstrap: bool = False) -> None:
        path = Path(source)
        if not path.is_file():
            if fresh_bootstrap:
                return
            raise ConversationBindingConflict("legacy conversation source absent")
        db, rows = self._legacy(path, writable=False)
        with closing(db):
            current = dict(
                db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'")
            )
            for operation in _RETIRE_OPERATIONS:
                name, sql = _fence_statement(operation)
                if current.get(name) != sql:
                    raise ConversationBindingConflict("legacy conversation writer not sealed")
        original = self._canonical(rows)
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            observed = {x[:2]: x for x in self._canonical(self._all_rows(pg))}
        if any(observed.get(x[:2]) != x for x in original):
            raise ConversationBindingConflict("legacy PostgreSQL identity drift")
