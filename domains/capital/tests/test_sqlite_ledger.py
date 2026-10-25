from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ordivon_capital.accounting.durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
    binding_for_namespace,
)
from ordivon_capital.accounting.sqlite_ledger import (
    LedgerApplyStatus,
    SQLiteAccountingLedger,
)
from ordivon_capital.accounting.substrate import (
    AccountingAccount,
    AccountingOperation,
    reservation_instruction,
    resolution_instruction,
    stable_accounting_id,
)


def prepare(path: Path):
    ledger = SQLiteAccountingLedger(path)
    ns = CapitalAccountNamespace("owner:test", "parcel:usd:test")
    fund = AccountingAccount(stable_accounting_id("test", "fund"))
    available = ns.account(CapitalAccountRole.AVAILABLE)
    encumbrance = ns.account(CapitalAccountRole.ENCUMBRANCE)
    assert ledger.create_account(fund) is LedgerApplyStatus.CREATED
    assert ledger.create_account(available) is LedgerApplyStatus.CREATED
    assert ledger.create_account(encumbrance) is LedgerApplyStatus.CREATED
    assert (
        ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("test", "funding"),
            debit_account_id=fund.account_id,
            credit_account_id=available.account_id,
            amount=1000,
        )
        is LedgerApplyStatus.CREATED
    )
    return ledger, ns


def test_reserve_void_post_replay_and_scarcity(tmp_path):
    ledger, ns = prepare(tmp_path / "ledger.sqlite3")
    first = binding_for_namespace(
        namespace=ns,
        reservation_ref="reservation:first",
        amount=700,
    )
    assert ledger.apply_instruction(reservation_instruction(first)) is LedgerApplyStatus.CREATED

    over = binding_for_namespace(
        namespace=ns,
        reservation_ref="reservation:over",
        amount=400,
    )
    assert (
        ledger.apply_instruction(reservation_instruction(over))
        is LedgerApplyStatus.EXCEEDS_CREDITS
    )

    release = resolution_instruction(
        binding=first,
        operation=AccountingOperation.VOID_PENDING_TRANSFER,
        resolution_ref="effect:release",
    )
    assert release is not None
    assert ledger.apply_instruction(release) is LedgerApplyStatus.CREATED

    second = binding_for_namespace(
        namespace=ns,
        reservation_ref="reservation:second",
        amount=600,
    )
    assert ledger.apply_instruction(reservation_instruction(second)) is LedgerApplyStatus.CREATED
    consume = resolution_instruction(
        binding=second,
        operation=AccountingOperation.POST_PENDING_TRANSFER,
        resolution_ref="effect:consume",
    )
    assert consume is not None
    assert ledger.apply_instruction(consume) is LedgerApplyStatus.CREATED
    assert ledger.apply_instruction(consume) is LedgerApplyStatus.EXISTS

    late_release = resolution_instruction(
        binding=second,
        operation=AccountingOperation.VOID_PENDING_TRANSFER,
        resolution_ref="effect:late-release",
    )
    assert late_release is not None
    assert (
        ledger.apply_instruction(late_release)
        is LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED
    )

    available = ledger.account(ns.available_account_id)
    encumbrance = ledger.account(ns.encumbrance_account_id)
    assert available.debits_pending == 0
    assert available.debits_posted == 600
    assert encumbrance.credits_pending == 0
    assert encumbrance.credits_posted == 600
    ledger.close()


def test_pending_and_terminal_state_survive_two_restarts(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    ledger, ns = prepare(path)
    binding = binding_for_namespace(
        namespace=ns,
        reservation_ref="reservation:restart",
        amount=700,
    )
    pending = reservation_instruction(binding)
    assert ledger.apply_instruction(pending) is LedgerApplyStatus.CREATED
    ledger.close()

    ledger = SQLiteAccountingLedger(path)
    assert ledger.account(ns.available_account_id).debits_pending == 700
    consume = resolution_instruction(
        binding=binding,
        operation=AccountingOperation.POST_PENDING_TRANSFER,
        resolution_ref="effect:restart-consume",
    )
    assert consume is not None
    assert ledger.apply_instruction(consume) is LedgerApplyStatus.CREATED
    ledger.close()

    ledger = SQLiteAccountingLedger(path)
    assert ledger.account(ns.available_account_id).debits_pending == 0
    assert ledger.account(ns.available_account_id).debits_posted == 700
    assert ledger.apply_instruction(consume) is LedgerApplyStatus.EXISTS
    assert ledger.transfer(binding.pending_transfer_id) is not None
    assert ledger.transfer(consume.transfer_id) is not None
    ledger.close()


def test_conflicting_replay_is_rejected_without_mutation(tmp_path):
    ledger, ns = prepare(tmp_path / "ledger.sqlite3")
    binding = binding_for_namespace(
        namespace=ns,
        reservation_ref="reservation:conflict",
        amount=100,
    )
    pending = reservation_instruction(binding)
    assert ledger.apply_instruction(pending) is LedgerApplyStatus.CREATED
    before = ledger.account(ns.available_account_id)

    conflicting = type(pending)(
        operation=pending.operation,
        transfer_id=pending.transfer_id,
        debit_account_id=pending.debit_account_id,
        credit_account_id=pending.credit_account_id,
        amount=101,
        pending_id=0,
    )
    assert ledger.apply_instruction(conflicting) is LedgerApplyStatus.ID_CONFLICT
    assert ledger.account(ns.available_account_id) == before
    ledger.close()


def test_sqlite_runtime_and_journal_mode_are_current_canonical_runtime(tmp_path):
    ledger, _ = prepare(tmp_path / "ledger.sqlite3")
    assert ledger.sqlite_version == sqlite3.sqlite_version
    assert tuple(map(int, sqlite3.sqlite_version.split("."))) >= (3, 53, 1)
    mode = ledger._db.execute("PRAGMA journal_mode").fetchone()[0]  # noqa: SLF001
    sync = ledger._db.execute("PRAGMA synchronous").fetchone()[0]  # noqa: SLF001
    assert mode == "wal"
    assert sync == 2
    ledger.close()


@pytest.mark.parametrize("second_amount", [7, 9])
def test_concurrent_transfer_natural_key_is_atomic_before_pg_cutover(tmp_path, second_amount):
    """Two independent DB connections must not leak a raw uniqueness failure.

    This qualification remains necessary while the SQLite accounting consumer
    is being replaced by the PostgreSQL-first store.
    """
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, BrokenBarrierError

    database = tmp_path / "concurrent.sqlite3"
    with SQLiteAccountingLedger(database) as ledger:
        assert ledger.create_account(AccountingAccount(101)) is LedgerApplyStatus.CREATED
        assert ledger.create_account(AccountingAccount(202)) is LedgerApplyStatus.CREATED

    # The old code checks existence before opening a write transaction. Force
    # both readers to see the same absent ID, rather than hoping for timing.
    reader_gate = Barrier(2)

    class InterleavedLedger(SQLiteAccountingLedger):
        def _existing_status(self, **kwargs):
            seen = super()._existing_status(**kwargs)
            try:
                reader_gate.wait(timeout=0.5)
            except BrokenBarrierError:
                pass  # After the fix the second reader waits for the writer.
            return seen

    def write(amount: int):
        with InterleavedLedger(database) as ledger:
            return ledger.apply_immediate_transfer(
                transfer_id=303,
                debit_account_id=101,
                credit_account_id=202,
                amount=amount,
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(write, 7)
        second = pool.submit(write, second_amount)
        results = {first.result(timeout=10), second.result(timeout=10)}

    expected_loser = (
        LedgerApplyStatus.EXISTS
        if second_amount == 7
        else LedgerApplyStatus.ID_CONFLICT
    )
    assert results == {LedgerApplyStatus.CREATED, expected_loser}
    with SQLiteAccountingLedger(database) as ledger:
        transfer = ledger.transfer(303)
        assert transfer is not None
        assert transfer.amount in {7, second_amount}
        assert ledger.account(101).debits_posted == transfer.amount
        assert ledger.account(202).credits_posted == transfer.amount


def test_concurrent_account_create_has_typed_exact_replay(tmp_path):
    """The absent account row cannot authorize two uncoordinated inserts."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier, BrokenBarrierError

    database = tmp_path / "racing-accounts.sqlite3"
    gate = Barrier(2)

    class CursorProxy:
        def __init__(self, real):
            self.real = real

        def fetchone(self):
            value = self.real.fetchone()
            try:
                gate.wait(timeout=0.5)
            except BrokenBarrierError:
                pass
            return value

    class ConnectionProxy:
        def __init__(self, real):
            self.real = real

        def execute(self, statement, *args):
            cur = self.real.execute(statement, *args)
            if statement.strip().startswith("SELECT no_overdraft FROM accounts"):
                return CursorProxy(cur)
            return cur

        def __getattr__(self, name):
            return getattr(self.real, name)

    def create(no_overdraft: bool):
        with SQLiteAccountingLedger(database) as ledger:
            ledger._db = ConnectionProxy(ledger._db)  # noqa: SLF001
            return ledger.create_account(AccountingAccount(505, no_overdraft))

    # Schema already exists before the workers connect.
    with SQLiteAccountingLedger(database):
        pass
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(create, True)
        second = pool.submit(create, True)
        results = {first.result(timeout=10), second.result(timeout=10)}
    assert results == {LedgerApplyStatus.CREATED, LedgerApplyStatus.EXISTS}
    with SQLiteAccountingLedger(database) as ledger:
        assert ledger.create_account(AccountingAccount(505, False)) is LedgerApplyStatus.ID_CONFLICT
