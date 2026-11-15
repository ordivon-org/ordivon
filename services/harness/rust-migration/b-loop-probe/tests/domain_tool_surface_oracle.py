#!/usr/bin/env python3
"""Source-oracle for Python DomainToolCatalog, grant digest, and ordered surface.

Only existing production constructors and _select/_granted_digest are the oracle.
No Python↔Rust translation assumptions are baked into expected digests.
"""
from __future__ import annotations

from anc_canonical import canonical_bytes
from ordivon_harness.domain_tools import AgentToolDefinition, DomainToolCatalog


def emit(catalog: DomainToolCatalog, allowed: tuple[str, ...]) -> None:
    raw_catalog = canonical_bytes(catalog.to_dict()).hex()
    raw_allowed = canonical_bytes(list(allowed)).hex()
    try:
        selected = catalog._select(allowed)
        selected_hex = canonical_bytes([tool.name for tool in selected]).hex()
        print("\t".join((
            "S", "1", raw_catalog, raw_allowed,
            selected_hex, catalog.digest, catalog._granted_digest(allowed),
        )))
    except ValueError:
        print("\t".join(("S", "0", raw_catalog, raw_allowed, "-", "-", "-")))


for i in range(32):
    tools = tuple(
        AgentToolDefinition(
            name=f"tool_{i}_{j}_" + ("中文🧩" if j % 2 else "simple"),
            description=f"Model-visible tool {i} / {j} 🛠",
            input_schema={
                "type": "object",
                "properties": {f"arg_{j}": {"type": "string"}},
                "required": [f"arg_{j}"],
                "additionalProperties": False,
            },
        )
        for j in range(1 + i % 7)
    )
    catalog = DomainToolCatalog(
        domain_id=f"domain:lab_{i}",
        revision=f"revision_{i}_未来",
        tools=tools,
    )
    names = tuple(tool.name for tool in tools)
    for allowed in (
        names,
        tuple(reversed(names)),
        (names[0],),
        tuple(names[::2]),
        ("tool-not-in-catalog",),
        (names[0], names[0]),
        (),
    ):
        emit(catalog, allowed)
