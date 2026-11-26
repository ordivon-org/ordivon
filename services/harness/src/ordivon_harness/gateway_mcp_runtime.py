"""Gateway Runtime adapter: submit/resolve/observe original remote MCP effects.

Gateway routes, Runtime performs physical execution; no extra state or
second issuer is created in this transport-facing capability.
"""

from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .agent_plugin import AgentPluginMcpComponent
from .gateway_execution_policy import (
    PluginGatewayExecutionGrant,
    is_original_effect_authority,
    require_gateway_workspace_effect,
)
from .gateway_mcp_wire import (
    _GATEWAY_CONCLUSIVE_EXECUTION_RESOLUTIONS,
    _gateway_delivery_disposition,
    _gateway_field,
    _required_text,
)
from .plugin_mcp import HarnessMcpClient
from .runtime_port import HarnessRuntimeClientError, WorkspaceBoundEffectAdmission


class GatewayMcpRuntimeAdapter:
    """Translate the Gateway public execution projection into the existing Runtime port.

    This adapter deliberately preserves Runtime as the physical execution owner. Gateway
    adds routing and a recovery lookup, while Harness retains durable intent/fence/receipt
    authority.
    """

    def __init__(
        self,
        component: AgentPluginMcpComponent,
        client: HarnessMcpClient,
        grant: PluginGatewayExecutionGrant,
        *,
        artifact_read_enabled: bool = False,
        workspace_admission: WorkspaceBoundEffectAdmission | None = None,
        require_workspace_admission: bool = False,
        run_ref: str | None = None,
        grant_digest: str | None = None,
    ) -> None:
        self.component = component
        self.client = client
        self._original_effect_client = client
        self.grant = grant
        # Only the caller's existing privacy consent + source-discovered
        # Gateway artifact.read enable text previews for the next model turn.
        self._artifact_read_enabled = artifact_read_enabled
        self._workspace_admission = workspace_admission
        self._workspace_admission_required = require_workspace_admission
        self._original_workspace_admission = workspace_admission
        self._original_workspace_admission_required = require_workspace_admission
        self._run_ref = run_ref
        self._grant_digest = grant_digest
        if workspace_admission is not None and (not run_ref or not grant_digest):
            raise ValueError("Gateway admission Port requires frozen Run and Tool Grant identities")
        self._operation_refs: dict[str, str] = {}
        self._operation_requests: dict[str, str] = {}
        # Local-only exact physical request fingerprint, never an authority
        # store. Original PG ToolIntent remains the durable identity source.
        self._operation_request_digests: dict[str, str] = {}

    def _verify_owner_job_identity(
        self,
        payload: dict[str, JsonValue],
        native_id: str,
        operation_ref: str,
    ) -> None:
        """One exact wire Job identity before ANY consumer binding or effect standing.

        The Gateway protocol owns the execution-ref representation. The
        Harness is its consumer: a valid-looking operationRef cannot claim
        another Runtime Job, execution capability or physical Owner. This
        proves source consistency, not authenticated Owner delivery.
        """
        owner = "runtime." + self.grant.capability.removeprefix("execution.")
        expected = f"ordivon-exec:v1:{owner}:{native_id}"
        if (
            payload.get("capability") != self.grant.capability
            or _gateway_field(payload, "owner_id", "ownerId") != owner
            or _gateway_field(payload, "operation_ref", "operationRef") != operation_ref
            or operation_ref != expected
        ):
            raise HarnessRuntimeClientError(
                "Gateway operation identity binding conflicts with capability, Owner, or Job reference"
            )

    def _retain_operation_binding(
        self, native_id: str, operation_ref: str, request_id: str
    ) -> None:
        """Fail closed on a contradictory Gateway receipt or recovery.

        The two existing ephemeral maps are the only local state. An accepted
        transition must preserve (nativeId, operationRef, clientRequestId)
        identity across late replies, retries, observation and cancellation.
        This is a local cache invariant, not a durable Gateway/Runtime proof.
        """
        previous_ref = self._operation_refs.get(native_id)
        previous_request = self._operation_requests.get(native_id)
        if (
            (previous_ref is not None and previous_ref != operation_ref)
            or (previous_request is not None and previous_request != request_id)
            or any(
                key != native_id and value == request_id
                for key, value in self._operation_requests.items()
            )
            or any(
                key != native_id and value == operation_ref
                for key, value in self._operation_refs.items()
            )
        ):
            raise HarnessRuntimeClientError(
                "Gateway execution identity binding conflicts with prior evidence"
            )
        # No writes may happen before all contradictions have been excluded.
        self._operation_refs[native_id] = operation_ref
        self._operation_requests[native_id] = request_id

    def _require_original_effect_source(self) -> None:
        # A frozen Factory is not sufficient if its effectful Adapter is
        # rebound after Bridge creation. Verify the original caller and Native
        # admission source before every external effect, including recovery.
        if not is_original_effect_authority(
            effect_client=self.client,
            original_effect_client=self._original_effect_client,
            admission_port=self._workspace_admission,
            original_admission_port=self._original_workspace_admission,
            admission_required=self._workspace_admission_required,
            original_admission_required=self._original_workspace_admission_required,
        ):
            raise HarnessRuntimeClientError(
                "Gateway Adapter effect client or Native admission drifted after Run birth"
            )

    def _call(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        self._require_original_effect_source()
        try:
            is_error, payload = self.client.call_tool(name, arguments)
        except Exception as exc:
            raise HarnessRuntimeClientError(
                f"Gateway MCP {name} transport/protocol failure: {type(exc).__name__}: {exc}"
            ) from exc
        if is_error:
            raise HarnessRuntimeClientError(f"Gateway MCP {name} returned an error result")
        validate_json_value(payload)
        return payload

    def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        self._require_original_effect_source()
        if name == "workspace.exec":
            return self._submit(arguments)
        if name == "task.list":
            return self._resolve(arguments)
        if name == "task.observe":
            return self._observe(arguments)
        raise HarnessRuntimeClientError(f"Gateway adapter does not expose Runtime operation {name}")

    def _submit(self, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        request_id = _required_text(arguments.get("clientRequestId"), "clientRequestId")
        execution = arguments.get("execution")
        if not isinstance(execution, dict):
            raise HarnessRuntimeClientError("Gateway execution lowering omitted execution")
        if execution.get("workspaceId") != self.grant.workspace_id:
            raise HarnessRuntimeClientError(
                "Gateway execution lowering changed workspace authority"
            )
        # The immutable Harness source Intent cannot be physically lowered
        # through a Gateway API that omits any of its materialized fields.
        # Reject unmatched future Runtime capabilities BEFORE owner dispatch
        # instead of silently weakening budget, prerequisites, context, steps.
        allowed_execution = {
            "workspaceId",
            "executable",
            "args",
            "cwdRelative",
            "foreignReferences",
            "env",
            "timeoutMs",
            "stdoutLimitBytes",
            "stderrLimitBytes",
        }
        unsupported = set(execution) - allowed_execution
        if unsupported:
            raise HarnessRuntimeClientError(
                "Gateway cannot faithfully lower frozen Runtime execution fields: "
                f"{sorted(unsupported)}"
            )
        foreign = execution.get("foreignReferences")
        if not isinstance(foreign, list) or any(not isinstance(item, dict) for item in foreign):
            raise HarnessRuntimeClientError(
                "Gateway execution lowering omitted authority references"
            )
        gateway_args: dict[str, JsonValue] = {
            "capability": self.grant.capability,
            "requestId": request_id,
            "workspaceId": self.grant.workspace_id,
            "executable": _required_text(execution.get("executable"), "executable"),
            "args": execution.get("args", []),
            "cwdRelative": execution.get("cwdRelative", "."),
            "authorityReferences": foreign,
        }
        if self.grant.context is not None:
            gateway_args["context"] = self.grant.context
        if "env" in execution:
            gateway_args["env"] = execution["env"]
        # Validate the materialized output ceilings BEFORE the final, already
        # qualified timeout projection -> physical Owner dispatch frame.
        # All output validation remains fail-closed, and this does not move
        # any physical effect ahead of Source Intent checks.
        for field in ("stdoutLimitBytes", "stderrLimitBytes"):
            if field in execution:
                value = execution[field]
                if type(value) is not int or not 1 <= value <= 2**64 - 1:
                    raise HarnessRuntimeClientError(
                        f"Gateway execution lowering has invalid {field} u64 bound"
                    )
                gateway_args[field] = value
        physical_request_digest = canonical_digest(arguments)
        # Replaying a *locally bound* physical request is an Owner readback,
        # never a second execution.submit. The verified Gateway may derive a
        # different native request key after the caller's ingress Principal
        # changes, even when the public clientRequestId stays identical.
        # Reject absent/conflicting original Job evidence before any new send.
        bound_jobs = [
            native_id
            for native_id, original_request in self._operation_requests.items()
            if original_request == request_id
        ]
        if bound_jobs:
            # A readback via Gateway execution.get can reconcile and in a
            # Legacy Runtime may dispatch an already Accepted native Job.
            # Preserve the same strict native effect gate on this path too.
            # The original exact Formal final-dispatch frame stays untouched.
            require_gateway_workspace_effect(
                workspace_admission=self._workspace_admission,
                admission_required=self._workspace_admission_required,
                run_ref=self._run_ref,
                workspace_id=self.grant.workspace_id,
                grant_digest=self._grant_digest,
                request_id=request_id,
                replay=True,
            )
            if len(bound_jobs) != 1:
                raise HarnessRuntimeClientError(
                    "Gateway existing request has ambiguous local physical Job bindings"
                )
            original_native_id = bound_jobs[0]
            # Replacing a repeated submit with readback must NOT discard
            # native idempotency-key conflict detection. Different executable,
            # args, timeout or Owner references under one request ID are not
            # the same physical effect, even if a prior Job exists.
            if self._operation_request_digests.get(original_native_id) != physical_request_digest:
                raise HarnessRuntimeClientError(
                    "Gateway bound original physical request bytes differ or cannot be proven"
                )
            recovered = self._resolve(
                {
                    "clientRequestId": request_id,
                    "workspaceId": self.grant.workspace_id,
                }
            )
            matches = recovered["jobs"]
            if len(matches) != 1 or matches[0]["jobId"] != original_native_id:
                raise HarnessRuntimeClientError(
                    "Gateway original bound Job is absent under current verified Principal"
                )
            operation_ref = _required_text(
                self._operation_refs.get(original_native_id), "existing operationRef"
            )
            return self._observe_operation(operation_ref, original_native_id, wait_ms=0)


        if "timeoutMs" in execution:
            gateway_args["timeoutMs"] = execution["timeoutMs"]

        # The final public Gateway boundary consumes the SAME trusted Runtime
        # Claim Port as the built-in Bridge. This checks lifetime/issuer only;
        # durable ToolIntent/Fence identity is separately verified upstream.
        require_gateway_workspace_effect(
            workspace_admission=self._workspace_admission,
            admission_required=self._workspace_admission_required,
            run_ref=self._run_ref,
            workspace_id=self.grant.workspace_id,
            grant_digest=self._grant_digest,
            request_id=request_id,
            replay=False,
        )
        receipt = self._call("execution.submit", gateway_args)
        operation_ref = _required_text(
            _gateway_field(receipt, "operation_ref", "operationRef"), "operationRef"
        )
        native_id = _required_text(_gateway_field(receipt, "native_id", "nativeId"), "nativeId")
        terminal = _gateway_field(receipt, "terminal", "terminal")
        if not isinstance(terminal, bool):
            raise HarnessRuntimeClientError("Gateway execution receipt omitted terminal")
        # Validate all source-owned fields before retaining a Job identity;
        # a forged Owner or malformed delivery must not poison recovery.
        self._verify_owner_job_identity(receipt, native_id, operation_ref)
        state = _required_text(receipt.get("state"), "state")
        delivery = _gateway_delivery_disposition(receipt, allow_missing=True)
        self._retain_operation_binding(native_id, operation_ref, request_id)
        self._operation_request_digests[native_id] = physical_request_digest
        if terminal:
            return self._observe_operation(operation_ref, native_id, wait_ms=0)
        return {
            "jobId": native_id,
            "status": state,
            "executionTerminal": False,
            "executionDisposition": None,
            "deliveryDisposition": delivery,
            "recoveryRequired": False,
            "resultAvailable": False,
            "semanticCompletionEvaluated": False,
            "artifactsAvailable": False,
            "artifacts": [],
        }

    def _resolve(self, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        request_id = _required_text(arguments.get("clientRequestId"), "clientRequestId")
        if arguments.get("workspaceId") != self.grant.workspace_id:
            raise HarnessRuntimeClientError("Gateway resolution changed granted Workspace identity")
        resolution = self._call(
            "execution.resolve",
            {"capability": self.grant.capability, "requestId": request_id},
        )
        # Gateway's own exact identity must be checked before projecting one
        # Runtime-compatible task.list row from the original Harness grant.
        if _gateway_field(resolution, "request_id", "requestId") != request_id:
            raise HarnessRuntimeClientError("Gateway execution resolution changed request identity")
        if resolution.get("capability") != self.grant.capability:
            raise HarnessRuntimeClientError(
                "Gateway execution resolution changed capability identity"
            )
        state = _required_text(resolution.get("resolution"), "resolution")
        if state == "absent":
            return {"jobs": [], "nextCursor": None}
        if state != "found":
            raise HarnessRuntimeClientError(f"Gateway execution resolution is {state}")
        native_id = _required_text(_gateway_field(resolution, "native_id", "nativeId"), "nativeId")
        operation_ref = _required_text(
            _gateway_field(resolution, "operation_ref", "operationRef"), "operationRef"
        )
        # Trust the resolved owner's observed Workspace, not the caller's
        # current grant alone. If that evidence is absent, recovery is UNKNOWN.
        workspace_id = _required_text(
            _gateway_field(resolution, "workspace_id", "workspaceId"), "workspaceId"
        )
        if workspace_id != self.grant.workspace_id:
            raise HarnessRuntimeClientError(
                "Gateway recovery returned a Job in a different workspace"
            )
        self._verify_owner_job_identity(resolution, native_id, operation_ref)
        self._retain_operation_binding(native_id, operation_ref, request_id)
        return {
            "jobs": [
                {
                    "jobId": native_id,
                    "clientRequestId": request_id,
                    "workspaceId": workspace_id,
                }
            ],
            "nextCursor": None,
        }

    def cancel_job(self, native_id: str) -> tuple[str, dict[str, JsonValue]]:
        operation_ref = self._operation_refs.get(native_id)
        if operation_ref is None:
            raise HarnessRuntimeClientError(
                "Gateway operationRef is unknown; reconcile before cancellation"
            )
        request_id = _required_text(
            self._operation_requests.get(native_id), "original clientRequestId"
        )
        receipt = self._call(
            "execution.cancel",
            {
                "operationRef": operation_ref,
                "requestId": request_id,
                "capability": self.grant.capability,
            },
        )
        if (
            _required_text(_gateway_field(receipt, "native_id", "nativeId"), "nativeId")
            != native_id
        ):
            raise HarnessRuntimeClientError(
                "Gateway cancellation changed native execution identity"
            )
        self._verify_owner_job_identity(receipt, native_id, operation_ref)
        # Source Gateway ExecutionReceipt.delivery_disposition is optional
        # for a cancellation acknowledgement; malformed presence is not.
        _gateway_delivery_disposition(receipt, allow_missing=True)
        terminal = _gateway_field(receipt, "terminal", "terminal")
        if not isinstance(terminal, bool):
            raise HarnessRuntimeClientError("Gateway cancellation receipt omitted terminal")
        state = _required_text(receipt.get("state"), "state")
        if terminal and state != "cancelled":
            return "terminal", self._observe_operation(operation_ref, native_id, wait_ms=0)
        return ("cancelled" if terminal else "cancel-requested"), {
            "operationRef": operation_ref,
            "jobId": native_id,
            "state": state,
            "terminal": terminal,
            "cancellationAcknowledged": True,
        }

    def _observe(self, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        native_id = _required_text(arguments.get("jobId"), "jobId")
        operation_ref = self._operation_refs.get(native_id)
        if operation_ref is None:
            raise HarnessRuntimeClientError(
                "Gateway operationRef is unknown; reconcile by clientRequestId first"
            )
        wait_ms = arguments.get("waitMs", 0)
        if type(wait_ms) is not int:
            raise HarnessRuntimeClientError("Gateway waitMs must be integer")
        return self._observe_operation(
            operation_ref, native_id, wait_ms=max(0, min(wait_ms, 30_000))
        )

    def _observe_operation(
        self, operation_ref: str, native_id: str, *, wait_ms: int
    ) -> dict[str, JsonValue]:
        request_id = _required_text(
            self._operation_requests.get(native_id), "original clientRequestId"
        )
        observed = self._call(
            "execution.get",
            {
                "operationRef": operation_ref,
                "eventLimit": 10,
                "waitMs": wait_ms,
                "requestId": request_id,
                "capability": self.grant.capability,
            },
        )
        if (
            _required_text(
                _gateway_field(observed, "operation_ref", "operationRef"), "operationRef"
            )
            != operation_ref
        ):
            raise HarnessRuntimeClientError("Gateway observation changed operation identity")
        if (
            _required_text(_gateway_field(observed, "native_id", "nativeId"), "nativeId")
            != native_id
        ):
            raise HarnessRuntimeClientError("Gateway observation changed native execution identity")
        self._verify_owner_job_identity(observed, native_id, operation_ref)
        terminal = _gateway_field(observed, "terminal", "terminal")
        if not isinstance(terminal, bool):
            raise HarnessRuntimeClientError("Gateway observation omitted terminal")
        # A terminal Job alone cannot establish that the observation belongs
        # to this Agent's granted Workspace. Reuse the existing Gateway
        # execution.resolve / Runtime job.list source-owned identity witness;
        # do NOT change Gateway's frozen MCP public schema or invent a lease.
        binding_confirmed = True
        if terminal:
            qualified = self._resolve(
                {
                    "clientRequestId": request_id,
                    "workspaceId": self.grant.workspace_id,
                }
            )
            matches = qualified["jobs"]
            binding_confirmed = bool(matches)
            if matches and matches[0]["jobId"] != native_id:
                raise HarnessRuntimeClientError(
                    "Gateway terminal observation conflicts with Runtime request/Workspace identity"
                )
        delivery = _gateway_delivery_disposition(observed)
        if terminal and not binding_confirmed:
            delivery = "reconciliation_required"
        disposition = _gateway_field(observed, "execution_disposition", "executionDisposition")
        if disposition is not None and not isinstance(disposition, str):
            raise HarnessRuntimeClientError("Gateway executionDisposition is invalid")
        # Native Runtime projects terminal status and executionDisposition
        # from one committed JobResolution. A mixed-version/stale Gateway
        # observation cannot certify the physical result merely by claiming
        # artifact inventory completeness; reject it before artifact.read.
        owner_state = _required_text(observed.get("state"), "state")
        if terminal and disposition is not None and owner_state != disposition:
            raise HarnessRuntimeClientError(
                "Gateway terminal state conflicts with executionDisposition"
            )
        if terminal and delivery == "committed" and disposition == "succeeded":
            success_exit = _gateway_field(observed, "exit_code", "exitCode")
            if type(success_exit) is not int or success_exit != 0:
                raise HarnessRuntimeClientError(
                    "Gateway succeeded execution lacks verified zero exitCode"
                )
        if terminal and delivery == "committed" and (
            disposition not in _GATEWAY_CONCLUSIVE_EXECUTION_RESOLUTIONS
        ):
            # The Owner's terminal status, committed delivery, and listed
            # Artifact IDs cannot certify an absent or uncertain Runner result.
            # UNKNOWN must not become resultAvailable or trigger artifact.read.
            raise HarnessRuntimeClientError(
                "Gateway committed executionDisposition lacks conclusive Runner evidence"
            )
        recovery = _gateway_field(observed, "recovery_required", "recoveryRequired")
        if terminal and recovery is None:
            raise HarnessRuntimeClientError("Gateway terminal observation omitted recoveryRequired")
        if recovery is None:
            recovery = False
        if not isinstance(recovery, bool):
            raise HarnessRuntimeClientError("Gateway recoveryRequired is invalid")
        if terminal and not binding_confirmed:
            recovery = True
        artifact_ids = _gateway_field(observed, "artifact_ids", "artifactIds")
        if artifact_ids is None:
            artifact_ids = []
        if not isinstance(artifact_ids, list) or any(
            not isinstance(item, str) or not item for item in artifact_ids
        ):
            raise HarnessRuntimeClientError("Gateway artifactIds are invalid")
        if len(artifact_ids) != len(set(artifact_ids)):
            # One repeated ID cannot account for multiple durable Artifacts,
            # even if a mixed-version Gateway claims a complete projection.
            raise HarnessRuntimeClientError("Gateway artifactIds contain duplicate identities")

        projection_complete = _gateway_field(
            observed, "artifact_projection_complete", "artifactProjectionComplete"
        )
        artifact_count = _gateway_field(observed, "artifact_count", "artifactCount")
        if artifact_count is not None and (type(artifact_count) is not int or artifact_count < 0):
            raise HarnessRuntimeClientError("Gateway artifactCount is invalid")
        if terminal and delivery == "committed" and not recovery:
            if artifact_count is None:
                # A claimed complete inventory without the Owner's total
                # cannot establish exact identity coverage or ResultAvailable.
                raise HarnessRuntimeClientError(
                    "Gateway committed artifactCount is missing"
                )
            if type(projection_complete) is not bool:
                raise HarnessRuntimeClientError(
                    "Gateway artifact projection completeness is missing or invalid"
                )
            if not projection_complete:
                # Physical completion and committed delivery are not sufficient
                # until the exact consumer-visible artifact set is projected.
                delivery = "reconciliation_required"
                recovery = True
            elif artifact_count is not None and artifact_count != len(artifact_ids):
                raise HarnessRuntimeClientError(
                    "Gateway artifact count differs from exact artifact identities"
                )
        # Gateway's artifact_projection_complete proves the *listed artifact
        # identities*, not existence of an original Runner execution_result.
        # In particular LOST + unknown + native_stop_evidence is NOT an
        # available Runner result. Do not synthesize one from an unknown
        # delivery label; the original native Owner remains the readback path.
        result_available = (
            terminal
            and not recovery
            and delivery == "committed"
            and projection_complete is True
        )
        response: dict[str, JsonValue] = {
            "jobId": native_id,
            "status": _required_text(observed.get("state"), "state"),
            "executionTerminal": terminal,
            "executionDisposition": disposition,
            "deliveryDisposition": delivery,
            "recoveryRequired": recovery,
            "resultAvailable": result_available,
            "semanticCompletionEvaluated": False,
            "exitCode": _gateway_field(observed, "exit_code", "exitCode"),
            "artifactsAvailable": bool(artifact_ids),
            "artifacts": [{"artifactId": item} for item in artifact_ids],
            # The installed Gateway certifies exact IDs, not each Owner
            # artifact kind/digest. A verified stdout prefix is not a full
            # ArtifactReference or independent durable-delivery receipt.
            "artifactMetadataStatus": (
                "unqualified_ids_only"
                if artifact_ids
                else ("qualified_empty" if result_available else "unavailable")
            ),
        }
        # Reuse existing Gateway artifact.read and the original bounded Tool
        # observation. Never fetch bytes for LOST/UNKNOWN or unqualified Jobs.
        if self._artifact_read_enabled and result_available:
            previews: dict[str, JsonValue] = {}
            for stream in ("stdout", "stderr"):
                matches = [
                    artifact_id
                    for artifact_id in artifact_ids
                    if artifact_id.endswith(f".{stream}")
                ]
                if len(matches) > 1:
                    raise HarnessRuntimeClientError(
                        f"Gateway returned multiple {stream} Artifact identities"
                    )
                if not matches:
                    continue
                artifact_id = matches[0]
                artifact = self._call(
                    "artifact.read",
                    {
                        "operationRef": operation_ref,
                        "artifactId": artifact_id,
                        "offset": 0,
                        "maxBytes": 4096,
                        "requestId": request_id,
                        "capability": self.grant.capability,
                    },
                )
                text = artifact.get("content")
                offset = artifact.get("offset")
                next_offset = _gateway_field(artifact, "next_offset", "nextOffset")
                eof = artifact.get("eof")
                digest = artifact.get("digest")
                if (
                    _gateway_field(artifact, "native_id", "nativeId") != native_id
                    or _gateway_field(artifact, "operation_ref", "operationRef") != operation_ref
                    or _gateway_field(artifact, "owner_id", "ownerId")
                    != "runtime." + self.grant.capability.removeprefix("execution.")
                    or _gateway_field(artifact, "artifact_id", "artifactId") != artifact_id
                    or type(offset) is not int
                    or offset != 0
                    or type(next_offset) is not int
                    or type(eof) is not bool
                    or not isinstance(text, str)
                    or not isinstance(digest, str)
                    or not digest.startswith("sha256:")
                    or not 0 <= next_offset <= 4096
                    or next_offset != len(text.encode("utf-8"))
                    or (not eof and next_offset == 0)
                ):
                    raise HarnessRuntimeClientError(
                        f"Gateway {stream} Artifact read lacks a progressing Owner byte window"
                    )
                previews[stream] = {
                    "artifactId": artifact_id,
                    "text": text,
                    "eof": eof,
                    "nextOffset": next_offset,
                    "truncated": not eof,
                    "digest": digest,
                }
            if previews:
                response["outputPreviews"] = previews
        return response
