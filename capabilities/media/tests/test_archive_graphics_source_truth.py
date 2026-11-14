"""Consumer-grounded checks for the Archive Archipelago visual generator.

The source-owner facts are the immutable catalog snapshot. The test does not
promote a graphic, a synthetic mutation, or a successful subprocess to source truth.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1] / 'productions' / 'archive-archipelago-001'
SOURCE = PRODUCTION / 'source' / 'creative-library-catalog-v1.json'


class ArchiveVisualContractTests(unittest.TestCase):
    def run_fixture(self, change=None):
        with tempfile.TemporaryDirectory(prefix='archive-visual-contract-') as temp:
            root = Path(temp)
            (root / 'source').mkdir()
            shutil.copy2(PRODUCTION / 'generate.py', root / 'generate.py')
            shutil.copy2(PRODUCTION / 'archive_source.py', root / 'archive_source.py')
            catalog = json.loads(SOURCE.read_text(encoding='utf-8'))
            if change is not None:
                change(catalog)
            (root / 'source' / SOURCE.name).write_text(
                json.dumps(catalog, ensure_ascii=False), encoding='utf-8'
            )
            run = subprocess.run(
                ['python3', 'generate.py'], cwd=root, capture_output=True,
                text=True, timeout=30, check=False,
            )
            outputs = {}
            for file in ('render/archive-archipelago-001.svg',
                         'render/build-manifest.json', 'interactive/data.js'):
                if (root / file).exists():
                    outputs[file] = (root / file).read_bytes()
            return run, outputs

    def test_frozen_real_consumer_is_byte_identical_to_approved_output(self):
        run, outputs = self.run_fixture()
        self.assertEqual(run.returncode, 0, run.stderr)
        for name, generated in outputs.items():
            self.assertEqual(generated, (PRODUCTION / name).read_bytes(), name)
        approved = next(
            row for row in json.loads((PRODUCTION / 'production.json').read_text())['outputs']
            if row['id'] == 'archive-archipelago-svg'
        )
        self.assertEqual(
            hashlib.sha256(outputs['render/archive-archipelago-001.svg']).hexdigest(),
            approved['blobDigest'].split(':', 1)[1],
        )

    def test_new_work_changes_only_declared_owner_and_total_counts(self):
        def add_work(catalog):
            row = dict(catalog['works'][0])
            row.update(workId='synthetic:future-work-r1', owner='Media', title='Synthetic only',
                       featured=False)
            catalog['works'].append(row)

        run, outputs = self.run_fixture(add_work)
        self.assertEqual(run.returncode, 0, run.stderr)
        svg = outputs['render/archive-archipelago-001.svg'].decode('utf-8')
        manifest = json.loads(outputs['render/build-manifest.json'])
        self.assertIn('304 FROZEN CREATIVE WORKS · 45 CATALOGUED RELATIONS', svg)
        self.assertIn('MEDIA / 137', svg)
        self.assertEqual(manifest['sourceWorkCount'], 304)
        self.assertEqual(manifest['ownerCounts']['Media'], 137)
        self.assertEqual(manifest['mappedRelationCount'], 45)

    def test_relation_change_updates_map_and_both_legend_paths(self):
        def drop_relation(catalog):
            catalog['relations'] = [
                r for r in catalog['relations']
                if (r.get('relation_type') or r.get('relationType') or r.get('type')) != 'DERIVATIVE_OF'
            ]

        run, outputs = self.run_fixture(drop_relation)
        self.assertEqual(run.returncode, 0, run.stderr)
        svg = outputs['render/archive-archipelago-001.svg'].decode('utf-8')
        manifest = json.loads(outputs['render/build-manifest.json'])
        self.assertIn('303 FROZEN CREATIVE WORKS · 10 CATALOGUED RELATIONS', svg)
        self.assertIn('DERIVATIVE_OF — 0', svg)
        self.assertIn('CONSUMER_OF — 10', svg)
        self.assertEqual(manifest['mappedRelationCount'], 10)
        self.assertEqual(manifest['relationTypes'], {'CONSUMER_OF': 10})

    def test_duplicate_work_identity_is_rejected(self):
        def duplicate(catalog):
            catalog['works'].append(dict(catalog['works'][0]))

        run, _ = self.run_fixture(duplicate)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('duplicate workId', run.stderr)

    def test_unknown_relation_endpoint_is_rejected(self):
        def orphan(catalog):
            row = dict(catalog['relations'][0])
            row['child_work_id'] = 'unknown:not-a-work'
            catalog['relations'].append(row)

        run, _ = self.run_fixture(orphan)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('unknown work', run.stderr)

    def test_unknown_relation_type_is_not_mislabelled(self):
        def unsupported(catalog):
            catalog['relations'][0]['relation_type'] = 'UNVERIFIED_DEPENDENCY'

        run, _ = self.run_fixture(unsupported)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('unsupported catalogued relation type', run.stderr)


if __name__ == '__main__':
    unittest.main()
