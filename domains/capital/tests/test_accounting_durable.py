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


def pending_obs(status: str = 'PENDING'):
    b = binding()
    return LedgerTransferObservation(
        transfer_id=b.pending_transfer_id,
        operation=AccountingOperation.PENDING,
        amount=b.amount,
        status=status,
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
        status=(
            "POSTED" if operation is AccountingOperation.POST_PENDING_TRANSFER else "VOIDED"
        ),
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
        pending=pending_obs("POSTED"),
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
        pending=pending_obs('POSTED'),
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
        pending=pending_obs('VOIDED'),
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
        pending=pending_obs('VOIDED'),
        resolution=terminal_obs(
            AccountingOperation.POST_PENDING_TRANSFER,
            "effect:consume",
        ),
    )
    assert result.standing is LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR
    assert result.ledger_repair_allowed is False


@pytest.mark.parametrize(
    "invalid_standing",
    ["RESERVED", "RELEASED", "CONSUMED", "UNKNOWN", None, 17],
)
def test_history_rejects_untyped_or_unknown_reservation_standing(invalid_standing) -> None:
    """Raw/malformed states cannot become terminal accounting authority."""
    with pytest.raises(AccountingMappingError, match="ReservationStanding"):
        DurableReservationHistory(
            binding=binding(),
            standing=invalid_standing,
            resolution_ref="effect:reconciliation",
        )


def test_raw_released_state_cannot_be_interpreted_as_consumed() -> None:
    """Prevent an invalid string standing from matching a POST resolution."""
    with pytest.raises(AccountingMappingError, match="ReservationStanding"):
        history = DurableReservationHistory(
            binding=binding(),
            standing="RELEASED",  # type: ignore[arg-type]
            resolution_ref="effect:wrong-action",
        )
        result = reconcile_durable_history(
            history=history,
            pending=pending_obs(),
            resolution=terminal_obs(
                AccountingOperation.POST_PENDING_TRANSFER,
                "effect:wrong-action",
            ),
        )
        if result.standing is LedgerReconciliationStanding.MATCH:
            pytest.fail("raw RELEASED was interpreted as consumed")


def test_partial_consumption_history_checks_exact_settled_amount():
    b = binding()
    history = DurableReservationHistory(
        b, ReservationStanding.CONSUMED, "effect:partial", posted_amount=240
    )
    resolution = resolution_instruction(
        binding=b, operation=AccountingOperation.POST_PENDING_TRANSFER,
        resolution_ref="effect:partial", posted_amount=240,
    )
    assert resolution is not None
    observed = LedgerTransferObservation(
        resolution.transfer_id, resolution.operation,
        resolution.amount, resolution.pending_id, status='POSTED',
    )
    assert reconcile_durable_history(
        history=history, pending=pending_obs('POSTED'), resolution=observed
    ).standing is LedgerReconciliationStanding.MATCH
    mismatch = LedgerTransferObservation(
        resolution.transfer_id, resolution.operation, 700, resolution.pending_id, status='POSTED'
    )
    actual = reconcile_durable_history(
        history=history, pending=pending_obs('POSTED'), resolution=mismatch
    )
    assert actual.standing is LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR


@pytest.mark.parametrize("invalid", [0, -1, 701, True, "240", 1.5])
def test_partial_consumption_history_rejects_false_amount(invalid):
    with pytest.raises(AccountingMappingError, match="posted_amount"):
        DurableReservationHistory(
            binding(), ReservationStanding.CONSUMED,
            "effect:partial", posted_amount=invalid,
        )


def test_non_consumed_history_must_not_claim_partial_post():
    with pytest.raises(AccountingMappingError, match="posted_amount"):
        DurableReservationHistory(
            binding(), ReservationStanding.RELEASED,
            "effect:release", posted_amount=240,
        )


def test_observed_reservation_status_cannot_lie_about_posted_money():
    result = reconcile_durable_history(
        history=DurableReservationHistory(binding(), ReservationStanding.RESERVED),
        pending=pending_obs("POSTED"),
        resolution=None,
    )
    assert result.standing is LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR


def test_missing_reservation_status_does_not_prove_state():
    pending = pending_obs()
    absent_status = LedgerTransferObservation(
        transfer_id=pending.transfer_id, operation=pending.operation,
        amount=pending.amount, pending_id=pending.pending_id,
    )
    result = reconcile_durable_history(
        history=DurableReservationHistory(binding(), ReservationStanding.RESERVED),
        pending=absent_status, resolution=None,
    )
    assert result.standing is LedgerReconciliationStanding.LEDGER_INCOMPLETE_NO_REPAIR


def test_wrong_terminal_resolution_status_is_contradiction():
    wrong = terminal_obs(AccountingOperation.POST_PENDING_TRANSFER, "effect:consume")
    wrong = LedgerTransferObservation(
        wrong.transfer_id, wrong.operation, wrong.amount, wrong.pending_id, status="PENDING"
    )
    result = reconcile_durable_history(
        history=DurableReservationHistory(
            binding(), ReservationStanding.CONSUMED, "effect:consume"
        ),
        pending=pending_obs("POSTED"), resolution=wrong,
    )
    assert result.standing is LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR
