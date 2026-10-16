"""Provider-capacity observation and pre-dispatch admission contracts.

Capacity is dynamic Provider/account state. It is deliberately separate from RunBudget,
Provider request identity, Gateway binding authority, credentials, and retry/fallback.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Protocol

from anc_canonical import JsonValue, canonical_digest

from ..protocol import HarnessProtocolError
from .model import AgentTurnRequest


def _text(value: object, label: str, *, max_bytes: int = 512) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise HarnessProtocolError(f"{label} must be a non-empty trimmed string")
    if len(value.encode("utf-8")) > max_bytes:
        raise HarnessProtocolError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


class ProviderCapacityStatus(str, Enum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    ERROR = "error"


class CapacityAdmissionStanding(str, Enum):
    ADMIT = "admit"
    HOLD = "hold"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProviderCapacityWindow:
    """One normalized quota window; 10_000 basis points == 100%."""

    kind: str
    remaining_basis_points: int
    resets_at_ms: int | None = None

    def __post_init__(self) -> None:
        _text(self.kind, "capacity window kind", max_bytes=200)
        if (
            type(self.remaining_basis_points) is not int
            or not 0 <= self.remaining_basis_points <= 10_000
        ):
            raise HarnessProtocolError(
                "capacity remaining basis points must be an integer in [0, 10000]"
            )
        if self.resets_at_ms is not None and (
            type(self.resets_at_ms) is not int or self.resets_at_ms < 0
        ):
            raise HarnessProtocolError(
                "capacity reset time must be a non-negative millisecond timestamp"
            )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "kind": self.kind,
            "remainingBasisPoints": self.remaining_basis_points,
            "resetsAtMs": self.resets_at_ms,
        }


@dataclass(frozen=True, slots=True)
class ProviderCapacitySnapshot:
    """Sanitized capacity evidence bound to the principal actually observed."""

    source: str
    observed_at_ms: int
    principal_ref: str
    source_node_ref: str
    app: str
    provider_id: str
    provider_name: str | None
    status: ProviderCapacityStatus
    windows: tuple[ProviderCapacityWindow, ...] = ()
    account_ref: str | None = None

    def __post_init__(self) -> None:
        _text(self.source, "capacity source", max_bytes=200)
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise HarnessProtocolError(
                "capacity observed time must be a non-negative millisecond timestamp"
            )
        _text(self.principal_ref, "capacity principal reference", max_bytes=300)
        _text(self.source_node_ref, "capacity source node reference", max_bytes=300)
        _text(self.app, "capacity app", max_bytes=100)
        _text(self.provider_id, "capacity Provider identity", max_bytes=300)
        if self.provider_name is not None:
            _text(self.provider_name, "capacity Provider name", max_bytes=300)
        if self.account_ref is not None:
            _text(self.account_ref, "capacity account reference", max_bytes=300)
        kinds = [window.kind for window in self.windows]
        if len(kinds) != len(set(kinds)):
            raise HarnessProtocolError("capacity window kinds must be unique")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.provider-capacity-snapshot",
            "source": self.source,
            "observedAtMs": self.observed_at_ms,
            "principalRef": self.principal_ref,
            "sourceNodeRef": self.source_node_ref,
            "app": self.app,
            "providerId": self.provider_id,
            "providerName": self.provider_name,
            "accountRef": self.account_ref,
            "status": self.status.value,
            "windows": [window.to_dict() for window in self.windows],
        }

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())


@dataclass(frozen=True, slots=True)
class CapacityAdmissionDecision:
    standing: CapacityAdmissionStanding
    snapshot_digest: str
    reason: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.snapshot_digest, str)
            or not self.snapshot_digest.startswith("sha256:")
            or len(self.snapshot_digest) != 71
            or any(c not in "0123456789abcdef" for c in self.snapshot_digest[7:])
        ):
            raise HarnessProtocolError("capacity decision snapshot digest is invalid")
        _text(self.reason, "capacity decision reason", max_bytes=2_048)

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "standing": self.standing.value,
            "snapshotDigest": self.snapshot_digest,
            "reason": self.reason,
        }

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())


class CapacityAdmissionGuard(Protocol):
    def check(
        self,
        request: AgentTurnRequest,
        *,
        request_token_upper_bound: int | None,
    ) -> CapacityAdmissionDecision: ...


@dataclass(slots=True)
class SnapshotCapacityAdmissionGuard:
    """Simple reserve-watermark policy over one already-frozen Provider route."""

    snapshot: ProviderCapacitySnapshot
    reserve_basis_points: int
    max_staleness_ms: int
    expected_principal_ref: str
    clock_ms: Callable[[], int] = lambda: time.time_ns() // 1_000_000

    def __post_init__(self) -> None:
        if (
            type(self.reserve_basis_points) is not int
            or not 0 <= self.reserve_basis_points <= 10_000
        ):
            raise ValueError("capacity reserve basis points must be in [0, 10000]")
        if type(self.max_staleness_ms) is not int or self.max_staleness_ms < 1:
            raise ValueError("capacity max staleness must be positive")
        _text(self.expected_principal_ref, "expected capacity principal", max_bytes=300)
        if not callable(self.clock_ms):
            raise TypeError("capacity clock must be callable")

    def check(
        self,
        request: AgentTurnRequest,
        *,
        request_token_upper_bound: int | None,
    ) -> CapacityAdmissionDecision:
        del request, request_token_upper_bound
        digest = self.snapshot.digest
        if self.snapshot.principal_ref != self.expected_principal_ref:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "capacity observation principal differs from the frozen Provider principal",
            )
        age_ms = self.clock_ms() - self.snapshot.observed_at_ms
        if age_ms < 0 or age_ms > self.max_staleness_ms:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "capacity observation is stale or has a future observation time",
            )
        if self.snapshot.status is not ProviderCapacityStatus.AVAILABLE:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                f"capacity source status is {self.snapshot.status.value}; UNKNOWN is not zero",
            )
        if not self.snapshot.windows:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "capacity source reported available without a normalized quota window",
            )
        tightest = min(
            self.snapshot.windows,
            key=lambda window: window.remaining_basis_points,
        )
        if tightest.remaining_basis_points <= self.reserve_basis_points:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.HOLD,
                digest,
                (
                    f"capacity window {tightest.kind} is at or below the configured "
                    f"reserve watermark: {tightest.remaining_basis_points}<="
                    f"{self.reserve_basis_points}"
                ),
            )
        return CapacityAdmissionDecision(
            CapacityAdmissionStanding.ADMIT,
            digest,
            (
                f"capacity window {tightest.kind} remains above the configured reserve "
                f"watermark: {tightest.remaining_basis_points}>{self.reserve_basis_points}"
            ),
        )


def snapshot_from_cc_switch_quota(
    value: str | bytes | dict[str, Any],
    *,
    principal_ref: str,
    source_node_ref: str,
    account_ref: str | None = None,
    windows: tuple[ProviderCapacityWindow, ...] = (),
) -> ProviderCapacitySnapshot:
    """Normalize the CC Switch quota envelope without retaining raw result bytes.

    Provider-specific result schemas are intentionally not guessed. A principal-local
    observer may normalize supported quota windows and pass them explicitly.
    """

    if isinstance(value, bytes):
        value = value.decode("utf-8")
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, dict):
        raise HarnessProtocolError("CC Switch quota output must be a JSON object")

    required = {
        "app",
        "providerId",
        "providerName",
        "target",
        "status",
        "available",
        "queriedAt",
        "result",
        "error",
    }
    if set(parsed) != required:
        raise HarnessProtocolError("CC Switch quota envelope fields differ from v5.11.x")
    app = _text(parsed["app"], "CC Switch app", max_bytes=100)
    provider_id = _text(parsed["providerId"], "CC Switch Provider identity", max_bytes=300)
    provider_name = parsed["providerName"]
    if provider_name is not None:
        provider_name = _text(provider_name, "CC Switch Provider name", max_bytes=300)
    queried_at = parsed["queriedAt"]
    if type(queried_at) is not int or queried_at < 0:
        raise HarnessProtocolError("CC Switch queriedAt is invalid")
    available = parsed["available"]
    if type(available) is not bool:
        raise HarnessProtocolError("CC Switch available must be boolean")
    raw_status = _text(parsed["status"], "CC Switch quota status", max_bytes=100)

    if parsed["error"] is not None or raw_status == "error":
        status = ProviderCapacityStatus.ERROR
    elif raw_status == "unsupported":
        status = ProviderCapacityStatus.UNSUPPORTED
    elif raw_status == "not_available" or not available:
        status = ProviderCapacityStatus.NOT_AVAILABLE
    elif raw_status == "available" and available:
        status = ProviderCapacityStatus.AVAILABLE
    else:
        status = ProviderCapacityStatus.UNKNOWN

    return ProviderCapacitySnapshot(
        source="cc-switch-cli:v5.11.x",
        observed_at_ms=queried_at,
        principal_ref=principal_ref,
        source_node_ref=source_node_ref,
        app=app,
        provider_id=provider_id,
        provider_name=provider_name,
        account_ref=account_ref,
        status=status,
        windows=windows,
    )


__all__ = [
    "CapacityAdmissionDecision",
    "CapacityAdmissionGuard",
    "CapacityAdmissionStanding",
    "ProviderCapacitySnapshot",
    "ProviderCapacityStatus",
    "ProviderCapacityWindow",
    "SnapshotCapacityAdmissionGuard",
    "snapshot_from_cc_switch_quota",
]
