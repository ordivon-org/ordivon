"""Pure identity and demand selection for validated producer metadata.

No file access, catalog mutation, or evidence admission belongs here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class LocalEvidenceBinding:
    product_id: str
    port_name: str
    path_property: str
    digest_property: str
    owner_root: Path
    # Optional because Bitol ODPS 1.1 permits unversioned ports. None
    # preserves the legacy behavior: require a unique port name.
    port_version: str | None = None
    # Omission is allowed only for a unique matching product version.
    product_version: str | None = None


def uuid_uri(value: str) -> str | None:
    """Keep upstream IDs as supplied; mint no URI for a non-UUID identifier."""
    try:
        return "urn:uuid:" + str(UUID(value))
    except ValueError:
        return None


def identity_key(value: str) -> tuple[str, str]:
    """Compare the identity actually emitted by this projection.

    UUID spellings can normalize to one RDF URI (RFC 9562); opaque source
    IDs retain exact spelling. The tags prevent collisions across kinds.
    """
    uri = uuid_uri(value)
    return ("uuid", uri) if uri is not None else ("opaque", value)


def select_bindings(
    products: list[dict[str, Any]],
    bindings: tuple[LocalEvidenceBinding, ...],
) -> list[tuple[int, int, LocalEvidenceBinding]]:
    """Resolve every binding to one product/version and one port before I/O."""
    by_identity: dict[tuple[str, str], list[int]] = {}
    for i, product in enumerate(products):
        by_identity.setdefault(identity_key(product["id"]), []).append(i)
    selected = []
    seen: set[tuple[int, int]] = set()
    for binding in bindings:
        for value, label in (
            (binding.product_id, "product identity"),
            (binding.port_name, "port name"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"binding {label} must be a nonempty string")
        for value, label in (
            (binding.product_version, "product version"),
            (binding.port_version, "port version"),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"binding {label} must be a nonempty string")
        candidates = [
            i
            for i in by_identity.get(identity_key(binding.product_id), [])
            if binding.product_version is None
            or products[i]["version"] == binding.product_version
        ]
        if len(candidates) != 1:
            raise ValueError(
                "binding requires exactly one product identity and product version"
            )
        product_index = candidates[0]
        ports = products[product_index]["outputPorts"]
        matches = [
            i
            for i, port in enumerate(ports)
            if port["name"] == binding.port_name
            and (
                binding.port_version is None
                or port.get("version") == binding.port_version
            )
        ]
        if len(matches) != 1:
            raise ValueError(
                "binding requires exactly one named output port at requested version"
            )
        port_index = matches[0]
        if ports[port_index].get("type") not in (
            "file/json",
            "file/parquet",
            "file/csv",
        ):
            raise ValueError("binding requires a supported file output port")
        key = (product_index, port_index)
        if key in seen:
            raise ValueError("duplicate local evidence binding for output port")
        seen.add(key)
        selected.append((product_index, port_index, binding))
    return selected
