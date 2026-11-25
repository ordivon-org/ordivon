"""Catalog-wide structural preflight, independent of physical observations."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
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

    def test_raw_surrogate_locator_never_maps_to_native_byte_filename(self):
        # POSIX surrogateescape can reopen a real non-UTF-8 filename.
        if os.name != "posix":
            self.skipTest("POSIX surrogateescape filename fixture")
        name = "evidence-\udc80"
        (self.root / name).write_bytes(b"known")
        for suffix in (name, "evidence-\ud800", "evidence-\udfff"):
            with self.subTest(suffix=ascii(suffix)):
                dist = {
                    **self.dist,
                    "dcat:accessURL": {"@id": self.root.as_uri() + "/" + suffix},
                }
                result = inspect_distribution(dist, (self.root,), True)
                self.assertEqual(result["verification"], "UNKNOWN")
                self.assertNotIn("observedDigest", result)

    def test_catalog_cli_preserves_invalid_locator_as_json_unknown(self):
        for suffix in ("evidence-\udc80", "evidence-\ud800"):
            with self.subTest(suffix=ascii(suffix)):
                dist = {
                    **self.dist,
                    "dcat:accessURL": {"@id": self.root.as_uri() + "/" + suffix},
                }
                product = {**self.product, "dcat:distribution": [dist]}
                path = self.root / "catalog.jsonld"
                path.write_text(
                    json.dumps({"@type": "dcat:Catalog", "dcat:dataset": [product]})
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "packages/data/scripts/inspect_federation.py"),
                        "--catalog",
                        str(path),
                        "--allow-root",
                        str(self.root),
                        "--verify-local",
                        "--require-verified",
                    ],
                    capture_output=True,
                    check=False,
                    timeout=20,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
                )
                self.assertEqual(result.returncode, 3, result.stderr)
                report = json.loads(result.stdout.decode("utf-8"))
                row = report["products"][0]["distributions"][0]
                self.assertEqual(row["verification"], "UNKNOWN")
                self.assertEqual(row["uri"], dist["dcat:accessURL"]["@id"])

    def test_valid_utf8_percent_encoded_locator_still_verifies(self):
        path = self.root / "数据 space#%.json"
        path.write_bytes(b"known")
        result = inspect_distribution(
            {**self.dist, "dcat:accessURL": {"@id": path.as_uri()}}, (self.root,), True
        )
        self.assertEqual(result["verification"], "VERIFIED")

    def test_cli_product_uuid_alias_selects_same_exact_port(self):
        path = self.root / "catalog.jsonld"
        path.write_text(
            json.dumps({"@type": "dcat:Catalog", "dcat:dataset": [self.product]})
        )
        cmd = [
            sys.executable,
            str(ROOT / "packages/data/scripts/inspect_federation.py"),
            "--catalog",
            str(path),
            "--allow-root",
            str(self.root),
            "--verify-local",
        ]
        pid = self.product["dct:identifier"]
        for alias in (pid, pid.upper(), pid.replace("-", "")):
            result = subprocess.run(
                cmd + ["--require-port", alias, "1.0.0", self.dist["@id"]],
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(result.stdout)["inspection"]["selectedPorts"][0][
                    "verification"
                ],
                "VERIFIED",
            )
        # An exact distribution URN and exact version remain required.
        result = subprocess.run(
            cmd + ["--require-port", pid, "2.0.0", self.dist["@id"]],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(result.returncode, 3, result.stderr)

    def test_cli_duplicate_uuid_alias_requests_reject_before_catalog_read(self):
        pid = self.product["dct:identifier"]
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "packages/data/scripts/inspect_federation.py"),
                "--catalog",
                str(self.root / "missing.jsonld"),
                "--verify-local",
                "--require-port",
                pid,
                "1.0.0",
                self.dist["@id"],
                "--require-port",
                pid.upper(),
                "1.0.0",
                self.dist["@id"],
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate --require-port", result.stderr)
        self.assertNotIn("catalog inspection failed", result.stderr)
