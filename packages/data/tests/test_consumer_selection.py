"""Operation-count regression for the independent CLI consumer gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))
from ordivon_data.consumer_selection import select_ports


class Counted(dict):
    reads = 0

    def __getitem__(self, key):
        if key == "id":
            Counted.reads += 1
        return super().__getitem__(key)


class ConsumerSelectionTests(unittest.TestCase):
    def test_dense_catalog_observations_index_once(self):
        size = 48
        products = [
            Counted(
                id="owner",
                version=str(i),
                distributions=[
                    Counted(id=f"urn:port:{j}", verification="VERIFIED")
                    for j in range(size)
                ],
            )
            for i in range(size)
        ]
        requests = [
            ["owner", str(i), f"urn:port:{j}"] for i in range(size) for j in range(size)
        ]
        Counted.reads = 0
        results = select_ports(products, requests)
        self.assertEqual(len(results), size * size)
        self.assertTrue(all(row["verification"] == "VERIFIED" for row in results))
        self.assertLessEqual(Counted.reads, size * (size + 1))

    def test_exact_distribution_uri_opaque_product_and_version(self):
        products = [
            {
                "id": "Owner-A",
                "version": "1",
                "distributions": [
                    {"id": "urn:port:a", "verification": "FALSIFIED"},
                    {"id": "urn:port:b", "verification": "VERIFIED"},
                    {"id": None, "verification": "VERIFIED"},
                ],
            }
        ]
        requests = [
            ["Owner-A", "1", "urn:port:a"],
            ["Owner-A", "1", "urn:port:b"],
            ["owner-a", "1", "urn:port:b"],
            ["Owner-A", "2", "urn:port:b"],
            ["Owner-A", "1", "urn:port:B"],
        ]
        self.assertEqual(
            [r["verification"] for r in select_ports(products, requests)],
            ["FALSIFIED", "VERIFIED", "UNKNOWN", "UNKNOWN", "UNKNOWN"],
        )

    def test_ambiguous_selected_observation_rejects(self):
        product = {
            "id": "owner",
            "version": "1",
            "distributions": [
                {"id": "urn:port:a", "verification": "VERIFIED"},
                {"id": "urn:port:a", "verification": "FALSIFIED"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "ambiguous --require-port"):
            select_ports([product], [["owner", "1", "urn:port:a"]])
