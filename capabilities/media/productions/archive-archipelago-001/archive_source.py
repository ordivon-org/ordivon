"""Read the exact archive snapshot for multiple authored visual consumers.

Production-local source projection, not a new Catalog or second truth authority.
The supplied catalogDigest remains a source declaration, while byteSha256
identifies the exact input file actually read during this invocation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArchiveSnapshot:
    catalog: dict[str, Any]
    works: tuple[dict[str, Any], ...]
    relations: tuple[dict[str, str], ...]
    byte_sha256: str


def _relation_alias(relation: dict[str, Any], *names: str) -> str | None:
    """Normalize legacy field aliases without silently choosing conflicting facts."""
    values = [relation[name] for name in names if name in relation and relation[name] is not None]
    if not values:
        return None
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f'invalid relation alias for {names[0]}')
    if len(set(values)) != 1:
        raise ValueError(f'conflicting relation aliases for {names[0]}')
    return values[0]


def load_archive_snapshot(path: Path) -> ArchiveSnapshot:
    source = path.read_bytes()
    catalog = json.loads(source)
    if not isinstance(catalog, dict):
        raise ValueError('archive catalog must be an object')
    works = catalog.get('works')
    raw_relations = catalog.get('relations')
    if not isinstance(works, list) or not works or not all(isinstance(w, dict) for w in works):
        raise ValueError('catalog requires nonempty works with valid workId strings')
    if not isinstance(raw_relations, list) or not all(isinstance(r, dict) for r in raw_relations):
        raise ValueError('catalog relations must be an array of objects')
    ids = [w.get('workId') for w in works]
    if any(not isinstance(i, str) or not i.strip() for i in ids):
        raise ValueError('catalog requires nonempty works with valid workId strings')
    if len(ids) != len(set(ids)):
        raise ValueError('catalog contains duplicate workId')
    known = set(ids)
    relations = []
    for relation in raw_relations:
        a = _relation_alias(relation, 'child_work_id', 'childWorkId', 'from')
        b = _relation_alias(relation, 'parent_work_id', 'parentWorkId', 'to')
        kind = _relation_alias(relation, 'relation_type', 'relationType', 'type')
        if a not in known or b not in known:
            raise ValueError(f'relation references unknown work: {a!r} -> {b!r}')
        # Existing authored map only has two semantically distinct visual routes.
        # Do not silently draw an unsupported relationship as CONSUMER_OF.
        if kind not in {'DERIVATIVE_OF', 'CONSUMER_OF'}:
            raise ValueError(f'unsupported catalogued relation type: {kind!r}')
        relations.append({'from': a, 'to': b, 'type': kind})
    return ArchiveSnapshot(
        catalog=catalog, works=tuple(works), relations=tuple(relations),
        byte_sha256=hashlib.sha256(source).hexdigest(),
    )
