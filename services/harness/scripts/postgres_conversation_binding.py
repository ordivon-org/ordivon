#!/usr/bin/env python3
"""Native PostgreSQL role-binding Owner, with explicit one-way legacy cutover.

The SQLite binding is an input to a one-time migration, not a second write
authority. Browserless consumers must qualify the old source as SEALED before
they read or admit any PostgreSQL binding; no implicit fresh database fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from contextlib import closing
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

try:
    from sqlite_conversation_binding import (
        ConversationBindingConflict,
        SQLiteConversationBindingStore,
        _canonical_digest,
        _text,
    )
except ModuleNotFoundError:
    from scripts.sqlite_conversation_binding import (
        ConversationBindingConflict,
        SQLiteConversationBindingStore,
        _canonical_digest,
        _text,
    )

_COLUMNS = (
    "campaign_ref",
    "agent_id",
    "provider_resource",
    "session_id",
    "evidence_digest",
    "request_id",
    "binding_digest",
    "created_at_ms",
)
_SCHEMA_LOCK = int.from_bytes(
    hashlib.sha256(b"ordivon:harness:wake-turn-pg-schema:v1").digest()[:8],
    "big",
    signed=True,
)


class PostgresConversationBindingStore:
    """Exactly one durable provider session per campaign role, on PostgreSQL."""

    def __init__(
        self,
        dsn: str,
        *,
        legacy_source: Path,
        fresh_bootstrap: bool = False,
    ) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("conversation binding PostgreSQL requires an explicit DSN")
        self.dsn = dsn
        self.legacy_source = Path(legacy_source)
        self.fresh_bootstrap = fresh_bootstrap
        # Coordinate schema creation with the already-installed PG wake Owner.
        with psycopg.connect(dsn) as pg:
            pg.execute("SELECT pg_advisory_xact_lock(%s)", (_SCHEMA_LOCK,))
            pg.execute("CREATE SCHEMA IF NOT EXISTS ordivon_harness")
            pg.execute(
                """
                CREATE TABLE IF NOT EXISTS ordivon_harness.conversation_bindings(
                    campaign_ref TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    provider_resource TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    evidence_digest TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    binding_digest TEXT NOT NULL,
                    created_at_ms BIGINT NOT NULL CHECK(created_at_ms >= 0),
                    PRIMARY KEY(campaign_ref, agent_id),
                    CONSTRAINT cft_binding_digests CHECK (
                        campaign_ref ~ '^sha256:[0-9a-f]{64}$'
                        AND evidence_digest ~ '^sha256:[0-9a-f]{64}$'
                        AND binding_digest ~ '^sha256:[0-9a-f]{64}$'
                    ),
                    CONSTRAINT cft_binding_uuid7 CHECK (
                        session_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                    )
                )
                """
            )
            # CREATE TABLE IF NOT EXISTS is not a source/proof certificate.
            # A conflicting table with matching columns but absent native
            # keys/checks can falsely admit non-atomic identities.
            physical = pg.execute(
                "SELECT column_name,data_type,is_nullable FROM information_schema.columns "
                "WHERE table_schema='ordivon_harness' AND table_name='conversation_bindings' "
                "ORDER BY ordinal_position"
            ).fetchall()
            expected = [
                (name, "bigint" if name == "created_at_ms" else "text", "NO")
                for name in _COLUMNS
            ]
            if physical != expected:
                raise ConversationBindingConflict("PostgreSQL binding schema shape differs")
            constraints = pg.execute(
                "SELECT contype,pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conrelid='ordivon_harness.conversation_bindings'::regclass"
            ).fetchall()
            if not (
                any(t == "p" and "(campaign_ref, agent_id)" in body for t, body in constraints)
                and any(t == "u" and "(request_id)" in body for t, body in constraints)
                and any(t == "c" and "created_at_ms" in body for t, body in constraints)
                and any(t == "c" and "sha256:" in body for t, body in constraints)
                and any(t == "c" and "session_id" in body for t, body in constraints)
            ):
                raise ConversationBindingConflict("PostgreSQL binding native uniqueness/check law absent")

    @staticmethod
    def _canonical_rows(rows: list[dict[str, Any]]) -> list[tuple[Any, ...]]:
        canonical: list[tuple[Any, ...]] = []
        for row in rows:
            payload = SQLiteConversationBindingStore._validated_payload(
                campaign_ref=row["campaign_ref"],
                agent_id=row["agent_id"],
                provider_resource=row["provider_resource"],
                session_id=row["session_id"],
                evidence_digest=row["evidence_digest"],
                request_id=row["request_id"],
            )
            if row["binding_digest"] != _canonical_digest(payload):
                raise ConversationBindingConflict("binding digest/source identity invalid")
            timestamp = row["created_at_ms"]
            if type(timestamp) is not int or timestamp < 0 or timestamp > (2**63 - 1):
                raise ConversationBindingConflict("binding timestamp not PostgreSQL BIGINT")
            canonical.append(tuple(row[col] for col in _COLUMNS))
        return sorted(canonical)

    @staticmethod
    def _receipt(row: dict[str, Any]) -> dict[str, Any]:
        return SQLiteConversationBindingStore._receipt(row)

    @staticmethod
    def _legacy(path: Path, *, write: bool = False):
        if not path.is_file():
            raise ConversationBindingConflict("legacy binding source missing")
        legacy = object.__new__(SQLiteConversationBindingStore)
        legacy.path = path
        db = legacy._connect(read_only=not write)
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            # Existing table must actually exist; do not fabricate a fresh
            # source to permit an ambiguous cutover.
            rows = [dict(row) for row in db.execute("SELECT * FROM conversation_bindings")]
            return db, rows
        except BaseException:
            db.close()
            raise

    @staticmethod
    def _fence_sql(operation: str) -> str:
        return (
            f"CREATE TRIGGER binding_pg_retired_{operation.lower()} "
            f"BEFORE {operation} ON conversation_bindings BEGIN "
            "SELECT RAISE(ABORT,'conversation binding retired to PostgreSQL'); END"
        )

    def _rows(self, pg: psycopg.Connection) -> list[dict[str, Any]]:
        return pg.execute(
            "SELECT * FROM ordivon_harness.conversation_bindings ORDER BY campaign_ref,agent_id"
        ).fetchall()

    def retire_legacy_and_import(self, source: Path) -> dict[str, Any]:
        """One-shot migration, under SQLite writer lock and PG transaction.

        Caller must quiesce and stop old writers before this method; reopening
        them after cutover is rejected by the installed legacy retirement fence.
        """
        if Path(source) != self.legacy_source:
            raise ConversationBindingConflict(
                "PG migration source differs from admission-bound legacy path"
            )
        legacy, old_rows = self._legacy(self.legacy_source, write=True)
        with closing(legacy):
            try:
                expected = self._canonical_rows(old_rows)
                observed_fences = {
                    name: sql
                    for name, sql in legacy.execute(
                        "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
                    )
                }
                fence_states = [
                    observed_fences.get(f"binding_pg_retired_{op.lower()}") == self._fence_sql(op)
                    for op in ("INSERT", "UPDATE", "DELETE")
                ]
                if any(fence_states) and not all(fence_states):
                    raise ConversationBindingConflict("partial legacy binding retirement fence")
                already_sealed = all(fence_states)
                with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
                    with pg.transaction():
                        pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        for row in expected:
                            pg.execute(
                                "INSERT INTO ordivon_harness.conversation_bindings "
                                "(campaign_ref,agent_id,provider_resource,session_id,"
                                "evidence_digest,request_id,binding_digest,created_at_ms) "
                                "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) "
                                "ON CONFLICT (campaign_ref,agent_id) DO NOTHING",
                                row,
                            )
                        observed = self._canonical_rows(self._rows(pg))
                        if already_sealed:
                            # PostgreSQL is the sole writer after retirement:
                            # new PG bindings must not invalidate replay of a
                            # previously completed old-source cutover.
                            old_keys = {(row[0], row[1]) for row in expected}
                            frozen = [row for row in observed if (row[0], row[1]) in old_keys]
                            matches = frozen == expected
                        else:
                            # The very first cutover cannot silently admit
                            # PG-only rows or a conflicting duplicate source.
                            matches = observed == expected
                        if not matches:
                            raise ConversationBindingConflict(
                                "PostgreSQL cutover differs from immutable legacy role bindings"
                            )
                        for operation in ("INSERT", "UPDATE", "DELETE"):
                            name = f"binding_pg_retired_{operation.lower()}"
                            sql = self._fence_sql(operation)
                            present = legacy.execute(
                                "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
                                (name,),
                            ).fetchone()
                            if present is not None and present["sql"] != sql:
                                raise ConversationBindingConflict(
                                    "legacy binding retirement fence changed"
                                )
                            if present is None:
                                legacy.execute(sql)
                legacy.execute("COMMIT")
                return {
                    "schemaVersion": 1,
                    "kind": "ordivon.conversation-binding-pg-cutover",
                    "standing": "source-sealed",
                    "sourceRows": len(expected),
                    "postgresRows": len(observed),
                    "identityDigest": "sha256:"
                    + hashlib.sha256(
                        json.dumps(expected, ensure_ascii=False, separators=(",", ":")).encode()
                    ).hexdigest(),
                }
            except BaseException:
                legacy.execute("ROLLBACK")
                raise

    def assert_legacy_sealed(self, source: Path, *, fresh_bootstrap: bool = False) -> None:
        source = Path(source)
        if not source.exists():
            if fresh_bootstrap:
                return
            raise ConversationBindingConflict(
                "legacy role binding source absent; no qualified fresh PG bootstrap"
            )
        old, rows = self._legacy(source)
        with closing(old):
            names = {
                name: sql
                for name, sql in old.execute(
                    "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
                )
            }
            for operation in ("INSERT", "UPDATE", "DELETE"):
                name = f"binding_pg_retired_{operation.lower()}"
                if names.get(name) != self._fence_sql(operation):
                    raise ConversationBindingConflict(
                        "legacy conversation binding writer is not retired"
                    )
        expected = self._canonical_rows(rows)
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            actual = {(row["campaign_ref"], row["agent_id"]): row for row in self._rows(pg)}
        # Only source rows are immutable; PG may admit more rows after cutover.
        for original in expected:
            row = actual.get((original[0], original[1]))
            if row is None or self._canonical_rows([row]) != [original]:
                raise ConversationBindingConflict(
                    "sealed legacy identity absent or altered in PostgreSQL"
                )

    def get_binding(self, campaign_ref: str, agent_id: str) -> dict[str, Any] | None:
        self.assert_legacy_sealed(self.legacy_source, fresh_bootstrap=self.fresh_bootstrap)
        campaign_ref = _text(campaign_ref, "campaignRef")
        agent_id = _text(agent_id, "agentId", max_bytes=128)
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            row = pg.execute(
                "SELECT * FROM ordivon_harness.conversation_bindings "
                "WHERE campaign_ref=%s AND agent_id=%s",
                (campaign_ref, agent_id),
            ).fetchone()
        if row is None:
            return None
        self._canonical_rows([row])
        return self._receipt(row)

    def adopt_binding(
        self,
        *,
        campaign_ref: str,
        agent_id: str,
        provider_resource: str,
        session_id: str,
        evidence_digest: str,
        request_id: str,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        self.assert_legacy_sealed(self.legacy_source, fresh_bootstrap=self.fresh_bootstrap)
        payload = SQLiteConversationBindingStore._validated_payload(
            campaign_ref=campaign_ref,
            agent_id=agent_id,
            provider_resource=provider_resource,
            session_id=session_id,
            evidence_digest=evidence_digest,
            request_id=request_id,
        )
        digest = _canonical_digest(payload)
        now = int(time.time() * 1000) if now_ms is None else now_ms
        if type(now) is not int or not 0 <= now <= (2**63 - 1):
            raise ValueError("createdAtMs outside PostgreSQL BIGINT")
        for retry in range(4):
            try:
                with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
                    with pg.transaction():
                        pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        previous = pg.execute(
                            "SELECT * FROM ordivon_harness.conversation_bindings "
                            "WHERE request_id=%s",
                            (payload["requestId"],),
                        ).fetchone()
                        if previous is not None:
                            self._canonical_rows([previous])
                            if (
                                any(
                                    previous[col] != payload[name]
                                    for col, name in (
                                        ("campaign_ref", "campaignRef"),
                                        ("agent_id", "agentId"),
                                        ("provider_resource", "providerResource"),
                                        ("session_id", "sessionId"),
                                        ("evidence_digest", "evidenceDigest"),
                                        ("request_id", "requestId"),
                                    )
                                )
                                or previous["binding_digest"] != digest
                            ):
                                raise ConversationBindingConflict(
                                    "same adoption request changed immutable role binding"
                                )
                            return self._receipt(previous)
                        pg.execute(
                            "INSERT INTO ordivon_harness.conversation_bindings "
                            "(campaign_ref,agent_id,provider_resource,session_id,"
                            "evidence_digest,request_id,binding_digest,created_at_ms) "
                            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s) "
                            "ON CONFLICT (campaign_ref,agent_id) DO NOTHING",
                            (
                                payload["campaignRef"],
                                payload["agentId"],
                                payload["providerResource"],
                                payload["sessionId"],
                                payload["evidenceDigest"],
                                payload["requestId"],
                                digest,
                                now,
                            ),
                        )
                        row = pg.execute(
                            "SELECT * FROM ordivon_harness.conversation_bindings "
                            "WHERE campaign_ref=%s AND agent_id=%s",
                            (payload["campaignRef"], payload["agentId"]),
                        ).fetchone()
                        if row is None:
                            raise ConversationBindingConflict("PG post-write receipt missing")
                        self._canonical_rows([row])
                        if (
                            any(
                                row[col] != payload[name]
                                for col, name in (
                                    ("campaign_ref", "campaignRef"),
                                    ("agent_id", "agentId"),
                                    ("provider_resource", "providerResource"),
                                    ("session_id", "sessionId"),
                                    ("evidence_digest", "evidenceDigest"),
                                    ("request_id", "requestId"),
                                )
                            )
                            or row["binding_digest"] != digest
                        ):
                            raise ConversationBindingConflict(
                                "campaign role bound to different conversation"
                            )
                        if row["created_at_ms"] != now:
                            raise ConversationBindingConflict(
                                "campaign role already has existing binding"
                            )
                        return self._receipt(row)
            except psycopg.errors.SerializationFailure as error:
                if retry == 3:
                    raise ConversationBindingConflict("PG serializable retry exhausted") from error
            except psycopg.errors.UniqueViolation as error:
                raise ConversationBindingConflict(
                    "PG request identity used by another role"
                ) from error
        raise AssertionError("unreachable")

    def resolve_binding(self, campaign_ref: str, agent_id: str) -> dict[str, Any] | None:
        return self.get_binding(campaign_ref, agent_id)


def main() -> int:
    """One-shot operator cutover; never selects production data implicitly."""
    parser = argparse.ArgumentParser(
        description="Import and retire one legacy role-binding authority"
    )
    parser.add_argument("--legacy-ledger", type=Path, required=True)
    parser.add_argument("--dsn-env", default="ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN")
    parser.add_argument(
        "--confirm-old-writers-quiesced",
        action="store_true",
        required=True,
        help="Operator independently verified all old Browserless role-binding writers are stopped",
    )
    args = parser.parse_args()
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        parser.error("explicit PG DSN environment variable is missing")
    owner = PostgresConversationBindingStore(dsn, legacy_source=args.legacy_ledger)
    receipt = owner.retire_legacy_and_import(args.legacy_ledger)
    owner.assert_legacy_sealed(args.legacy_ledger)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
