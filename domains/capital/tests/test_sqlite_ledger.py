from __future__ import annotations

import sqlite3
from pathlib import Path

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
