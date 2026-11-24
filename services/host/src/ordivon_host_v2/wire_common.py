"""Shared MCP wire vocabulary; no cross-domain owner state or cursor persistence."""

from typing import Annotated, Literal

from pydantic import Field

from .postgres_bounds import HOST_WIRE_INT_MAX

AdmissionWire = Literal["committed", "existing"]

# Exact integer on the incoming MCP wire. FastMCP otherwise silently converts
# True, 1.0 and "1" into cursor 1 before Store-level checks can run.
# Expose the actual interoperable numeric domain in native tools/list.
NonnegativeHostInteger = Annotated[int, Field(strict=True, ge=0, le=HOST_WIRE_INT_MAX)]
PositiveHostInteger = Annotated[int, Field(strict=True, ge=1, le=HOST_WIRE_INT_MAX)]
ExactCursorWire = NonnegativeHostInteger
