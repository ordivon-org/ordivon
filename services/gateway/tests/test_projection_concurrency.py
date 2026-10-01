from __future__ import annotations

import asyncio
from collections import Counter
from typing import Any

import pytest

from ordivon_gateway.service import GatewayService


def runtime_payload(owner: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "node": {
            "nodeId": owner,
            "platform": "linux" if owner.endswith("linux") else "windows",
            "native": True,
        },
        "targets": [
            {
                "target": "local_linux" if owner.endswith("linux") else "windows_native",
                "configured": True,
                "available": True,
                "executionProfiles": ["trusted_local"],
            }
        ],
    }


def test_independent_owner_observations_start_without_waiting_for_each_other() -> None:
    async def scenario() -> None:
        started: set[str] = set()
        ready = asyncio.Event()
        calls: list[tuple[str, str]] = []

        class Caller:
            def is_configured(self, owner: str) -> bool:
                return owner in {"runtime.linux", "runtime.windows", "host"}

            async def call_tool(self, owner: str, tool: str, args: dict) -> dict:
                calls.append((owner, tool))
                started.add(owner)
                if len(started) == 3:
                    ready.set()
                await asyncio.wait_for(ready.wait(), timeout=0.2)
                return {"schemaVersion": 3} if owner == "host" else runtime_payload(owner)

        projection = await GatewayService(Caller()).capability_describe()
        by_id = {item.capability: item for item in projection.capabilities}
        assert by_id["execution.linux"].available
        assert by_id["execution.windows"].available
        assert by_id["continuity.external"].available
        assert by_id["artifact.runtime"].available
        assert Counter(calls) == {
            ("runtime.linux", "runtime.describe"): 1,
            ("runtime.windows", "runtime.describe"): 1,
            ("host", "host.status"): 1,
        }
        assert [item.capability for item in projection.capabilities] == sorted(by_id)

    asyncio.run(scenario())


def test_slow_owner_becomes_unknown_without_hiding_healthy_owner() -> None:
    async def scenario() -> None:
        cancelled = asyncio.Event()

        class Caller:
            def is_configured(self, owner: str) -> bool:
                return owner in {"runtime.linux", "runtime.windows", "host"}

            async def call_tool(self, owner: str, tool: str, args: dict) -> dict:
                if owner == "runtime.linux":
                    try:
                        await asyncio.Event().wait()
                    finally:
                        cancelled.set()
                return {"schemaVersion": 3} if owner == "host" else runtime_payload(owner)

        service = GatewayService(Caller(), projection_timeout_seconds=0.02)
        projection = await asyncio.wait_for(service.capability_describe(), timeout=0.5)
        by_id = {item.capability: item for item in projection.capabilities}
        assert not by_id["execution.linux"].available
        assert by_id["execution.linux"].configured
        assert "TimeoutError" in (by_id["execution.linux"].observation_error or "")
        assert by_id["execution.windows"].available
        assert by_id["continuity.external"].available
        assert by_id["artifact.runtime"].available
        assert cancelled.is_set()
        result = await service.capability_search(query="linux", include_unavailable=False)
        assert result.total_matches == 1
        assert result.matches[0].capability.observation_error

    asyncio.run(scenario())


def test_selected_capability_probes_only_its_owner_and_reobserves_next_request() -> None:
    async def scenario() -> None:
        available = True
        calls: list[str] = []

        class Caller:
            def is_configured(self, owner: str) -> bool:
                return True

            async def call_tool(self, owner: str, tool: str, args: dict) -> dict:
                calls.append(owner)
                result = runtime_payload(owner)
                result["targets"][0]["available"] = available
                return result

        service = GatewayService(Caller())
        first = await service.capability_describe("execution.windows")
        available = False
        second = await service.capability_describe("execution.windows")
        assert first.capabilities[0].available
        assert not second.capabilities[0].available
        assert first.projection_digest != second.projection_digest
        assert calls == ["runtime.windows", "runtime.windows"]

    asyncio.run(scenario())


def test_cancelling_projection_leaves_no_owner_observation_running() -> None:
    async def scenario() -> None:
        started: set[str] = set()
        stopped: set[str] = set()
        ready = asyncio.Event()

        class Caller:
            def is_configured(self, owner: str) -> bool:
                return owner in {"runtime.linux", "runtime.windows", "host"}

            async def call_tool(self, owner: str, tool: str, args: dict) -> dict:
                started.add(owner)
                if len(started) == 3:
                    ready.set()
                try:
                    await asyncio.Event().wait()
                finally:
                    stopped.add(owner)

        task = asyncio.create_task(GatewayService(Caller()).capability_describe())
        try:
            await asyncio.wait_for(ready.wait(), timeout=0.2)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert stopped == {"runtime.linux", "runtime.windows", "host"}

    asyncio.run(scenario())


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True])
def test_invalid_observation_budget_is_rejected(timeout: float) -> None:
    with pytest.raises(ValueError, match="positive finite"):
        GatewayService(object(), projection_timeout_seconds=timeout)
