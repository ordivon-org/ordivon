from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .semantic import SemanticViolation


TIGERBEETLE_VERSION = "0.17.9"
TIGERBEETLE_BINARY = Path("/usr/local/bin/tigerbeetle")
TIGERBEETLE_CLIENT_PYTHON = Path(
    "/opt/ordivon/external/tigerbeetle/0.17.9/python-client/bin/python"
)

# TigerBeetle is a mechanical accounting provider. These keys belong to Market
# Capital's semantic layer and must never be accepted as provider-minted truth.
_DOMAIN_TRUTH_KEYS = frozenset(
    {
        "capitalTruth",
        "claimRoot",
        "parcel",
        "treasuryStanding",
        "scarcityAuthority",
        "reservationStanding",
        "grantStanding",
        "effectAuthority",
        "settlementTruth",
        "legalOwnership",
        "withdrawability",
        "deployability",
        "externalFinancialWriteAdmission",
    }
)


@dataclass(frozen=True)
class TigerBeetleProviderContract:
    version: str = TIGERBEETLE_VERSION
    binary: Path = TIGERBEETLE_BINARY
    client_python: Path = TIGERBEETLE_CLIENT_PYTHON

    def installation_present(self) -> bool:
        return self.binary.is_file() and self.client_python.is_file()


@dataclass(frozen=True)
class AccountingAccount:
    """Provider-neutral account mechanics.

    `account_id`, `ledger`, and `code` are provider identifiers. They do not
    establish ownership, settlement, availability, deployability, or authority.
    """

    account_id: int
    ledger: int
    code: int
    debits_must_not_exceed_credits: bool = False
    history: bool = True

    def __post_init__(self) -> None:
        _require_u128_nonzero("account_id", self.account_id)
        _require_u32_nonzero("ledger", self.ledger)
        _require_u16_nonzero("code", self.code)

    def as_wire_record(self) -> dict[str, int]:
        # The numeric flag values are deliberately resolved by the external
        # official client runner, not duplicated here.
        return {
            "id": self.account_id,
            "debits_pending": 0,
            "debits_posted": 0,
            "credits_pending": 0,
            "credits_posted": 0,
            "user_data_128": 0,
            "user_data_64": 0,
            "user_data_32": 0,
            "ledger": self.ledger,
            "code": self.code,
            "timestamp": 0,
        }


@dataclass(frozen=True)
class AccountingTransfer:
    """Provider-neutral atomic transfer mechanics request."""

    transfer_id: int
    debit_account_id: int
    credit_account_id: int
    amount: int
    ledger: int
    code: int

    def __post_init__(self) -> None:
        _require_u128_nonzero("transfer_id", self.transfer_id)
        _require_u128_nonzero("debit_account_id", self.debit_account_id)
        _require_u128_nonzero("credit_account_id", self.credit_account_id)
        _require_u128("amount", self.amount)
        _require_u32_nonzero("ledger", self.ledger)
        _require_u16_nonzero("code", self.code)
        if self.debit_account_id == self.credit_account_id:
            raise SemanticViolation("TigerBeetle debit and credit accounts must differ")

    def as_wire_record(self) -> dict[str, int]:
        return {
            "id": self.transfer_id,
            "debit_account_id": self.debit_account_id,
            "credit_account_id": self.credit_account_id,
            "amount": self.amount,
            "pending_id": 0,
            "user_data_128": 0,
            "user_data_64": 0,
            "user_data_32": 0,
            "timeout": 0,
            "ledger": self.ledger,
            "code": self.code,
            "flags": 0,
            "timestamp": 0,
        }


def assert_mechanical_provider_record(record: Mapping[str, Any]) -> None:
    leaked = sorted(_DOMAIN_TRUTH_KEYS.intersection(record))
    if leaked:
        raise SemanticViolation(
            "TigerBeetle mechanical state cannot mint Market Capital domain truth: "
            + ", ".join(leaked)
        )


def _require_int(name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SemanticViolation(f"{name} must be an integer")
    return value


def _require_u128(name: str, value: object) -> None:
    n = _require_int(name, value)
    if n < 0 or n >= 2**128:
        raise SemanticViolation(f"{name} must fit unsigned 128-bit range")


def _require_u128_nonzero(name: str, value: object) -> None:
    _require_u128(name, value)
    if value == 0:
        raise SemanticViolation(f"{name} must be non-zero")


def _require_u32_nonzero(name: str, value: object) -> None:
    n = _require_int(name, value)
    if n <= 0 or n >= 2**32:
        raise SemanticViolation(f"{name} must fit non-zero unsigned 32-bit range")


def _require_u16_nonzero(name: str, value: object) -> None:
    n = _require_int(name, value)
    if n <= 0 or n >= 2**16:
        raise SemanticViolation(f"{name} must fit non-zero unsigned 16-bit range")
