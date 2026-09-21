from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .substrate import (
    AccountingAccount,
    AccountingMappingError,
    AccountingOperation,
    CapitalReservationBinding,
    resolution_instruction,
    stable_accounting_id,
)


class CapitalAccountRole(StrEnum):
    AVAILABLE = "AVAILABLE"
    ENCUMBRANCE = "ENCUMBRANCE"


@dataclass(frozen=True)
class CapitalAccountNamespace:
    owner_root: str
    resource_identity: str

    def __post_init__(self) -> None:
        if not self.owner_root.strip():
            raise AccountingMappingError("owner_root required")
        if not self.resource_identity.strip():
            raise AccountingMappingError("resource_identity required")

    def account_id(self, role: CapitalAccountRole) -> int:
        if not isinstance(role, CapitalAccountRole):
            raise AccountingMappingError("role must be a CapitalAccountRole")
        return stable_accounting_id(
            "ordivon-capital:accounting:account",
            self.owner_root,
            self.resource_identity,
            role.value,
        )

    def account(self, role: CapitalAccountRole) -> AccountingAccount:
        return AccountingAccount(
            account_id=self.account_id(role),
            no_overdraft=role is CapitalAccountRole.AVAILABLE,
        )

    @property
    def available_account_id(self) -> int:
        return self.account_id(CapitalAccountRole.AVAILABLE)

    @property
    def encumbrance_account_id(self) -> int:
        return self.account_id(CapitalAccountRole.ENCUMBRANCE)


class ReservationStanding(StrEnum):
    RESERVED = "RESERVED"
    RELEASED = "RELEASED"
    CONSUMED = "CONSUMED"


class LedgerReconciliationStanding(StrEnum):
    MATCH = "MATCH"
    LEDGER_INCOMPLETE_NO_REPAIR = "LEDGER_INCOMPLETE_NO_REPAIR"
    CONTRADICTION_NO_REPAIR = "CONTRADICTION_NO_REPAIR"


@dataclass(frozen=True)
class LedgerTransferObservation:
    transfer_id: int
    operation: AccountingOperation
    amount: int
    pending_id: int = 0


@dataclass(frozen=True)
class DurableReservationHistory:
    binding: CapitalReservationBinding
    standing: ReservationStanding
    resolution_ref: str | None = None

    def __post_init__(self) -> None:
        if self.standing is ReservationStanding.RESERVED:
            if self.resolution_ref is not None:
                raise AccountingMappingError(
                    "RESERVED history cannot carry a resolution_ref"
                )
        elif not self.resolution_ref or not self.resolution_ref.strip():
            raise AccountingMappingError(
                "terminal reservation history requires resolution_ref"
            )


@dataclass(frozen=True)
class DurableReconciliationResult:
    standing: LedgerReconciliationStanding
    terminal_history_preserved: bool
    ledger_repair_allowed: bool
    reason: str


def binding_for_namespace(
    *,
    namespace: CapitalAccountNamespace,
    reservation_ref: str,
    amount: int,
) -> CapitalReservationBinding:
    return CapitalReservationBinding(
        reservation_ref=reservation_ref,
        resource_identity=namespace.resource_identity,
        source_account_id=namespace.available_account_id,
        encumbrance_account_id=namespace.encumbrance_account_id,
        amount=amount,
    )


def reconcile_durable_history(
    *,
    history: DurableReservationHistory,
    pending: LedgerTransferObservation | None,
    resolution: LedgerTransferObservation | None,
) -> DurableReconciliationResult:
    expected_pending_id = history.binding.pending_transfer_id
    if pending is None:
        return _result(
            LedgerReconciliationStanding.LEDGER_INCOMPLETE_NO_REPAIR,
            history,
            "ledger is missing the reservation transfer; do not recreate from history",
        )
    if (
        pending.transfer_id != expected_pending_id
        or pending.operation is not AccountingOperation.PENDING
        or pending.amount != history.binding.amount
        or pending.pending_id != 0
    ):
        return _result(
            LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR,
            history,
            "ledger reservation transfer contradicts the exact reservation binding",
        )

    if history.standing is ReservationStanding.RESERVED:
        if resolution is None:
            return _result(
                LedgerReconciliationStanding.MATCH,
                history,
                "ledger retains exact pending reservation",
            )
        return _result(
            LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR,
            history,
            "ledger has a terminal resolution absent from reservation history",
        )

    operation = (
        AccountingOperation.VOID_PENDING_TRANSFER
        if history.standing is ReservationStanding.RELEASED
        else AccountingOperation.POST_PENDING_TRANSFER
    )
    expected = resolution_instruction(
        binding=history.binding,
        operation=operation,
        resolution_ref=history.resolution_ref or "",
    )
    assert expected is not None
    if resolution is None:
        return _result(
            LedgerReconciliationStanding.LEDGER_INCOMPLETE_NO_REPAIR,
            history,
            "terminal reservation history is missing its ledger resolution",
        )
    if (
        resolution.transfer_id != expected.transfer_id
        or resolution.operation is not expected.operation
        or resolution.pending_id != expected_pending_id
    ):
        return _result(
            LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR,
            history,
            "ledger resolution contradicts exact terminal reservation history",
        )
    if (
        operation is AccountingOperation.POST_PENDING_TRANSFER
        and resolution.amount != history.binding.amount
    ):
        return _result(
            LedgerReconciliationStanding.CONTRADICTION_NO_REPAIR,
            history,
            "ledger consume amount differs from terminal reservation amount",
        )
    return _result(
        LedgerReconciliationStanding.MATCH,
        history,
        "ledger history matches terminal reservation history",
    )


def _result(
    standing: LedgerReconciliationStanding,
    history: DurableReservationHistory,
    reason: str,
) -> DurableReconciliationResult:
    return DurableReconciliationResult(
        standing=standing,
        terminal_history_preserved=history.standing
        is not ReservationStanding.RESERVED,
        ledger_repair_allowed=False,
        reason=reason,
    )
