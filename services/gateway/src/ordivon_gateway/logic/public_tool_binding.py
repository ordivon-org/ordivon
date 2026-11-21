"""Request-local public MCP call identity, distinct from Host Tool catalog.

The existing Gateway Security middleware binds decoded public action/arguments
for the duration of an Owner delegate call. This witness is not authentication,
authorization, policy storage, or physical execution evidence.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

_PUBLIC_TOOL_CALL: ContextVar[tuple[str, Mapping[str, Any]] | None] = ContextVar(
    "ordivon_gateway_public_tool_call", default=None
)


@contextmanager
def bind_public_tool_call(tool_name: str, arguments: Mapping[str, Any]) -> Iterator[None]:
    token = _PUBLIC_TOOL_CALL.set((tool_name, dict(arguments)))
    try:
        yield
    finally:
        _PUBLIC_TOOL_CALL.reset(token)


def current_public_tool_call() -> tuple[str, Mapping[str, Any]] | None:
    return _PUBLIC_TOOL_CALL.get()
