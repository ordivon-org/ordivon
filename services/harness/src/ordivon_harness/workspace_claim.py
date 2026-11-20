"""Fail-closed Run-birth consumer of Runtime's *native* PG Workspace Claim.

Harness and Runtime have independent databases: a Harness journal commit never
implies a physical Workspace pin. This module keeps no second claim store.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .core_contracts import HarnessRunContract
from .runtime_port import HarnessWorkspaceAdmissionUnavailable


class NativeWorkspaceClaimClient(Protocol):
    """Authenticated Runtime MCP tool adapter, e.g. OfficialMcpClient.

    This is deliberately distinct from Gateway's execution-only lowering API.
    The transport owns the authenticating principal and may not be silently
    rebound to an unauthenticated Workspace client.
    """

    def call_tool(
        self, name: str, arguments: dict[str, JsonValue]
    ) -> tuple[bool, dict[str, JsonValue]]: ...


def _digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(c in "0123456789abcdef" for c in value[7:])
    )


@dataclass(frozen=True, slots=True)
class WorkspaceRunClaim:
    contract: HarnessRunContract
    workspace_id: str
    client: NativeWorkspaceClaimClient

    @property
    def request_id(self) -> str:
        # Intentionally *not* scoped by workspace: one original Run cannot
        # switch to another physical Workspace during ambiguous recovery.
        digest = canonical_digest({
            "schemaVersion": 1,
            "kind": "ordivon.harness-native-workspace-claim-request",
            "harnessRunId": self.contract.harness_run_id,
            "contractDigest": self.contract.digest,
        })
        return f"request:harness-workspace-claim:{digest[7:39]}"

    def _call(
        self, name: str, arguments: dict[str, JsonValue], *, allow_absent: bool = False
    ) -> dict[str, JsonValue] | None:
        try:
            is_error, result = self.client.call_tool(name, arguments)
            validate_json_value(result)
        except Exception as exc:
            raise HarnessWorkspaceAdmissionUnavailable(
                f"native Runtime {name} unavailable/UNKNOWN; Run is not usable"
            ) from exc
        if type(is_error) is not bool or not isinstance(result, dict):
            raise HarnessWorkspaceAdmissionUnavailable(
                f"native Runtime {name} returned invalid transport evidence"
            )
        if is_error:
            error = result.get("error")
            if (
                allow_absent and isinstance(error, dict)
                and error.get("code") == "WORKSPACE_NOT_FOUND"
                and error.get("commitState") == "not_committed"
            ):
                return None
            raise HarnessWorkspaceAdmissionUnavailable(
                f"native Runtime {name} rejected or outcome UNKNOWN"
            )
        return result

    def get(self, *, allow_absent: bool = False) -> dict[str, JsonValue] | None:
        result = self._call(
            "workspace.claim.get", {
                "schemaVersion": 1, "clientRequestId": self.request_id,
            }, allow_absent=allow_absent,
        )
        if result is None:
            return None
        if (
            result.get("schemaVersion") != 1
            or result.get("workspaceId") != self.workspace_id
            or result.get("runRef") != self.contract.harness_run_id
            or result.get("clientRequestId") != self.request_id
            or not isinstance(result.get("claimId"), str)
            or not result["claimId"]
            or not isinstance(result.get("storeRoot"), str)
            or not result["storeRoot"]
            or not _digest(result.get("sourceStateDigestAtReserve"))
            or result.get("state") not in {"held", "released"}
        ):
            raise HarnessWorkspaceAdmissionUnavailable(
                "native Runtime Claim identity or source authority differs from original Run"
            )
        return result

    def require_held(self) -> dict[str, JsonValue]:
        # An authenticated native NOT_COMMITTED absence is actionable (not
        # HELD); transport failure, malformed evidence and lost replies
        # remain UNKNOWN and must never become permission to auto-reserve.
        claim = self.get(allow_absent=True)
        if claim is None or claim["state"] != "held":
            raise HarnessWorkspaceAdmissionUnavailable(
                "original native Runtime Workspace Claim is not HELD"
            )
        return claim

    def reserve_or_recover(self) -> dict[str, JsonValue]:
        # GET first: if an earlier reserve response was lost, current Git may
        # have changed. The *original* source digest remains authoritative.
        existing = self.get(allow_absent=True)
        if existing is not None:
            return self.require_held()

        workspace = self._call("workspace.get", {
            "schemaVersion": 1, "workspaceId": self.workspace_id,
        })
        if workspace is None or workspace.get("workspaceId") != self.workspace_id:
            raise HarnessWorkspaceAdmissionUnavailable(
                "native Runtime Workspace identity unavailable before Run-birth pin"
            )
        digest = workspace.get("sourceStateDigest")
        if not _digest(digest):
            raise HarnessWorkspaceAdmissionUnavailable(
                "native Workspace exact sourceStateDigest unavailable"
            )
        try:
            self._call("workspace.claim.reserve", {
                "schemaVersion": 1,
                "clientRequestId": self.request_id,
                "workspaceId": self.workspace_id,
                "runRef": self.contract.harness_run_id,
                "expectedSourceStateDigest": digest,
            })
        except HarnessWorkspaceAdmissionUnavailable:
            # An uncertain effect is never retried under another identity.
            # GET may discover that the original transaction did commit.
            recovered = self.get(allow_absent=True)
            if recovered is None:
                raise
        # Readback, not a local Boolean or a successful HTTP status, proves
        # that native Runtime physically pins the Workspace.
        return self.require_held()
