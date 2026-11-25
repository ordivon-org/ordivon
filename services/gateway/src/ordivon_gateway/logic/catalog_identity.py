"""Pure catalog identity and description projection; no package or Owner I/O."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict

from ..contracts import CapabilityRoute, OwnerDescriptor, SystemDescription

_OWNER_ROLES = {
    "runtime.linux": "physical execution owner",
    "runtime.windows": "physical execution owner",
    "runtime.harness": "issuer-fenced execution profile of the Linux Runtime owner",
    "host": "external semantic continuity owner",
    "skills": "procedural Skill discovery and exact binding owner",
    "research.composition": "non-authoritative Research composition metadata",
}


def digest_json(value: object) -> str:
    """Preserve the existing sorted UTF-8 JSON digest contract."""
    return (
        "sha256:"
        + hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()
    )


def route_digest(routes: Mapping[str, CapabilityRoute]) -> str:
    return digest_json([asdict(routes[key]) for key in sorted(routes)])


def project_system_description(
    routes: Mapping[str, CapabilityRoute],
    *,
    gateway_version: str,
    route_identity: str,
    owner_configured: Mapping[str, bool],
) -> SystemDescription:
    return SystemDescription(
        gateway_version=gateway_version,
        route_digest=route_identity,
        owners=[
            OwnerDescriptor(owner_id=owner, role=role, configured=owner_configured[owner])
            for owner, role in _OWNER_ROLES.items()
        ],
        capabilities=sorted(routes),
    )
