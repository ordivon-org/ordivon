#!/usr/bin/env python3
"""PostgreSQL-native durable Browserless turn-effect authority.

The migration path stages legacy evidence but intentionally cannot activate a
source-backed cutover: provider subprocess quiescence must first be proven.
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
                        "('legacy','PENDING',%s)", (digest,)
                    )
                elif marker["source_digest"] != digest:
                    raise TurnEffectConflict("legacy effect source changed after staging")
                for row in rows:
                    pg.execute(
                        "INSERT INTO ordivon_harness.turn_effects "
                        "(turn_request_id,prompt_digest,target_coordinate,state,"
                        "receipt_json,updated_at_ms) VALUES(%s,%s,%s,%s,%s,%s) "
                        "ON CONFLICT(turn_request_id) DO NOTHING", row
                    )
                names = (
                    "turn_request_id", "prompt_digest", "target_coordinate",
                    "state", "receipt_json", "updated_at_ms",
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
            "SELECT state FROM ordivon_harness.turn_effect_cutover "
            "WHERE cutover_id='legacy'"
        ).fetchone()
        if marker is None or marker["state"] != "ACTIVE":
            raise TurnEffectConflict("PG effects cutover PENDING or not certified")

    def get(self, turn_id: str) -> dict[str, Any] | None:
        with psycopg.connect(self.dsn, row_factory=dict_row) as pg:
            with pg.transaction():
                self._require_active(pg)
                row = pg.execute(
                    "SELECT * FROM ordivon_harness.turn_effects WHERE turn_request_id=%s",
                    (turn_id,)
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
                            (turn_id, prompt, target, now)
                        ).fetchone()
                        row = pg.execute(
                            "SELECT * FROM ordivon_harness.turn_effects "
                            "WHERE turn_request_id=%s", (turn_id,)
                        ).fetchone()
                        if row is None or (row["prompt_digest"], row["target_coordinate"]) != (prompt, target):
                            raise TurnEffectConflict("turn effect identity conflict")
                        if inserted is not None and (
                            row["state"] != "UNKNOWN" or row["receipt_json"] is not None
                        ):
                            raise TurnEffectConflict("new PG claim has a forged terminal receipt")
                        return {"admittedToSend": inserted is not None, "state": row["state"],
                                "receipt_json": row["receipt_json"], "turnRequestId": turn_id}
            except psycopg.errors.SerializationFailure as error:
                if attempt == 4:
                    raise TurnEffectConflict("effect claim serializable retries exhausted") from error
        raise AssertionError("unreachable")

    def record_after_send(
        self, turn_id: str, prompt: str, target: str, state: str,
        receipt: dict[str, Any], *, now_ms: int | None = None
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
                    "WHERE turn_request_id=%s FOR UPDATE", (turn_id,)
                ).fetchone()
                if row is None or (row["prompt_digest"], row["target_coordinate"]) != (prompt, target):
                    raise TurnEffectConflict("unclaimed or conflicting effect identity")
                if row["receipt_json"] is None:
                    pg.execute(
                        "UPDATE ordivon_harness.turn_effects SET state=%s,"
                        "receipt_json=%s,updated_at_ms=%s WHERE turn_request_id=%s",
                        (state, evidence, now, turn_id)
                    )
                elif row["state"] != state or json.loads(row["receipt_json"]) != receipt:
                    raise TurnEffectConflict("effect receipt cannot be rebound")
                persisted = pg.execute(
                    "SELECT state,receipt_json FROM ordivon_harness.turn_effects "
                    "WHERE turn_request_id=%s", (turn_id,)
                ).fetchone()
                if persisted["state"] != state or json.loads(persisted["receipt_json"]) != receipt:
                    raise TurnEffectConflict("PG effect durable readback differs")
        return {"state": state, "safeToResend": False, "turnRequestId": turn_id}
