"""Qualify native Git listing against the committed tree identities.

The listing is a projection, not an authority. Reconstruct only direct canonical
tree records from the projection; native object-byte verification remains a
separate obligation. Noncanonical historical tree modes fail closed.
"""

from __future__ import annotations

import hashlib
import re

_MODES = {
    b"040000": (b"tree", b"40000"),
    b"100644": (b"blob", b"100644"),
    b"100755": (b"blob", b"100755"),
    b"120000": (b"blob", b"120000"),
    b"160000": (b"commit", b"160000"),
}


def qualify_tree_listing(
    raw: bytes, root_tree: str, algorithm: str
) -> tuple[set[str], list[tuple[str, str]]]:
    """Check every direct tree commitment, retaining only selected ODPS paths."""
    if algorithm not in ("sha1", "sha256"):
        raise ValueError("unsupported Git object format")
    width = 40 if algorithm == "sha1" else 64
    oid_pattern = re.compile(rb"[0-9a-f]{%d}" % width)
    root_oid = root_tree.encode("ascii")
    if oid_pattern.fullmatch(root_oid) is None:
        raise ValueError("Git root tree identity mismatch")
    if not raw.endswith(b"\0"):
        raise ValueError("incomplete Git tree listing")
    entries = raw.split(b"\0")
    entries.pop()
    tree_paths = {b"": root_oid}
    children: dict[bytes, dict[bytes, tuple[bytes, bytes, bytes]]] = {}
    products: list[tuple[str, str]] = []
    for entry in entries:
        metadata, separator, path = entry.partition(b"\t")
        if not separator or not metadata or not path:
            raise ValueError("incomplete Git tree listing")
        fields = metadata.split(b" ")
        if len(fields) != 3:
            raise ValueError("incomplete Git tree listing")
        mode, kind, oid = fields
        if (
            mode not in _MODES
            or _MODES[mode][0] != kind
            or oid_pattern.fullmatch(oid) is None
        ):
            raise ValueError("invalid Git tree listing entry")
        parent, _, name = path.rpartition(b"/")
        if (
            not name
            or path.startswith(b"/")
            or name in (b".", b"..")
            or parent.endswith(b"/")
        ):
            raise ValueError("invalid Git tree listing path")
        siblings = children.setdefault(parent, {})
        if name in siblings:
            raise ValueError("duplicate Git tree listing path")
        siblings[name] = (_MODES[mode][1], kind, bytes.fromhex(oid.decode("ascii")))
        if kind == b"tree":
            tree_paths[path] = oid
        elif path.endswith(b"/odps.json"):
            if mode not in (b"100644", b"100755"):
                raise ValueError("ODPS tracked source is not a regular Git blob")
            products.append((path.decode("utf-8"), oid.decode("ascii")))

    if not children.keys() <= tree_paths.keys():
        raise ValueError("Git tree identity mismatch: orphan listing path")
    # Git compares directory names as if suffixed with slash. No recursive
    # traversal or duplicate materialization of a whole tree object is needed.
    for parent, oid in tree_paths.items():
        siblings = children.get(parent, {})
        ordered = sorted(
            siblings.items(),
            key=lambda item: item[0] + (b"/" if item[1][1] == b"tree" else b""),
        )
        size = sum(
            len(mode) + 1 + len(name) + 1 + len(binary_oid)
            for name, (mode, _, binary_oid) in ordered
        )
        digest = hashlib.new(algorithm, b"tree " + str(size).encode("ascii") + b"\0")
        for name, (mode, _, binary_oid) in ordered:
            digest.update(mode + b" " + name + b"\0")
            digest.update(binary_oid)
        if digest.hexdigest().encode("ascii") != oid:
            raise ValueError("Git tree identity mismatch: incomplete listing")
    return {oid.decode("ascii") for oid in tree_paths.values()}, products
