"""API-specific Provider capacity evidence and pre-dispatch admission.

API capacity is not subscription entitlement. It can be constrained independently by:
- request/token rate buckets,
- prepaid credit exhaustion,
- organization/project usage limits,
- organization/project spend limits.

This module does not choose another route, retry a request, buy credits, or mutate limits.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from anc_canonical import JsonValue, canonical_digest

from ..protocol import HarnessProtocolError
from .capacity import (
    CapacityAdmissionDecision,
    CapacityAdmissionStanding,
    ProviderCapacityStatus,
    _text,
)
from .model import AgentTurnRequest


class ApiRateLimitKind(str, Enum):
    REQUESTS = "requests"
    TOKENS = "tokens"
    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"


class ApiSpendStanding(str, Enum):
    AVAILABLE = "available"
    EXHAUSTED = "exhausted"
    UNKNOWN = "unknown"


class ApiCapacityFailureKind(str, Enum):
    TRANSIENT_RATE_LIMIT = "transient_rate_limit"
    CREDIT_EXHAUSTED = "credit_exhausted"
    USAGE_LIMIT_EXCEEDED = "usage_limit_exceeded"
    SPEND_LIMIT_EXCEEDED = "spend_limit_exceeded"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ProviderApiRateLimit:
    kind: ApiRateLimitKind
    limit: int
    remaining: int
    resets_at_ms: int | None = None

    def __post_init__(self) -> None:
        if type(self.limit) is not int or self.limit < 1:
            raise HarnessProtocolError("API rate limit must be a positive integer")
        if type(self.remaining) is not int or not 0 <= self.remaining <= self.limit:
            raise HarnessProtocolError("API rate remaining must be an integer in [0, limit]")
        if self.resets_at_ms is not None and (
            type(self.resets_at_ms) is not int or self.resets_at_ms < 0
        ):
            raise HarnessProtocolError(
                "API rate reset time must be a non-negative millisecond timestamp"
            )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "kind": self.kind.value,
            "limit": self.limit,
            "remaining": self.remaining,
            "resetsAtMs": self.resets_at_ms,
        }


@dataclass(frozen=True, slots=True)
class ProviderApiSpendCapacity:
    standing: ApiSpendStanding
    reason_code: str | None = None
    remaining_microusd: int | None = None
    resets_at_ms: int | None = None

    def __post_init__(self) -> None:
        if self.reason_code is not None:
            _text(self.reason_code, "API spend reason code", max_bytes=200)
        if self.remaining_microusd is not None and (
            type(self.remaining_microusd) is not int or self.remaining_microusd < 0
        ):
            raise HarnessProtocolError(
                "API remaining spend must be a non-negative integer of micro-USD"
            )
        if self.resets_at_ms is not None and (
            type(self.resets_at_ms) is not int or self.resets_at_ms < 0
        ):
            raise HarnessProtocolError(
                "API spend reset time must be a non-negative millisecond timestamp"
            )
        if self.standing is ApiSpendStanding.EXHAUSTED and self.reason_code is None:
            raise HarnessProtocolError("exhausted API spend capacity requires a reason code")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "standing": self.standing.value,
            "reasonCode": self.reason_code,
            "remainingMicroUsd": self.remaining_microusd,
            "resetsAtMs": self.resets_at_ms,
        }


@dataclass(frozen=True, slots=True)
class ProviderApiCapacitySnapshot:
    """Sanitized API capacity evidence for one Provider principal/model route."""

    source: str
    observed_at_ms: int
    principal_ref: str
    source_node_ref: str
    provider_id: str
    model_id: str | None
    status: ProviderCapacityStatus
    rate_limits: tuple[ProviderApiRateLimit, ...] = ()
    spend: ProviderApiSpendCapacity | None = None
    account_ref: str | None = None

    def __post_init__(self) -> None:
        _text(self.source, "API capacity source", max_bytes=200)
        if type(self.observed_at_ms) is not int or self.observed_at_ms < 0:
            raise HarnessProtocolError(
                "API capacity observed time must be a non-negative millisecond timestamp"
            )
        _text(self.principal_ref, "API capacity principal reference", max_bytes=300)
        _text(self.source_node_ref, "API capacity source node reference", max_bytes=300)
        _text(self.provider_id, "API capacity Provider identity", max_bytes=300)
        if self.model_id is not None:
            _text(self.model_id, "API capacity model identity", max_bytes=300)
        if self.account_ref is not None:
            _text(self.account_ref, "API capacity account reference", max_bytes=300)
        kinds = [item.kind for item in self.rate_limits]
        if len(kinds) != len(set(kinds)):
            raise HarnessProtocolError("API rate-limit kinds must be unique")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.provider-api-capacity-snapshot",
            "source": self.source,
            "observedAtMs": self.observed_at_ms,
            "principalRef": self.principal_ref,
            "sourceNodeRef": self.source_node_ref,
            "providerId": self.provider_id,
            "modelId": self.model_id,
            "accountRef": self.account_ref,
            "status": self.status.value,
            "rateLimits": [item.to_dict() for item in self.rate_limits],
            "spend": None if self.spend is None else self.spend.to_dict(),
        }

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())


@dataclass(slots=True)
class ApiCapacityAdmissionGuard:
    """Fail closed on stale/missing required API capacity before Provider dispatch.

    Rate evidence can protect one physical dispatch using exact request/token reserves.
    Spend evidence is authoritative only for the external status it observed; this guard
    does not estimate model price or reserve money without a separate pricing authority.
    """

    snapshot: ProviderApiCapacitySnapshot
    max_staleness_ms: int
    expected_principal_ref: str
    required_rate_kinds: tuple[ApiRateLimitKind, ...] = ()
    reserve_requests: int = 0
    reserve_tokens: int = 0
    require_spend_capacity: bool = False
    clock_ms: Callable[[], int] = lambda: time.time_ns() // 1_000_000

    def __post_init__(self) -> None:
        if type(self.max_staleness_ms) is not int or self.max_staleness_ms < 1:
            raise ValueError("API capacity max staleness must be positive")
        _text(self.expected_principal_ref, "expected API capacity principal", max_bytes=300)
        if len(self.required_rate_kinds) != len(set(self.required_rate_kinds)):
            raise ValueError("required API rate kinds must be unique")
        if type(self.reserve_requests) is not int or self.reserve_requests < 0:
            raise ValueError("API request reserve must be non-negative")
        if type(self.reserve_tokens) is not int or self.reserve_tokens < 0:
            raise ValueError("API token reserve must be non-negative")
        if type(self.require_spend_capacity) is not bool:
            raise ValueError("require_spend_capacity must be boolean")
        if not callable(self.clock_ms):
            raise TypeError("API capacity clock must be callable")

    def check(
        self,
        request: AgentTurnRequest,
        *,
        request_token_upper_bound: int | None,
    ) -> CapacityAdmissionDecision:
        del request
        digest = self.snapshot.digest
        if self.snapshot.principal_ref != self.expected_principal_ref:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "API capacity observation principal differs from the frozen Provider principal",
            )
        age_ms = self.clock_ms() - self.snapshot.observed_at_ms
        if age_ms < 0 or age_ms > self.max_staleness_ms:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "API capacity observation is stale or has a future observation time",
            )
        if self.snapshot.status is not ProviderCapacityStatus.AVAILABLE:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                f"API capacity source status is {self.snapshot.status.value}; UNKNOWN is not zero",
            )

        spend = self.snapshot.spend
        if spend is not None and spend.standing is ApiSpendStanding.EXHAUSTED:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.HOLD,
                digest,
                f"API spend/credit capacity is exhausted: {spend.reason_code}",
            )
        if self.require_spend_capacity and (
            spend is None or spend.standing is ApiSpendStanding.UNKNOWN
        ):
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "required API spend/credit capacity is not observable",
            )

        observed = {item.kind: item for item in self.snapshot.rate_limits}
        for kind in self.required_rate_kinds:
            if kind not in observed:
                return CapacityAdmissionDecision(
                    CapacityAdmissionStanding.UNKNOWN,
                    digest,
                    f"required API rate capacity is not observable: {kind.value}",
                )

        requests = observed.get(ApiRateLimitKind.REQUESTS)
        if requests is not None and requests.remaining <= self.reserve_requests:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.HOLD,
                digest,
                (
                    "API request-rate capacity is at or below reserve: "
                    f"{requests.remaining}<={self.reserve_requests}"
                ),
            )

        component_rate_kinds = {
            ApiRateLimitKind.INPUT_TOKENS,
            ApiRateLimitKind.OUTPUT_TOKENS,
        }
        required_component_kinds = [
            kind for kind in self.required_rate_kinds if kind in component_rate_kinds
        ]
        if required_component_kinds:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                (
                    "Harness exposes only a total request token upper bound; component "
                    "input/output rate admission remains unproven for: "
                    + ",".join(kind.value for kind in required_component_kinds)
                ),
            )

        total_tokens = observed.get(ApiRateLimitKind.TOKENS)
        if total_tokens is not None:
            if request_token_upper_bound is None:
                if ApiRateLimitKind.TOKENS in self.required_rate_kinds:
                    return CapacityAdmissionDecision(
                        CapacityAdmissionStanding.UNKNOWN,
                        digest,
                        "API token-rate admission requires an exact request token upper bound",
                    )
            elif total_tokens.remaining - self.reserve_tokens < request_token_upper_bound:
                return CapacityAdmissionDecision(
                    CapacityAdmissionStanding.HOLD,
                    digest,
                    (
                        "API total-token capacity cannot fit the request upper bound "
                        f"after reserve: {total_tokens.remaining}-{self.reserve_tokens}"
                        f"<{request_token_upper_bound}"
                    ),
                )

        if not self.snapshot.rate_limits and spend is None:
            return CapacityAdmissionDecision(
                CapacityAdmissionStanding.UNKNOWN,
                digest,
                "API capacity source is available but exposed no rate or spend facet",
            )
        return CapacityAdmissionDecision(
            CapacityAdmissionStanding.ADMIT,
            digest,
            "API rate and spend capacity admit one dispatch on the frozen route",
        )


_OPENAI_TRANSIENT_RATE_CODES = frozenset({"rate_limit_exceeded"})
_OPENAI_CREDIT_CODES = frozenset({"credit_balance_exhausted"})
_OPENAI_USAGE_CODES = frozenset({"organization_usage_limit_exceeded"})
_OPENAI_SPEND_CODES = frozenset(
    {
        "organization_spend_limit_exceeded",
        "project_spend_limit_exceeded",
    }
)


def classify_openai_api_capacity_error(error_code: str | None) -> ApiCapacityFailureKind:
    """Classify current documented OpenAI API capacity codes without retrying them."""

    if error_code is None:
        return ApiCapacityFailureKind.UNKNOWN
    _text(error_code, "OpenAI API error code", max_bytes=200)
    if error_code in _OPENAI_TRANSIENT_RATE_CODES:
        return ApiCapacityFailureKind.TRANSIENT_RATE_LIMIT
    if error_code in _OPENAI_CREDIT_CODES:
        return ApiCapacityFailureKind.CREDIT_EXHAUSTED
    if error_code in _OPENAI_USAGE_CODES:
        return ApiCapacityFailureKind.USAGE_LIMIT_EXCEEDED
    if error_code in _OPENAI_SPEND_CODES:
        return ApiCapacityFailureKind.SPEND_LIMIT_EXCEEDED
    return ApiCapacityFailureKind.UNKNOWN


__all__ = [
    "ApiCapacityAdmissionGuard",
    "ApiCapacityFailureKind",
    "ApiRateLimitKind",
    "ApiSpendStanding",
    "ProviderApiCapacitySnapshot",
    "ProviderApiRateLimit",
    "ProviderApiSpendCapacity",
    "classify_openai_api_capacity_error",
]
