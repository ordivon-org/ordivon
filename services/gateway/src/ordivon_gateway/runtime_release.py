"""Route qualified Linux Runtime self-release to its existing MCP Owner.

No shell Runner, second installer, local receipts or automatic effect retry.
The original Runtime release.get is the sole recovery query after response loss.
"""

from __future__ import annotations

from typing import Any

from .contracts import RuntimeReleaseAdmission, RuntimeReleaseProjection
from .execution_refs import GatewayError
from .upstream import OwnerToolCaller

_OWNER = "runtime.linux"
_NODE = "linux-pg"


class RuntimeReleaseProxy:
    def __init__(self, caller: OwnerToolCaller) -> None:
        self._caller = caller

    async def apply(
        self,
        *,
        request_id: str,
        workspace_id: str,
        commit: str,
        candidate_manifest_digest: str,
        expected_tool_count: int,
    ) -> RuntimeReleaseAdmission:
        # A fixed Owner route is not a CLI or a nodeId supplied by the caller.
        # Owner-side qualification/replay remains Runtime's authority, including
        # after a changed Release configuration or a lost Tool response. Gateway
        # checks node identity only; it must not reimplement release admission.
        described = await self._caller.call_tool(_OWNER, "runtime.describe", {"schemaVersion": 1})
        node = described.get("node")
        targets = described.get("targets")
        if (
            not isinstance(node, dict)
            or node.get("nodeId") != _NODE
            or node.get("platform") != "linux"
            or node.get("native") is not True
            or not isinstance(targets, list)
            or not any(
                isinstance(t, dict)
                and t.get("target") == "local_linux"
                and t.get("configured") is True
                and t.get("available") is True
                for t in targets
            )
        ):
            raise GatewayError("Linux Runtime native structured release is not qualified")
        result = await self._caller.call_tool(
            _OWNER,
            "release.apply",
            {
                "schemaVersion": 1,
                "clientRequestId": request_id,
                "workspaceId": workspace_id,
                "commit": commit,
                "candidateManifestDigest": candidate_manifest_digest,
                "expectedToolCount": expected_tool_count,
            },
        )
        admission = RuntimeReleaseAdmission.model_validate(result)
        release = admission.release
        if (
            release.client_request_id != request_id
            or release.workspace_id != workspace_id
            or release.commit != commit
            or release.candidate_manifest_digest != candidate_manifest_digest
            or release.expected_tool_count != expected_tool_count
        ):
            raise GatewayError("Runtime release.apply returned a different original effect")
        return admission

    async def get(self, *, request_id: str) -> RuntimeReleaseProjection:
        # NO describe/preflight: a release can replace Runtime during a lost
        # response. The read must preserve the exact original request scope.
        result: dict[str, Any] = await self._caller.call_tool(
            _OWNER, "release.get", {"schemaVersion": 1, "clientRequestId": request_id}
        )
        projected = RuntimeReleaseProjection.model_validate(result)
        if projected.client_request_id != request_id:
            raise GatewayError("Runtime release.get returned a different original request")
        return projected
