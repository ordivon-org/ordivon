"""PostgreSQL-only accounting ledger: native SERIALIZABLE transactions, no SQLite writes."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import TypeVar

import psycopg
from psycopg.errors import DeadlockDetected, SerializationFailure, UniqueViolation

from .substrate import (
    AccountingAccount,
    AccountingInstruction,
    AccountingOperation,
    AccountState,
    LedgerApplyStatus,
    TransferState,
)

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
                self._verify_schema(db)

    @staticmethod
    def _verify_schema(db: psycopg.Connection) -> None:
        """Reject same-name counterfeit tables before admitting accounting effects.

        PostgreSQL pg_catalog is the authoritative type/constraint structure.
        This validates admission topology; it is not a proof of arbitrary SQL
        trigger or constraint expressions nor a production deployment receipt.
        """
        expected_columns = {
            "accounts": [
                ("id", "text", True),
                ("no_overdraft", "boolean", True),
                ("debits_pending", "numeric(39,0)", True),
                ("debits_posted", "numeric(39,0)", True),
                ("credits_pending", "numeric(39,0)", True),
                ("credits_posted", "numeric(39,0)", True),
            ],
            "transfers": [
                ("id", "text", True),
                ("debit_id", "text", True),
                ("credit_id", "text", True),
                ("amount", "numeric(39,0)", True),
                ("pending_id", "text", False),
                ("operation", "text", True),
                ("status", "text", True),
            ],
        }
        expected_constraints = {
            "accounts": {
                ("p", ("id",)),
                *{("c", (name,)) for name in (
                    "debits_pending", "debits_posted", "credits_pending", "credits_posted"
                )},
            },
            "transfers": {
                ("p", ("id",)),
                ("f", ("debit_id",)),
                ("f", ("credit_id",)),
                ("c", ("amount",)),
                ("c", ("operation",)),
                ("c", ("status",)),
            },
        }
        # PostgreSQL 18 native deparser is the constraint expression oracle.
        # Matching only CHECK count/columns admits weakening like x > -100.
        # On a future PostgreSQL deparser change this deliberately fails closed
        # until the exact new server SourceCut is independently qualified.
        required_checks = {
            "accounts": {
                "debits_pending": "CHECK ((debits_pending >= (0)::numeric))",
                "debits_posted": "CHECK ((debits_posted >= (0)::numeric))",
                "credits_pending": "CHECK ((credits_pending >= (0)::numeric))",
                "credits_posted": "CHECK ((credits_posted >= (0)::numeric))",
            },
            "transfers": {
                "amount": "CHECK ((amount >= (0)::numeric))",
                "operation": (
                    "CHECK ((operation = ANY (ARRAY['IMMEDIATE'::text, "
                    "'PENDING'::text, 'POST'::text, 'VOID'::text])))"
                ),
                "status": (
                    "CHECK ((status = ANY (ARRAY['PENDING'::text, "
                    "'POSTED'::text, 'VOIDED'::text])))"
                ),
            },
        }
        for table, columns in expected_columns.items():
            observed = db.execute(
                """
                SELECT c.oid, c.relkind, c.relpersistence, c.relrowsecurity, c.relforcerowsecurity,
                    a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod),
                    a.attnotnull
                FROM pg_catalog.pg_namespace n
                JOIN pg_catalog.pg_class c ON c.relnamespace=n.oid
                JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid
                WHERE n.nspname='ordivon_capital' AND c.relname=%s
                    AND a.attnum>0 AND NOT a.attisdropped
                ORDER BY a.attnum
                """,
                (table,),
            ).fetchall()
            if (
                len(observed) != len(columns)
                or [(name, kind, nullable) for _, _, _, _, _, name, kind, nullable in observed]
                != columns
                or any(
                    kind != "r" or durability != "p" or rls or forced
                    for _, kind, durability, rls, forced, *_ in observed
                )
            ):
                raise RuntimeError(f"PostgreSQL accounting schema mismatch: {table} columns")
            oid = observed[0][0]
            constraints = db.execute(
                """
                SELECT con.contype, array_agg(att.attname ORDER BY cols.position),
                    bool_and(con.convalidated), pg_catalog.pg_get_constraintdef(con.oid),
                    con.confrelid
                FROM pg_catalog.pg_constraint con
                JOIN LATERAL unnest(con.conkey) WITH ORDINALITY
                    AS cols(attnum, position) ON TRUE
                JOIN pg_catalog.pg_attribute att
                    ON att.attrelid=con.conrelid AND att.attnum=cols.attnum
                WHERE con.conrelid=%s AND con.contype IN ('p', 'f', 'c')
                GROUP BY con.oid, con.contype
                """,
                (oid,),
            ).fetchall()
            actual = {
                (kind, tuple(fields)) for kind, fields, valid, _, _ in constraints
                if valid
            }
            if actual != expected_constraints[table] or len(constraints) != len(actual):
                raise RuntimeError(f"PostgreSQL accounting schema mismatch: {table} constraints")
            for kind, fields, valid, definition, reference in constraints:
                if not valid:
                    raise RuntimeError(f"PostgreSQL accounting schema mismatch: {table} validation")
                if kind == "c" and definition != required_checks[table][fields[0]]:
                    raise RuntimeError(f"PostgreSQL accounting schema mismatch: {table} checks")
                if kind == "f":
                    parent = db.execute(
                        "SELECT 'ordivon_capital.accounts'::regclass::oid"
                    ).fetchone()[0]
                    if reference != parent:
                        raise RuntimeError(f"PostgreSQL accounting schema mismatch: {table} foreign key")
            if db.execute(
                """
                SELECT EXISTS(
                    SELECT 1 FROM pg_catalog.pg_trigger
                    WHERE tgrelid=%s AND NOT tgisinternal
                )
                """,
                (oid,),
            ).fetchone()[0]:
                raise RuntimeError(f"PostgreSQL accounting schema mismatch: {table} triggers")

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
        return self._atomic(lambda db: self._create_account_in_transaction(db, account))

    @staticmethod
    def _create_account_in_transaction(
        db: psycopg.Connection, account: AccountingAccount,
    ) -> LedgerApplyStatus:
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

    def account(self, account_id: int) -> AccountState:
        with self._connect() as db:
            return self._account_in_transaction(db, account_id)

    @staticmethod
    def _account_in_transaction(db: psycopg.Connection, account_id: int) -> AccountState:
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
        return self._atomic(lambda db: self._apply_in_transaction(
            db, transfer_id=transfer_id, debit_account_id=debit_account_id,
            credit_account_id=credit_account_id, amount=amount,
            operation=operation, pending_id=pending_id,
        ))

    @staticmethod
    def _apply_in_transaction(
        db: psycopg.Connection, *, transfer_id: int, debit_account_id: int,
        credit_account_id: int, amount: int, operation: str, pending_id: int,
    ) -> LedgerApplyStatus:
        if amount < 0 or amount >= 2**128 or debit_account_id == credit_account_id:
            raise ValueError("invalid accounting amount or account identity")

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
