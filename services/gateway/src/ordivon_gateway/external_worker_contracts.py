from __future__ import annotations

from dataclasses import dataclass


class WorkerError(RuntimeError):
    pass


class WorkerAuthError(WorkerError):
    pass


class WorkerConflict(WorkerError):
    pass


@dataclass(frozen=True)
class ExternalOperation:
    operation_id: str
    capability: str
    request_id: str
    state: str
    terminal: bool
    desired_state: str
    exit_code: int | None
    artifact_ids: list[str]
    # Existing durable admitted parcel: owner-observed Workspace or UNKNOWN.
    workspace_id: str | None = None
