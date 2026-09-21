from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AccountingMappingError(ValueError):
    """Invalid bounded accounting mapping."""


class AccountingOperation(StrEnum):
    PENDING = "PENDING"
    POST_PENDING_TRANSFER = "POST_PENDING_TRANSFER"
    VOID_PENDING_TRANSFER = "VOID_PENDING_TRANSFER"


@dataclass(frozen=True)
class AccountingAccount:
    account_id: int
    no_overdraft: bool = False

    def __post_init__(self) -> None:
        _require_u128_nonzero("account_id", self.account_id)


@dataclass(frozen=True)
class CapitalReservationBinding:
    reservation_ref: str
    resource_identity: str
    source_account_id: int
    encumbrance_account_id: int
    amount: int

    def __post_init__(self) -> None:
        if not self.reservation_ref.strip():
            raise AccountingMappingError("reservation_ref required")
        if not self.resource_identity.strip():
            raise AccountingMappingError("resource_identity required")
        _require_u128_nonzero("source_account_id", self.source_account_id)
        _require_u128_nonzero("encumbrance_account_id", self.encumbrance_account_id)
        _require_u128("amount", self.amount)
        if self.source_account_id == self.encumbrance_account_id:
            raise AccountingMappingError("reservation accounts must differ")
        if self.amount <= 0:
            raise AccountingMappingError("capital reservation amount must be positive")

    @property
    def pending_transfer_id(self) -> int:
        return stable_accounting_id(
            "ordivon-capital:accounting:reservation",
            self.reservation_ref,
            self.resource_identity,
        )


@dataclass(frozen=True)
class AccountingInstruction:
    operation: AccountingOperation
    transfer_id: int
    debit_account_id: int
    credit_account_id: int
    amount: int
    pending_id: int = 0

    def __post_init__(self) -> None:
        _require_u128_nonzero("transfer_id", self.transfer_id)
        _require_u128_nonzero("debit_account_id", self.debit_account_id)
        _require_u128_nonzero("credit_account_id", self.credit_account_id)
        _require_u128("amount", self.amount)
        _require_u128("pending_id", self.pending_id)
        if self.debit_account_id == self.credit_account_id:
            raise AccountingMappingError("debit and credit accounts must differ")
        if self.operation is AccountingOperation.PENDING:
            if self.amount <= 0:
                raise AccountingMappingError("pending amount must be positive")
            if self.pending_id != 0:
                raise AccountingMappingError("pending instruction cannot reference pending_id")
        else:
            if self.pending_id == 0:
                raise AccountingMappingError("resolution requires pending_id")
        if (
            self.operation is AccountingOperation.VOID_PENDING_TRANSFER
            and self.amount != 0
        ):
            raise AccountingMappingError("void pending transfer amount must be zero")


def reservation_instruction(binding: CapitalReservationBinding) -> AccountingInstruction:
    return AccountingInstruction(
        operation=AccountingOperation.PENDING,
        transfer_id=binding.pending_transfer_id,
        debit_account_id=binding.source_account_id,
        credit_account_id=binding.encumbrance_account_id,
        amount=binding.amount,
    )


def resolution_instruction(
    *,
    binding: CapitalReservationBinding,
    operation: AccountingOperation | None,
    resolution_ref: str,
) -> AccountingInstruction | None:
    if operation is None:
        return None
    if operation not in {
        AccountingOperation.POST_PENDING_TRANSFER,
        AccountingOperation.VOID_PENDING_TRANSFER,
    }:
        raise AccountingMappingError("resolution operation must POST or VOID")
    if not resolution_ref.strip():
        raise AccountingMappingError("resolution_ref required")
    if resolution_ref == binding.reservation_ref:
        raise AccountingMappingError(
            "resolution identity must differ from reservation identity"
        )
    amount = (
        0
        if operation is AccountingOperation.VOID_PENDING_TRANSFER
        else binding.amount
    )
    return AccountingInstruction(
        operation=operation,
        transfer_id=stable_accounting_id(
            "ordivon-capital:accounting:resolution",
            resolution_ref,
            binding.reservation_ref,
            binding.resource_identity,
            operation.value,
        ),
        debit_account_id=binding.source_account_id,
        credit_account_id=binding.encumbrance_account_id,
        amount=amount,
        pending_id=binding.pending_transfer_id,
    )


def stable_accounting_id(namespace: str, *parts: str) -> int:
    if not namespace.strip() or not parts or any(not part.strip() for part in parts):
        raise AccountingMappingError(
            "accounting identity binding requires non-empty namespace and parts"
        )
    payload = "\x1f".join((namespace, *parts)).encode()
    value = int.from_bytes(hashlib.sha256(payload).digest()[:16], "big")
    return value or 1


def ensure_accounting_only(record: dict[str, Any]) -> None:
    forbidden = {
        "settlementFinal",
        "legalOwnership",
        "withdrawable",
        "deployable",
        "venueOrderStatus",
        "venueFillStatus",
        "externalWriteAllowed",
        "reconciliationStanding",
    }
    leaked = sorted(forbidden.intersection(record))
    if leaked:
        raise AccountingMappingError(
            "accounting state cannot carry non-accounting domain fields: "
            + ", ".join(leaked)
        )


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
