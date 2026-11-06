"""Atomic PostgreSQL paper-account close using the Capital cash ledger."""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict
from datetime import date, datetime
from os import environ
from pathlib import Path

from psycopg import Connection
from psycopg.types.json import Jsonb

from .paper_close import PaperSession, PaperValuation, decode_session, value_session
from .postgres_ledger import PostgresAccountingLedger
from .substrate import AccountingAccount, LedgerApplyStatus, stable_accounting_id


def _iso(value: date | datetime) -> str:
    return value.isoformat()


class _PaperLedger(PostgresAccountingLedger):
    def _connect(self) -> Connection:
        db = super()._connect()
        try:
            if db.execute("SELECT pg_catalog.current_database()").fetchone() != ("ordivon_paper",):
                raise ValueError("paper close requires the dedicated ordivon_paper database")
        except BaseException:
            db.close()
            raise
        return db


class PostgresPaperClose:
    """Owns paper positions and receipts. Requires a dedicated paper database."""

    def __init__(self, paper_dsn: str) -> None:
        self._ledger = _PaperLedger(paper_dsn)
        self._ledger._atomic(self._create_schema)

    @staticmethod
    def _create_schema(db: Connection) -> None:
        db.execute("SELECT pg_advisory_xact_lock(3294464535185897073)")
        db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_paper")
        db.execute(
            """CREATE TABLE IF NOT EXISTS ordivon_paper.daily_close (
                account_key TEXT NOT NULL,
                session DATE NOT NULL,
                request_sha256 TEXT NOT NULL,
                request JSONB NOT NULL,
                receipt JSONB NOT NULL,
                PRIMARY KEY (account_key, session)
            )"""
        )

        admitted = db.execute(
            """
            SELECT c.relkind = 'r' AND c.relpersistence = 'p'
                   AND NOT (c.relrowsecurity OR c.relhasrules OR c.relhastriggers)
                   AND EXISTS (
                       SELECT FROM pg_catalog.pg_constraint p
                       WHERE p.conrelid = c.oid AND p.contype = 'p'
                         AND NOT p.condeferrable
                         AND pg_catalog.pg_get_constraintdef(p.oid)
                             = 'PRIMARY KEY (account_key, session)'
                   )
            FROM pg_catalog.pg_class c
            WHERE c.oid = 'ordivon_paper.daily_close'::pg_catalog.regclass
            """
        ).fetchone()
        if admitted != (True,):
            raise RuntimeError("paper receipt table must be permanent with its original key")

    def close_session(self, account_key: str, day: PaperSession) -> dict:
        if re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", account_key) is None:
            raise ValueError("invalid paper account key")
        # Canonicalize and copy caller-owned mutable input before retrying a transaction.
        payload = json.dumps(asdict(day), default=_iso, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode()).hexdigest()
        request = json.loads(payload)
        day = decode_session(request)

        def close(db: Connection) -> dict:
            existing = db.execute(
                "SELECT request_sha256, receipt FROM ordivon_paper.daily_close "
                "WHERE account_key = %s AND session = %s", (account_key, day.session),
            ).fetchone()
            if existing:
                if existing[0] != digest:
                    raise ValueError("conflicting inputs for an already closed paper session")
                return existing[1]
            head = db.execute(
                "SELECT session, request_sha256, receipt FROM ordivon_paper.daily_close WHERE account_key = %s "
                "ORDER BY session DESC LIMIT 1", (account_key,),
            ).fetchone()
            previous = (
                PaperValuation(**(head[2]["valuation"] | {"session": head[0]}))
                if head else None
            )
            valuation = value_session(previous, day)
            self._post_cash(db, account_key, day, previous, valuation)
            receipt = asdict(valuation) | {"session": day.session.isoformat()}
            result = {
                "schema_version": 1,
                "valuation": receipt,
                "mode": "PAPER",
                "request_sha256": digest,
                "previous_request_sha256": head[1] if head else None,
                "account_key": account_key,
            }
            written = db.execute(
                "INSERT INTO ordivon_paper.daily_close "
                "(account_key, session, request_sha256, request, receipt) "
                "VALUES (%s, %s, %s, %s, %s) "
                "RETURNING account_key, session, request_sha256, request, receipt",
                (account_key, day.session, digest, Jsonb(request), Jsonb(result)),
            ).fetchone()
            if written != (account_key, day.session, digest, request, result):
                raise RuntimeError("paper receipt read-back mismatch")
            return result

        return self._ledger._atomic(close)

    def _post_cash(
        self, db: Connection, key: str, day: PaperSession,
        previous: PaperValuation | None, valuation: PaperValuation,
    ) -> None:
        def identity(*parts: str) -> int:
            return stable_accounting_id("ordivon-capital:paper-close:usd:v1", key, *parts)

        cash, fund, clearing = (identity(role) for role in ("cash", "fund", "clearing"))
        if previous is None:
            accounts = (AccountingAccount(cash, True), AccountingAccount(fund), AccountingAccount(clearing))
            for account in accounts:
                status = self._ledger._create_account_in_transaction(db, account)
                if status is not LedgerApplyStatus.CREATED:
                    raise ValueError("paper account identity is already occupied")

        def post(reference, debit, credit, amount, operation, pending_id=0):
            status = self._ledger._apply_in_transaction(
                db, transfer_id=reference, debit_account_id=debit, credit_account_id=credit,
                amount=amount, operation=operation, pending_id=pending_id,
            )
            if status is not LedgerApplyStatus.CREATED:
                raise ValueError(f"paper cash posting rejected: {status}")

        if previous:
            for fill_id, amount in previous.pending.items():
                post(identity("settle", fill_id), cash, clearing, amount, "POST", identity("buy", fill_id))
        if day.contribution_minor:
            post(identity("deposit", day.session.isoformat()), fund, cash, day.contribution_minor, "IMMEDIATE")
        for fill_id, amount in valuation.pending.items():
            post(identity("buy", fill_id), cash, clearing, amount, "PENDING")
        state = self._ledger._account_in_transaction(db, cash)
        if (
            state.credits_posted - state.debits_posted != valuation.cash_minor
            or state.debits_pending != valuation.payable_minor
        ):
            raise ValueError("paper cash ledger and valuation disagree")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        day = decode_session(json.loads(args.input.read_text(encoding="utf-8")))
        dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", "")
        result = PostgresPaperClose(dsn).close_session(args.account, day)
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(f"paper close rejected: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
