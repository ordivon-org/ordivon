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
            LedgerApplyStatus.EXISTS,
            LedgerApplyStatus.EXCEEDS_CREDITS,
            LedgerApplyStatus.CREATED,
            LedgerApplyStatus.CREATED,
            MISSING,
            MISSING,
        )[second]
    if first == 1:
        return (
            LedgerApplyStatus.EXCEEDS_CREDITS,
            LedgerApplyStatus.EXISTS,
            MISSING,
            MISSING,
            LedgerApplyStatus.CREATED,
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
                admin.execute("TRUNCATE ordivon_capital.transfers, ordivon_capital.accounts")
            ns = CapitalAccountNamespace("owner:bounded", "parcel:bounded:usd")
            fund = AccountingAccount(stable_accounting_id("pg-trace", "fund"))
            available = ns.account(CapitalAccountRole.AVAILABLE)
            encumbrance = ns.account(CapitalAccountRole.ENCUMBRANCE)
            for account in (fund, available, encumbrance):
                assert ledger.create_account(account) is LedgerApplyStatus.CREATED
            assert (
                ledger.apply_immediate_transfer(
                    transfer_id=stable_accounting_id("pg-trace", "funding"),
                    debit_account_id=fund.account_id,
                    credit_account_id=available.account_id,
                    amount=1000,
                )
                is LedgerApplyStatus.CREATED
            )
            a = binding_for_namespace(namespace=ns, reservation_ref="pg-trace:a", amount=300)
            b = binding_for_namespace(namespace=ns, reservation_ref="pg-trace:b", amount=800)
            actions = (
                reservation_instruction(a),
                reservation_instruction(b),
                resolution_instruction(
                    binding=a,
                    operation=AccountingOperation.POST_PENDING_TRANSFER,
                    resolution_ref="pg-trace:post-a",
                ),
                resolution_instruction(
                    binding=a,
                    operation=AccountingOperation.VOID_PENDING_TRANSFER,
                    resolution_ref="pg-trace:void-a",
                ),
                resolution_instruction(
                    binding=b,
                    operation=AccountingOperation.POST_PENDING_TRANSFER,
                    resolution_ref="pg-trace:post-b",
                ),
                resolution_instruction(
                    binding=b,
                    operation=AccountingOperation.VOID_PENDING_TRANSFER,
                    resolution_ref="pg-trace:void-b",
                ),
            )
            assert all(action is not None for action in actions)
            assert ledger.apply_instruction(actions[first]) is (
                LedgerApplyStatus.CREATED if first in (0, 1) else MISSING
            )
            assert ledger.apply_instruction(actions[second]) is _expected_next(first, second)
            pending, posted = _expected_cash(first, second)
            assert ledger.account(fund.account_id) == AccountState(fund.account_id, 0, 1000, 0, 0)
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
                resolved = (
                    first in (0, 1)
                    and second in ((2, 3) if first == 0 else (4, 5))
                    and action is actions[second]
                )
                assert (ledger.transfer(action.transfer_id) is not None) is resolved


# Stateful generated traces extend the exhaustive two-action model above.
# Model state uses only integers and action identities, never ledger internals.
from uuid import uuid4

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule


class ReservationMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        assert DSN
        self.ledger = PostgresAccountingLedger(DSN)
        token = uuid4().hex
        ns = CapitalAccountNamespace("owner:stateful:" + token, "parcel:stateful:" + token + ":usd")
        self.fund = AccountingAccount(stable_accounting_id("pg-stateful", token))
        self.available = ns.account(CapitalAccountRole.AVAILABLE)
        self.encumbrance = ns.account(CapitalAccountRole.ENCUMBRANCE)
        self.amounts = (200, 600, 800)
        self.bindings = tuple(
            binding_for_namespace(namespace=ns, reservation_ref=f"stateful:{token}:{i}", amount=a)
            for i, a in enumerate(self.amounts)
        )
        self.states = {}
        self.accepted = {}
        self.posted = 0
        self.all_ids = set()
        for account in (self.fund, self.available, self.encumbrance):
            assert self.ledger.create_account(account) is LedgerApplyStatus.CREATED
        self.funding_id = stable_accounting_id("pg-stateful-funding", token)
        assert (
            self.ledger.apply_immediate_transfer(
                transfer_id=self.funding_id,
                debit_account_id=self.fund.account_id,
                credit_account_id=self.available.account_id,
                amount=1000,
            )
            is LedgerApplyStatus.CREATED
        )

    @rule(
        index=st.integers(0, 2),
        kind=st.sampled_from(("reserve", "post", "void")),
        slot=st.integers(0, 1),
        fraction=st.integers(1, 4),
    )
    def action(self, index, kind, slot, fraction):
        amount = self.amounts[index]
        binding = self.bindings[index]
        if kind == "reserve":
            identity = (index, kind, 0)
            payload = amount
            instruction = reservation_instruction(binding)
        else:
            identity = (index, kind, slot)
            payload = amount * fraction // 4 if kind == "post" else 0
            instruction = resolution_instruction(
                binding=binding,
                operation=AccountingOperation.POST_PENDING_TRANSFER
                if kind == "post"
                else AccountingOperation.VOID_PENDING_TRANSFER,
                resolution_ref=f"stateful:{kind}:{slot}",
                posted_amount=payload if kind == "post" else None,
            )
        assert instruction is not None
        self.all_ids.add(instruction.transfer_id)
        state = self.states.get(index)
        if identity in self.accepted:
            expected = (
                LedgerApplyStatus.EXISTS
                if self.accepted[identity] == payload
                else LedgerApplyStatus.ID_CONFLICT
            )
        elif kind == "reserve":
            pending = sum(self.amounts[i] for i, s in self.states.items() if s == "PENDING")
            expected = (
                LedgerApplyStatus.CREATED
                if amount <= 1000 - self.posted - pending
                else LedgerApplyStatus.EXCEEDS_CREDITS
            )
        else:
            expected = {
                None: LedgerApplyStatus.PENDING_TRANSFER_NOT_FOUND,
                "PENDING": LedgerApplyStatus.CREATED,
                "POSTED": LedgerApplyStatus.PENDING_TRANSFER_ALREADY_POSTED,
                "VOIDED": LedgerApplyStatus.PENDING_TRANSFER_ALREADY_VOIDED,
            }[state]
        actual = self.ledger.apply_instruction(instruction)
        assert actual is expected
        if expected is LedgerApplyStatus.CREATED:
            self.accepted[identity] = payload
            self.states[index] = {"reserve": "PENDING", "post": "POSTED", "void": "VOIDED"}[kind]
            if kind == "post":
                self.posted += payload
        observed = self.ledger.transfer(instruction.transfer_id)
        assert (observed is not None) == (identity in self.accepted)
        if observed is not None:
            assert observed.amount == self.accepted[identity]

    @invariant()
    def conservation_and_terminal_state(self):
        pending = sum(self.amounts[i] for i, s in self.states.items() if s == "PENDING")
        assert 0 <= pending + self.posted <= 1000
        assert self.ledger.account(self.fund.account_id) == AccountState(
            self.fund.account_id, 0, 1000, 0, 0
        )
        assert self.ledger.account(self.available.account_id) == AccountState(
            self.available.account_id, pending, self.posted, 0, 1000
        )
        assert self.ledger.account(self.encumbrance.account_id) == AccountState(
            self.encumbrance.account_id, 0, 0, pending, self.posted
        )
        for i, b in enumerate(self.bindings):
            row = self.ledger.transfer(b.pending_transfer_id)
            assert (row.status if row is not None else None) == self.states.get(i)

    def teardown(self):
        self.ledger.close()
        # Delete only this generated trace's own records in the disposable DB.
        with psycopg.connect(DSN) as db:
            db.execute(
                "DELETE FROM ordivon_capital.transfers WHERE id = ANY(%s)",
                ([str(v) for v in self.all_ids | {self.funding_id}],),
            )
            db.execute(
                "DELETE FROM ordivon_capital.accounts WHERE id = ANY(%s)",
                ([str(a.account_id) for a in (self.fund, self.available, self.encumbrance)],),
            )


TestReservationMachine = ReservationMachine.TestCase
TestReservationMachine.settings = settings(
    max_examples=24, stateful_step_count=12, derandomize=True, deadline=None
)
