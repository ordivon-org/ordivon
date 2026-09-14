from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import authority_catalog as catalog


class AuthorityCatalogTests(unittest.TestCase):
    def test_build_is_deterministic_and_sorted(self):
        first = catalog.build_index()
        second = catalog.build_index()
        self.assertEqual(first, second)
        ids = [x["id"] for x in first["entries"]]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(first["recordCount"], len(ids))

    def test_progressive_disclosure_keeps_source_out_of_index(self):
        index = catalog.build_index()
        self.assertNotIn("officialSource", index["entries"][0])
        _, record = catalog.get_record("iso-31000-2018")
        self.assertIn("officialSource", record["identity"])

    def test_task_local_semantics_do_not_leak_into_records(self):
        for authority_id, (_, record) in catalog.records().items():
            self.assertEqual(catalog.forbidden_fields(record), [], authority_id)

    def test_lexical_find_prefers_exact_semantics_without_vector_index(self):
        rows = catalog.build_index()["entries"]
        ranked = sorted(((catalog.score_entry(row, "risk management"), row["id"]) for row in rows), key=lambda x: (-x[0], x[1]))
        self.assertEqual(ranked[0][1], "iso-31000-2018")
        ranked = sorted(((catalog.score_entry(row, "software supply chain"), row["id"]) for row in rows), key=lambda x: (-x[0], x[1]))
        self.assertIn(ranked[0][1], {"slsa-1.2", "nist-sp-800-218-ssdf-1.1"})

    def test_latest_observation_is_append_only_date_selection(self):
        latest = catalog.latest_observation("iso-9001-2026")
        self.assertIsNotNone(latest)
        self.assertEqual(latest[1]["observedDate"], "2026-09-14")
        self.assertEqual(latest[1]["lifecycleStatus"], "under-publication")

    def test_refresh_is_a_plan_not_mutation(self):
        _, record = catalog.get_record("iso-31000-2018")
        before = json.dumps(record, sort_keys=True)
        # The CLI implementation is intentionally read-only; rebuilding the plan uses loaded source only.
        latest = catalog.latest_observation("iso-31000-2018")
        self.assertIsNotNone(latest)
        after = json.dumps(catalog.get_record("iso-31000-2018")[1], sort_keys=True)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
