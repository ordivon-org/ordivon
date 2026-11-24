"""Bounded read-only natural-Owner observation adapter.

This is an effect-boundary capability, not an alternate readiness policy or
store. The caller remains the only Owner transport; each instance belongs to
one discovery request and never survives into the next request.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..logic.owner_protocol import OwnerToolCaller, _configured

OwnerStatusResult = tuple[dict[str, Any] | None, str | None]


class OwnerStatusObserver:
    def __init__(self, caller: OwnerToolCaller, timeout_seconds: float) -> None:
        self._caller = caller
        self._timeout_seconds = timeout_seconds
        # Request-scoped Runtime status: not a cache of physical execution facts.
        self.runtime_cache: dict[str, OwnerStatusResult] = {}

    async def observe(
        self, owner_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> OwnerStatusResult:
        """Observe status once, retaining a distinct timeout/error UNKNOWN."""
        started = asyncio.get_running_loop().time()
        try:
            async with asyncio.timeout(self._timeout_seconds):
                result = await self._caller.call_tool(owner_id, tool_name, arguments)
            return result, None
        except TimeoutError:
            elapsed_ms = int((asyncio.get_running_loop().time() - started) * 1000)
            return (
                None,
                f"TimeoutError: observation {owner_id}/{tool_name} timed out "
                f"after {elapsed_ms}ms (budget={self._timeout_seconds:g}s); "
                "Owner readiness UNKNOWN",
            )
        except Exception as exc:
            return None, f"{type(exc).__name__}: {str(exc)[:240]}"

    async def runtime_description(self, owner_id: str) -> OwnerStatusResult:
        cached = self.runtime_cache.get(owner_id)
        if cached is not None:
            return cached
        if not _configured(self._caller, owner_id):
            value: OwnerStatusResult = (None, None)
            self.runtime_cache[owner_id] = value
            return value
        value = await self.observe(owner_id, "runtime.describe", {"schemaVersion": 1})
        self.runtime_cache[owner_id] = value
        return value
