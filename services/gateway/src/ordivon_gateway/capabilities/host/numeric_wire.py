"""Interoperable Host V1 coordinate projection (RFC 7493 / RFC 8785).

Host owns the domain. Gateway preserves exact original values and rejects
out-of-domain input before an Owner call. Native SDK differential tests
qualify this projection; never import Host storage into Gateway.
"""

from typing import Annotated

from pydantic import Field

HOST_WIRE_INT_MAX = (1 << 53) - 1
HostNonnegativeInteger = Annotated[int, Field(strict=True, ge=0, le=HOST_WIRE_INT_MAX)]
HostPositiveInteger = Annotated[int, Field(strict=True, ge=1, le=HOST_WIRE_INT_MAX)]
HostPositiveRevision = HostPositiveInteger
HostAdvancableRevision = Annotated[int, Field(strict=True, ge=1, le=HOST_WIRE_INT_MAX - 1)]
