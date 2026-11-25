"""Operation-count and behavioral tests for the in-memory selector."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))
from ordivon_data.binding_selection import LocalEvidenceBinding, select_bindings


class CountedRow(dict):
    reads = 0

    def __getitem__(self, key):
        if key in ("name", "version"):
            CountedRow.reads += 1
        return super().__getitem__(key)


class BindingIndexTests(unittest.TestCase):
    @staticmethod
    def request(version, name, port_version):
        return LocalEvidenceBinding(
            "product",
            name,
            "path",
            "digest",
            ROOT,
            port_version=port_version,
            product_version=version,
        )

    def test_dense_requests_do_not_rescan_version_or_port_lists(self):
        size = 48
        products = [
            CountedRow(
                id="product",
                version=str(i),
                outputPorts=[
                    CountedRow(name=f"port-{j}", version="1", type="file/json")
                    for j in range(size)
                ],
            )
            for i in range(size)
        ]
        bindings = tuple(
            self.request(str(i), f"port-{j}", "1")
            for i in range(size)
            for j in range(size)
        )
        CountedRow.reads = 0
        selected = select_bindings(products, bindings)
        reads = CountedRow.reads
        self.assertEqual(
            [(i, j) for i, j, _ in selected],
            [(i, j) for i in range(size) for j in range(size)],
        )
        self.assertLessEqual(reads, 3 * size * size + 2 * size)

    def test_unversioned_port_not_counted_twice_and_ambiguity_preserved(self):
        products = [
            {
                "id": "product",
                "version": "1",
                "outputPorts": [
                    {"name": "a", "type": "file/json"},
                    {"name": "b", "version": "1", "type": "file/json"},
                    {"name": "b", "version": "2", "type": "file/json"},
                ],
            }
        ]
        a = self.request(None, "a", None)
        b = self.request("1", "b", "2")
        self.assertEqual(select_bindings(products, (a, b)), [(0, 0, a), (0, 2, b)])
        for request in (self.request("1", "b", None), self.request("1", "a", "1")):
            with self.assertRaises(ValueError):
                select_bindings(products, (request,))
        with self.assertRaisesRegex(ValueError, "duplicate local evidence"):
            select_bindings(products, (a, a))
