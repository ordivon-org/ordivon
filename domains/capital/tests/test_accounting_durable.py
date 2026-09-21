from __future__ import annotations

import pytest

from ordivon_capital.accounting.durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
    DurableReservationHistory,
    LedgerReconciliationStanding,
    LedgerTransferObservation,
    ReservationStanding,
    binding_for_namespace,
    reconcile_durable_history,
)
from ordivon_capital.accounting.substrate import (
    AccountingMappingError,
    AccountingOperation,
    resolution_instruction,
)


def namespace() -> CapitalAccountNamespace:
    return CapitalAccountNamespace("owner:primary", "parcel:usd:canonical")


def binding():
    return binding_for_namespace(
        namespace=namespace(),
        reservation_ref="reservation:durable",
        amount=700,
    )


def pending_obs():
    b = binding()
    return LedgerTransferObservation(
        transfer_id=b.pending_transfer_id,
        operation=AccountingOperation.PENDING,
        amount=b.amount,
    )


def terminal_obs(operation: AccountingOperation, resolution_ref: str):
    b = binding()
    instruction = resolution_instruction(
        binding=b,
        operation=operation,
        resolution_ref=resolution_ref,
    )
    assert instruction is not None
    return LedgerTransferObservation(
        transfer_id=instruction.transfer_id,
        operation=instruction.operation,
        amount=instruction.amount,
        pending_id=instruction.pending_id,
    )


def test_account_namespace_is_stable_and_role_separated():
    ns = namespace()
    assert ns.available_account_id == ns.account_id(CapitalAccountRole.AVAILABLE)
    assert ns.encumbrance_account_id == ns.account_id(CapitalAccountRole.ENCUMBRANCE)
    assert ns.available_account_id != ns.encumbrance_account_id
    assert ns.account(CapitalAccountRole.AVAILABLE).no_overdraft is True
    assert ns.account(CapitalAccountRole.ENCUMBRANCE).no_overdraft is False


def test_namespace_changes_when_owner_or_resource_changes():
    a = namespace()
    b = CapitalAccountNamespace("owner:secondary", a.resource_identity)
    c = CapitalAccountNamespace(a.owner_root, "parcel:eur:canonical")
    assert a.available_account_id != b.available_account_id
    assert a.available_account_id != c.available_account_id


def test_raw_string_role_is_rejected():
    with pytest.raises(AccountingMappingError, match="CapitalAccountRole"):
        namespace().account_id("AVAILABLE")  # type: ignore[arg-type]


def test_reserved_history_matches_exact_pending_ledger_history():
    result = reconcile_durable_history(
        history=DurableReservationHistory(binding(), ReservationStanding.RESERVED),
        pending=pending_obs(),
        resolution=None,
    )
    assert result.standing is LedgerReconciliationStanding.MATCH
    assert result.terminal_history_preserved is False
    assert result.ledger_repair_allowed is False


def test_consumed_history_survives_missing_resolution_without_reopening():
    result = reconcile_durable_history(
        history=DurableReservationHistory(
            binding(),
            ReservationStanding.CONSUMED,
            "effect:consume",
        ),
        pending=pending_obs(),
        resolution=None,
    )
    assert result.standing is LedgerReconciliationStanding.LEDGER_INCOMPLETE_NO_REPAIR
    assert result.terminal_history_preserved is True
    assert result.ledger_repair_allowed is False


def test_consumed_and_released_history_match_exact_resolution():
    consumed = reconcile_durable_history(
        history=DurableReservationHistory(
            binding(),
            ReservationStanding.CONSUMED,
            "effect:consume",
        ),
        pending=pending_obs(),
        resolution=terminal_obs(
            AccountingOperation.POST_PENDING_TRANSFER,
            "effect:consume",
        ),
    )
    assert consumed.standing is LedgerReconciliationStanding.MATCH

    released = reconcile_durable_history(
        history=DurableReservationHistory(
            binding(),
            ReservationStanding.RELEASED,
            "effect:release",
        ),
        pending=pending_obs(),
        resolution=terminal_obs(
            AccountingOperation.VOID_PENDING_TRANSFER,
            "effect:release",
        ),
    )
    assert released.standing is LedgerReconciliationStanding.MATCH


def test_terminal_contradiction_never_repairs_ledger():
    result = reconcile_durable_history(
        history=DurableReservationHistory(
            binding(),
            ReservationStanding.RELEASED,
            "effect:release",
        ),
        pending=pending_obs(),
        resolution=terminal_obs(
            AccountingOperation.POST_PENDING_TRANSFER,
            "effect:consume",
        ),
    )
    assert result.standing is LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR
    assert result.ledger_repair_allowed is False
