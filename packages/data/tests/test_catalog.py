from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

DATA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DATA_ROOT.parents[1]
sys.path.insert(0, str(DATA_ROOT / "src"))

from ordivon_data.catalog import inspect_catalog, inspect_distribution


class CatalogProjectionTests(TestCase):
    def test_existing_three_product_federation_is_discovered_without_promoting_truth(
        self,
    ):
        path = (
            REPO_ROOT
            / "studies/data-lifecycle/evidence/data-products-r2/federated-catalog.dcat.jsonld"
        )
        result = inspect_catalog(path)
        self.assertEqual(len(result["products"]), 3)
        self.assertEqual(sum(len(p["distributions"]) for p in result["products"]), 4)
        self.assertTrue(
            all(
                d["verification"] == "NOT_CHECKED"
                for p in result["products"]
                for d in p["distributions"]
            )
        )
        self.assertIn("not_domain_truth", result["scope"])

    def test_valid_scoped_file_digest_is_verified_and_mismatch_is_falsified(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.json"
            source.write_bytes(b'{"observed":true}')
            correct = hashlib.sha256(source.read_bytes()).hexdigest()
            dist = {
                "@id": "urn:fixture:data",
                "dcat:accessURL": {"@id": source.as_uri()},
                "dct:identifier": "sha256:" + correct,
            }
            self.assertEqual(
                inspect_distribution(dist, (root,), True)["verification"], "VERIFIED"
            )
            source.write_bytes(b'{"observed":false}')
            self.assertEqual(
                inspect_distribution(dist, (root,), True)["verification"], "FALSIFIED"
            )

    def test_missing_and_external_files_remain_unknown(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = {"dcat:accessURL": {"@id": (root / "missing.csv").as_uri()}}
            observed = inspect_distribution(missing, (root,), True)
            self.assertEqual(
                (observed["verification"], observed["reason"]),
                ("UNKNOWN", "local_file_unavailable"),
            )
            invalid = {
                "dcat:accessURL": {
                    "@id": "file://studies/experimental-episodes/evidence/corpus-r1/manifest.json"
                }
            }
            self.assertEqual(
                inspect_distribution(invalid, (root,), True)["reason"],
                "unsupported_uri_or_authority",
            )
            remote = {"dcat:accessURL": {"@id": "https://example.org/data.csv"}}
            self.assertEqual(
                inspect_distribution(remote, (root,), True)["verification"], "UNKNOWN"
            )
            offscope = {"dcat:accessURL": {"@id": (root / "elsewhere.csv").as_uri()}}
            self.assertEqual(
                inspect_distribution(offscope, (root.parent / "nope",), True)["reason"],
                "outside_explicit_scope",
            )

    def test_non_catalog_projection_is_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "not-catalog.json"
            path.write_text(json.dumps({"@type": "dcat:Dataset"}))
            with self.assertRaises(ValueError):
                inspect_catalog(path)

    def test_duplicate_product_version_and_malformed_distribution_fail(self):
        source = (
            REPO_ROOT
            / "studies/data-lifecycle/evidence/data-products-r2/federated-catalog.dcat.jsonld"
        )
        catalog = json.loads(source.read_text(encoding="utf-8"))
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "catalog.json"
            catalog["dcat:dataset"].append(dict(catalog["dcat:dataset"][0]))
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate data product"):
                inspect_catalog(path)

            catalog["dcat:dataset"].pop()
            catalog["dcat:dataset"][0]["dcat:distribution"] = [None]
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(TypeError, "list of objects"):
                inspect_catalog(path)

            catalog["dcat:dataset"][0]["dcat:distribution"] = []
            catalog["dcat:dataset"][0].pop("dcat:version")
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "identifier and version"):
                inspect_catalog(path)
