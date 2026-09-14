from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .semantic import EffectDisposition, SemanticViolation
from .tigerbeetle_substrate import (
    AccountingAccount,
    CapitalReservationBinding,
    TigerBeetleOperation,
    resolution_instruction,
    stable_provider_id,
)


class CapitalAccountRole(str, Enum):
    AVAILABLE = "AVAILABLE"
    ENCUMBRANCE = "ENCUMBRANCE"


@dataclass(frozen=True)
class CapitalAccountNamespace:
    owner_root: str
    resource_identity: str
    ledger: int
    account_code: int

    def __post_init__(self) -> None:
        if not self.owner_root.strip():
            raise SemanticViolation("owner_root required")
        if not self.resource_identity.strip():
            raise SemanticViolation("resource_identity required")
        if not isinstance(self.ledger, int) or isinstance(self.ledger, bool) or not (0 < self.ledger < 2**32):
            raise SemanticViolation("ledger must fit non-zero unsigned 32-bit range")
        if not isinstance(self.account_code, int) or isinstance(self.account_code, bool) or not (0 < self.account_code < 2**16):
            raise SemanticViolation("account_code must fit non-zero unsigned 16-bit range")

    def account_id(self, role: CapitalAccountRole) -> int:
        if not isinstance(role, CapitalAccountRole):
            raise SemanticViolation("role must be a CapitalAccountRole")
        return stable_provider_id(
            "market-capital:tigerbeetle:account",
            self.owner_root,
            self.resource_identity,
            str(self.ledger),
            str(self.account_code),
            role.value,
        )

    def account(self, role: CapitalAccountRole) -> AccountingAccount:
        return AccountingAccount(
            account_id=self.account_id(role),
            ledger=self.ledger,
            code=self.account_code,
            debits_must_not_exceed_credits=role is CapitalAccountRole.AVAILABLE,
            history=True,
        )

    @property
    def available_account_id(self) -> int:
        return self.account_id(CapitalAccountRole.AVAILABLE)

    @property
    def encumbrance_account_id(self) -> int:
        return self.account_id(CapitalAccountRole.ENCUMBRANCE)


class SemanticReservationStanding(str, Enum):
    RESERVED = "RESERVED"
    RELEASED = "RELEASED"
    CONSUMED = "CONSUMED"


class DurableProviderStanding(str, Enum):
    MATCH = "MATCH"
    PROVIDER_INCOMPLETE_RETAIN = "PROVIDER_INCOMPLETE_RETAIN"
    CONTRADICTION_RETAIN = "CONTRADICTION_RETAIN"


@dataclass(frozen=True)
class ProviderTransferObservation:
    transfer_id: int
    operation: TigerBeetleOperation
    amount: int
    pending_id: int = 0


@dataclass(frozen=True)
class DurableReservationHistory:
    binding: CapitalReservationBinding
    standing: SemanticReservationStanding
    resolution_ref: str | None = None

    def __post_init__(self) -> None:
        if self.standing is SemanticReservationStanding.RESERVED:
            if self.resolution_ref is not None:
                raise SemanticViolation("RESERVED history cannot carry a resolution_ref")
        elif not self.resolution_ref or not self.resolution_ref.strip():
            raise SemanticViolation("terminal reservation history requires resolution_ref")


@dataclass(frozen=True)
class DurableReconciliationResult:
    standing: DurableProviderStanding
    semantic_terminal_preserved: bool
    provider_repair_allowed: bool
    reason: str


def binding_for_namespace(
    *,
    namespace: CapitalAccountNamespace,
    reservation_ref: str,
    amount: int,
    transfer_code: int,
    timeout_seconds: int = 0,
) -> CapitalReservationBinding:
    return CapitalReservationBinding(
        reservation_ref=reservation_ref,
        resource_identity=namespace.resource_identity,
        source_account_id=namespace.available_account_id,
        encumbrance_account_id=namespace.encumbrance_account_id,
        amount=amount,
        ledger=namespace.ledger,
        code=transfer_code,
        timeout_seconds=timeout_seconds,
    )


def reconcile_durable_history(
    *,
    history: DurableReservationHistory,
    pending: ProviderTransferObservation | None,
    resolution: ProviderTransferObservation | None,
) -> DurableReconciliationResult:
    """Compare durable domain history against provider history without repairing it.

    A mismatch never authorizes recreation, reopening, posting, or voiding. In
    particular a terminal semantic standing remains terminal even when provider state
    is missing or appears stale after restart/recovery.
    """

    expected_pending_id = history.binding.pending_transfer_id
    if pending is None:
        return _result(
            DurableProviderStanding.PROVIDER_INCOMPLETE_RETAIN,
            history,
            "provider is missing the reservation transfer; do not recreate from semantic history",
        )
    if (
        pending.transfer_id != expected_pending_id
        or pending.operation is not TigerBeetleOperation.PENDING
        or pending.amount != history.binding.amount
        or pending.pending_id != 0
    ):
        return _result(
            DurableProviderStanding.CONTRADICTION_RETAIN,
            history,
            "provider reservation transfer does not match exact semantic binding",
        )

    if history.standing is SemanticReservationStanding.RESERVED:
        if resolution is None:
            return _result(DurableProviderStanding.MATCH, history, "provider retains exact pending reservation")
        return _result(
            DurableProviderStanding.CONTRADICTION_RETAIN,
            history,
            "provider has a terminal resolution absent from semantic history",
        )

    disposition = (
        EffectDisposition.RELEASE
        if history.standing is SemanticReservationStanding.RELEASED
        else EffectDisposition.CONSUME
    )
    expected_resolution = resolution_instruction(
        binding=history.binding,
        disposition=disposition,
        resolution_ref=history.resolution_ref or "",
    )
    assert expected_resolution is not None
    if resolution is None:
        return _result(
            DurableProviderStanding.PROVIDER_INCOMPLETE_RETAIN,
            history,
            "terminal semantic history is missing its provider resolution; terminal history remains authoritative",
        )
    if (
        resolution.transfer_id != expected_resolution.transfer_id
        or resolution.operation is not expected_resolution.operation
        or resolution.pending_id != expected_pending_id
    ):
        return _result(
            DurableProviderStanding.CONTRADICTION_RETAIN,
            history,
            "provider resolution contradicts exact terminal semantic history",
        )
    if disposition is EffectDisposition.CONSUME and resolution.amount != history.binding.amount:
        return _result(
            DurableProviderStanding.CONTRADICTION_RETAIN,
            history,
            "provider consume amount differs from terminal semantic reservation amount",
        )
    return _result(DurableProviderStanding.MATCH, history, "provider history matches terminal semantic history")


def _result(
    standing: DurableProviderStanding,
    history: DurableReservationHistory,
    reason: str,
) -> DurableReconciliationResult:
    return DurableReconciliationResult(
        standing=standing,
        semantic_terminal_preserved=history.standing is not SemanticReservationStanding.RESERVED,
        provider_repair_allowed=False,
        reason=reason,
    )
