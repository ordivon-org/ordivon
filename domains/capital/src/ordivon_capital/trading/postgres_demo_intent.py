"""Native PostgreSQL Demo order intent precommit, not an OMS or financial ledger.

A durable EFFECT_UNKNOWN claim precedes each possible provider POST.
Neither Runtime retry nor a missing provider lookup permits replaying it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import psycopg


class DemoIntentConflict(ValueError):
    """Intent identity, economic terms or state changed; no effect may be sent."""


@dataclass(frozen=True)
class DemoIntent:
    intent_id: str
    account_ref: str
    client_order_id: str
    instrument_id: str
    side: str
    size: str
    limit_price: str
    decision_ref: str
    risk_evidence_digest: str
    policy_evidence_digest: str

    def canonical(self) -> dict[str, str]:
        if not self.intent_id or not self.account_ref or len(self.intent_id) > 128:
            raise ValueError("stable intent and account identity required")
        if not isinstance(self.client_order_id, str) or not self.client_order_id.isalnum() or not 1 <= len(self.client_order_id) <= 32:
            raise ValueError("invalid clOrdId")
        if not isinstance(self.instrument_id, str) or "-" not in self.instrument_id:
            raise ValueError("invalid instrument")
        if self.side not in ("buy", "sell"):
            raise ValueError("invalid side")
        if not self.decision_ref or not self.risk_evidence_digest or not self.policy_evidence_digest:
            raise ValueError("decision, risk and policy evidence references required")
        for name in ("risk_evidence_digest", "policy_evidence_digest"):
            val = getattr(self, name)
            if not (val.startswith("sha256:") and len(val) == 71 and
                    all(x in "0123456789abcdef" for x in val[7:])):
                raise ValueError(f"{name} must be sha256 digest")
        def decimal(v: str) -> str:
            try:
                d = Decimal(v)
            except (InvalidOperation, ValueError, TypeError) as exc:
                raise ValueError("invalid decimal") from exc
            if not d.is_finite() or d <= 0:
                raise ValueError("invalid decimal")
            return format(d, "f")
        return {
            "intentId": self.intent_id,
            "accountRef": self.account_ref,
            "clOrdId": self.client_order_id,
            "instId": self.instrument_id,
            "side": self.side,
            "size": decimal(self.size),
            "limitPrice": decimal(self.limit_price),
            "decisionRef": self.decision_ref,
            "riskDigest": self.risk_evidence_digest,
            "policyDigest": self.policy_evidence_digest,
        }


class PostgresDemoIntentStore:
    """Small Trading PG authority: immutable order intent and effect-uncertain claim."""

    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("PostgreSQL DSN required")
        self._dsn = dsn
        self._init_schema()

    def _db(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self._dsn, autocommit=True)

    def _init_schema(self) -> None:
        with self._db() as db:
            with db.transaction():
                key = int.from_bytes(hashlib.sha256(b"ordivon:capital:trading-demo-intent:v1").digest()[:8], "big", signed=True)
                db.execute("SELECT pg_advisory_xact_lock(%s)", (key,))
                db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_capital")
                db.execute("""
                    CREATE TABLE IF NOT EXISTS ordivon_capital.demo_order_intents (
                      intent_id TEXT PRIMARY KEY,
                      account_ref TEXT NOT NULL,
                      client_order_id TEXT NOT NULL,
                      intent_digest TEXT NOT NULL,
                      intent_document JSONB NOT NULL,
                      state TEXT NOT NULL DEFAULT 'STAGED'
                        CHECK (state IN ('STAGED','EFFECT_UNKNOWN','ACKNOWLEDGED')),
                      provider_order_id TEXT,
                      cancel_standing TEXT NOT NULL DEFAULT 'NOT_REQUESTED'
                        CHECK (cancel_standing IN ('NOT_REQUESTED','EFFECT_UNKNOWN','ACK_ACCEPTED_NOT_FINAL')),
                      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                      claimed_at TIMESTAMPTZ,
                      acknowledged_at TIMESTAMPTZ,
                      UNIQUE (account_ref, client_order_id),
                      UNIQUE (account_ref, provider_order_id)
                    )
                """)

    @staticmethod
    def _digest(data: dict[str, str]) -> str:
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(payload).hexdigest()

    def stage(self, intent: DemoIntent) -> dict[str, Any]:
        """Idempotent only for identical immutable economic/evidence terms."""
        doc = intent.canonical()
        digest = self._digest(doc)
        with self._db() as db:
            with db.transaction():
                db.execute("""
                    INSERT INTO ordivon_capital.demo_order_intents
                      (intent_id, account_ref, client_order_id, intent_digest, intent_document)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT DO NOTHING
                """, (intent.intent_id, intent.account_ref, intent.client_order_id,
                      digest, json.dumps(doc, sort_keys=True)))
                row = db.execute("""
                    SELECT intent_digest, intent_document, state, provider_order_id
                    FROM ordivon_capital.demo_order_intents WHERE intent_id=%s FOR UPDATE
                """, (intent.intent_id,)).fetchone()
                if row is None or row[0] != digest or row[1] != doc:
                    raise DemoIntentConflict("immutable intent identity or client-order ID collision")
                return {"intentId": intent.intent_id, "digest": digest, "state": row[2],
                        "providerOrderId": row[3]}

    def inspect(self, intent_id: str) -> dict[str, Any] | None:
        with self._db() as db:
            row = db.execute("""
                SELECT intent_digest, intent_document, state, provider_order_id,
                       cancel_standing
                FROM ordivon_capital.demo_order_intents WHERE intent_id=%s
            """, (intent_id,)).fetchone()
        if row is None:
            return None
        return {"digest": row[0], "intent": row[1], "state": row[2],
                "providerOrderId": row[3], "cancelStanding": row[4]}

    def claim_once(self, intent_id: str, expected_digest: str) -> dict[str, str]:
        """One committed irreversible effect claim before the physical POST."""
        with self._db() as db:
            with db.transaction():
                row = db.execute("""
                    UPDATE ordivon_capital.demo_order_intents
                       SET state='EFFECT_UNKNOWN', claimed_at=now()
                     WHERE intent_id=%s AND intent_digest=%s AND state='STAGED'
                    RETURNING intent_document
                """, (intent_id, expected_digest)).fetchone()
                if row is None:
                    raise DemoIntentConflict("intent was not STAGED; do not repeat POST")
                return row[0]

    def record_ack(self, intent_id: str, order_id: str) -> None:
        if not isinstance(order_id, str) or not order_id.isdecimal():
            raise ValueError("external order ID must be numeric")
        with self._db() as db:
            with db.transaction():
                row = db.execute("""
                    UPDATE ordivon_capital.demo_order_intents
                       SET state='ACKNOWLEDGED', provider_order_id=%s,
                           acknowledged_at=now()
                     WHERE intent_id=%s AND state='EFFECT_UNKNOWN'
                    RETURNING provider_order_id
                """, (order_id, intent_id)).fetchone()
                if row is None:
                    previous = db.execute("""
                        SELECT state, provider_order_id
                        FROM ordivon_capital.demo_order_intents WHERE intent_id=%s
                    """, (intent_id,)).fetchone()
                    if previous != ("ACKNOWLEDGED", order_id):
                        raise DemoIntentConflict("provider acknowledgement conflicts with durable intent")

    def claim_cancel_once(self, intent_id: str, order_id: str) -> None:
        with self._db() as db:
            with db.transaction():
                row = db.execute("""
                    UPDATE ordivon_capital.demo_order_intents
                       SET cancel_standing='EFFECT_UNKNOWN'
                     WHERE intent_id=%s AND state='ACKNOWLEDGED'
                       AND provider_order_id=%s AND cancel_standing='NOT_REQUESTED'
                    RETURNING intent_id
                """, (intent_id, order_id)).fetchone()
                if row is None:
                    raise DemoIntentConflict("cancellation is not a new, acknowledged provider order")

    def record_cancel_ack(self, intent_id: str) -> None:
        with self._db() as db:
            with db.transaction():
                row = db.execute("""
                    UPDATE ordivon_capital.demo_order_intents
                       SET cancel_standing='ACK_ACCEPTED_NOT_FINAL'
                     WHERE intent_id=%s AND cancel_standing='EFFECT_UNKNOWN'
                    RETURNING intent_id
                """, (intent_id,)).fetchone()
                if row is None:
                    previous = db.execute("""
                        SELECT cancel_standing
                        FROM ordivon_capital.demo_order_intents WHERE intent_id=%s
                    """, (intent_id,)).fetchone()
                    if previous != ("ACK_ACCEPTED_NOT_FINAL",):
                        raise DemoIntentConflict("cancel acknowledgement not eligible")
