"""Shared Host MCP wire byte-budget boundaries."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

HostCollectionBytes = Annotated[int, Field(ge=16_384, le=4_194_304)]
HostMessageBytes = Annotated[int, Field(ge=131_072, le=4_194_304)]
