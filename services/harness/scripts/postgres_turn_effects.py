#!/usr/bin/env python3
"""PostgreSQL-native durable Browserless turn-effect authority.

The migration path stages legacy evidence but intentionally cannot activate a
source-backed cutover: provider subprocess quiescence must first be proven.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import json
import time
from contextlib import closing
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

try:
    from sqlite_wake_turn_map import SQLiteWakeTurnMap
except ModuleNotFoundError:
    from scripts.sqlite_wake_turn_map import SQLiteWakeTurnMap


class TurnEffectConflict(RuntimeError):
    pass


class PostgresTurnEffects:
    _LOCK_KEY = 57163519194019

    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("PostgreSQL turn effect authority requires a DSN")
        self.dsn = dsn
        with psycopg.connect(dsn) as db:
            db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_harness")
            db.execute("""
                CREATE TABLE IF NOT EXISTS ordivon_harness.turn_effects(
                    turn_request_id TEXT PRIMARY KEY,
                    prompt_digest TEXT NOT NULL,
                    target_coordinate TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('UNKNOWN','COMPLETED')),
                    receipt_json TEXT,
                    updated_at_ms BIGINT NOT NULL CHECK (updated_at_ms >= 0)
                )""")
            db.execute("""
                CREATE TABLE IF NOT EXISTS ordivon_harness.turn_effect_cutover(
                    cutover_id TEXT PRIMARY KEY CHECK(cutover_id='legacy'),
                    state TEXT NOT NULL CHECK(state IN ('PENDING','ACTIVE')),
                    source_digest TEXT
                )""")

    @staticmethod
    def _validate_row(row: tuple[Any, ...]) -> tuple[str, str, str, str, str | None, int]:
        key, prompt, target, state, receipt, updated = row
        if not all(isinstance(x, str) and x for x in (key, prompt, target)):
            raise TurnEffectConflict("turn effect identity missing")
        if state not in ("UNKNOWN", "COMPLETED"):
            raise TurnEffectConflict("unsupported legacy effect state")
        if receipt is not None:
            if not isinstance(receipt, str):
                raise TurnEffectConflict("effect receipt is not JSON text")
            try:
                json.loads(receipt)
            except (ValueError, TypeError) as error:
                raise TurnEffectConflict("effect receipt JSON is invalid") from error
        if type(updated) is not int or updated < 0:
            raise TurnEffectConflict("effect timestamp invalid")
        return (key, prompt, target, state, receipt, updated)

    @staticmethod
    def _legacy_rows(source: Path) -> list[tuple[str, str, str, str, str | None, int]]:
        source = Path(source)
        if not source.is_file() or source.is_symlink():
            raise TurnEffectConflict("exact legacy effects source missing")
        # Reuse the qualified legacy source-reader capability. Introducing a
        # second direct SQLite API would increase source debt before PG cutover.
        legacy = object.__new__(SQLiteWakeTurnMap)
        legacy.path = source
        with closing(legacy._connect(read_only=True)) as db:
            rows = db.execute(
                "SELECT turn_request_id,prompt_digest,target_coordinate,state,"
                "receipt_json,updated_at_ms FROM turn_effects ORDER BY turn_request_id"
            ).fetchall()
        return sorted(PostgresTurnEffects._validate_row(tuple(r)) for r in rows)

    @staticmethod
    def _digest(rows: list[tuple[Any, ...]]) -> str:
        raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    def stage_legacy(self, source: Path) -> dict[str, Any]:
        """Copy and verify source in PG; deliberately keep PENDING and no SEND."""
        source = Path(source)
        rows = self._legacy_rows(source)
        digest = self._digest(rows)
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            with pg.transaction():
                pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                pg.execute("SELECT pg_advisory_xact_lock(%s)", (self._LOCK_KEY,))
                marker = pg.execute(
                    "SELECT state,source_digest FROM ordivon_harness.turn_effect_cutover "
                    "WHERE cutover_id='legacy' FOR UPDATE"
                ).fetchone()
                if marker is not None and marker["state"] != "PENDING":
                    raise TurnEffectConflict("active PG effect source cannot be restaged")
                if marker is None:
                    pg.execute(
                        "INSERT INTO ordivon_harness.turn_effect_cutover VALUES "
                        "('legacy','PENDING',%s)",
                        (digest,),
                    )
                elif marker["source_digest"] != digest:
                    raise TurnEffectConflict("legacy effect source changed after staging")
                for row in rows:
                    pg.execute(
                        "INSERT INTO ordivon_harness.turn_effects "
                        "(turn_request_id,prompt_digest,target_coordinate,state,"
                        "receipt_json,updated_at_ms) VALUES(%s,%s,%s,%s,%s,%s) "
                        "ON CONFLICT(turn_request_id) DO NOTHING",
                        row,
                    )
                names = (
                    "turn_request_id",
                    "prompt_digest",
                    "target_coordinate",
                    "state",
                    "receipt_json",
                    "updated_at_ms",
                )
                actual = [
                    self._validate_row(tuple(r[k] for k in names))
                    for r in pg.execute(
                        "SELECT turn_request_id,prompt_digest,target_coordinate,state,"
                        "receipt_json,updated_at_ms FROM ordivon_harness.turn_effects "
                        "ORDER BY turn_request_id"
                    ).fetchall()
                ]
                if actual != rows:
                    raise TurnEffectConflict("PG staged effect data differs from source")
        if self._legacy_rows(source) != rows:
            raise TurnEffectConflict("legacy effect source changed during staging")
        return {"standing": "PENDING", "rows": len(rows), "sourceDigest": digest}

    @staticmethod
    def _retirement_sql(operation: str) -> str:
        """Exact source writer-denial witness; old data are migration inputs only."""
        return (
            f"CREATE TRIGGER turn_effect_pg_retired_{operation.lower()} "
            f"BEFORE {operation} ON turn_effects BEGIN "
            "SELECT RAISE(ABORT,'turn effects retired to PostgreSQL'); END"
        )

    def activate_staged_legacy(
        self, source: Path, *, old_writers_quiesced: bool = False
    ) -> dict[str, Any]:
        """Promote source-backed PG only after quiescence, parity, and writer retirement.

        First call stage_legacy(source). The caller must independently stop all
        old provider workers (including in-flight SENDs). A Boolean declaration
        is not independent process evidence. A crash after sealing the old source
        but before PG ACTIVE leaves PG PENDING and is safely replayable here.
        No old database is repaired or made into a long-lived secondary owner.
        """
        if not old_writers_quiesced:
            raise TurnEffectConflict("old turn-effect writers must be quiesced before cutover")
        source = Path(source)
        if not source.is_file() or source.is_symlink():
            raise TurnEffectConflict("exact legacy effects source missing")
        legacy = object.__new__(SQLiteWakeTurnMap)
        legacy.path = source
        db = legacy._connect(read_only=False)
        source_committed = False
        with closing(db):
            db.execute("BEGIN IMMEDIATE")
            try:
                columns = (
                    "turn_request_id",
                    "prompt_digest",
                    "target_coordinate",
                    "state",
                    "receipt_json",
                    "updated_at_ms",
                )
                expected = sorted(
                    self._validate_row(tuple(row))
                    for row in db.execute(
                        "SELECT turn_request_id,prompt_digest,target_coordinate,"
                        "state,receipt_json,updated_at_ms FROM turn_effects "
                        "ORDER BY turn_request_id"
                    ).fetchall()
                )
                digest = self._digest(expected)
                existing_triggers = {
                    name: sql
                    for name, sql in db.execute(
                        "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
                    ).fetchall()
                }
                names = [
                    f"turn_effect_pg_retired_{op.lower()}" for op in ("INSERT", "UPDATE", "DELETE")
                ]
                present = [
                    existing_triggers.get(name) == self._retirement_sql(op)
                    for name, op in zip(names, ("INSERT", "UPDATE", "DELETE"))
                ]
                if any(name in existing_triggers and not ok for name, ok in zip(names, present)):
                    raise TurnEffectConflict("legacy effect retirement barrier has drifted")
                if any(present) and not all(present):
                    raise TurnEffectConflict("legacy effect source has partial retirement barrier")
                sealed_before = all(present)
                with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
                    with pg.transaction():
                        pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        pg.execute("SELECT pg_advisory_xact_lock(%s)", (self._LOCK_KEY,))
                        marker = pg.execute(
                            "SELECT state,source_digest FROM ordivon_harness.turn_effect_cutover "
                            "WHERE cutover_id='legacy' FOR UPDATE"
                        ).fetchone()
                        if marker is None or marker["source_digest"] != digest:
                            raise TurnEffectConflict(
                                "staged effect source changed or was not staged"
                            )
                        if marker["state"] not in ("PENDING", "ACTIVE"):
                            raise TurnEffectConflict("unsupported PG effect promotion standing")
                        if marker["state"] == "ACTIVE" and not sealed_before:
                            raise TurnEffectConflict(
                                "ACTIVE PG effects lack exact legacy source seal"
                            )
                        actual = sorted(
                            self._validate_row(tuple(row[col] for col in columns))
                            for row in pg.execute(
                                "SELECT turn_request_id,prompt_digest,target_coordinate,"
                                "state,receipt_json,updated_at_ms FROM ordivon_harness.turn_effects "
                                "ORDER BY turn_request_id"
                            ).fetchall()
                        )
                        if marker["state"] == "ACTIVE":
                            # New PG-only identities may be written after activation.
                            old_ids = {row[0] for row in expected}
                            actual = [row for row in actual if row[0] in old_ids]
                        if actual != expected:
                            raise TurnEffectConflict("PostgreSQL staged effects differ from source")
                        if not sealed_before:
                            for op, name in zip(("INSERT", "UPDATE", "DELETE"), names):
                                db.execute(self._retirement_sql(op))
                        db.execute("COMMIT")
                        source_committed = True
                        # A completed source retirement is required before PG's
                        # admission fence changes; failure preserves PENDING.
                        if self._legacy_rows(source) != expected:
                            raise TurnEffectConflict("retired legacy effect source changed")
                        with closing(legacy._connect(read_only=True)) as sealed_db:
                            observed = dict(
                                sealed_db.execute(
                                    "SELECT name,sql FROM sqlite_master WHERE type='trigger'"
                                ).fetchall()
                            )
                            if any(
                                observed.get(name) != self._retirement_sql(op)
                                for name, op in zip(names, ("INSERT", "UPDATE", "DELETE"))
                            ):
                                raise TurnEffectConflict(
                                    "legacy turn effect source retirement not durable"
                                )
                        if marker["state"] == "PENDING":
                            pg.execute(
                                "UPDATE ordivon_harness.turn_effect_cutover SET state='ACTIVE' "
                                "WHERE cutover_id='legacy' AND state='PENDING'"
                            )
                return {"standing": "ACTIVE", "rows": len(expected), "sourceDigest": digest}
            except BaseException:
                if not source_committed:
                    db.execute("ROLLBACK")
                raise

    def activate_empty_fresh(self, legacy_source: Path) -> None:
        """Fresh-only PG bootstrap; refuses to mislabel an existing SQLite authority."""
        if Path(legacy_source).exists():
            raise TurnEffectConflict("legacy source exists: explicit cutover not certified")
        with psycopg.connect(self.dsn) as db:
            with db.transaction():
                db.execute("SELECT pg_advisory_xact_lock(%s)", (self._LOCK_KEY,))
                if db.execute("SELECT 1 FROM ordivon_harness.turn_effects LIMIT 1").fetchone():
                    raise TurnEffectConflict("PG effect store already contains historical data")
                db.execute(
                    "INSERT INTO ordivon_harness.turn_effect_cutover "
                    "(cutover_id,state,source_digest) VALUES('legacy','ACTIVE',NULL) "
                    "ON CONFLICT(cutover_id) DO NOTHING"
                )
                marker = db.execute(
                    "SELECT state,source_digest FROM ordivon_harness.turn_effect_cutover "
                    "WHERE cutover_id='legacy'"
                ).fetchone()
                if marker != ("ACTIVE", None):
                    raise TurnEffectConflict("PG cutover already pending or sealed")

    def _require_active(self, pg: psycopg.Connection) -> None:
        pg.execute("SELECT pg_advisory_xact_lock_shared(%s)", (self._LOCK_KEY,))
        marker = pg.execute(
            "SELECT state FROM ordivon_harness.turn_effect_cutover WHERE cutover_id='legacy'"
        ).fetchone()
        if marker is None or marker["state"] != "ACTIVE":
            raise TurnEffectConflict("PG effects cutover PENDING or not certified")

    def get(self, turn_id: str) -> dict[str, Any] | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            with pg.transaction():
                self._require_active(pg)
                row = pg.execute(
                    "SELECT * FROM ordivon_harness.turn_effects WHERE turn_request_id=%s",
                    (turn_id,),
                ).fetchone()
                return dict(row) if row else None

    def claim_before_send(
        self, turn_id: str, prompt: str, target: str, *, now_ms: int | None = None
    ) -> dict[str, Any]:
        if not all(isinstance(x, str) and x for x in (turn_id, prompt, target)):
            raise TurnEffectConflict("missing effect identity")
        now = int(time.time() * 1000) if now_ms is None else now_ms
        if type(now) is not int or now < 0:
            raise TurnEffectConflict("invalid effect time")
        for attempt in range(5):
            try:
                with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
                    with pg.transaction():
                        pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        self._require_active(pg)
                        inserted = pg.execute(
                            "INSERT INTO ordivon_harness.turn_effects VALUES "
                            "(%s,%s,%s,'UNKNOWN',NULL,%s) "
                            "ON CONFLICT(turn_request_id) DO NOTHING RETURNING turn_request_id",
                            (turn_id, prompt, target, now),
                        ).fetchone()
                        row = pg.execute(
                            "SELECT * FROM ordivon_harness.turn_effects WHERE turn_request_id=%s",
                            (turn_id,),
                        ).fetchone()
                        if row is None or (row["prompt_digest"], row["target_coordinate"]) != (
                            prompt,
                            target,
                        ):
                            raise TurnEffectConflict("turn effect identity conflict")
                        if inserted is not None and (
                            row["state"] != "UNKNOWN" or row["receipt_json"] is not None
                        ):
                            raise TurnEffectConflict("new PG claim has a forged terminal receipt")
                        return {
                            "admittedToSend": inserted is not None,
                            "state": row["state"],
                            "receipt_json": row["receipt_json"],
                            "turnRequestId": turn_id,
                        }
            except psycopg.errors.SerializationFailure as error:
                if attempt == 4:
                    raise TurnEffectConflict(
                        "effect claim serializable retries exhausted"
                    ) from error
        raise AssertionError("unreachable")

    def record_after_send(
        self,
        turn_id: str,
        prompt: str,
        target: str,
        state: str,
        receipt: dict[str, Any],
        *,
        now_ms: int | None = None,
    ) -> dict[str, Any]:
        if state not in ("UNKNOWN", "COMPLETED") or not isinstance(receipt, dict):
            raise TurnEffectConflict("invalid effect outcome")
        now = int(time.time() * 1000) if now_ms is None else now_ms
        if type(now) is not int or now < 0:
            raise TurnEffectConflict("invalid effect outcome time")
        evidence = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            with pg.transaction():
                self._require_active(pg)
                row = pg.execute(
                    "SELECT * FROM ordivon_harness.turn_effects "
                    "WHERE turn_request_id=%s FOR UPDATE",
                    (turn_id,),
                ).fetchone()
                if row is None or (row["prompt_digest"], row["target_coordinate"]) != (
                    prompt,
                    target,
                ):
                    raise TurnEffectConflict("unclaimed or conflicting effect identity")
                if row["receipt_json"] is None:
                    pg.execute(
                        "UPDATE ordivon_harness.turn_effects SET state=%s,"
                        "receipt_json=%s,updated_at_ms=%s WHERE turn_request_id=%s",
                        (state, evidence, now, turn_id),
                    )
                elif row["state"] != state or json.loads(row["receipt_json"]) != receipt:
                    raise TurnEffectConflict("effect receipt cannot be rebound")
                persisted = pg.execute(
                    "SELECT state,receipt_json FROM ordivon_harness.turn_effects "
                    "WHERE turn_request_id=%s",
                    (turn_id,),
                ).fetchone()
                if persisted["state"] != state or json.loads(persisted["receipt_json"]) != receipt:
                    raise TurnEffectConflict("PG effect durable readback differs")
        return {"state": state, "safeToResend": False, "turnRequestId": turn_id}


def main(argv: list[str] | None = None) -> int:
    """Explicit, source-fenced one-way effect cutover, never a live auto-migration."""
    parser = argparse.ArgumentParser(
        description="Qualify and activate source-backed PG turn effects"
    )
    parser.add_argument("--legacy-ledger", type=Path, required=True)
    parser.add_argument("--dsn-env", default="ORDIVON_TURN_EFFECT_POSTGRES_DSN")
    parser.add_argument("--confirm-old-writers-quiesced", action="store_true")
    args = parser.parse_args(argv)
    if not args.confirm_old_writers_quiesced:
        parser.error("old Browserless/provider effect writers must be proven quiesced")
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        parser.error(f"missing PostgreSQL DSN in environment variable {args.dsn_env}")
    owner = PostgresTurnEffects(dsn)
    # Stage is deliberately non-authoritative. Activation independently
    # rechecks source parity under a native writer lock.
    staged = owner.stage_legacy(args.legacy_ledger)
    receipt = owner.activate_staged_legacy(args.legacy_ledger, old_writers_quiesced=True)
    if receipt["sourceDigest"] != staged["sourceDigest"]:
        raise TurnEffectConflict("source identity changed across PG promotion")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
