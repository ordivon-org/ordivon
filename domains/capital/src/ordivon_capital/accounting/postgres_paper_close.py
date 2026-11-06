"""Atomic PostgreSQL paper-account close using the Capital cash ledger."""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, replace
from datetime import date, datetime
from os import environ
from pathlib import Path

import psycopg
from psycopg import Connection
from psycopg.types.json import Jsonb

from ..markets.etf_eod_snapshot import AdmittedEtfEodSnapshot, admit_etf_eod_snapshot
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

        PostgresPaperClose._verify_receipt_table(db)

    @staticmethod
    def _verify_receipt_table(db: Connection, *, lock: bool = True) -> None:
        # Close is writable; readback may verify catalog under READ ONLY.
        if lock:
            db.execute("LOCK TABLE ordivon_paper.daily_close IN ROW EXCLUSIVE MODE")
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

    def close_session(
        self, account_key: str, day: PaperSession, *,
        mark_snapshot: AdmittedEtfEodSnapshot | None = None,
    ) -> dict:
        """Close using inline fixture marks or the trusted output of Markets admission."""
        if re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", account_key) is None:
            raise ValueError("invalid paper account key")
        market_evidence = {"standing": "CALLER_SUPPLIED_MARKS"}
        if mark_snapshot is not None:
            if day.marks:
                raise ValueError("inline marks cannot accompany an admitted snapshot")
            session = day.session.isoformat()
            try:
                marks = mark_snapshot.prices_for(session)
            except KeyError as error:
                raise ValueError("market snapshot does not cover the close session") from error
            day = replace(day, marks=marks)
            market_evidence = {
                "standing": "OPERATOR_BOUND_MARKS",
                "sha256": mark_snapshot.sha256,
                "source_id": mark_snapshot.source_id,
                "rights_ref": mark_snapshot.rights_ref,
                "corporate_actions_ref": mark_snapshot.corporate_actions_ref,
                "captured_at": mark_snapshot.captured_at.isoformat(),
                "valuation_as_of": mark_snapshot.decision_at.isoformat(),
                "session_closes": {
                    mark.session_date: mark.session_close_at.isoformat()
                    for mark in mark_snapshot.marks
                },
                "instrument_ids": sorted({mark.instrument_id for mark in mark_snapshot.marks}),
                "supersedes_sha256": mark_snapshot.supersedes_sha256,
            }
        # Freeze caller-owned input before retrying a transaction.
        encoded_day = asdict(day)
        if not day.sells:
            # Keep the stored request identity for existing buy-only closes.
            del encoded_day["sells"]
        for fill in encoded_day["buys"]:
            if fill["settlement_date"] is None:
                # Preserve identity for previously admitted fixture requests.
                del fill["settlement_date"]
        payload = json.dumps(
            encoded_day | {"market_evidence": market_evidence},
            default=_iso, sort_keys=True, separators=(",", ":"),
        )
        digest = hashlib.sha256(payload.encode()).hexdigest()
        request = json.loads(payload)
        day = decode_session({key: value for key, value in request.items() if key != "market_evidence"})

        def close(db: Connection) -> dict:
            self._verify_receipt_table(db)
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
            if mark_snapshot is not None:
                covered = set(previous.positions) if previous else set()
                covered.update(fill.symbol for fill in (*day.buys, *day.sells))
                if covered - day.marks.keys():
                    raise ValueError("market snapshot does not cover every held or traded instrument")
            valuation = value_session(previous, day)
            self._post_cash(db, account_key, day, previous, valuation)
            receipt = asdict(valuation) | {"session": day.session.isoformat()}
            if not day.sells and not (previous and previous.pending_sales):
                for key in ("pending_sales", "sale_settlement_dates", "receivable_minor"):
                    del receipt[key]
            result = {
                "schema_version": 1,
                "valuation": receipt,
                "mode": "PAPER",
                "request_sha256": digest,
                "previous_request_sha256": head[1] if head else None,
                "account_key": account_key,
                "market_evidence": market_evidence,
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

        buy_ids = {fill.fill_id for fill in day.buys}
        sell_ids = {fill.fill_id for fill in day.sells}
        opposite_transfers = [
            *(str(identity("sell", fill_id)) for fill_id in buy_ids),
            *(str(identity("buy", fill_id)) for fill_id in sell_ids),
        ]
        if buy_ids & sell_ids or (
            opposite_transfers and db.execute(
                "SELECT 1 FROM ordivon_capital.transfers WHERE id = ANY(%s) LIMIT 1",
                (opposite_transfers,),
            ).fetchone()
        ):
            raise ValueError("paper fill identity already used for the opposite side")

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
            for fill_id, amount in previous.payable_due_on(day.session).items():
                post(identity("settle", fill_id), cash, clearing, amount, "POST", identity("buy", fill_id))
            for fill_id, amount in previous.receivable_due_on(day.session).items():
                post(identity("settle-sell", fill_id), clearing, cash, amount, "POST", identity("sell", fill_id))
        if day.contribution_minor:
            post(identity("deposit", day.session.isoformat()), fund, cash, day.contribution_minor, "IMMEDIATE")
        for fill in day.buys:
            post(identity("buy", fill.fill_id), cash, clearing, fill.cost_minor, "PENDING")
        for fill in day.sells:
            post(identity("sell", fill.fill_id), clearing, cash, fill.proceeds_minor, "PENDING")
        state = self._ledger._account_in_transaction(db, cash)
        if (
            state.credits_posted - state.debits_posted != valuation.cash_minor
            or state.debits_pending != valuation.payable_minor
            or state.credits_pending != valuation.receivable_minor
        ):
            raise ValueError("paper cash ledger and valuation disagree")


def read_committed_paper_close(paper_dsn: str, account_key: str, session: date) -> dict:
    """Read the actual durable receipt via PostgreSQL, without creating a schema.

    This is an Accounting-owned readback of current local database truth;
    it is not an independent attestation of third-party market data.
    """
    if not paper_dsn:
        raise ValueError("paper readback requires an explicit paper database DSN")
    if re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", account_key) is None:
        raise ValueError("invalid paper account key")
    if type(session) is not date:
        raise ValueError("paper readback requires a concrete ISO session date")
    try:
        with psycopg.connect(paper_dsn) as db:
            db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            if db.execute("SELECT pg_catalog.current_database()").fetchone() != (
                "ordivon_paper",
            ):
                raise ValueError("paper readback requires dedicated ordivon_paper database")
            PostgresPaperClose._verify_receipt_table(db, lock=False)
            row = db.execute(
                "SELECT request_sha256, request, receipt FROM ordivon_paper.daily_close "
                "WHERE account_key = %s AND session = %s",
                (account_key, session),
            ).fetchone()
            if row is None:
                raise ValueError("no committed paper receipt for requested account session")
            digest, request, receipt = row
            recomputed = hashlib.sha256(
                json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            if (
                recomputed != digest
                or receipt.get("request_sha256") != digest
                or receipt.get("account_key") != account_key
                or receipt.get("mode") != "PAPER"
                or receipt.get("valuation", {}).get("session") != session.isoformat()
            ):
                raise ValueError("committed paper receipt and stored request disagree")
            return receipt
    except psycopg.Error as exc:
        raise ValueError("paper database readback unavailable") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--market-snapshot", type=Path)
    parser.add_argument("--market-binding", type=Path)
    args = parser.parse_args()
    if bool(args.market_snapshot) != bool(args.market_binding):
        parser.error("--market-snapshot and --market-binding must be supplied together")
    try:
        day = decode_session(json.loads(args.input.read_text(encoding="utf-8")))
        snapshot = None
        if args.market_snapshot:
            binding = json.loads(args.market_binding.read_text(encoding="utf-8"))
            snapshot = admit_etf_eod_snapshot(args.market_snapshot.read_bytes(), **binding)
        dsn = environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", "")
        result = PostgresPaperClose(dsn).close_session(args.account, day, mark_snapshot=snapshot)
    except (ValueError, TypeError, KeyError, OSError) as error:
        print(f"paper close rejected: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
