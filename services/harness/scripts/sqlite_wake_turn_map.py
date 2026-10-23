#!/usr/bin/env python3
"""Stable wake-intent to turn-request mapping inside the existing turn ledger."""

from __future__ import annotations

import re
import sqlite3
import time
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Callable

try:
    from standard_identifiers import require_uuid7
except ModuleNotFoundError:
    from scripts.standard_identifiers import require_uuid7

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class WakeTurnConflict(RuntimeError):
    pass


def _text(value: str, label: str, *, max_bytes: int = 4096) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > max_bytes
    ):
        raise ValueError(f"{label} must be non-empty, trimmed, and <= {max_bytes} UTF-8 bytes")
    return value


def _digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be canonical sha256:<lowercase-hex>")
    return value


def _uuid7() -> str:
    return str(uuid.uuid7())


class SQLiteWakeTurnMap:
    def __init__(
        self,
        path: Path,
        *,
        uuid7_factory: Callable[[], str] = _uuid7,
        now_ms: Callable[[], int] = lambda: int(time.time() * 1000),
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._uuid7_factory = uuid7_factory
        self._now_ms = now_ms
        self._initialize()

    def _connect(self, *, read_only: bool = False) -> sqlite3.Connection:
        if read_only:
            db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, timeout=30)
        else:
            db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("PRAGMA busy_timeout=30000")
        db.row_factory = sqlite3.Row
        return db

    def _initialize(self) -> None:
        with closing(self._connect()) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS wake_turn_map(
                    wake_intent_id TEXT PRIMARY KEY,
                    campaign_ref TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    prompt_digest TEXT NOT NULL,
                    turn_request_id TEXT NOT NULL UNIQUE,
                    created_at_ms INTEGER NOT NULL
                )
                """
            )

    @staticmethod
    def _receipt(row: sqlite3.Row, disposition: str) -> dict[str, Any]:
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

    def get(self, wake_intent_id: str) -> dict[str, Any] | None:
        wake_intent_id = _text(wake_intent_id, "wakeIntentId")
        if not self.path.is_file():
            return None
        db = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            exists = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='wake_turn_map'"
            ).fetchone()
            if exists is None:
                return None
            row = db.execute(
                "SELECT * FROM wake_turn_map WHERE wake_intent_id=?",
                (wake_intent_id,),
            ).fetchone()
        finally:
            db.close()
        return None if row is None else self._receipt(row, "existing")

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
        now = int(self._now_ms())
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM wake_turn_map WHERE wake_intent_id=?",
                (wake_intent_id,),
            ).fetchone()
            if existing is not None:
                observed = (
                    existing["campaign_ref"],
                    existing["agent_id"],
                    existing["prompt_digest"],
                )
                if observed != semantic:
                    db.execute("ROLLBACK")
                    raise WakeTurnConflict(
                        "wake intent identity changed campaign, role, or prompt semantics"
                    )
                db.execute("COMMIT")
                return self._receipt(existing, "existing")

            turn_request_id = require_uuid7(self._uuid7_factory(), "turnRequestId")
            db.execute(
                """
                INSERT INTO wake_turn_map(
                    wake_intent_id,campaign_ref,agent_id,prompt_digest,turn_request_id,created_at_ms
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    wake_intent_id,
                    campaign_ref,
                    agent_id,
                    prompt_digest,
                    turn_request_id,
                    now,
                ),
            )
            row = db.execute(
                "SELECT * FROM wake_turn_map WHERE wake_intent_id=?",
                (wake_intent_id,),
            ).fetchone()
            db.execute("COMMIT")
            assert row is not None
            return self._receipt(row, "created")
