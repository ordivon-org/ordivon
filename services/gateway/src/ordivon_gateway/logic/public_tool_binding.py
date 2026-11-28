"""Request-local public MCP call identity, distinct from Host Tool catalog.

The witness is not authentication, authorization, or physical execution evidence.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from typing import Any

# A request-local identity witness, NOT another authentication/authorization
# authority. The already installed MCP Security middleware binds the public
# Tool and its original args for precisely the duration of call_next(ctx).
# Natural Host and Security continue to own domain effects and PDP decisions.
_PUBLIC_TOOL_CALL: ContextVar[tuple[str, Mapping[str, Any]] | None] = ContextVar(
    "ordivon_gateway_public_tool_call", default=None
)


@contextmanager
def bind_public_tool_call(tool_name: str, arguments: Mapping[str, Any]) -> Iterator[None]:
    token = _PUBLIC_TOOL_CALL.set((tool_name, deepcopy(dict(arguments))))
    try:
        yield
    finally:
        _PUBLIC_TOOL_CALL.reset(token)


def current_public_tool_call() -> tuple[str, Mapping[str, Any]] | None:
    # Never expose the mutable stored witness to downstream Tool code.
    return deepcopy(_PUBLIC_TOOL_CALL.get())
