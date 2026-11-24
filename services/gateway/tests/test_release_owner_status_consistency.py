"""Release discovery and effect preflight must share strict Runtime status law."""

from __future__ import annotations

import asyncio
from copy import deepcopy

import pytest

from ordivon_gateway.capabilities.execution.release import RuntimeReleaseProxy
from ordivon_gateway.logic.capability_projection import project_native_release_capability
from ordivon_gateway.logic.execution_refs import GatewayError
from ordivon_gateway.logic.routing import default_routes

VALID = {
    "schemaVersion": 1,
    "node": {"nodeId": "linux-pg", "platform": "linux", "native": True},
    "targets": [{"target": "local_linux", "configured": True, "available": True}],
    "structuredReleaseConfigured": True,
}


class RecordedOwner:
    def __init__(self, status: dict) -> None:
        self.status = status
        self.calls: list[str] = []

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict) -> dict:
        assert owner_id == "runtime.linux"
        self.calls.append(tool_name)
        if tool_name != "runtime.describe":
            pytest.fail("invalid release status must never dispatch an effect")
        return self.status


@pytest.mark.parametrize(
    "mutation",
    (
        lambda s: s.update(schemaVersion=True),
        lambda s: s["targets"].append(deepcopy(s["targets"][0])),
        lambda s: s["targets"].append({"target": "other", "configured": False, "available": True}),
        lambda s: s["targets"].append({"target": "other", "configured": "true", "available": True}),
    ),
)
def test_invalid_global_inventory_blocks_release_effect(mutation) -> None:
    status = deepcopy(VALID)
    mutation(status)
    caller = RecordedOwner(status)
    proxy = RuntimeReleaseProxy(caller)
    with pytest.raises(GatewayError, match="not qualified"):
        asyncio.run(
            proxy.apply(
                request_id="r",
                workspace_id="ws",
                commit="a" * 40,
                candidate_manifest_digest="sha256:" + "a" * 64,
                expected_tool_count=1,
            )
        )
    assert caller.calls == ["runtime.describe"]
    projection = project_native_release_capability(
        default_routes()["runtime.release.linux"],
        configured_at_gateway=True,
        owner_response=status,
    )
    assert projection.available is False
    assert projection.configured is False
    assert projection.observation_error is not None
