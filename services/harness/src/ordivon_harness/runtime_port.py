from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from anc_canonical import JsonValue


@runtime_checkable
class HarnessRuntimeClient(Protocol):
    def call_tool(
        self,
        name: str,
        arguments: dict[str, JsonValue],
    ) -> dict[str, JsonValue]: ...


class HarnessRuntimeClientError(RuntimeError):
    """Transport or protocol failure with unknown physical Runtime outcome."""


@dataclass(frozen=True, slots=True)
class HarnessRuntimeErrorDetail:
    code: str
    message: str
    commit_state: str
    retryable: bool = False
    field: str | None = None

    def __post_init__(self) -> None:
        if not self.code or self.code != self.code.strip():
            raise ValueError("Runtime error code must be non-empty and trimmed")
        if not self.message or self.message != self.message.strip():
            raise ValueError("Runtime error message must be non-empty and trimmed")
        if self.commit_state not in {
            "not_started",
            "not_committed",
            "committed",
            "unknown",
        }:
            raise ValueError("Runtime commit state is unsupported")
        if type(self.retryable) is not bool:
            raise ValueError("Runtime retryable must be boolean")
        if self.field is not None and (not self.field or self.field != self.field.strip()):
            raise ValueError("Runtime error field must be trimmed")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "code": self.code,
            "message": self.message,
            "commitState": self.commit_state,
            "retryable": self.retryable,
            "field": self.field,
        }


class HarnessRuntimeToolRejected(HarnessRuntimeClientError):
    def __init__(
        self,
        operation: str,
        detail: HarnessRuntimeErrorDetail,
    ) -> None:
        super().__init__(f"{operation} rejected [{detail.code}]: {detail.message}")
        self.operation = operation
        self.detail = detail
