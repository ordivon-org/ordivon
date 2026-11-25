"""Pure selected-port admission over a catalog observation, not file I/O."""

from __future__ import annotations

from typing import Any

from .binding_selection import identity_key

PortKey = tuple[tuple[str, str], str, str]


def qualify_port_requests(requests: list[list[str]]) -> list[PortKey]:
    """Canonicalize product identity; preserve exact version and distribution URN."""
    keys = [(identity_key(pid), version, port) for pid, version, port in requests]
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate --require-port selection")
    return keys


def select_ports(
    products: list[dict[str, Any]], requests: list[list[str]]
) -> list[dict[str, str]]:
    """Index requested observations once; unknown is not a failed byte comparison."""
    keys = qualify_port_requests(requests)
    if not keys:
        return []
    requested = set(keys)
    requested_products = {(identity, version) for identity, version, _ in keys}
    matched: dict[PortKey, str] = {}
    for product in products:
        identity = identity_key(product["id"])
        version = product["version"]
        if (identity, version) not in requested_products:
            continue
        for distribution in product["distributions"]:
            port = distribution["id"]
            if not isinstance(port, str):
                continue
            key = (identity, version, port)
            if key not in requested:
                continue
            if key in matched:
                raise ValueError("ambiguous --require-port distribution identity")
            matched[key] = distribution["verification"]
    return [
        {
            "productId": pid,
            "productVersion": version,
            "distributionId": port,
            "verification": matched.get(key, "UNKNOWN"),
        }
        for (pid, version, port), key in zip(requests, keys, strict=True)
    ]
