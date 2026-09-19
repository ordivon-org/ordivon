import pytest

from ordivon_capital.accounting.tigerbeetle_durable import (
    CapitalAccountNamespace,
    CapitalAccountRole,
    DurableProviderStanding,
    DurableReservationHistory,
    ProviderTransferObservation,
    ReservationStanding,
    binding_for_namespace,
    reconcile_durable_history,
)
from ordivon_capital.accounting.tigerbeetle_substrate import AccountingMappingError, TigerBeetleOperation, resolution_instruction


def namespace() -> CapitalAccountNamespace:
    return CapitalAccountNamespace(
        owner_root="owner:primary",
        resource_identity="parcel:usd:canonical",
        ledger=11,
        account_code=718,
    )


def binding():
    return binding_for_namespace(
        namespace=namespace(),
        reservation_ref="reservation:r32:1",
        amount=700,
        transfer_code=720,
    )


def pending_obs():
    b=binding()
    return ProviderTransferObservation(
        transfer_id=b.pending_transfer_id,
        operation=TigerBeetleOperation.PENDING,
        amount=b.amount,
    )


def terminal_obs(operation: TigerBeetleOperation, resolution_ref: str):
    b=binding()
    i=resolution_instruction(binding=b, operation=operation, resolution_ref=resolution_ref)
    assert i is not None
    return ProviderTransferObservation(
        transfer_id=i.transfer_id,
        operation=i.operation,
        amount=i.amount,
        pending_id=i.pending_id,
    )


def test_account_namespace_is_stable_and_role_separated() -> None:
    a=namespace(); b=namespace()
    assert a.available_account_id == b.available_account_id
    assert a.encumbrance_account_id == b.encumbrance_account_id
    assert a.available_account_id != a.encumbrance_account_id
    assert a.account(CapitalAccountRole.AVAILABLE).debits_must_not_exceed_credits is True
    assert a.account(CapitalAccountRole.ENCUMBRANCE).debits_must_not_exceed_credits is False


def test_namespace_changes_when_owner_or_resource_changes() -> None:
    a=namespace()
    other_owner=CapitalAccountNamespace("owner:secondary",a.resource_identity,a.ledger,a.account_code)
    other_resource=CapitalAccountNamespace(a.owner_root,"parcel:eur:canonical",a.ledger,a.account_code)
    assert a.available_account_id != other_owner.available_account_id
    assert a.available_account_id != other_resource.available_account_id


def test_raw_string_role_is_rejected() -> None:
    with pytest.raises(AccountingMappingError, match="CapitalAccountRole"):
        namespace().account_id("AVAILABLE")  # type: ignore[arg-type]


def test_reserved_history_matches_exact_pending_provider_history() -> None:
    r=reconcile_durable_history(
        history=DurableReservationHistory(binding(),ReservationStanding.RESERVED),
        pending=pending_obs(),
        resolution=None,
    )
    assert r.standing is DurableProviderStanding.MATCH
    assert r.provider_repair_allowed is False
    assert r.terminal_history_preserved is False


def test_consumed_history_survives_missing_provider_resolution_without_reopening() -> None:
    r=reconcile_durable_history(
        history=DurableReservationHistory(binding(),ReservationStanding.CONSUMED,"effect:r32:consume"),
        pending=pending_obs(),
        resolution=None,
    )
    assert r.standing is DurableProviderStanding.PROVIDER_INCOMPLETE_NO_REPAIR
    assert r.terminal_history_preserved is True
    assert r.provider_repair_allowed is False


def test_consumed_history_matches_exact_provider_post() -> None:
    r=reconcile_durable_history(
        history=DurableReservationHistory(binding(),ReservationStanding.CONSUMED,"effect:r32:consume"),
        pending=pending_obs(),
        resolution=terminal_obs(TigerBeetleOperation.POST_PENDING_TRANSFER,"effect:r32:consume"),
    )
    assert r.standing is DurableProviderStanding.MATCH
    assert r.terminal_history_preserved is True


def test_released_history_rejects_provider_post_contradiction() -> None:
    r=reconcile_durable_history(
        history=DurableReservationHistory(binding(),ReservationStanding.RELEASED,"effect:r32:release"),
        pending=pending_obs(),
        resolution=terminal_obs(TigerBeetleOperation.POST_PENDING_TRANSFER,"effect:r32:consume"),
    )
    assert r.standing is DurableProviderStanding.CONTRADICTION_NO_REPAIR
    assert r.terminal_history_preserved is True
    assert r.provider_repair_allowed is False


def test_reserved_history_rejects_provider_terminal_ahead_of_semantics() -> None:
    r=reconcile_durable_history(
        history=DurableReservationHistory(binding(),ReservationStanding.RESERVED),
        pending=pending_obs(),
        resolution=terminal_obs(TigerBeetleOperation.VOID_PENDING_TRANSFER,"effect:r32:release"),
    )
    assert r.standing is DurableProviderStanding.CONTRADICTION_NO_REPAIR
    assert r.provider_repair_allowed is False
