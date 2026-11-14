#!/usr/bin/env python3
"""Produce an editable Vega-Lite specification from a selected archive catalog.

This is an optional authored companion to the source-bound archipelago map.
It does not change existing approved Outputs or require a renderer for discovery.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from archive_source import load_archive_snapshot

SOURCE = Path(__file__).resolve().parent / 'source' / 'creative-library-catalog-v1.json'


def build_spec(source: Path) -> dict:
    snapshot = load_archive_snapshot(source)
    owners = Counter(work.get('owner') or 'Unknown' for work in snapshot.works)
    return {
        '$schema': 'https://vega.github.io/schema/vega-lite/v6.json',
        'description': 'Counts of works by owner in a frozen Creative Library catalog. Not geography, dependency, or quality.',
        'title': {
            'text': 'Archive Archipelago — works by owner',
            'subtitle': [
                f'{len(snapshot.works)} catalogued works · {len(snapshot.relations)} catalogued relations',
                'Owner attribution only · no inferred dependencies or geography',
            ],
            'anchor': 'start',
        },
        'width': 620,
        'height': {'step': 50},
        'data': {'values': [
            {'owner': owner, 'works': count} for owner, count in sorted(owners.items())
        ]},
        'mark': {'type': 'bar', 'cornerRadiusEnd': 4},
        'encoding': {
            'y': {'field': 'owner', 'type': 'nominal', 'sort': '-x', 'title': None},
            'x': {'field': 'works', 'type': 'quantitative', 'title': 'Catalogue works',
                  'scale': {'zero': True}, 'axis': {'tickMinStep': 1}},
            'tooltip': [
                {'field': 'owner', 'type': 'nominal', 'title': 'Owner'},
                {'field': 'works', 'type': 'quantitative', 'title': 'Works', 'format': 'd'},
            ],
        },
        'config': {'background': '#ffffff', 'view': {'stroke': None}, 'font': 'sans-serif'},
        'usermeta': {
            'origin': 'ordivon.media.archive-archipelago-001',
            'sourceSha256': 'sha256:' + snapshot.byte_sha256,
            'declaredCatalogDigest': snapshot.catalog.get('catalogDigest'),
            'sourceWorkCount': len(snapshot.works),
            'sourceRelationCount': len(snapshot.relations),
            'status': 'derived-editable-preview-not-approved-output',
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE,
                        help='exact selected Creative Library source snapshot')
    parser.add_argument('--output', type=Path,
                        help='write Vega-Lite JSON spec to an explicit destination; otherwise stdout')
    args = parser.parse_args()
    payload = json.dumps(build_spec(args.source), ensure_ascii=False, sort_keys=True, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
