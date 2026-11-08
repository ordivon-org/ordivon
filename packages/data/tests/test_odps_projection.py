"""Actual domain ODPS source-bound consumers; no invented source file locations."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[3]
import sys

sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data.catalog import inspect_catalog
from ordivon_data.odps_projection import project_catalog


class OwnerProductProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sources = [
            ROOT / "domains/capital/data-products/crypto-public-shadow-r2/odps.json",
            ROOT / "catalogs/data-products/experimental-episode-corpus-r1/odps.json",
        ]

    def test_real_owner_products_project_to_dcat_without_fake_access(self) -> None:
        projected = project_catalog(self.sources)
        reversed_order = project_catalog(list(reversed(self.sources)))
        self.assertEqual(projected, reversed_order)
        self.assertEqual(len(projected["dcat:dataset"]), 2)
        self.assertEqual(
            sum(len(x["dcat:distribution"]) for x in projected["dcat:dataset"]), 3
        )
        self.assertTrue(
            all(
                "dcat:accessURL" not in dist and "dct:identifier" not in dist
                for product in projected["dcat:dataset"]
                for dist in product["dcat:distribution"]
            )
        )
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "catalog.jsonld"
            output.write_text(json.dumps(projected), encoding="utf-8")
            readback = inspect_catalog(output, verify_local=True, allowed_roots=(ROOT,))
            self.assertEqual(len(readback["products"]), 2)
            self.assertEqual(
                sum(len(p["distributions"]) for p in readback["products"]), 3
            )
            self.assertTrue(
                all(
                    dist["verification"] == "UNKNOWN"
                    for product in readback["products"]
                    for dist in product["distributions"]
                )
            )

    def test_duplicate_product_version_cannot_be_silently_overridden(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate owner product"):
            project_catalog([self.sources[0], self.sources[0]])

    def test_malformed_product_does_not_fall_back_to_unsafe_metadata(self) -> None:
        data = json.loads(self.sources[0].read_text(encoding="utf-8"))
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / "product.json"
            data["apiVersion"] = "v4.2.0"
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ODPS DataProduct v1.1.0"):
                project_catalog([file])
            data["apiVersion"] = "v1.1.0"
            # ODPS 1.1 port versions are independent of product versions.
            data["outputPorts"][0]["version"] = "port-v2"
            file.write_text(json.dumps(data), encoding="utf-8")
            projected = project_catalog([file])
            self.assertEqual(
                projected["dcat:dataset"][0]["dcat:distribution"][0]["dcat:version"],
                "port-v2",
            )

            # ODPS 1.1 port id and version are optional; do not mint identities.
            port = data["outputPorts"][0]
            port.pop("id")
            port.pop("version")
            file.write_text(json.dumps(data), encoding="utf-8")
            projected = project_catalog([file])
            distribution = projected["dcat:dataset"][0]["dcat:distribution"][0]
            self.assertNotIn("@id", distribution)
            self.assertNotIn("dcat:version", distribution)

            data["outputPorts"].append(dict(port))
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError, "duplicate output port name and version"
            ):
                project_catalog([file])
