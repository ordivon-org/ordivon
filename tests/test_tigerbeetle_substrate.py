from pathlib import Path

import pytest

from market_capital.semantic import EffectDisposition, SemanticViolation, reject_false_green
from market_capital.tigerbeetle_substrate import (
    AccountingAccount,
    AccountingTransfer,
    CapitalReservationBinding,
    TigerBeetleOperation,
    TigerBeetleProviderContract,
    assert_mechanical_provider_record,
    reservation_instruction,
    resolution_instruction,
    stable_provider_id,
)


def binding(*, ref: str = "reservation:alpha", resource: str = "parcel:usd:1", amount: int = 700) -> CapitalReservationBinding:
    return CapitalReservationBinding(
        reservation_ref=ref,
        resource_identity=resource,
        source_account_id=101,
        encumbrance_account_id=202,
        amount=amount,
        ledger=1,
        code=720,
    )


def test_provider_contract_is_pinned_without_owning_domain_truth() -> None:
    provider = TigerBeetleProviderContract()
    assert provider.version == "0.17.9"
    assert provider.binary == Path("/usr/local/bin/tigerbeetle")
    assert provider.client_python == Path(
        "/opt/ordivon/external/tigerbeetle/0.17.9/python-client/bin/python"
    )


def test_account_wire_record_is_mechanics_only() -> None:
    account = AccountingAccount(account_id=101, ledger=1, code=718)
    record = account.as_wire_record()
    assert record["id"] == 101
    assert record["ledger"] == 1
    assert record["code"] == 718
    assert_mechanical_provider_record(record)


def test_immediate_transfer_wire_record_matches_provider_shape() -> None:
    transfer = AccountingTransfer(
        transfer_id=501,
        debit_account_id=101,
        credit_account_id=202,
        amount=500,
        ledger=1,
        code=720,
    )
    record = transfer.as_wire_record()
    assert record["amount"] == 500
    assert record["pending_id"] == 0
    assert record["flags"] == 0
    assert_mechanical_provider_record(record)


def test_zero_amount_immediate_transfer_is_not_locally_rejected() -> None:
    transfer = AccountingTransfer(
        transfer_id=501,
        debit_account_id=101,
        credit_account_id=202,
        amount=0,
        ledger=1,
        code=720,
    )
    assert transfer.as_wire_record()["amount"] == 0


def test_reservation_identity_binding_is_deterministic_and_exact() -> None:
    a = binding()
    b = binding()
    c = binding(resource="parcel:usd:2")
    assert a.pending_transfer_id == b.pending_transfer_id
    assert a.pending_transfer_id != c.pending_transfer_id
    assert a.pending_transfer_id == stable_provider_id(
        "market-capital:tigerbeetle:reservation",
        "reservation:alpha",
        "parcel:usd:1",
    )


def test_reservation_maps_to_pending_transfer_only() -> None:
    instruction = reservation_instruction(binding())
    assert instruction.operation is TigerBeetleOperation.PENDING
    assert instruction.amount == 700
    assert instruction.pending_id == 0
    assert instruction.as_wire_record()["flag_name"] == "PENDING"


def test_retain_means_no_provider_mutation() -> None:
    assert resolution_instruction(
        binding=binding(),
        disposition=EffectDisposition.RETAIN,
        resolution_ref="effect:retain:1",
    ) is None


def test_release_maps_to_void_pending_transfer() -> None:
    b = binding()
    instruction = resolution_instruction(
        binding=b,
        disposition=EffectDisposition.RELEASE,
        resolution_ref="effect:release:1",
    )
    assert instruction is not None
    assert instruction.operation is TigerBeetleOperation.VOID_PENDING_TRANSFER
    assert instruction.pending_id == b.pending_transfer_id
    assert instruction.amount == 0


def test_consume_maps_to_post_pending_transfer_for_reserved_amount() -> None:
    b = binding(amount=600)
    instruction = resolution_instruction(
        binding=b,
        disposition=EffectDisposition.CONSUME,
        resolution_ref="effect:consume:1",
    )
    assert instruction is not None
    assert instruction.operation is TigerBeetleOperation.POST_PENDING_TRANSFER
    assert instruction.pending_id == b.pending_transfer_id
    assert instruction.amount == 600


def test_provider_adapter_will_not_accept_caller_string_as_disposition() -> None:
    with pytest.raises(SemanticViolation, match="Market Capital EffectDisposition"):
        resolution_instruction(
            binding=binding(),
            disposition="RELEASE",  # type: ignore[arg-type]
            resolution_ref="effect:release:1",
        )


def test_reservation_requires_positive_amount() -> None:
    with pytest.raises(SemanticViolation, match="must be positive"):
        binding(amount=0)


def test_self_transfer_fails_before_provider() -> None:
    with pytest.raises(SemanticViolation, match="must differ"):
        AccountingTransfer(
            transfer_id=501,
            debit_account_id=101,
            credit_account_id=101,
            amount=500,
            ledger=1,
            code=720,
        )


def test_provider_record_cannot_mint_market_capital_truth() -> None:
    with pytest.raises(SemanticViolation, match="cannot mint"):
        assert_mechanical_provider_record(
            {"id": 501, "ledger": 1, "deployability": True}
        )


def test_existing_false_green_law_rejects_ledger_balance_as_deployable_capital() -> None:
    with pytest.raises(SemanticViolation, match="ledger balance is not deployable capital"):
        reject_false_green("tigerbeetle_balance")
