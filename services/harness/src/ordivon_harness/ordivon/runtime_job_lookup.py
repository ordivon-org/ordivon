"""Runtime Job recovery lookup; one bounded read-only Port adapter.

This is an external Runtime I/O operation, never the authority to reconcile an
ambiguous Job by reissuing it. The returned matching identities remain merely
Runtime observations until Harness can verify the original committed Intent.
"""
from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from ..runtime_port import HarnessRuntimeClient, HarnessRuntimeClientError


def _find_runtime_jobs_by_client_request(
    runtime: HarnessRuntimeClient,
    client_request_id: str,
    workspace_id: str,
    *,
    max_pages: int = 100,
) -> list[dict[str, JsonValue]]:
    if not client_request_id or client_request_id != client_request_id.strip():
        raise ValueError("Runtime clientRequestId is required and trimmed")
    if not workspace_id or workspace_id != workspace_id.strip():
        raise ValueError("Runtime Workspace identity is required and trimmed")
    if max_pages < 1:
        raise ValueError("Runtime Job lookup page limit must be positive")
    cursor: dict[str, JsonValue] | None = None
    seen_cursors: set[str] = set()
    matches: list[dict[str, JsonValue]] = []
    for _ in range(max_pages):
        arguments: dict[str, JsonValue] = {
            "limit": 100,
            "clientRequestId": client_request_id,
            "workspaceId": workspace_id,
        }
        if cursor is not None:
            arguments["cursor"] = cursor
        page = runtime.call_tool("task.list", arguments)
        validate_json_value(page)
        jobs = page.get("jobs")
        if not isinstance(jobs, list):
            raise HarnessRuntimeClientError("task.list omitted jobs")
        for item in jobs:
            if not isinstance(item, dict):
                raise HarnessRuntimeClientError("task.list returned a non-object Job")
            job = dict(item)
            if job.get("clientRequestId") != client_request_id:
                raise HarnessRuntimeClientError(
                    "filtered task.list returned another clientRequestId"
                )
            if job.get("workspaceId") != workspace_id:
                raise HarnessRuntimeClientError(
                    "filtered task.list returned a Job from another Workspace"
                )
            matches.append(job)
        next_cursor = page.get("nextCursor")
        if next_cursor is None:
            return matches
        if not isinstance(next_cursor, dict):
            raise HarnessRuntimeClientError("task.list returned an invalid cursor")
        # RuntimeJobListCursor is an exact Rust wire type:
        # {createdAtMs: u64, jobId: String} with denied unknown fields.
        # In Python bool is an int subclass; type() is required to avoid
        # admitting a forged boolean timestamp during lost-response recovery.
        timestamp = next_cursor.get("createdAtMs")
        job_id = next_cursor.get("jobId")
        if (
            set(next_cursor) != {"createdAtMs", "jobId"}
            or type(timestamp) is not int
            or not 0 <= timestamp <= 2**64 - 1
            or not isinstance(job_id, str)
            or not job_id
            or job_id != job_id.strip()
        ):
            raise HarnessRuntimeClientError("task.list cursor fields are invalid")
        typed: dict[str, JsonValue] = {"createdAtMs": timestamp, "jobId": job_id}
        digest = canonical_digest(typed)
        if digest in seen_cursors:
            raise HarnessRuntimeClientError("task.list repeated a pagination cursor")
        seen_cursors.add(digest)
        cursor = typed
    raise HarnessRuntimeClientError("task.list pagination exceeded the Harness bound")
