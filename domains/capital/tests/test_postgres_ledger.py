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
from ordivon_capital.accounting.sqlite_ledger import LedgerApplyStatus
from ordivon_capital.accounting.substrate import (
    AccountingAccount,
    AccountingOperation,
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

def test_pg_migrates_only_quiesced_real_sqlite_source_and_rejects_duplicate(tmp_path):
    from ordivon_capital.accounting.sqlite_ledger import SQLiteAccountingLedger
    assert DSN
    source = tmp_path / "capital#snapshot.sqlite3"
    with SQLiteAccountingLedger(source) as legacy:
        assert legacy.create_account(AccountingAccount(101)) == LedgerApplyStatus.CREATED
        assert legacy.create_account(AccountingAccount(202)) == LedgerApplyStatus.CREATED
        assert legacy.apply_immediate_transfer(
            transfer_id=303, debit_account_id=101, credit_account_id=202, amount=42
        ) == LedgerApplyStatus.CREATED
    before = source.read_bytes()
    with PostgresAccountingLedger(DSN) as pg:
        with pytest.raises(RuntimeError, match="quiescence"):
            pg.import_quiesced_sqlite(source)
        witness = pg.import_quiesced_sqlite(source, confirmed_quiesced=True)
        assert witness["standing"] == "VERIFIED_COPY_NOT_CONSUMER_CUTOVER"
        assert witness["sourceAccounts"] == witness["postgresAccounts"] == 2
        assert witness["sourceTransfers"] == witness["postgresTransfers"] == 1
        assert pg.transfer(303).amount == 42
        assert pg.account(101).debits_posted == 42
        with pytest.raises(RuntimeError, match="empty"):
            pg.import_quiesced_sqlite(source, confirmed_quiesced=True)
    assert source.read_bytes() == before


def test_pg_import_rejects_broken_sqlite_source_without_admitting_rows(tmp_path):
    assert DSN
    bad = tmp_path / "corrupt#source.sqlite3"
    bad.write_bytes(b"not a database")
    with PostgresAccountingLedger(DSN) as pg:
        with pytest.raises(Exception):
            pg.import_quiesced_sqlite(bad, confirmed_quiesced=True)
        import psycopg
        with psycopg.connect(DSN) as db:
            assert db.execute("SELECT count(*) FROM ordivon_capital.accounts").fetchone()[0] == 0

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


def test_pg_import_readback_corruption_rolls_back_all_rows(tmp_path):
    assert DSN
    import psycopg

    from ordivon_capital.accounting.sqlite_ledger import SQLiteAccountingLedger

    source=tmp_path/"ledger#tamper.sqlite3"
    with SQLiteAccountingLedger(source) as legacy:
        assert legacy.create_account(AccountingAccount(801)) == LedgerApplyStatus.CREATED
        assert legacy.create_account(AccountingAccount(802)) == LedgerApplyStatus.CREATED
        assert legacy.apply_immediate_transfer(
            transfer_id=803, debit_account_id=801,
            credit_account_id=802, amount=25,
        ) == LedgerApplyStatus.CREATED
    pg=PostgresAccountingLedger(DSN)
    with psycopg.connect(DSN) as db:
        db.execute("""CREATE FUNCTION ordivon_capital.corrupt_import()
            RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                UPDATE ordivon_capital.transfers
                SET status='VOIDED' WHERE id=NEW.id;
                RETURN NEW;
            END $$""")
        db.execute("""CREATE TRIGGER corrupt_import_after_insert
            AFTER INSERT ON ordivon_capital.transfers
            FOR EACH ROW EXECUTE FUNCTION ordivon_capital.corrupt_import()""")
    try:
        with pytest.raises(RuntimeError, match="readback"):
            pg.import_quiesced_sqlite(source, confirmed_quiesced=True)
        with psycopg.connect(DSN) as db:
            for table in ("accounts", "transfers"):
                assert db.execute(
                    f"SELECT count(*) FROM ordivon_capital.{table}"
                ).fetchone()[0] == 0
    finally:
        with psycopg.connect(DSN) as db:
            db.execute(
                "DROP TRIGGER IF EXISTS corrupt_import_after_insert "
                "ON ordivon_capital.transfers"
            )
            db.execute("DROP FUNCTION IF EXISTS ordivon_capital.corrupt_import()")


@pytest.mark.parametrize(
    ("column", "malformed", "sqlite_storage"),
    [
        ("credits_posted", 1.75, "real"),
        ("no_overdraft", "false", "text"),
    ],
)
def test_pg_import_rejects_noncanonical_legacy_integer_cells(
    tmp_path, column, malformed, sqlite_storage,
):
    """The source must be typed before its PG equality proof or digest."""
    assert DSN
    import sqlite3

    import psycopg

    from ordivon_capital.accounting.sqlite_ledger import SQLiteAccountingLedger

    source = tmp_path / "typed#legacy.sqlite3"
    with SQLiteAccountingLedger(source) as legacy:
        assert legacy.create_account(AccountingAccount(101)) == LedgerApplyStatus.CREATED
    with sqlite3.connect(source) as db:
        db.execute(f"UPDATE accounts SET {column}=? WHERE id=?", (malformed, "101"))
        observed = db.execute(
            f"SELECT typeof({column}),{column} FROM accounts WHERE id='101'"
        ).fetchone()
    assert observed == (sqlite_storage, malformed)
    with PostgresAccountingLedger(DSN) as pg:
        with pytest.raises(ValueError, match="noncanonical"):
            pg.import_quiesced_sqlite(source, confirmed_quiesced=True)
    with psycopg.connect(DSN) as pg:
        for table in ("accounts", "transfers"):
            assert pg.execute(
                f"SELECT count(*) FROM ordivon_capital.{table}"
            ).fetchone()[0] == 0


def test_pg_import_rejects_noncanonical_legacy_transfer_amount(tmp_path):
    """A silent REAL-to-int conversion must never pass the source parity gate."""
    assert DSN
    import sqlite3

    import psycopg

    from ordivon_capital.accounting.sqlite_ledger import SQLiteAccountingLedger

    source = tmp_path / "typed#transfer.sqlite3"
    with SQLiteAccountingLedger(source) as legacy:
        for account_id in (101, 202):
            assert (
                legacy.create_account(AccountingAccount(account_id))
                == LedgerApplyStatus.CREATED
            )
        assert (
            legacy.apply_immediate_transfer(
                transfer_id=303,
                debit_account_id=101,
                credit_account_id=202,
                amount=42,
            )
            == LedgerApplyStatus.CREATED
        )
    with sqlite3.connect(source) as db:
        db.execute("UPDATE transfers SET amount=1.75 WHERE id='303'")
        assert db.execute(
            "SELECT typeof(amount), amount FROM transfers WHERE id='303'"
        ).fetchone() == ("real", 1.75)
    with PostgresAccountingLedger(DSN) as pg:
        with pytest.raises(ValueError, match="noncanonical"):
            pg.import_quiesced_sqlite(source, confirmed_quiesced=True)
    with psycopg.connect(DSN) as pg:
        for table in ("accounts", "transfers"):
            assert pg.execute(
                f"SELECT count(*) FROM ordivon_capital.{table}"
            ).fetchone()[0] == 0
