"""Durable Run budget, stop standing and result contracts.

This module owns the typed Run representation, not the sequential cognition,
provider and tool orchestration. Keep the existing loop import facade while
real consumers transition to the natural contract boundary.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from anc_canonical import JsonValue

from ..agent_tool_observation import HarnessToolObservation
from .events import HarnessTrace
from .model import AgentRunConclusion


class RunStopCode(str, Enum):
    CANDIDATE_COMPLETED = "candidate_completed"
    NEEDS_INPUT = "needs_input"
    NO_PROGRESS = "no_progress"
    BUDGET_EXHAUSTED = "budget_exhausted"
    CANCELLED = "cancelled"
    CANCEL_UNKNOWN = "cancel_unknown"
    PROVIDER_FAILED = "provider_failed"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_TRANSPORT_FAILED = "provider_transport_failed"
    PROVIDER_REJECTED = "provider_rejected"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_STATE_UNKNOWN = "provider_state_unknown"
    INVALID_TOOL_CALL = "invalid_tool_call"
    RUNTIME_UNKNOWN = "runtime_unknown"
    INVALID_MODEL_OUTPUT = "invalid_model_output"
    HARNESS_FAILED = "harness_failed"


@dataclass(frozen=True, slots=True)
class RunBudget:
    max_model_calls: int
    max_tool_calls: int
    max_observation_bytes: int
    max_wall_time_ms: int
    max_total_tokens: int = 131_072
    max_model_retries: int = 2
    max_tool_corrections: int = 3
    max_conclusion_corrections: int = 3
    max_observation_only_turns: int = 6
    max_no_progress_turns: int = 3
    max_model_observation_bytes: int = 32_768

    def __post_init__(self) -> None:
        if (
            min(
                self.max_model_calls,
                self.max_observation_bytes,
                self.max_wall_time_ms,
                self.max_total_tokens,
            )
            < 1
        ):
            raise ValueError("Ordivon Harness primary budgets must be positive")
        if self.max_tool_calls < 0:
            raise ValueError("Ordivon Harness Tool Call budget must be non-negative")
        if (
            self.max_model_retries < 0
            or self.max_tool_corrections < 0
            or self.max_conclusion_corrections < 0
            or self.max_observation_only_turns < 0
            or self.max_no_progress_turns < 0
        ):
            raise ValueError("Ordivon Harness secondary budgets must be non-negative")
        if self.max_model_observation_bytes < 1:
            raise ValueError("Ordivon Harness Observation message bound must be positive")

    def to_contract_dict(self) -> dict[str, JsonValue]:
        """Return the complete durable budget projection for a new Run Contract."""
        return {
            "maxModelCalls": self.max_model_calls,
            "maxToolCalls": self.max_tool_calls,
            "maxObservationBytes": self.max_observation_bytes,
            "maxWallTimeMs": self.max_wall_time_ms,
            "maxTotalTokens": self.max_total_tokens,
            "maxModelRetries": self.max_model_retries,
            "maxToolCorrections": self.max_tool_corrections,
            "maxConclusionCorrections": self.max_conclusion_corrections,
            "maxObservationOnlyTurns": self.max_observation_only_turns,
            "maxNoProgressTurns": self.max_no_progress_turns,
            "maxModelObservationBytes": self.max_model_observation_bytes,
        }

    @classmethod
    def from_contract_dict(cls, contract_budget: Mapping[str, JsonValue]) -> RunBudget:
        """Materialize schema-v1 Contract budget authority for execution.

        Early caller-neutral Contracts may omit fields that predate the complete
        budget projection. Missing fields use the historical Harness defaults;
        every field that is present remains exact authority and unknown fields
        fail closed through ``require_contract_match``.
        """
        defaults = cls(
            max_model_calls=8,
            max_tool_calls=16,
            max_observation_bytes=1_048_576,
            max_wall_time_ms=600_000,
            max_total_tokens=131_072,
            max_model_retries=2,
            max_tool_corrections=3,
            max_conclusion_corrections=3,
            max_observation_only_turns=6,
            max_no_progress_turns=3,
            max_model_observation_bytes=32_768,
        )
        names = {
            "maxModelCalls": "max_model_calls",
            "maxToolCalls": "max_tool_calls",
            "maxObservationBytes": "max_observation_bytes",
            "maxWallTimeMs": "max_wall_time_ms",
            "maxTotalTokens": "max_total_tokens",
            "maxModelRetries": "max_model_retries",
            "maxToolCorrections": "max_tool_corrections",
            "maxConclusionCorrections": "max_conclusion_corrections",
            "maxObservationOnlyTurns": "max_observation_only_turns",
            "maxNoProgressTurns": "max_no_progress_turns",
            "maxModelObservationBytes": "max_model_observation_bytes",
        }
        unknown = set(contract_budget) - set(names)
        if unknown:
            raise ValueError(
                "Harness Run Contract budget has unsupported fields: " + ", ".join(sorted(unknown))
            )
        values = {name: getattr(defaults, name) for name in names.values()}
        for field, value in contract_budget.items():
            if type(value) is not int:
                raise ValueError(f"Harness Run Contract budget {field} must be an integer")
            values[names[field]] = value
        materialized = cls(**values)
        materialized.require_contract_match(contract_budget)
        return materialized

    def require_contract_match(self, contract_budget: Mapping[str, JsonValue]) -> None:
        """Require every budget bound claimed by a Contract to match execution.

        Early schema-v1 independent Contracts bound only a subset of RunBudget.
        Missing known fields therefore retain their historical unbound/default
        meaning. A claimed known field is authoritative and must match exactly;
        an unknown field cannot be silently ignored by an executing Runner.
        """
        execution = self.to_contract_dict()
        unknown = set(contract_budget) - set(execution)
        if unknown:
            raise ValueError(
                "Standalone Runner Contract budget has unsupported fields: "
                + ", ".join(sorted(unknown))
            )
        for field, claimed in contract_budget.items():
            if type(claimed) is not int:
                raise ValueError(f"Standalone Runner Contract budget {field} must be an integer")
            if claimed != execution[field]:
                raise ValueError(f"Standalone Runner budget differs at {field}")

    def observation_gate_reason(
        self, *, no_progress_turns: int, observation_only_turns: int
    ) -> str | None:
        """Read-only soft observation policy; actual Tool admission remains in the Loop."""
        if self.max_no_progress_turns > 0 and no_progress_turns >= self.max_no_progress_turns:
            return (
                "external observation gate closed after "
                f"{no_progress_turns} consecutive turns without a mutation, "
                "check, materially new bounded observation, or conclusion"
            )
        if (
            self.max_observation_only_turns > 0
            and observation_only_turns >= self.max_observation_only_turns
        ):
            return (
                "external observation gate closed after "
                f"{observation_only_turns} consecutive observation-only turns "
                "without a mutation, check, or conclusion"
            )
        return None

    def remaining(
        self,
        *,
        model_calls: int,
        tool_calls: int,
        observation_bytes: int,
        elapsed_ms: int,
        total_tokens: int = 0,
        model_retries: int = 0,
        tool_corrections: int = 0,
        conclusion_corrections: int = 0,
        observation_only_turns: int = 0,
        no_progress_turns: int = 0,
    ) -> dict[str, JsonValue]:
        return {
            "modelCalls": max(0, self.max_model_calls - model_calls),
            "toolCalls": max(0, self.max_tool_calls - tool_calls),
            "observationBytes": max(0, self.max_observation_bytes - observation_bytes),
            "wallTimeMs": max(0, self.max_wall_time_ms - elapsed_ms),
            "totalTokens": max(0, self.max_total_tokens - total_tokens),
            "modelRetries": max(0, self.max_model_retries - model_retries),
            "toolCorrections": max(0, self.max_tool_corrections - tool_corrections),
            "conclusionCorrections": max(
                0, self.max_conclusion_corrections - conclusion_corrections
            ),
            "observationOnlyTurns": max(
                0, self.max_observation_only_turns - observation_only_turns
            ),
            "noProgressTurns": max(0, self.max_no_progress_turns - no_progress_turns),
        }


@dataclass(frozen=True, slots=True)
class AgentLoopResult:
    harness_run_id: str
    stop_code: RunStopCode
    trace: HarnessTrace
    conclusion: AgentRunConclusion | None
    messages: tuple[dict[str, JsonValue], ...]
    observations: tuple[HarnessToolObservation, ...]
    model_calls: int
    tool_calls: int
    observation_bytes: int
    usage: dict[str, JsonValue]

    @property
    def candidate_completed(self) -> bool:
        return self.stop_code is RunStopCode.CANDIDATE_COMPLETED
