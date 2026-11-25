"""Catalog-wide structural preflight, independent of physical observations."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))
from ordivon_data.catalog import inspect_catalog, inspect_distribution


class CatalogAdmissionTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        data = self.root / "data.json"
        data.write_bytes(b"known")
        self.digest = "sha256:" + hashlib.sha256(b"known").hexdigest()
        self.dist = {
            "@id": "urn:uuid:4664e208-2cdc-5d4f-a83d-e70e187b046a",
            "dcat:accessURL": {"@id": data.as_uri()},
            "dct:identifier": self.digest,
        }
        self.product = {
            "@type": "dcat:Dataset",
            "dct:identifier": "4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b",
            "dcat:version": "1.0.0",
            "dcat:distribution": [self.dist],
        }

    def inspect(self, products, verify=True):
        file = self.root / "catalog.jsonld"
        file.write_text(json.dumps({"@type": "dcat:Catalog", "dcat:dataset": products}))
        return inspect_catalog(file, verify_local=verify, allowed_roots=(self.root,))

    def test_canonical_product_alias_rejects_before_io(self):
        alias = copy.deepcopy(self.product)
        alias["dct:identifier"] = alias["dct:identifier"].upper()
        for rows in ([self.product, alias], [alias, self.product]):
            with patch(
                "ordivon_data.catalog.scoped_sha256",
                return_value=(self.digest[7:], "observed"),
            ) as observe:
                with self.assertRaisesRegex(
                    ValueError, "duplicate data product identity"
                ):
                    self.inspect(rows)
                observe.assert_not_called()

    def test_later_structural_failure_does_not_read_earlier_distribution(self):
        for invalid in (
            {"@type": "unknown"},
            {
                **self.product,
                "dcat:version": "2",
                "dcat:distribution": [self.dist, self.dist],
            },
            {
                **self.product,
                "dcat:version": "2",
                "dcat:distribution": [
                    {**self.dist, "spdx:checksum": {"@type": "wrong"}}
                ],
            },
        ):
            with patch(
                "ordivon_data.catalog.scoped_sha256",
                return_value=(self.digest[7:], "observed"),
            ) as observe:
                with self.assertRaises(ValueError):
                    self.inspect([self.product, invalid])
                observe.assert_not_called()

    def test_independent_versions_still_observed(self):
        other = {**self.product, "dcat:version": "2.0.0"}
        result = self.inspect([self.product, other])
        expected = inspect_distribution(self.dist, (self.root,), True)
        self.assertEqual(
            [row["distributions"] for row in result["products"]],
            [[expected], [expected]],
        )

    def test_opaque_identity_not_casefolded(self):
        rows = [
            {**self.product, "dct:identifier": identity}
            for identity in ("Owner-A", "owner-a")
        ]
        result = self.inspect(rows, verify=False)
        self.assertEqual([p["id"] for p in result["products"]], ["Owner-A", "owner-a"])
        self.assertTrue(
            all(
                p["distributions"][0]["verification"] == "NOT_CHECKED"
                for p in result["products"]
            )
        )
