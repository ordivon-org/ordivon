#!/usr/bin/env python3
"""Exact conversation-role bindings inside the Agent Automation SQLite authority.

This module adds one table to the existing materialization-ledger SQLite file. It owns
binding identity only: no browser/provider effect, scheduling, or conversation lifecycle.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import Any

try:
    from chatgpt_provider_resource import normalize_provider_resource
    from standard_identifiers import require_uuid7
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import normalize_provider_resource
    from scripts.standard_identifiers import require_uuid7

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ConversationBindingConflict(RuntimeError):
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


def _canonical_digest(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class SQLiteConversationBindingStore:
    """One current exact provider binding per campaignRef+agentId."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
                CREATE TABLE IF NOT EXISTS conversation_bindings (
                    campaign_ref TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    provider_resource TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    evidence_digest TEXT NOT NULL,
                    request_id TEXT NOT NULL UNIQUE,
                    binding_digest TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    PRIMARY KEY(campaign_ref, agent_id)
                )
                """
            )

    @staticmethod
    def _receipt(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.conversation-binding",
            "bindingStanding": "ADOPTED",
            "campaignRef": row["campaign_ref"],
            "agentId": row["agent_id"],
            "providerResource": row["provider_resource"],
            "sessionId": row["session_id"],
            "evidenceDigest": row["evidence_digest"],
            "requestId": row["request_id"],
            "bindingDigest": row["binding_digest"],
            "createdAtMs": int(row["created_at_ms"]),
        }

    @staticmethod
    def _validated_payload(
        *,
        campaign_ref: str,
        agent_id: str,
        provider_resource: str,
        session_id: str,
        evidence_digest: str,
        request_id: str,
    ) -> dict[str, str]:
        campaign_ref = _text(campaign_ref, "campaignRef")
        agent_id = _text(agent_id, "agentId", max_bytes=128)
        request_id = _text(request_id, "adoption requestId")
        session_id = require_uuid7(session_id, "sessionId")
        evidence_digest = _digest(evidence_digest, "evidenceDigest")
        provider_resource = normalize_provider_resource(
            _text(provider_resource, "providerResource", max_bytes=8192)
        )
        return {
            "campaignRef": campaign_ref,
            "agentId": agent_id,
            "providerResource": provider_resource,
            "sessionId": session_id,
            "evidenceDigest": evidence_digest,
            "requestId": request_id,
        }

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
        payload = self._validated_payload(
            campaign_ref=campaign_ref,
            agent_id=agent_id,
            provider_resource=provider_resource,
            session_id=session_id,
            evidence_digest=evidence_digest,
            request_id=request_id,
        )
        binding_digest = _canonical_digest(payload)
        now = int(time.time() * 1000) if now_ms is None else int(now_ms)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            by_request = db.execute(
                "SELECT * FROM conversation_bindings WHERE request_id=?",
                (payload["requestId"],),
            ).fetchone()
            if by_request is not None:
                if by_request["binding_digest"] != binding_digest:
                    db.execute("ROLLBACK")
                    raise ConversationBindingConflict(
                        "same adoption request identity changed conversation binding"
                    )
                db.execute("COMMIT")
                return self._receipt(by_request)

            by_role = db.execute(
                "SELECT * FROM conversation_bindings WHERE campaign_ref=? AND agent_id=?",
                (payload["campaignRef"], payload["agentId"]),
            ).fetchone()
            if by_role is not None:
                db.execute("ROLLBACK")
                raise ConversationBindingConflict(
                    "campaign role already has an exact conversation binding"
                )

            db.execute(
                """
                INSERT INTO conversation_bindings(
                    campaign_ref, agent_id, provider_resource, session_id, evidence_digest,
                    request_id, binding_digest, created_at_ms
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    payload["campaignRef"],
                    payload["agentId"],
                    payload["providerResource"],
                    payload["sessionId"],
                    payload["evidenceDigest"],
                    payload["requestId"],
                    binding_digest,
                    now,
                ),
            )
            row = db.execute(
                "SELECT * FROM conversation_bindings WHERE request_id=?",
                (payload["requestId"],),
            ).fetchone()
            db.execute("COMMIT")
            assert row is not None
            return self._receipt(row)

    def get_binding(self, campaign_ref: str, agent_id: str) -> dict[str, Any] | None:
        campaign_ref = _text(campaign_ref, "campaignRef")
        agent_id = _text(agent_id, "agentId", max_bytes=128)
        with closing(self._connect(read_only=True)) as db:
            row = db.execute(
                "SELECT * FROM conversation_bindings WHERE campaign_ref=? AND agent_id=?",
                (campaign_ref, agent_id),
            ).fetchone()
        return None if row is None else self._receipt(row)

    def resolve_binding(self, campaign_ref: str, agent_id: str) -> dict[str, Any] | None:
        return self.get_binding(campaign_ref, agent_id)
