"""PostgreSQL-only accounting ledger: native SERIALIZABLE transactions, no SQLite writes."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import TypeVar

import psycopg
from psycopg.errors import DeadlockDetected, SerializationFailure, UniqueViolation

from .sqlite_ledger import (
    AccountState,
    LedgerApplyStatus,
    TransferState,
)
from .substrate import AccountingAccount, AccountingInstruction, AccountingOperation

T = TypeVar("T")


class PostgresAccountingLedger:
    """PG-first accounting capability. An explicit DSN is mandatory.

    Replays, balance effects, and transfer identity are one serializable transaction.
    The original SQLite owner remains read-only historical migration evidence,
    not a fallback on missing PostgreSQL.
    """

    def __init__(self, dsn: str) -> None:
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("PostgreSQL accounting requires explicit DSN")
        self.dsn = dsn
        self._initialize_schema()

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.dsn, autocommit=True)

    def _initialize_schema(self) -> None:
        with self._connect() as db:
            with db.transaction():
                key = int.from_bytes(
                    hashlib.sha256(b"ordivon:capital:pg-accounting:v1").digest()[:8],
                    "big",
                    signed=True,
                )
                db.execute("SELECT pg_advisory_xact_lock(%s)", (key,))
                db.execute("CREATE SCHEMA IF NOT EXISTS ordivon_capital")
                db.execute(
                    """CREATE TABLE IF NOT EXISTS ordivon_capital.accounts(
                        id TEXT PRIMARY KEY,
                        no_overdraft BOOLEAN NOT NULL,
                        debits_pending NUMERIC(39,0) NOT NULL DEFAULT 0,
                        debits_posted NUMERIC(39,0) NOT NULL DEFAULT 0,
                        credits_pending NUMERIC(39,0) NOT NULL DEFAULT 0,
                        credits_posted NUMERIC(39,0) NOT NULL DEFAULT 0,
                        CHECK (debits_pending >= 0),
                        CHECK (debits_posted >= 0),
                        CHECK (credits_pending >= 0),
                        CHECK (credits_posted >= 0)
                    )"""
                )
                db.execute(
                    """CREATE TABLE IF NOT EXISTS ordivon_capital.transfers(
                        id TEXT PRIMARY KEY,
                        debit_id TEXT NOT NULL REFERENCES ordivon_capital.accounts(id),
                        credit_id TEXT NOT NULL REFERENCES ordivon_capital.accounts(id),
                        amount NUMERIC(39,0) NOT NULL CHECK (amount >= 0),
                        pending_id TEXT,
                        operation TEXT NOT NULL
                            CHECK (operation IN ('IMMEDIATE','PENDING','POST','VOID')),
                        status TEXT NOT NULL CHECK (status IN ('PENDING','POSTED','VOIDED'))
                    )"""
                )

    def close(self) -> None:
        """Connections are owned by each operation; no long-lived SQLite handle."""

    def __enter__(self) -> PostgresAccountingLedger:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _atomic(self, fn: Callable[[psycopg.Connection], T]) -> T:
        for attempt in range(8):
            try:
                with self._connect() as db:
                    with db.transaction():
                        db.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                        return fn(db)
            except (SerializationFailure, DeadlockDetected, UniqueViolation):
                if attempt == 7:
                    raise
        raise AssertionError("unreachable")

    def create_account(self, account: AccountingAccount) -> LedgerApplyStatus:
        def operation(db: psycopg.Connection) -> LedgerApplyStatus:
            inserted = db.execute(
                "INSERT INTO ordivon_capital.accounts(id,no_overdraft) "
                "VALUES(%s,%s) ON CONFLICT(id) DO NOTHING RETURNING id",
                (str(account.account_id), account.no_overdraft),
            ).fetchone()
            if inserted:
                return LedgerApplyStatus.CREATED
            observed = db.execute(
                "SELECT no_overdraft FROM ordivon_capital.accounts WHERE id=%s",
                (str(account.account_id),),
            ).fetchone()
            if observed is None:
                raise RuntimeError("account conflict disappeared")
            return (
                LedgerApplyStatus.EXISTS
                if observed[0] == account.no_overdraft
                else LedgerApplyStatus.ID_CONFLICT
            )
        return self._atomic(operation)

    def account(self, account_id: int) -> AccountState:
        with self._connect() as db:
            row = db.execute(
                "SELECT debits_pending,debits_posted,credits_pending,credits_posted "
                "FROM ordivon_capital.accounts WHERE id=%s", (str(account_id),)
            ).fetchone()
        if row is None:
            raise KeyError(account_id)
        return AccountState(account_id, *(int(x) for x in row))

    def transfer(self, transfer_id: int) -> TransferState | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT debit_id,credit_id,amount,pending_id,operation,status "
                "FROM ordivon_capital.transfers WHERE id=%s", (str(transfer_id),)
            ).fetchone()
        if row is None:
            return None
        debit, credit, amount, pending, operation, status = row
        return TransferState(
            transfer_id=transfer_id,
            debit_account_id=int(debit),
            credit_account_id=int(credit),
            amount=int(amount),
            pending_id=int(pending or 0),
            operation=str(operation),
            status=str(status),
        )

    def apply_immediate_transfer(
        self, *, transfer_id: int, debit_account_id: int,
        credit_account_id: int, amount: int,
    ) -> LedgerApplyStatus:
        return self._apply(
            transfer_id=transfer_id, debit_account_id=debit_account_id,
            credit_account_id=credit_account_id, amount=amount,
            operation="IMMEDIATE", pending_id=0,
        )

    def apply_instruction(self, instruction: AccountingInstruction) -> LedgerApplyStatus:
        kind = {
            AccountingOperation.PENDING: "PENDING",
            AccountingOperation.POST_PENDING_TRANSFER: "POST",
            AccountingOperation.VOID_PENDING_TRANSFER: "VOID",
        }[instruction.operation]
        return self._apply(
            transfer_id=instruction.transfer_id,
            debit_account_id=instruction.debit_account_id,
            credit_account_id=instruction.credit_account_id,
            amount=instruction.amount,
            operation=kind,
            pending_id=instruction.pending_id,
        )

    def _apply(
        self, *, transfer_id: int, debit_account_id: int,
        credit_account_id: int, amount: int, operation: str, pending_id: int,
    ) -> LedgerApplyStatus:
        if amount < 0 or amount >= 2**128 or debit_account_id == credit_account_id:
            raise ValueError("invalid accounting amount or account identity")

        def operation_tx(db: psycopg.Connection) -> LedgerApplyStatus:
            existing = db.execute(
                "SELECT debit_id,credit_id,amount,pending_id,operation "
                "FROM ordivon_capital.transfers WHERE id=%s", (str(transfer_id),)
            ).fetchone()
            expected = (
                str(debit_account_id), str(credit_account_id),
                amount, str(pending_id) if pending_id else None, operation,
            )
            if existing is not None:
                return (
                    LedgerApplyStatus.EXISTS
                    if tuple(existing) == expected
                    else LedgerApplyStatus.ID_CONFLICT
                )

            # Lock accounts in stable order to exclude update races; PostgreSQL
            # SERIALIZABLE also detects predicate conflicts and retries the WHOLE txn.
            rows = db.execute(
                "SELECT id,no_overdraft,debits_pending,debits_posted,"
                "credits_pending,credits_posted FROM ordivon_capital.accounts "
                "WHERE id = ANY(%s) ORDER BY id FOR UPDATE",
                ([str(debit_account_id), str(credit_account_id)],),
            ).fetchall()
            if len(rows) != 2:
                raise KeyError("account missing")
            accounts = {row[0]: row for row in rows}
            if operation in ("IMMEDIATE", "PENDING"):
                debit = accounts[str(debit_account_id)]
                available = int(debit[5]) - int(debit[3]) - int(debit[2])
                if debit[1] and amount > available:
                    return LedgerApplyStatus.EXCEEDS_CREDITS
                suffix = "posted" if operation == "IMMEDIATE" else "pending"
                db.execute(
                    f"UPDATE ordivon_capital.accounts "
                    f"SET debits_{suffix}=debits_{suffix}+%s WHERE id=%s",
                    (amount, str(debit_account_id)),
                )
                db.execute(
                    f"UPDATE ordivon_capital.accounts "
                    f"SET credits_{suffix}=credits_{suffix}+%s WHERE id=%s",
                    (amount, str(credit_account_id)),
                )
                status = "POSTED" if operation == "IMMEDIATE" else "PENDING"
            else:
                pending = db.execute(
                    "SELECT debit_id,credit_id,amount,status "
                    "FROM ordivon_capital.transfers "
                    "WHERE id=%s AND operation='PENDING' FOR UPDATE",
                    (str(pending_id),),
                ).fetchone()
                if pending is None:
                    return LedgerApplyStatus.PENDING_TRANSFER_NOT_FOUND
                pdebit, pcredit, pamount, pstatus = pending
                if pstatus == "POSTED":
                    return LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED
                if pstatus == "VOIDED":
                    return LedgerApplyStatus.PENDING_TRANSFER_ALREADY_VOIDED
                if (pdebit, pcredit) != (str(debit_account_id), str(credit_account_id)):
                    return LedgerApplyStatus.ID_CONFLICT
                if operation == "POST" and amount != pamount:
                    return LedgerApplyStatus.PENDING_TRANSFER_AMOUNT_MISMATCH
                for direction, account in (
                    ("debits", debit_account_id), ("credits", credit_account_id)
                ):
                    posted = ", " + f"{direction}_posted={direction}_posted+%s" if operation == "POST" else ""
                    args = (
                        (pamount, pamount, str(account))
                        if operation == "POST" else (pamount, str(account))
                    )
                    db.execute(
                        f"UPDATE ordivon_capital.accounts SET "
                        f"{direction}_pending={direction}_pending-%s{posted} WHERE id=%s",
                        args,
                    )
                db.execute(
                    "UPDATE ordivon_capital.transfers SET status=%s WHERE id=%s",
                    ("POSTED" if operation == "POST" else "VOIDED", str(pending_id)),
                )
                status = "POSTED" if operation == "POST" else "VOIDED"
            db.execute(
                "INSERT INTO ordivon_capital.transfers("
                "id,debit_id,credit_id,amount,pending_id,operation,status"
                ") VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (
                    str(transfer_id), str(debit_account_id), str(credit_account_id),
                    amount, str(pending_id) if pending_id else None, operation, status,
                ),
            )
            return LedgerApplyStatus.CREATED

        return self._atomic(operation_tx)

    def import_quiesced_sqlite(
        self, source: str | Path, *, confirmed_quiesced: bool = False,
    ) -> dict[str, object]:
        """One-way verified copy; never mutates the legacy source.

        Caller must have disabled every SQLite producer before invocation.
        This method does not claim it can remotely stop installed workers.
        PostgreSQL target must be empty. Result is not a deployment cutover.
        """
        import json
        import sqlite3

        path = Path(source)
        if not confirmed_quiesced:
            raise RuntimeError("legacy SQLite writer quiescence must be independently proven")
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("legacy SQLite source must be a regular non-symlink file")
        # Read the exact path: SQLite URI interpolation treats literal #/? as syntax.
        with closing(sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)) as legacy:
            legacy.execute("BEGIN")
            accounts = legacy.execute(
                "SELECT id,no_overdraft,debits_pending,debits_posted,"
                "credits_pending,credits_posted FROM accounts ORDER BY id"
            ).fetchall()
            transfers = legacy.execute(
                "SELECT id,debit_id,credit_id,amount,pending_id,operation,status "
                "FROM transfers ORDER BY id"
            ).fetchall()
            # Normalize only mathematical integer fields, not opaque u128 IDs.
            original_accounts = sorted([
                (str(a[0]), bool(a[1]), *(int(x) for x in a[2:]))
                for a in accounts
            ])
            original_transfers = sorted([
                (str(t[0]),str(t[1]),str(t[2]),int(t[3]),
                 str(t[4]) if t[4] is not None else None,str(t[5]),str(t[6]))
                for t in transfers
            ])
            digest = "sha256:" + hashlib.sha256(
                json.dumps(
                    [original_accounts, original_transfers], separators=(",", ":")
                ).encode()
            ).hexdigest()
            with self._connect() as pg:
                with pg.transaction():
                    pg.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                    # No silent upsert or partial merges; exact empty target only.
                    size = pg.execute(
                        "(SELECT count(*) FROM ordivon_capital.accounts) UNION ALL "
                        "(SELECT count(*) FROM ordivon_capital.transfers)"
                    ).fetchall()
                    if any(int(x[0]) for x in size):
                        raise RuntimeError("PG accounting migration target must be empty")
                    for row in original_accounts:
                        pg.execute(
                            "INSERT INTO ordivon_capital.accounts VALUES(%s,%s,%s,%s,%s,%s)",
                            row,
                        )
                    for row in original_transfers:
                        pg.execute(
                            "INSERT INTO ordivon_capital.transfers VALUES(%s,%s,%s,%s,%s,%s,%s)",
                            row,
                        )
                    pg_accounts = sorted([
                        (str(a[0]),bool(a[1]),*(int(x) for x in a[2:]))
                        for a in pg.execute(
                            "SELECT id,no_overdraft,debits_pending,debits_posted,"
                            "credits_pending,credits_posted "
                            "FROM ordivon_capital.accounts"
                        ).fetchall()
                    ])
                    pg_transfers = sorted([
                        (str(t[0]),str(t[1]),str(t[2]),int(t[3]),
                         str(t[4]) if t[4] is not None else None,str(t[5]),str(t[6]))
                        for t in pg.execute(
                            "SELECT id,debit_id,credit_id,amount,pending_id,operation,status "
                            "FROM ordivon_capital.transfers"
                        ).fetchall()
                    ])
                    if pg_accounts != original_accounts or pg_transfers != original_transfers:
                        raise RuntimeError("PostgreSQL migration readback identity mismatch")
                    # Both source read snapshot and PG transaction remain active here.
            return {
                "sourceDigest": digest,
                "sourceAccounts": len(original_accounts),
                "sourceTransfers": len(original_transfers),
                "postgresAccounts": len(pg_accounts),
                "postgresTransfers": len(pg_transfers),
                "standing": "VERIFIED_COPY_NOT_CONSUMER_CUTOVER",
            }
