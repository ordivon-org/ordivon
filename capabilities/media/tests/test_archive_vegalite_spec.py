"""Native source/visual fidelity tests for a real Media Production's Vega-Lite spec."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1] / 'productions' / 'archive-archipelago-001'
GENERATOR = PRODUCTION / 'generate_owner_summary_vegalite.py'
SOURCE = PRODUCTION / 'source' / 'creative-library-catalog-v1.json'


class VegaLiteArchiveConsumerTests(unittest.TestCase):
    def generate(self, source):
        return subprocess.run(
            ['python3', str(GENERATOR), '--source', str(source)],
            capture_output=True, text=True, check=False, timeout=20,
        )

    def test_frozen_catalog_is_mapped_to_true_owner_counts_and_digest(self):
        completed = self.generate(SOURCE)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        spec = json.loads(completed.stdout)
        self.assertEqual(spec['$schema'], 'https://vega.github.io/schema/vega-lite/v6.json')
        self.assertEqual(spec['data']['values'], [
            {'owner': 'Game', 'works': 33},
            {'owner': 'Media', 'works': 136},
            {'owner': 'Web', 'works': 56},
            {'owner': 'Workstation', 'works': 78},
        ])
        self.assertEqual(sum(row['works'] for row in spec['data']['values']), 303)
        self.assertEqual(spec['usermeta']['sourceWorkCount'], 303)
        self.assertEqual(spec['usermeta']['sourceRelationCount'], 45)
        self.assertEqual(spec['usermeta']['sourceSha256'],
                         'sha256:' + hashlib.sha256(SOURCE.read_bytes()).hexdigest())
        self.assertEqual(completed.stdout, self.generate(SOURCE).stdout)

    def test_changed_owner_data_updates_spec_without_rewriting_map(self):
        catalog = json.loads(SOURCE.read_text(encoding='utf-8'))
        moved = catalog['works'][0]
        original = moved['owner']
        replacement = 'Web' if original != 'Web' else 'Game'
        moved['owner'] = replacement
        with tempfile.TemporaryDirectory() as temp:
            new_source = Path(temp) / 'changed.json'
            new_source.write_text(json.dumps(catalog), encoding='utf-8')
            completed = self.generate(new_source)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        spec = json.loads(completed.stdout)
        counts = {row['owner']: row['works'] for row in spec['data']['values']}
        self.assertEqual(counts[original], {'Game': 33, 'Media': 136, 'Web': 56, 'Workstation': 78}[original] - 1)
        self.assertEqual(counts[replacement], {'Game': 33, 'Media': 136, 'Web': 56, 'Workstation': 78}[replacement] + 1)
        self.assertEqual(sum(counts.values()), 303)
        self.assertNotEqual(spec['usermeta']['sourceSha256'],
                            'sha256:' + hashlib.sha256(SOURCE.read_bytes()).hexdigest())

    def test_rejects_orphan_relation_instead_of_rendering_false_fact(self):
        catalog = json.loads(SOURCE.read_text(encoding='utf-8'))
        catalog['relations'][0]['parent_work_id'] = 'nonexistent-archive-work'
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'bad.json'
            source.write_text(json.dumps(catalog), encoding='utf-8')
            completed = self.generate(source)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('unknown work', completed.stderr)


if __name__ == '__main__':
    unittest.main()
