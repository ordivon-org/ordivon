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
        a = relation.get('child_work_id') or relation.get('childWorkId') or relation.get('from')
        b = relation.get('parent_work_id') or relation.get('parentWorkId') or relation.get('to')
        kind = relation.get('relation_type') or relation.get('relationType') or relation.get('type')
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
