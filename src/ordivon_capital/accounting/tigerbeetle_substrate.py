from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

TIGERBEETLE_VERSION = "0.17.9"
TIGERBEETLE_BINARY = Path("/usr/local/bin/tigerbeetle")
TIGERBEETLE_CLIENT_PYTHON = Path(
    "/opt/ordivon/external/tigerbeetle/0.17.9/python-client/bin/python"
)


class AccountingMappingError(ValueError):
    """Invalid mapping into TigerBeetle mechanical accounting records."""

_NON_ACCOUNTING_FIELDS = frozenset(
    {
        "settlementFinal",
        "legalOwnership",
        "withdrawable",
        "deployable",
        "deployability",
        "venueOrderStatus",
        "venueFillStatus",
        "externalWriteAllowed",
        "reconciliationStanding",
    }
)


class TigerBeetleOperation(StrEnum):
    PENDING = "PENDING"
    POST_PENDING_TRANSFER = "POST_PENDING_TRANSFER"
    VOID_PENDING_TRANSFER = "VOID_PENDING_TRANSFER"


@dataclass(frozen=True)
class TigerBeetleProviderContract:
    version: str = TIGERBEETLE_VERSION
    binary: Path = TIGERBEETLE_BINARY
    client_python: Path = TIGERBEETLE_CLIENT_PYTHON

    def installation_present(self) -> bool:
        return self.binary.is_file() and self.client_python.is_file()


@dataclass(frozen=True)
class AccountingAccount:
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
    transfer_id: int
    debit_account_id: int
    credit_account_id: int
    amount: int
    ledger: int
    code: int

    def __post_init__(self) -> None:
        _validate_transfer_fields(
            transfer_id=self.transfer_id,
            debit_account_id=self.debit_account_id,
            credit_account_id=self.credit_account_id,
            amount=self.amount,
            ledger=self.ledger,
            code=self.code,
        )

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


@dataclass(frozen=True)
class CapitalReservationBinding:
    reservation_ref: str
    resource_identity: str
    source_account_id: int
    encumbrance_account_id: int
    amount: int
    ledger: int
    code: int
    timeout_seconds: int = 0

    def __post_init__(self) -> None:
        if not self.reservation_ref.strip():
            raise AccountingMappingError("reservation_ref required")
        if not self.resource_identity.strip():
            raise AccountingMappingError("resource_identity required")
        _validate_transfer_fields(
            transfer_id=self.pending_transfer_id,
            debit_account_id=self.source_account_id,
            credit_account_id=self.encumbrance_account_id,
            amount=self.amount,
            ledger=self.ledger,
            code=self.code,
        )
        if self.amount <= 0:
            raise AccountingMappingError("capital reservation amount must be positive")
        _require_u32("timeout_seconds", self.timeout_seconds)

    @property
    def pending_transfer_id(self) -> int:
        return stable_provider_id(
            "market-capital:tigerbeetle:reservation",
            self.reservation_ref,
            self.resource_identity,
        )


@dataclass(frozen=True)
class TigerBeetleTransferInstruction:
    operation: TigerBeetleOperation
    transfer_id: int
    debit_account_id: int
    credit_account_id: int
    amount: int
    pending_id: int
    ledger: int
    code: int
    timeout_seconds: int = 0

    def __post_init__(self) -> None:
        _validate_transfer_fields(
            transfer_id=self.transfer_id,
            debit_account_id=self.debit_account_id,
            credit_account_id=self.credit_account_id,
            amount=self.amount,
            ledger=self.ledger,
            code=self.code,
        )
        _require_u128("pending_id", self.pending_id)
        _require_u32("timeout_seconds", self.timeout_seconds)
        if self.operation is TigerBeetleOperation.PENDING:
            if self.pending_id != 0:
                raise AccountingMappingError("pending reservation transfer cannot reference pending_id")
        else:
            if self.pending_id == 0:
                raise AccountingMappingError("pending resolution requires pending_id")
            if self.timeout_seconds != 0:
                raise AccountingMappingError("pending resolution timeout must be zero")
        if self.operation is TigerBeetleOperation.VOID_PENDING_TRANSFER and self.amount != 0:
            raise AccountingMappingError("void pending transfer amount must be zero")

    def as_wire_record(self) -> dict[str, int | str]:
        return {
            "id": self.transfer_id,
            "debit_account_id": self.debit_account_id,
            "credit_account_id": self.credit_account_id,
            "amount": self.amount,
            "pending_id": self.pending_id,
            "user_data_128": 0,
            "user_data_64": 0,
            "user_data_32": 0,
            "timeout": self.timeout_seconds,
            "ledger": self.ledger,
            "code": self.code,
            "flag_name": self.operation.value,
            "timestamp": 0,
        }


def reservation_instruction(binding: CapitalReservationBinding) -> TigerBeetleTransferInstruction:
    return TigerBeetleTransferInstruction(
        operation=TigerBeetleOperation.PENDING,
        transfer_id=binding.pending_transfer_id,
        debit_account_id=binding.source_account_id,
        credit_account_id=binding.encumbrance_account_id,
        amount=binding.amount,
        pending_id=0,
        ledger=binding.ledger,
        code=binding.code,
        timeout_seconds=binding.timeout_seconds,
    )


def resolution_instruction(
    *,
    binding: CapitalReservationBinding,
    operation: TigerBeetleOperation | None,
    resolution_ref: str,
) -> TigerBeetleTransferInstruction | None:
    if operation is None:
        return None
    if operation not in {
        TigerBeetleOperation.VOID_PENDING_TRANSFER,
        TigerBeetleOperation.POST_PENDING_TRANSFER,
    }:
        raise AccountingMappingError("resolution operation must POST or VOID a pending TigerBeetle transfer")
    if not resolution_ref.strip():
        raise AccountingMappingError("resolution_ref required")
    if resolution_ref == binding.reservation_ref:
        raise AccountingMappingError("resolution identity must differ from reservation identity")

    amount = 0 if operation is TigerBeetleOperation.VOID_PENDING_TRANSFER else binding.amount
    return TigerBeetleTransferInstruction(
        operation=operation,
        transfer_id=stable_provider_id(
            "market-capital:tigerbeetle:resolution",
            resolution_ref,
            binding.reservation_ref,
            binding.resource_identity,
            operation.value,
        ),
        debit_account_id=binding.source_account_id,
        credit_account_id=binding.encumbrance_account_id,
        amount=amount,
        pending_id=binding.pending_transfer_id,
        ledger=binding.ledger,
        code=binding.code,
        timeout_seconds=0,
    )


def stable_provider_id(namespace: str, *parts: str) -> int:
    if not namespace.strip() or not parts or any(not p.strip() for p in parts):
        raise AccountingMappingError("provider identity binding requires non-empty namespace and parts")
    payload = "\x1f".join((namespace, *parts)).encode("utf-8")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return value or 1


def assert_mechanical_provider_record(record: Mapping[str, Any]) -> None:
    leaked = sorted(_NON_ACCOUNTING_FIELDS.intersection(record))
    if leaked:
        raise AccountingMappingError(
            "TigerBeetle accounting records cannot carry non-accounting domain fields: "
            + ", ".join(leaked)
        )


def _validate_transfer_fields(
    *,
    transfer_id: int,
    debit_account_id: int,
    credit_account_id: int,
    amount: int,
    ledger: int,
    code: int,
) -> None:
    _require_u128_nonzero("transfer_id", transfer_id)
    _require_u128_nonzero("debit_account_id", debit_account_id)
    _require_u128_nonzero("credit_account_id", credit_account_id)
    _require_u128("amount", amount)
    _require_u32_nonzero("ledger", ledger)
    _require_u16_nonzero("code", code)
    if debit_account_id == credit_account_id:
        raise AccountingMappingError("TigerBeetle debit and credit accounts must differ")


def _require_int(name: str, value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise AccountingMappingError(f"{name} must be an integer")
    return value


def _require_u128(name: str, value: object) -> None:
    n = _require_int(name, value)
    if n < 0 or n >= 2**128:
        raise AccountingMappingError(f"{name} must fit unsigned 128-bit range")


def _require_u128_nonzero(name: str, value: object) -> None:
    _require_u128(name, value)
    if value == 0:
        raise AccountingMappingError(f"{name} must be non-zero")


def _require_u32(name: str, value: object) -> None:
    n = _require_int(name, value)
    if n < 0 or n >= 2**32:
        raise AccountingMappingError(f"{name} must fit unsigned 32-bit range")


def _require_u32_nonzero(name: str, value: object) -> None:
    _require_u32(name, value)
    if value == 0:
        raise AccountingMappingError(f"{name} must be non-zero")


def _require_u16_nonzero(name: str, value: object) -> None:
    n = _require_int(name, value)
    if n <= 0 or n >= 2**16:
        raise AccountingMappingError(f"{name} must fit non-zero unsigned 16-bit range")
