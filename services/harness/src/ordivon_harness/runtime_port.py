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


class HarnessWorkspaceAdmissionUnavailable(HarnessRuntimeClientError):
    """Workspace-bound Run has no current Runtime-owned HELD/issuer qualification.

    This is an infrastructure/authority uncertainty, never a model-correctable
    Tool argument error. Caller must not invoke Provider or new physical Effect.
    """


@runtime_checkable
class WorkspaceBoundEffectAdmission(Protocol):
    """Trusted issuer-backed consumer of the Runtime PG Workspace Claim.

    A caller-supplied RunRef or a local Boolean cannot authenticate HELD.
    Implementations MUST use the original claim key and the Runtime Owner
    qualified reserve/get and current-issuer evidence. Any missing/UNKNOWN,
    revoked, or identity-mismatched evidence raises the exception above.
    No long PostgreSQL transaction may span an Agent model Turn.

    This is a Port contract, not a new Store or a claim that Runtime has
    deployed the required native issuer/claim endpoint.
    """

    def require_turn_ready(
        self,
        *,
        run_ref: str,
        workspace_id: str,
        tool_grant_digest: str,
        turn_id: str | None = None,
    ) -> None: ...

    def require_effect_ready(
        self,
        *,
        run_ref: str,
        workspace_id: str,
        tool_grant_digest: str,
        runtime_operation: str,
        client_request_id: str,
    ) -> None: ...
