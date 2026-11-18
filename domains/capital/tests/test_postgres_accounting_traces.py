"""36 PostgreSQL accounting traces against independent contract expectations.

No SQLite ledger, mocked DB, or migration. Requires a disposable PG DSN.
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
from ordivon_capital.accounting.substrate import (
    AccountingAccount,
    AccountingOperation,
    AccountState,
    LedgerApplyStatus,
    reservation_instruction,
    resolution_instruction,
    stable_accounting_id,
)

DSN = os.environ.get("ORDIVON_CAPITAL_PG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="disposable PostgreSQL required")
MISSING = LedgerApplyStatus.PENDING_TRANSFER_NOT_FOUND


def _expected_next(first: int, second: int) -> LedgerApplyStatus:
    if first == 0:
        return (
            LedgerApplyStatus.EXISTS, LedgerApplyStatus.EXCEEDS_CREDITS,
            LedgerApplyStatus.CREATED, LedgerApplyStatus.CREATED,
            MISSING, MISSING,
        )[second]
    if first == 1:
        return (
            LedgerApplyStatus.EXCEEDS_CREDITS, LedgerApplyStatus.EXISTS,
            MISSING, MISSING, LedgerApplyStatus.CREATED,
            LedgerApplyStatus.CREATED,
        )[second]
    return LedgerApplyStatus.CREATED if second in (0, 1) else MISSING


def _expected_cash(first: int, second: int) -> tuple[int, int]:
    """Independent two-action conservation: pending, posted, no overdraft."""
    if first == 0:
        if second == 2:
            return (0, 300)
        if second == 3:
            return (0, 0)
        return (300, 0)
    if first == 1:
        if second == 4:
            return (0, 800)
        if second == 5:
            return (0, 0)
        return (800, 0)
    return (300 if second == 0 else 800 if second == 1 else 0, 0)


def test_postgres_36_contract_traces_no_retired_backend() -> None:
    assert DSN
    for first, second in product(range(6), repeat=2):
        with PostgresAccountingLedger(DSN) as ledger:
            with psycopg.connect(DSN) as admin:
                admin.execute(
                    "TRUNCATE ordivon_capital.transfers, ordivon_capital.accounts"
                )
            ns = CapitalAccountNamespace("owner:bounded", "parcel:bounded:usd")
            fund = AccountingAccount(stable_accounting_id("pg-trace", "fund"))
            available = ns.account(CapitalAccountRole.AVAILABLE)
            encumbrance = ns.account(CapitalAccountRole.ENCUMBRANCE)
            for account in (fund, available, encumbrance):
                assert ledger.create_account(account) is LedgerApplyStatus.CREATED
            assert ledger.apply_immediate_transfer(
                transfer_id=stable_accounting_id("pg-trace", "funding"),
                debit_account_id=fund.account_id,
                credit_account_id=available.account_id,
                amount=1000,
            ) is LedgerApplyStatus.CREATED
            a = binding_for_namespace(
                namespace=ns, reservation_ref="pg-trace:a", amount=300
            )
            b = binding_for_namespace(
                namespace=ns, reservation_ref="pg-trace:b", amount=800
            )
            actions = (
                reservation_instruction(a),
                reservation_instruction(b),
                resolution_instruction(
                    binding=a, operation=AccountingOperation.POST_PENDING_TRANSFER,
                    resolution_ref="pg-trace:post-a",
                ),
                resolution_instruction(
                    binding=a, operation=AccountingOperation.VOID_PENDING_TRANSFER,
                    resolution_ref="pg-trace:void-a",
                ),
                resolution_instruction(
                    binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
                    resolution_ref="pg-trace:post-b",
                ),
                resolution_instruction(
                    binding=b, operation=AccountingOperation.VOID_PENDING_TRANSFER,
                    resolution_ref="pg-trace:void-b",
                ),
            )
            assert all(action is not None for action in actions)
            assert ledger.apply_instruction(actions[first]) is (
                LedgerApplyStatus.CREATED if first in (0, 1) else MISSING
            )
            assert ledger.apply_instruction(actions[second]) is _expected_next(
                first, second
            )
            pending, posted = _expected_cash(first, second)
            assert ledger.account(fund.account_id) == AccountState(
                fund.account_id, 0, 1000, 0, 0
            )
            assert ledger.account(available.account_id) == AccountState(
                available.account_id, pending, posted, 0, 1000
            )
            assert ledger.account(encumbrance.account_id) == AccountState(
                encumbrance.account_id, 0, 0, pending, posted
            )
            for idx, binding in enumerate((a, b)):
                admitted = first == idx or (first not in (0, 1) and second == idx)
                observed = ledger.transfer(binding.pending_transfer_id)
                if not admitted:
                    assert observed is None
                    continue
                assert observed is not None and observed.operation == "PENDING"
                status = "PENDING"
                if first == idx and second == (2, 4)[idx]:
                    status = "POSTED"
                if first == idx and second == (3, 5)[idx]:
                    status = "VOIDED"
                assert observed.status == status
            for action in actions[2:]:
                resolved = first in (0, 1) and second in (
                    (2, 3) if first == 0 else (4, 5)
                ) and action is actions[second]
                assert (ledger.transfer(action.transfer_id) is not None) is resolved
