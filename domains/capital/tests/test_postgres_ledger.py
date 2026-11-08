"""Physical PostgreSQL-first accounting contract against a dedicated disposable cluster."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ordivon_capital.accounting.durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
    binding_for_namespace,
)
from ordivon_capital.accounting.postgres_ledger import PostgresAccountingLedger
from ordivon_capital.accounting.substrate import (
    AccountingAccount,
    AccountingOperation,
    LedgerApplyStatus,
    reservation_instruction,
    resolution_instruction,
    stable_accounting_id,
)

DSN = os.environ.get("ORDIVON_CAPITAL_PG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="disposable PostgreSQL DSN is required")


@pytest.fixture(autouse=True)
def clear_disposable_pg_ledger():
    if not DSN:
        yield
        return
    import psycopg

    PostgresAccountingLedger(DSN).close()
    with psycopg.connect(DSN) as db:
        db.execute("TRUNCATE ordivon_capital.transfers, ordivon_capital.accounts")
    yield


def test_pg_reserve_void_post_restart_and_exact_replay():
    assert DSN
    with PostgresAccountingLedger(DSN) as ledger:
        ns = CapitalAccountNamespace("owner:test", "parcel:usd:test")
        fund = AccountingAccount(stable_accounting_id("test", "fund"))
        available = ns.account(CapitalAccountRole.AVAILABLE)
        encumbrance = ns.account(CapitalAccountRole.ENCUMBRANCE)
        for account in (fund, available, encumbrance):
            assert ledger.create_account(account) == LedgerApplyStatus.CREATED
        assert ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("test", "funding"),
            debit_account_id=fund.account_id,
            credit_account_id=available.account_id,
            amount=1000,
        ) == LedgerApplyStatus.CREATED
        first = binding_for_namespace(
            namespace=ns, reservation_ref="reservation:first", amount=700
        )
        assert ledger.apply_instruction(reservation_instruction(first)) == LedgerApplyStatus.CREATED
        over = binding_for_namespace(
            namespace=ns, reservation_ref="reservation:over", amount=400
        )
        assert ledger.apply_instruction(reservation_instruction(over)) == LedgerApplyStatus.EXCEEDS_CREDITS
        release = resolution_instruction(
            binding=first, operation=AccountingOperation.VOID_PENDING_TRANSFER,
            resolution_ref="effect:release",
        )
        assert ledger.apply_instruction(release) == LedgerApplyStatus.CREATED
        second = binding_for_namespace(
            namespace=ns, reservation_ref="reservation:second", amount=600
        )
        assert ledger.apply_instruction(reservation_instruction(second)) == LedgerApplyStatus.CREATED
        consume = resolution_instruction(
            binding=second, operation=AccountingOperation.POST_PENDING_TRANSFER,
            resolution_ref="effect:consume",
        )
        assert ledger.apply_instruction(consume) == LedgerApplyStatus.CREATED
    with PostgresAccountingLedger(DSN) as reopened:
        assert reopened.apply_instruction(consume) == LedgerApplyStatus.EXISTS
        assert reopened.account(ns.available_account_id).debits_pending == 0
        assert reopened.account(ns.available_account_id).debits_posted == 600
        assert reopened.account(ns.encumbrance_account_id).credits_posted == 600
        late = resolution_instruction(
            binding=second, operation=AccountingOperation.VOID_PENDING_TRANSFER,
            resolution_ref="effect:late-release",
        )
        assert reopened.apply_instruction(late) == LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED


@pytest.mark.parametrize("same_amount", [True, False])
def test_pg_concurrent_transfer_identity_and_balance_are_one_commit(same_amount):
    assert DSN
    with PostgresAccountingLedger(DSN) as store:
        for n in (101, 202):
            assert store.create_account(AccountingAccount(n)) == LedgerApplyStatus.CREATED
    gate = Barrier(12)
    amounts = [7] * 12 if same_amount else [7 if i % 2 else 9 for i in range(12)]
    def operation(amount):
        gate.wait(timeout=25)
        with PostgresAccountingLedger(DSN) as store:
            return store.apply_immediate_transfer(
                transfer_id=303, debit_account_id=101, credit_account_id=202,
                amount=amount,
            )
    with ThreadPoolExecutor(max_workers=12) as pool:
        states = list(pool.map(operation, amounts))
    assert states.count(LedgerApplyStatus.CREATED) == 1
    assert set(states) <= {LedgerApplyStatus.CREATED, LedgerApplyStatus.EXISTS, LedgerApplyStatus.ID_CONFLICT}
    with PostgresAccountingLedger(DSN) as ledger:
        item = ledger.transfer(303)
        assert item is not None
        assert ledger.account(101).debits_posted == item.amount
        assert ledger.account(202).credits_posted == item.amount


def test_pg_concurrent_account_identity():
    assert DSN
    gate = Barrier(10)
    def operation(_):
        gate.wait(timeout=25)
        with PostgresAccountingLedger(DSN) as store:
            return store.create_account(AccountingAccount(505, True))
    with ThreadPoolExecutor(max_workers=10) as pool:
        statuses = list(pool.map(operation, range(10)))
    assert statuses.count(LedgerApplyStatus.CREATED) == 1
    assert statuses.count(LedgerApplyStatus.EXISTS) == 9
    with PostgresAccountingLedger(DSN) as ledger:
        assert ledger.create_account(AccountingAccount(505, False)) == LedgerApplyStatus.ID_CONFLICT




def test_pg_concurrent_scarcity_is_one_serializable_balance():
    assert DSN
    with PostgresAccountingLedger(DSN) as ledger:
        assert ledger.create_account(AccountingAccount(701)) == LedgerApplyStatus.CREATED
        assert ledger.create_account(AccountingAccount(702, True)) == LedgerApplyStatus.CREATED
        assert ledger.create_account(AccountingAccount(703)) == LedgerApplyStatus.CREATED
        assert ledger.apply_immediate_transfer(
            transfer_id=711, debit_account_id=701, credit_account_id=702, amount=1000,
        ) == LedgerApplyStatus.CREATED
    gate=Barrier(2)
    def reserve(identity):
        gate.wait(timeout=15)
        with PostgresAccountingLedger(DSN) as ledger:
            return ledger.apply_immediate_transfer(
                transfer_id=identity, debit_account_id=702, credit_account_id=703,
                amount=700,
            )
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(reserve,(712,713)))
    assert sorted(outcomes)==sorted((
        LedgerApplyStatus.CREATED, LedgerApplyStatus.EXCEEDS_CREDITS
    ))
    with PostgresAccountingLedger(DSN) as ledger:
        assert ledger.account(702).debits_posted == 700
        assert ledger.account(703).credits_posted == 700


def test_pg_twelve_concurrent_cold_schema_admissions_have_one_authority():
    assert DSN
    import psycopg
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS ordivon_capital CASCADE")
    gate=Barrier(12)
    def bootstrap(_):
        gate.wait(timeout=20)
        return PostgresAccountingLedger(DSN)
    with ThreadPoolExecutor(max_workers=12) as pool:
        stores=list(pool.map(bootstrap, range(12)))
    assert len(stores)==12
    with psycopg.connect(DSN) as db:
        assert db.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='ordivon_capital'"
        ).fetchone()[0]==2







def test_pg_rejects_counterfeit_existing_accounts_schema():
    """A same-name table is not proof of the authoritative accounting contract."""
    assert DSN
    import psycopg

    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS ordivon_capital CASCADE")
        db.execute("CREATE SCHEMA ordivon_capital")
        db.execute(
            "CREATE TABLE ordivon_capital.accounts(id TEXT PRIMARY KEY)"
        )
    try:
        with pytest.raises(RuntimeError, match="schema"):
            PostgresAccountingLedger(DSN)
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute("DROP SCHEMA IF EXISTS ordivon_capital CASCADE")
        # Reestablish a canonical empty schema for other tests.
        PostgresAccountingLedger(DSN)

def test_pg_rejects_counterfeit_existing_balance_check():
    """Matching column types and CHECK count do not imply negative-balance safety."""
    assert DSN
    import psycopg

    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(
            "ALTER TABLE ordivon_capital.accounts "
            "DROP CONSTRAINT accounts_debits_pending_check"
        )
        db.execute(
            "ALTER TABLE ordivon_capital.accounts "
            "ADD CONSTRAINT counterfeit_check CHECK (debits_pending > -100)"
        )
    try:
        with pytest.raises(RuntimeError, match="schema"):
            PostgresAccountingLedger(DSN)
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute("DROP SCHEMA IF EXISTS ordivon_capital CASCADE")
        PostgresAccountingLedger(DSN)

def test_pg_rejects_unlogged_accounting_authority():
    """An unlogged table cannot supply crash-durable accounting receipts."""
    assert DSN
    import psycopg

    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("ALTER TABLE ordivon_capital.transfers SET UNLOGGED")
    try:
        with pytest.raises(RuntimeError, match="schema"):
            PostgresAccountingLedger(DSN)
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute("DROP SCHEMA IF EXISTS ordivon_capital CASCADE")
        PostgresAccountingLedger(DSN)


def test_pg_partial_post_is_one_atomic_resolution_and_releases_remainder():
    assert DSN
    ns = CapitalAccountNamespace("owner:partial", "parcel:usd:partial")
    fund = AccountingAccount(stable_accounting_id("test-partial", "fund"))
    b = binding_for_namespace(namespace=ns, reservation_ref="partial:700", amount=700)
    with PostgresAccountingLedger(DSN) as ledger:
        for account in (fund, ns.account(CapitalAccountRole.AVAILABLE),
                        ns.account(CapitalAccountRole.ENCUMBRANCE)):
            assert ledger.create_account(account) is LedgerApplyStatus.CREATED
        assert ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("test-partial", "funding"),
            debit_account_id=fund.account_id, credit_account_id=ns.available_account_id,
            amount=1000,
        ) is LedgerApplyStatus.CREATED
        assert ledger.apply_instruction(reservation_instruction(b)) is LedgerApplyStatus.CREATED
        consumed = resolution_instruction(
            binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
            resolution_ref="effect:partial-terminal", posted_amount=240,
        )
        assert consumed is not None
        assert ledger.apply_instruction(consumed) is LedgerApplyStatus.CREATED
    with PostgresAccountingLedger(DSN) as ledger:
        assert ledger.apply_instruction(consumed) is LedgerApplyStatus.EXISTS
        available = ledger.account(ns.available_account_id)
        encumbrance = ledger.account(ns.encumbrance_account_id)
        assert available.debits_pending == 0
        assert available.debits_posted == 240
        assert available.credits_posted == 1000
        assert encumbrance.credits_pending == 0
        assert encumbrance.credits_posted == 240
        assert ledger.transfer(b.pending_transfer_id).status == "POSTED"
        assert ledger.transfer(consumed.transfer_id).amount == 240
        assert ledger.apply_instruction(
            resolution_instruction(
                binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
                resolution_ref="effect:another-post", posted_amount=100,
            )
        ) is LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED
        later = binding_for_namespace(
            namespace=ns, reservation_ref="partial:remaining-available", amount=760,
        )
        assert ledger.apply_instruction(reservation_instruction(later)) is LedgerApplyStatus.CREATED


def test_pg_rejects_overposting_without_mutating_pending_balance():
    assert DSN
    ns = CapitalAccountNamespace("owner:partial", "parcel:usd:bounds")
    b = binding_for_namespace(namespace=ns, reservation_ref="partial:300", amount=300)
    with PostgresAccountingLedger(DSN) as ledger:
        for acct in (ns.account(CapitalAccountRole.AVAILABLE),
                     ns.account(CapitalAccountRole.ENCUMBRANCE)):
            assert ledger.create_account(acct) is LedgerApplyStatus.CREATED
        ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("test-partial", "seed"),
            debit_account_id=ns.encumbrance_account_id,
            credit_account_id=ns.available_account_id, amount=300,
        )
        assert ledger.apply_instruction(reservation_instruction(b)) is LedgerApplyStatus.CREATED
        from ordivon_capital.accounting.substrate import AccountingInstruction
        over = AccountingInstruction(
            operation=AccountingOperation.POST_PENDING_TRANSFER,
            transfer_id=stable_accounting_id("test-partial", "over"),
            debit_account_id=b.source_account_id,
            credit_account_id=b.encumbrance_account_id,
            amount=301, pending_id=b.pending_transfer_id,
        )
        assert ledger.apply_instruction(over) is LedgerApplyStatus.PENDING_TRANSFER_AMOUNT_MISMATCH
        assert ledger.account(b.source_account_id).debits_pending == 300
        assert ledger.account(b.encumbrance_account_id).credits_pending == 300
        assert ledger.transfer(over.transfer_id) is None



@pytest.mark.parametrize("posted", [1, 77, 699, 700])
def test_pg_partial_post_accounting_identity_at_boundary_values(posted: int):
    assert DSN
    ns = CapitalAccountNamespace("owner:partial", "parcel:usd:boundary")
    fund = AccountingAccount(stable_accounting_id("test-partial-bound", "fund"))
    b = binding_for_namespace(namespace=ns, reservation_ref="partial:bound", amount=700)
    with PostgresAccountingLedger(DSN) as ledger:
        for account in (fund, ns.account(CapitalAccountRole.AVAILABLE),
                        ns.account(CapitalAccountRole.ENCUMBRANCE)):
            assert ledger.create_account(account) == LedgerApplyStatus.CREATED
        assert ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("test-partial-bound", "funding"),
            debit_account_id=fund.account_id, credit_account_id=ns.available_account_id,
            amount=1000,
        ) == LedgerApplyStatus.CREATED
        assert ledger.apply_instruction(reservation_instruction(b)) == LedgerApplyStatus.CREATED
        resolution = resolution_instruction(
            binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
            resolution_ref="partial:bound:effect", posted_amount=posted,
        )
        assert ledger.apply_instruction(resolution) == LedgerApplyStatus.CREATED
        available = ledger.account(ns.available_account_id)
        held = ledger.account(ns.encumbrance_account_id)
        assert available.debits_pending == 0
        assert available.debits_posted == posted
        assert available.credits_posted - available.debits_posted == 1000 - posted
        assert held.credits_pending == 0
        assert held.credits_posted == posted
        assert ledger.transfer(resolution.transfer_id).amount == posted


def test_pg_partial_resolve_competing_once():
    assert DSN
    ns = CapitalAccountNamespace("owner:partial", "parcel:usd:race")
    fund = AccountingAccount(stable_accounting_id("partial-race", "fund"))
    b = binding_for_namespace(namespace=ns, reservation_ref="partial:race", amount=700)
    with PostgresAccountingLedger(DSN) as ledger:
        for account in (fund, ns.account(CapitalAccountRole.AVAILABLE),
                        ns.account(CapitalAccountRole.ENCUMBRANCE)):
            assert ledger.create_account(account) == LedgerApplyStatus.CREATED
        assert ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("partial-race", "funding"),
            debit_account_id=fund.account_id, credit_account_id=ns.available_account_id,
            amount=1000,
        ) == LedgerApplyStatus.CREATED
        assert ledger.apply_instruction(reservation_instruction(b)) == LedgerApplyStatus.CREATED
    gate = Barrier(2)
    def resolve(value: int):
        resolution = resolution_instruction(
            binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
            resolution_ref=f"partial:race:{value}", posted_amount=value,
        )
        gate.wait(timeout=15)
        with PostgresAccountingLedger(DSN) as ledger:
            return ledger.apply_instruction(resolution)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(resolve, (240, 310)))
    assert results.count(LedgerApplyStatus.CREATED) == 1
    assert results.count(LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED) == 1
    with PostgresAccountingLedger(DSN) as ledger:
        actual = ledger.account(ns.available_account_id)
        assert actual.debits_pending == 0
        assert actual.debits_posted in (240, 310)
        assert ledger.account(ns.encumbrance_account_id).credits_posted == actual.debits_posted



def test_pg_partial_post_readback_refines_history_including_status():
    assert DSN
    from ordivon_capital.accounting.durable import (
        DurableReservationHistory,
        LedgerReconciliationStanding,
        LedgerTransferObservation,
        ReservationStanding,
        reconcile_durable_history,
    )
    ns = CapitalAccountNamespace("owner:partial", "parcel:usd:durable-refinement")
    fund = AccountingAccount(stable_accounting_id("partial-refinement", "fund"))
    b = binding_for_namespace(namespace=ns, reservation_ref="partial:refinement", amount=700)
    resolution = resolution_instruction(
        binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
        resolution_ref="partial:refinement:post", posted_amount=240,
    )
    assert resolution is not None
    with PostgresAccountingLedger(DSN) as ledger:
        for account in (fund, ns.account(CapitalAccountRole.AVAILABLE),
                        ns.account(CapitalAccountRole.ENCUMBRANCE)):
            assert ledger.create_account(account) is LedgerApplyStatus.CREATED
        assert ledger.apply_immediate_transfer(
            transfer_id=stable_accounting_id("partial-refinement", "funding"),
            debit_account_id=fund.account_id, credit_account_id=ns.available_account_id,
            amount=1000,
        ) is LedgerApplyStatus.CREATED
        assert ledger.apply_instruction(reservation_instruction(b)) is LedgerApplyStatus.CREATED
        assert ledger.apply_instruction(resolution) is LedgerApplyStatus.CREATED
    with PostgresAccountingLedger(DSN) as ledger:
        p = ledger.transfer(b.pending_transfer_id)
        r = ledger.transfer(resolution.transfer_id)
        assert p is not None and r is not None
        assert p.status == "POSTED" and r.status == "POSTED"
        pending = LedgerTransferObservation(
            p.transfer_id, AccountingOperation.PENDING, p.amount, 0, status=p.status
        )
        terminal = LedgerTransferObservation(
            r.transfer_id, AccountingOperation.POST_PENDING_TRANSFER,
            r.amount, r.pending_id, status=r.status,
        )
        history = DurableReservationHistory(
            b, ReservationStanding.CONSUMED, "partial:refinement:post", posted_amount=240
        )
        verified = reconcile_durable_history(
            history=history, pending=pending, resolution=terminal
        )
        assert verified.standing is LedgerReconciliationStanding.MATCH
        forged = LedgerTransferObservation(
            p.transfer_id, AccountingOperation.PENDING, p.amount, 0, status="PENDING"
        )
        assert reconcile_durable_history(
            history=history, pending=forged, resolution=terminal
        ).standing is LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR
