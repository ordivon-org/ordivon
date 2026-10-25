from __future__ import annotations

import sqlite3
from pathlib import Path

from .substrate import (
    AccountingAccount,
    AccountingInstruction,
    AccountingOperation,
    AccountState,
    LedgerApplyStatus,
    TransferState,
)


class SQLiteAccountingLedger:
    """Bounded single-host mechanical accounting substrate on SQLite WAL."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._db = sqlite3.connect(path, isolation_level=None)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts(
              id TEXT PRIMARY KEY,
              no_overdraft INTEGER NOT NULL,
              debits_pending INTEGER NOT NULL DEFAULT 0,
              debits_posted INTEGER NOT NULL DEFAULT 0,
              credits_pending INTEGER NOT NULL DEFAULT 0,
              credits_posted INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS transfers(
              id TEXT PRIMARY KEY,
              debit_id TEXT NOT NULL REFERENCES accounts(id),
              credit_id TEXT NOT NULL REFERENCES accounts(id),
              amount INTEGER NOT NULL,
              pending_id TEXT,
              operation TEXT NOT NULL,
              status TEXT NOT NULL
            );
            """
        )

    @property
    def sqlite_version(self) -> str:
        return sqlite3.sqlite_version

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> SQLiteAccountingLedger:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create_account(self, account: AccountingAccount) -> LedgerApplyStatus:
        expected = int(account.no_overdraft)
        # Natural-key admission is owned by the database, not a prior absent
        # SELECT: concurrent creators otherwise both attempt an INSERT.
        inserted = self._db.execute(
            "INSERT INTO accounts(id,no_overdraft) VALUES(?,?) "
            "ON CONFLICT(id) DO NOTHING RETURNING id",
            (str(account.account_id), expected),
        ).fetchone()
        if inserted is not None:
            return LedgerApplyStatus.CREATED
        row = self._db.execute(
            "SELECT no_overdraft FROM accounts WHERE id=?",
            (str(account.account_id),),
        ).fetchone()
        if row is None:
            raise RuntimeError("account conflict vanished during readback")
        return (
            LedgerApplyStatus.EXISTS
            if row[0] == expected
            else LedgerApplyStatus.ID_CONFLICT
        )

    def apply_immediate_transfer(
        self,
        *,
        transfer_id: int,
        debit_account_id: int,
        credit_account_id: int,
        amount: int,
    ) -> LedgerApplyStatus:
        return self._apply(
            transfer_id=transfer_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            operation="IMMEDIATE",
            pending_id=0,
        )

    def apply_instruction(
        self, instruction: AccountingInstruction
    ) -> LedgerApplyStatus:
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

    def account(self, account_id: int) -> AccountState:
        row = self._db.execute(
            """
            SELECT debits_pending,debits_posted,credits_pending,credits_posted
            FROM accounts WHERE id=?
            """,
            (str(account_id),),
        ).fetchone()
        if row is None:
            raise KeyError(account_id)
        return AccountState(account_id, *map(int, row))

    def transfer(self, transfer_id: int) -> TransferState | None:
        row = self._db.execute(
            """
            SELECT debit_id,credit_id,amount,pending_id,operation,status
            FROM transfers WHERE id=?
            """,
            (str(transfer_id),),
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

    def _existing_status(
        self,
        *,
        transfer_id: int,
        debit_account_id: int,
        credit_account_id: int,
        amount: int,
        pending_id: int,
        operation: str,
    ) -> LedgerApplyStatus | None:
        row = self._db.execute(
            """
            SELECT debit_id,credit_id,amount,pending_id,operation
            FROM transfers WHERE id=?
            """,
            (str(transfer_id),),
        ).fetchone()
        if row is None:
            return None
        expected = (
            str(debit_account_id),
            str(credit_account_id),
            amount,
            str(pending_id) if pending_id else None,
            operation,
        )
        return (
            LedgerApplyStatus.EXISTS
            if tuple(row) == expected
            else LedgerApplyStatus.ID_CONFLICT
        )

    def _apply(
        self,
        *,
        transfer_id: int,
        debit_account_id: int,
        credit_account_id: int,
        amount: int,
        operation: str,
        pending_id: int,
    ) -> LedgerApplyStatus:
        # The absent-ID lookup must be serialized with the subsequent
        # balance effects and insert. Never decide replay outside this write
        # transaction: concurrent connections may both observe absence.
        self._db.execute("BEGIN IMMEDIATE")
        try:
            existing = self._existing_status(
                transfer_id=transfer_id,
                debit_account_id=debit_account_id,
                credit_account_id=credit_account_id,
                amount=amount,
                pending_id=pending_id,
                operation=operation,
            )
            if existing is not None:
                self._db.execute("COMMIT")
                return existing

            if operation in {"IMMEDIATE", "PENDING"}:
                debit = self.account(debit_account_id)
                no_overdraft = self._db.execute(
                    "SELECT no_overdraft FROM accounts WHERE id=?",
                    (str(debit_account_id),),
                ).fetchone()
                if no_overdraft is None:
                    raise KeyError(debit_account_id)
                available = (
                    debit.credits_posted
                    - debit.debits_posted
                    - debit.debits_pending
                )
                if no_overdraft[0] and amount > available:
                    self._db.execute("ROLLBACK")
                    return LedgerApplyStatus.EXCEEDS_CREDITS
                if operation == "IMMEDIATE":
                    self._db.execute(
                        "UPDATE accounts SET debits_posted=debits_posted+? WHERE id=?",
                        (amount, str(debit_account_id)),
                    )
                    self._db.execute(
                        "UPDATE accounts SET credits_posted=credits_posted+? WHERE id=?",
                        (amount, str(credit_account_id)),
                    )
                    status = "POSTED"
                else:
                    self._db.execute(
                        "UPDATE accounts SET debits_pending=debits_pending+? WHERE id=?",
                        (amount, str(debit_account_id)),
                    )
                    self._db.execute(
                        "UPDATE accounts SET credits_pending=credits_pending+? WHERE id=?",
                        (amount, str(credit_account_id)),
                    )
                    status = "PENDING"
            else:
                pending = self._db.execute(
                    """
                    SELECT debit_id,credit_id,amount,status
                    FROM transfers WHERE id=? AND operation='PENDING'
                    """,
                    (str(pending_id),),
                ).fetchone()
                if pending is None:
                    self._db.execute("ROLLBACK")
                    return LedgerApplyStatus.PENDING_TRANSFER_NOT_FOUND
                pdebit, pcredit, pamount, pstatus = pending
                if pstatus == "POSTED":
                    self._db.execute("ROLLBACK")
                    return LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED
                if pstatus == "VOIDED":
                    self._db.execute("ROLLBACK")
                    return LedgerApplyStatus.PENDING_TRANSFER_ALREADY_VOIDED
                if (
                    str(debit_account_id) != pdebit
                    or str(credit_account_id) != pcredit
                ):
                    self._db.execute("ROLLBACK")
                    return LedgerApplyStatus.ID_CONFLICT
                if operation == "POST":
                    if amount != pamount:
                        self._db.execute("ROLLBACK")
                        return LedgerApplyStatus.PENDING_TRANSFER_AMOUNT_MISMATCH
                    self._db.execute(
                        """
                        UPDATE accounts
                        SET debits_pending=debits_pending-?,
                            debits_posted=debits_posted+?
                        WHERE id=?
                        """,
                        (pamount, pamount, str(debit_account_id)),
                    )
                    self._db.execute(
                        """
                        UPDATE accounts
                        SET credits_pending=credits_pending-?,
                            credits_posted=credits_posted+?
                        WHERE id=?
                        """,
                        (pamount, pamount, str(credit_account_id)),
                    )
                    self._db.execute(
                        "UPDATE transfers SET status='POSTED' WHERE id=?",
                        (str(pending_id),),
                    )
                    status = "POSTED"
                elif operation == "VOID":
                    self._db.execute(
                        "UPDATE accounts SET debits_pending=debits_pending-? WHERE id=?",
                        (pamount, str(debit_account_id)),
                    )
                    self._db.execute(
                        "UPDATE accounts SET credits_pending=credits_pending-? WHERE id=?",
                        (pamount, str(credit_account_id)),
                    )
                    self._db.execute(
                        "UPDATE transfers SET status='VOIDED' WHERE id=?",
                        (str(pending_id),),
                    )
                    status = "VOIDED"
                else:
                    raise ValueError(f"unsupported accounting operation: {operation}")

            self._db.execute(
                """
                INSERT INTO transfers(
                  id,debit_id,credit_id,amount,pending_id,operation,status
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    str(transfer_id),
                    str(debit_account_id),
                    str(credit_account_id),
                    amount,
                    str(pending_id) if pending_id else None,
                    operation,
                    status,
                ),
            )
            self._db.execute("COMMIT")
            return LedgerApplyStatus.CREATED
        except Exception:
            self._db.execute("ROLLBACK")
            raise
