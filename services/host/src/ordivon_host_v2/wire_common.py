"""Shared MCP wire vocabulary; no cross-domain owner state or cursor persistence."""

from typing import Annotated, Literal

from pydantic import Field

AdmissionWire = Literal["committed", "existing"]

# Exact integer on the incoming MCP wire. FastMCP otherwise silently converts
# True, 1.0 and "1" into cursor 1 before Store-level checks can run.
# JSON Schema remains {"type":"integer"}, so existing valid client schemas remain stable.
ExactCursorWire = Annotated[int, Field(strict=True)]
