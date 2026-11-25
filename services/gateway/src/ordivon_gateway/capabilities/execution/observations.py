from __future__ import annotations

from typing import Any

from ...contracts import (
    ArtifactChunk,
    CapabilityRoute,
    ExecutionObservation,
    ExecutionResolution,
)
from ...logic.execution_refs import (
    GatewayError,
    parse_execution_ref,
    validate_artifact_cursor,
    validate_observation_wait,
)
from ...logic.execution_refs import format_execution_ref as _execution_ref
from ...logic.owner_protocol import (
    OwnerToolCaller,
    _owner_optional_disposition,
    _owner_receipt_state,
    _required_bool,
    _required_str,
)


class ExecutionObservationMethods:
    """Gateway owner delegation; authoritative Job and Artifact data stay upstream."""

    _caller: OwnerToolCaller
    _routes: dict[str, CapabilityRoute]

    def __init__(self, caller: OwnerToolCaller, routes: dict[str, CapabilityRoute]) -> None:
        self._caller = caller
        self._routes = routes

    async def execution_resolve(self, *, capability: str, request_id: str) -> ExecutionResolution:
        if not request_id:
            raise GatewayError("requestId is required")
        route = self._routes.get(capability)
        if route is None:
            raise GatewayError(f"unknown capability: {capability}")
        if route.category != "execution" or route.owner_tool != "workspace.exec":
            raise GatewayError(f"capability is not executable: {capability}")

        page = await self._caller.call_tool(
            route.owner_id,
            "job.list",
            {
                "limit": 2,
                "clientRequestId": request_id,
            },
        )
        jobs = page.get("jobs")
        if not isinstance(jobs, list) or any(not isinstance(item, dict) for item in jobs):
            raise GatewayError("Runtime job.list omitted jobs")
        for job in jobs:
            if job.get("clientRequestId") != request_id:
                raise GatewayError("Runtime job.list returned another clientRequestId")
        next_cursor = page.get("nextCursor")
        ambiguous = len(jobs) > 1 or next_cursor is not None
        if ambiguous:
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id=route.owner_id,
                resolution="ambiguous",
            )
        if not jobs:
            return ExecutionResolution(
                request_id=request_id,
                capability=capability,
                owner_id=route.owner_id,
                resolution="absent",
            )
        native_id = _required_str(jobs[0], "jobId")
        # Do not invent a workspace from the caller's route/grant. The
        # Runtime list row is the physical identity witness for this lookup.
        workspace_id = _required_str(jobs[0], "workspaceId")
        return ExecutionResolution(
            request_id=request_id,
            capability=capability,
            owner_id=route.owner_id,
            resolution="found",
            operation_ref=_execution_ref(route.owner_id, native_id),
            native_id=native_id,
            workspace_id=workspace_id,
        )

    async def execution_get(
        self, operation_ref: str, *, event_limit: int = 10, wait_ms: int = 0
    ) -> ExecutionObservation:
        owner_id, native_id = parse_execution_ref(operation_ref)
        # eventLimit is retained on the northbound surface for connector compatibility.
        # Runtime's execution observation authority is job.observe; Gateway does not
        # project the job.get event timeline, so forwarding eventLimit would add no truth.
        _ = event_limit
        validate_observation_wait(wait_ms)
        result = await self._caller.call_tool(
            owner_id,
            "job.observe",
            {
                "schemaVersion": 1,
                "jobId": native_id,
                "waitMs": wait_ms,
                "waitUntil": "change_or_terminal",
                "stdoutTailBytes": 0,
                "stderrTailBytes": 0,
            },
        )
        observed_native_id = _required_str(result, "jobId")
        if observed_native_id != native_id:
            raise GatewayError("Runtime job.observe returned mismatched job identity")

        def artifact_ids(payload: dict[str, Any]) -> tuple[list[str], bool]:
            # A filtered invalid Owner row is not proof that zero Artifacts
            # exist. Observe only explicitly list-valued, well-formed inventory.
            raw = payload.get("artifacts")
            if not isinstance(raw, list):
                return [], False
            values: list[str] = []
            qualified = True
            for item in raw:
                artifact_id = item.get("artifactId") if isinstance(item, dict) else None
                if isinstance(artifact_id, str) and artifact_id.strip():
                    values.append(artifact_id)
                else:
                    qualified = False
            return values, qualified

        def identities_complete(
            ids: list[str], expected_count: int, inventory_qualified: bool
        ) -> bool:
            # Every raw row must be a valid identity before an Owner count
            # can establish complete coverage; filtering is lossy.
            return (
                inventory_qualified
                and len(ids) == expected_count
                and len(set(ids)) == expected_count
            )

        artifacts, inventory_qualified = artifact_ids(result)
        artifacts_available = (
            bool(result["artifactsAvailable"])
            if isinstance(result.get("artifactsAvailable"), bool)
            else None
        )
        artifact_count = len(artifacts)
        artifact_projection_complete: bool | None = None

        if _required_bool(result, "executionTerminal") or artifacts_available:
            inspection = await self._caller.call_tool(
                owner_id,
                "job.get",
                {
                    "schemaVersion": 1,
                    "jobId": native_id,
                    "eventLimit": 1,
                },
            )
            job = inspection.get("job")
            if not isinstance(job, dict) or job.get("jobId") != native_id:
                raise GatewayError("Runtime job.get returned mismatched job identity")
            summary = inspection.get("artifacts")
            # An Owner summary is evidence of completeness only when its
            # count is an actual nonnegative JSON integer. bool is NOT a
            # count, and absent/invalid counts cannot establish "complete".
            raw_count = summary.get("count") if isinstance(summary, dict) else None
            summary_count = raw_count if type(raw_count) is int and raw_count >= 0 else None
            if summary_count is not None:
                artifact_count = summary_count
                if not identities_complete(artifacts, summary_count, inventory_qualified):
                    refreshed = await self._caller.call_tool(
                        owner_id,
                        "job.observe",
                        {
                            "schemaVersion": 1,
                            "jobId": native_id,
                            "waitMs": 0,
                            "waitUntil": "change_or_terminal",
                            "stdoutTailBytes": 0,
                            "stderrTailBytes": 0,
                        },
                    )
                    if _required_str(refreshed, "jobId") != native_id:
                        raise GatewayError(
                            "Runtime job.observe refresh returned mismatched job identity"
                        )
                    artifacts, inventory_qualified = artifact_ids(refreshed)
                    artifacts_available = (
                        bool(refreshed["artifactsAvailable"])
                        if isinstance(refreshed.get("artifactsAvailable"), bool)
                        else artifacts_available
                    )
                artifact_projection_complete = identities_complete(
                    artifacts, summary_count, inventory_qualified
                )
            # Without the Owner's qualified total, any completeness claim is
            # UNKNOWN even if the projected list contains some Artifact IDs.

        raw_exit_code = result.get("exitCode")
        if raw_exit_code is not None and type(raw_exit_code) is not int:
            raise GatewayError("Runtime job.observe returned non-integer exitCode")

        return ExecutionObservation(
            operation_ref=operation_ref,
            capability=(
                {
                    "runtime.windows": "execution.windows",
                    "runtime.harness": "execution.harness",
                }.get(owner_id, "execution.linux")
            ),
            owner_id=owner_id,
            native_id=observed_native_id,
            state=_owner_receipt_state(result),
            terminal=_required_bool(result, "executionTerminal"),
            delivery_disposition=_owner_optional_disposition(result, "deliveryDisposition"),
            execution_disposition=_owner_optional_disposition(result, "executionDisposition"),
            exit_code=raw_exit_code,
            recovery_required=(
                bool(result["recoveryRequired"])
                if isinstance(result.get("recoveryRequired"), bool)
                else None
            ),
            artifacts_available=artifacts_available,
            artifact_count=artifact_count,
            artifact_ids=artifacts,
            artifact_projection_complete=artifact_projection_complete,
        )

    async def artifact_read(
        self,
        operation_ref: str,
        artifact_id: str,
        *,
        offset: int = 0,
        max_bytes: int = 1_048_576,
    ) -> ArtifactChunk:
        owner_id, native_id = parse_execution_ref(operation_ref)
        validate_artifact_cursor(offset, max_bytes)
        result = await self._caller.call_tool(
            owner_id,
            "artifact.read",
            {
                "schemaVersion": 1,
                "jobId": native_id,
                "artifactId": artifact_id,
                "offset": offset,
                "maxBytes": max_bytes,
            },
        )
        if result.get("jobId") != native_id or result.get("artifactId") != artifact_id:
            raise GatewayError("artifact owner returned mismatched identity")
        # The natural Owner's range and EOF report is the Agent's cursor,
        # not a free-form object for Python truthiness/string coercion.
        # "false" as a string must NEVER be interpreted as EOF=True.
        observed_offset = result.get("offset")
        next_offset = result.get("nextOffset")
        if (
            type(observed_offset) is not int
            or observed_offset != offset
            or type(next_offset) is not int
            or not offset <= next_offset <= offset + max_bytes
        ):
            raise GatewayError("artifact owner returned an invalid range/cursor")
        eof = _required_bool(result, "eof")
        # A nonterminal zero-progress range cannot be consumed by any Agent:
        # the Owner is not proof of EOF and repeating this cursor would loop.
        # True EOF may legitimately return an empty final range.
        if not eof and next_offset == offset:
            raise GatewayError("artifact owner returned a non-progressing cursor before EOF")
        content = result.get("content")
        if not isinstance(content, str):
            raise GatewayError("artifact owner returned invalid content")
        # The cursor is measured in bytes, not Python code points. Refuse
        # a contradictory range even at EOF; otherwise an Agent may silently
        # skip bytes or consume overlapping content. Do not replace bad UTF-8.
        try:
            content_bytes = len(content.encode("utf-8"))
        except UnicodeEncodeError:
            raise GatewayError("artifact owner returned invalid UTF-8 content") from None
        if content_bytes != next_offset - observed_offset:
            raise GatewayError("artifact owner returned content inconsistent with byte cursor")
        return ArtifactChunk(
            operation_ref=operation_ref,
            owner_id=owner_id,
            native_id=native_id,
            artifact_id=artifact_id,
            offset=observed_offset,
            next_offset=next_offset,
            eof=eof,
            digest=_required_str(result, "digest"),
            content=content,
        )
