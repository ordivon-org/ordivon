from pathlib import Path

import pytest

from market_capital.semantic import SemanticViolation, reject_false_green
from market_capital.tigerbeetle_substrate import (
    AccountingAccount,
    AccountingTransfer,
    TigerBeetleProviderContract,
    assert_mechanical_provider_record,
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


def test_transfer_wire_record_matches_provider_shape() -> None:
    transfer = AccountingTransfer(
        transfer_id=501,
        debit_account_id=101,
        credit_account_id=202,
        amount=500,
        ledger=1,
        code=720,
    )
    record = transfer.as_wire_record()
    assert record == {
        "id": 501,
        "debit_account_id": 101,
        "credit_account_id": 202,
        "amount": 500,
        "pending_id": 0,
        "user_data_128": 0,
        "user_data_64": 0,
        "user_data_32": 0,
        "timeout": 0,
        "ledger": 1,
        "code": 720,
        "flags": 0,
        "timestamp": 0,
    }
    assert_mechanical_provider_record(record)


def test_zero_amount_is_not_locally_rejected_because_provider_017_allows_it() -> None:
    transfer = AccountingTransfer(
        transfer_id=501,
        debit_account_id=101,
        credit_account_id=202,
        amount=0,
        ledger=1,
        code=720,
    )
    assert transfer.as_wire_record()["amount"] == 0


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
