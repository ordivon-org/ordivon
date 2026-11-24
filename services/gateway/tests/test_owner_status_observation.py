"""Owner observation is request-scoped, read-only and non-authoritative."""

from __future__ import annotations

import asyncio

from ordivon_gateway.capabilities.owner_observation import OwnerStatusObserver


class FakeCaller:
    def __init__(self, *, slow: bool = False) -> None:
        self.slow = slow
        self.calls: list[tuple[str, str, dict]] = []

    def is_configured(self, owner_id: str) -> bool:
        return owner_id != "runtime.harness"

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict) -> dict:
        self.calls.append((owner_id, tool_name, arguments))
        if self.slow:
            await asyncio.sleep(0.1)
        return {"schemaVersion": 1, "targets": []}


def test_runtime_observation_caches_only_one_request_and_only_status() -> None:
    async def run() -> None:
        caller = FakeCaller()
        observer = OwnerStatusObserver(caller, 0.5)
        first = await observer.runtime_description("runtime.linux")
        second = await observer.runtime_description("runtime.linux")
        assert first == second
        assert caller.calls == [("runtime.linux", "runtime.describe", {"schemaVersion": 1})]
        assert await observer.runtime_description("runtime.harness") == (None, None)
        assert len(caller.calls) == 1
        another = OwnerStatusObserver(caller, 0.5)
        await another.runtime_description("runtime.linux")
        assert len(caller.calls) == 2
        assert all(name == "runtime.describe" for _, name, _ in caller.calls)

    asyncio.run(run())


def test_timeout_stays_unobserved_and_never_retries_effect() -> None:
    async def run() -> None:
        caller = FakeCaller(slow=True)
        observer = OwnerStatusObserver(caller, 0.001)
        result, error = await observer.runtime_description("runtime.windows")
        assert result is None
        assert error is not None and error.startswith("TimeoutError:")
        assert len(caller.calls) == 1
        assert await observer.runtime_description("runtime.windows") == (result, error)
        assert len(caller.calls) == 1

    asyncio.run(run())


def test_explicit_host_status_observation_does_not_touch_runtime_cache() -> None:
    async def run() -> None:
        caller = FakeCaller()
        observer = OwnerStatusObserver(caller, 0.5)
        result, error = await observer.observe("host.read", "host.status", {"detail": "summary"})
        assert result == {"schemaVersion": 1, "targets": []}
        assert error is None
        assert observer.runtime_cache == {}
        assert caller.calls == [("host.read", "host.status", {"detail": "summary"})]

    asyncio.run(run())
