"""Bounded PostgreSQL accounting trace refinement against retiring SQLite semantics.

The only SQLite effects here are isolated disposable test oracles. No legacy
production DB repair, no live consumer cutover, no universal refinement claim.
"""
from __future__ import annotations

import os
from itertools import product

import psycopg
import pytest

from ordivon_capital.accounting.durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
    binding_for_namespace,
)
from ordivon_capital.accounting.postgres_ledger import PostgresAccountingLedger
from ordivon_capital.accounting.sqlite_ledger import LedgerApplyStatus, SQLiteAccountingLedger
from ordivon_capital.accounting.substrate import (
    AccountingAccount,
    AccountingOperation,
    reservation_instruction,
    resolution_instruction,
    stable_accounting_id,
)

DSN = os.environ.get("ORDIVON_CAPITAL_PG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="disposable PostgreSQL DSN is required")


def test_pg_36_bounded_traces_preserve_ledger_observations(tmp_path):
    """One canonical arithmetic oracle; six operations, ordered pairs = 36 traces."""
    assert DSN
    for index, trace in enumerate(product(range(6), repeat=2)):
        with PostgresAccountingLedger(DSN) as pg:
            with psycopg.connect(DSN) as admin:
                admin.execute(
                    "TRUNCATE ordivon_capital.transfers, ordivon_capital.accounts"
                )
            with SQLiteAccountingLedger(tmp_path / f"retiring_oracle_{index}.sqlite3") as old:
                ns = CapitalAccountNamespace("owner:bounded", "parcel:bounded:usd")
                fund = AccountingAccount(stable_accounting_id("pg-trace", "fund"))
                available = ns.account(CapitalAccountRole.AVAILABLE)
                encumbrance = ns.account(CapitalAccountRole.ENCUMBRANCE)
                for account in (fund, available, encumbrance):
                    assert pg.create_account(account) is old.create_account(account)
                init = {
                    "transfer_id": stable_accounting_id("pg-trace", "funding"),
                    "debit_account_id": fund.account_id,
                    "credit_account_id": available.account_id,
                    "amount": 1000,
                }
                assert (
                    pg.apply_immediate_transfer(**init)
                    is old.apply_immediate_transfer(**init)
                    is LedgerApplyStatus.CREATED
                )

                a = binding_for_namespace(
                    namespace=ns, reservation_ref="pg-trace:a", amount=300
                )
                b = binding_for_namespace(
                    namespace=ns, reservation_ref="pg-trace:b", amount=800
                )

                def complete(binding, kind, ref):
                    return resolution_instruction(
                        binding=binding, operation=kind, resolution_ref=ref
                    )

                actions = (
                    reservation_instruction(a),
                    reservation_instruction(b),
                    complete(a, AccountingOperation.POST_PENDING_TRANSFER, "pg-trace:post-a"),
                    complete(a, AccountingOperation.VOID_PENDING_TRANSFER, "pg-trace:void-a"),
                    complete(b, AccountingOperation.POST_PENDING_TRANSFER, "pg-trace:post-b"),
                    complete(b, AccountingOperation.VOID_PENDING_TRANSFER, "pg-trace:void-b"),
                )
                assert all(action is not None for action in actions)
                for selected in trace:
                    instruction = actions[selected]
                    assert pg.apply_instruction(instruction) is old.apply_instruction(instruction)
                    for account_id in (
                        fund.account_id, ns.available_account_id, ns.encumbrance_account_id
                    ):
                        assert pg.account(account_id) == old.account(account_id)
                    for pending_id in (a.pending_transfer_id, b.pending_transfer_id):
                        assert pg.transfer(pending_id) == old.transfer(pending_id)
