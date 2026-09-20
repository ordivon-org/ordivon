#!/usr/bin/env python3
"""Durable carrier materializer for ConversationRelay.

This is a small effect ledger, not a scheduler and not ChatGPT-specific logic. It persists one
exact materialization request before crossing the external-effect boundary, never retries an
ambiguous effect as a fresh request, and lets a replacement process reconcile the same request.

The injected target owns mechanical creation/submission and target-specific reconciliation.
Rendered assistant output is outside this contract.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

try:
    from conversation_relay_carrier import (
        CarrierConflict,
        CarrierMaterializationReceipt,
        CarrierMaterializationRequest,
        MaterializationStanding,
    )
except ModuleNotFoundError:
    from scripts.conversation_relay_carrier import (
        CarrierConflict,
        CarrierMaterializationReceipt,
        CarrierMaterializationRequest,
        MaterializationStanding,
    )


class TargetPreEffectFailure(RuntimeError):
    def __init__(self, detail: str, *, evidence_digest: str) -> None:
        self.detail = detail
        self.evidence_digest = evidence_digest
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class TargetMaterializationObservation:
    standing: MaterializationStanding
    provider_conversation_coordinate: str | None = None
    evidence_digest: str | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        # Reuse receipt validation without inventing a request identity.
        CarrierMaterializationReceipt(
            request_id="target-observation:validation",
            request_digest="sha256:" + "0" * 64,
            standing=self.standing,
            provider_conversation_coordinate=self.provider_conversation_coordinate,
            evidence_digest=self.evidence_digest,
            detail=self.detail,
        )


class ConversationMaterializationTarget(Protocol):
    def materialize(
        self, request: CarrierMaterializationRequest
    ) -> TargetMaterializationObservation: ...

    def reconcile(
        self, request: CarrierMaterializationRequest
    ) -> TargetMaterializationObservation: ...

    def resume_after_human(
        self, request: CarrierMaterializationRequest
    ) -> TargetMaterializationObservation: ...


class SQLiteConversationMaterializer:
    """One-request durable ledger with replacement-safe reconciliation."""

    def __init__(self, path: Path, target: ConversationMaterializationTarget) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.target = target
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("PRAGMA busy_timeout=30000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    request_id TEXT PRIMARY KEY,
                    request_digest TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    standing TEXT NOT NULL,
                    provider_coordinate TEXT,
                    evidence_digest TEXT,
                    detail TEXT,
                    effect_generation INTEGER NOT NULL DEFAULT 0,
                    created_at_ms INTEGER NOT NULL,
                    updated_at_ms INTEGER NOT NULL
                )
                """
            )

    @staticmethod
    def _request_json(request: CarrierMaterializationRequest) -> str:
        value = {
            "requestId": request.request_id,
            "requestDigest": request.request_digest,
            "preparationDigest": request.preparation_digest,
            "bootstrapPrompt": request.bootstrap_prompt,
        }
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _load(self, request_id: str) -> sqlite3.Row | None:
        with closing(self._connect()) as db:
            return db.execute("SELECT * FROM requests WHERE request_id=?", (request_id,)).fetchone()

    @staticmethod
    def _receipt(row: sqlite3.Row) -> CarrierMaterializationReceipt:
        return CarrierMaterializationReceipt(
            request_id=row["request_id"],
            request_digest=row["request_digest"],
            standing=MaterializationStanding(row["standing"]),
            provider_conversation_coordinate=row["provider_coordinate"],
            evidence_digest=row["evidence_digest"],
            detail=row["detail"],
        )

    def _record_intent(self, request: CarrierMaterializationRequest, *, now_ms: int) -> sqlite3.Row:
        payload = self._request_json(request)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            if row is None:
                db.execute(
                    """
                    INSERT INTO requests(
                        request_id,request_digest,request_json,standing,created_at_ms,updated_at_ms
                    ) VALUES(?,?,?,?,?,?)
                    """,
                    (
                        request.request_id,
                        request.request_digest,
                        payload,
                        MaterializationStanding.PREPARED.value,
                        now_ms,
                        now_ms,
                    ),
                )
                row = db.execute(
                    "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
                ).fetchone()
            else:
                if (
                    row["request_digest"] != request.request_digest
                    or row["request_json"] != payload
                ):
                    db.execute("ROLLBACK")
                    raise CarrierConflict("same durable materialization identity changed request")
            db.execute("COMMIT")
            assert row is not None
            return row

    def _apply(
        self,
        request: CarrierMaterializationRequest,
        observation: TargetMaterializationObservation,
        *,
        now_ms: int,
        effect_generation_increment: int = 0,
    ) -> CarrierMaterializationReceipt:
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise CarrierConflict("materialization request has no durable intent")
            current = MaterializationStanding(row["standing"])
            terminal = {
                MaterializationStanding.BOUND,
                MaterializationStanding.READY_CONFIRMED,
            }
            if current in terminal:
                # Terminal standing is immutable; process replacement reads it rather than replacing it.
                db.execute("COMMIT")
                return self._receipt(row)
            if (
                current is MaterializationStanding.SUBMIT_OBSERVED
                and observation.standing is MaterializationStanding.PRE_EFFECT_FAILED
            ):
                db.execute("ROLLBACK")
                raise CarrierConflict("observed effect cannot regress to pre-effect failure")
            db.execute(
                """
                UPDATE requests
                SET standing=?,provider_coordinate=?,evidence_digest=?,detail=?,
                    effect_generation=effect_generation+?,updated_at_ms=?
                WHERE request_id=?
                """,
                (
                    observation.standing.value,
                    observation.provider_conversation_coordinate,
                    observation.evidence_digest,
                    observation.detail,
                    effect_generation_increment,
                    now_ms,
                    request.request_id,
                ),
            )
            updated = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            db.execute("COMMIT")
            assert updated is not None
            return self._receipt(updated)

    def _claim_effect_attempt(
        self, request: CarrierMaterializationRequest, *, now_ms: int
    ) -> tuple[bool, CarrierMaterializationReceipt]:
        """Atomically move one PREPARED request across the effect-ambiguous boundary.

        The boolean is true for exactly one concurrent caller. Every other caller observes the
        durable standing and must return/reconcile rather than invoke the target again.
        """
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise CarrierConflict("materialization request has no durable intent")
            if row["request_digest"] != request.request_digest:
                db.execute("ROLLBACK")
                raise CarrierConflict("materialization request digest differs from durable intent")
            current = MaterializationStanding(row["standing"])
            # PRE_EFFECT_FAILED is the one standing that proves the target did not cross SEND.
            # It may therefore re-enter the same effect identity for a bounded retry. UNKNOWN and
            # SUBMIT_OBSERVED remain non-retryable because their provider outcome is ambiguous.
            if current not in {
                MaterializationStanding.PREPARED,
                MaterializationStanding.PRE_EFFECT_FAILED,
            }:
                db.execute("COMMIT")
                return False, self._receipt(row)
            db.execute(
                """
                UPDATE requests
                SET standing=?,detail=?,effect_generation=effect_generation+1,updated_at_ms=?
                WHERE request_id=? AND standing=?
                """,
                (
                    MaterializationStanding.UNKNOWN.value,
                    (
                        "safe pre-effect retry admitted; reconcile if caller disappears"
                        if current is MaterializationStanding.PRE_EFFECT_FAILED
                        else "external materialization attempt admitted; reconcile if caller disappears"
                    ),
                    now_ms,
                    request.request_id,
                    current.value,
                ),
            )
            if db.execute("SELECT changes()").fetchone()[0] != 1:
                db.execute("ROLLBACK")
                raise CarrierConflict("materialization effect claim lost transactional race")
            claimed = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            db.execute("COMMIT")
            assert claimed is not None
            return True, self._receipt(claimed)

    def materialize(
        self, request: CarrierMaterializationRequest, *, now_ms: int | None = None
    ) -> CarrierMaterializationReceipt:
        now = int(time.time() * 1000) if now_ms is None else now_ms
        self._record_intent(request, now_ms=now)
        claimed, retained = self._claim_effect_attempt(request, now_ms=now)
        if not claimed:
            return retained
        try:
            observation = self.target.materialize(request)
        except TargetPreEffectFailure as error:
            observation = TargetMaterializationObservation(
                standing=MaterializationStanding.PRE_EFFECT_FAILED,
                evidence_digest=error.evidence_digest,
                detail=error.detail,
            )
        except Exception as error:
            observation = TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail=f"{type(error).__name__}: {str(error)[:1800]}",
            )
        return self._apply(request, observation, now_ms=now)

    def _claim_human_resume(
        self, request: CarrierMaterializationRequest, *, now_ms: int
    ) -> tuple[bool, CarrierMaterializationReceipt]:
        """Atomically admit one human-verified resume against the same provider-effect identity.

        HUMAN_REQUIRED proves the prompt SEND has not occurred. Exactly one caller may move that
        request back to UNKNOWN and cross the SEND boundary after revalidation. If that caller
        disappears, replacement processes reconcile UNKNOWN rather than blind-resend.
        """
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            if row is None:
                db.execute("ROLLBACK")
                raise CarrierConflict("human resume has no durable materialization intent")
            if row["request_digest"] != request.request_digest:
                db.execute("ROLLBACK")
                raise CarrierConflict("human resume request digest differs from durable intent")
            if (
                MaterializationStanding(row["standing"])
                is not MaterializationStanding.HUMAN_REQUIRED
            ):
                db.execute("COMMIT")
                return False, self._receipt(row)
            db.execute(
                """
                UPDATE requests
                SET standing=?,detail=?,effect_generation=effect_generation+1,updated_at_ms=?
                WHERE request_id=? AND standing=?
                """,
                (
                    MaterializationStanding.UNKNOWN.value,
                    "human verification revalidation/SEND attempt admitted; reconcile if caller disappears",
                    now_ms,
                    request.request_id,
                    MaterializationStanding.HUMAN_REQUIRED.value,
                ),
            )
            if db.execute("SELECT changes()").fetchone()[0] != 1:
                db.execute("ROLLBACK")
                raise CarrierConflict("human resume claim lost transactional race")
            claimed = db.execute(
                "SELECT * FROM requests WHERE request_id=?", (request.request_id,)
            ).fetchone()
            db.execute("COMMIT")
            assert claimed is not None
            return True, self._receipt(claimed)

    def resume_human(
        self, request: CarrierMaterializationRequest, *, now_ms: int | None = None
    ) -> CarrierMaterializationReceipt:
        now = int(time.time() * 1000) if now_ms is None else now_ms
        claimed, retained = self._claim_human_resume(request, now_ms=now)
        if not claimed:
            return retained
        try:
            observation = self.target.resume_after_human(request)
        except Exception as error:
            observation = TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail=f"{type(error).__name__}: {str(error)[:1800]}",
            )
        return self._apply(request, observation, now_ms=now)

    def reconcile(
        self, request: CarrierMaterializationRequest, *, now_ms: int | None = None
    ) -> CarrierMaterializationReceipt:
        now = int(time.time() * 1000) if now_ms is None else now_ms
        row = self._load(request.request_id)
        if row is None:
            raise CarrierConflict("cannot reconcile materialization without durable intent")
        retained = self._receipt(row)
        if retained.request_digest != request.request_digest:
            raise CarrierConflict("reconcile request digest differs from durable intent")
        if retained.standing in {
            MaterializationStanding.BOUND,
            MaterializationStanding.READY_CONFIRMED,
            MaterializationStanding.PRE_EFFECT_FAILED,
            MaterializationStanding.HUMAN_REQUIRED,
        }:
            return retained
        try:
            observation = self.target.reconcile(request)
        except Exception as error:
            observation = TargetMaterializationObservation(
                standing=MaterializationStanding.UNKNOWN,
                detail=f"{type(error).__name__}: {str(error)[:1800]}",
            )
        return self._apply(request, observation, now_ms=now)

    def doctor(self) -> dict[str, int | bool]:
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT standing,COUNT(*) AS n FROM requests GROUP BY standing"
            ).fetchall()
            counts = {row["standing"]: int(row["n"]) for row in rows}
            total = sum(counts.values())
            unresolved = sum(
                counts.get(value.value, 0)
                for value in (
                    MaterializationStanding.PREPARED,
                    MaterializationStanding.SUBMIT_OBSERVED,
                    MaterializationStanding.HUMAN_REQUIRED,
                    MaterializationStanding.UNKNOWN,
                )
            )
            ambiguous = counts.get(MaterializationStanding.SUBMIT_OBSERVED.value, 0) + counts.get(
                MaterializationStanding.UNKNOWN.value, 0
            )
            return {
                "healthy": True,
                "requests": total,
                # Compatibility aggregate: this is a truth-preserving backlog count, not a health
                # failure count and never implies permission to retry an ambiguous provider effect.
                "unresolved": unresolved,
                "standingCounts": counts,
                "effectOutcomeAmbiguous": ambiguous,
                "humanRequired": counts.get(MaterializationStanding.HUMAN_REQUIRED.value, 0),
                "prepared": counts.get(MaterializationStanding.PREPARED.value, 0),
                "unresolvedAffectsHealth": False,
            }
