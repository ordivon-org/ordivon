from __future__ import annotations

import pytest

from ordivon_capital.accounting.substrate import (
    AccountingMappingError,
    AccountingOperation,
    CapitalReservationBinding,
    ensure_accounting_only,
    reservation_instruction,
    resolution_instruction,
    stable_accounting_id,
)


def binding(amount: int = 700) -> CapitalReservationBinding:
    return CapitalReservationBinding(
        reservation_ref="reservation:alpha",
        resource_identity="parcel:usd:1",
        source_account_id=101,
        encumbrance_account_id=202,
        amount=amount,
    )


def test_stable_accounting_identity_is_deterministic_and_domain_separated():
    a = stable_accounting_id("ordivon:test:a", "one", "two")
    b = stable_accounting_id("ordivon:test:a", "one", "two")
    c = stable_accounting_id("ordivon:test:b", "one", "two")
    assert a == b
    assert a != c
    assert 0 < a < 2**128


def test_reservation_and_terminal_instructions_are_exact():
    b = binding()
    pending = reservation_instruction(b)
    assert pending.operation is AccountingOperation.PENDING
    assert pending.transfer_id == b.pending_transfer_id
    assert pending.amount == 700
    assert pending.pending_id == 0

    post = resolution_instruction(
        binding=b,
        operation=AccountingOperation.POST_PENDING_TRANSFER,
        resolution_ref="effect:consume",
    )
    assert post is not None
    assert post.amount == 700
    assert post.pending_id == b.pending_transfer_id

    void = resolution_instruction(
        binding=b,
        operation=AccountingOperation.VOID_PENDING_TRANSFER,
        resolution_ref="effect:void",
    )
    assert void is not None
    assert void.amount == 0
    assert void.pending_id == b.pending_transfer_id

    assert (
        resolution_instruction(
            binding=b,
            operation=None,
            resolution_ref="effect:retain",
        )
        is None
    )


def test_resolution_identity_cannot_reuse_reservation_identity():
    b = binding()
    with pytest.raises(AccountingMappingError, match="identity must differ"):
        resolution_instruction(
            binding=b,
            operation=AccountingOperation.POST_PENDING_TRANSFER,
            resolution_ref=b.reservation_ref,
        )


def test_reservation_rejects_self_transfer_and_nonpositive_amount():
    with pytest.raises(AccountingMappingError, match="accounts must differ"):
        CapitalReservationBinding("r", "resource", 1, 1, 1)
    with pytest.raises(AccountingMappingError, match="amount must be positive"):
        CapitalReservationBinding("r", "resource", 1, 2, 0)


def test_accounting_records_cannot_smuggle_domain_truth():
    ensure_accounting_only({"amount": 1, "account": 2})
    with pytest.raises(AccountingMappingError, match="non-accounting domain"):
        ensure_accounting_only({"amount": 1, "legalOwnership": True})
