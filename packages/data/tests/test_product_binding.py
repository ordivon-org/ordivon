"""Actual product metadata with two independently bound versions."""

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
from ordivon_data.local_evidence import LocalEvidenceBinding
from ordivon_data.odps_projection import project_catalog, project_odps


class ProductBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = (
            ROOT / "catalogs/data-products/experimental-episode-corpus-r1/odps.json"
        )
        original = json.loads(source.read_bytes())
        self.versions = []
        for version in ("1.0.0", "2.0.0"):
            product = copy.deepcopy(original)
            product["version"] = version
            payload = version.encode()
            path = self.root / (version + ".json")
            path.write_bytes(payload)
            for prop in product["customProperties"]:
                if prop["property"] == "corpusManifestRelativePath":
                    prop["value"] = path.name
                if prop["property"] == "corpusManifestSha256":
                    prop["value"] = hashlib.sha256(payload).hexdigest()
            self.versions.append(product)
        self.id = original["id"]

    def binding(self, **kwargs):
        return LocalEvidenceBinding(
            self.id,
            "episode-corpus-manifest-json",
            "corpusManifestRelativePath",
            "corpusManifestSha256",
            self.root,
            port_version="1.0.0",
            **kwargs,
        )

    def sources(self):
        return [json.dumps(product).encode() for product in self.versions]

    def test_ambiguous_legacy_binding_rejects_before_file_observation(self):
        for order, sources in enumerate(
            (self.sources(), list(reversed(self.sources())))
        ):
            with (
                self.subTest(order=order),
                patch("ordivon_data.local_evidence.scoped_sha256") as observe,
            ):
                with self.assertRaisesRegex(
                    ValueError, "product version|product identity"
                ):
                    project_catalog(sources, bindings=(self.binding(),))
                observe.assert_not_called()

    def test_exact_version_binds_only_one_product_independent_of_order(self):
        sources = self.sources()
        selected = self.binding(product_version="2.0.0")
        result = project_catalog(sources, bindings=(selected,))
        self.assertEqual(result, project_catalog(sources[::-1], bindings=(selected,)))
        rows = {
            p["dcat:version"]: p["dcat:distribution"] for p in result["dcat:dataset"]
        }
        self.assertFalse(any("spdx:checksum" in d for d in rows["1.0.0"]))
        checksums = [
            d["spdx:checksum"]["spdx:checksumValue"]["@value"]
            for d in rows["2.0.0"]
            if "spdx:checksum" in d
        ]
        self.assertEqual(checksums, [hashlib.sha256(b"2.0.0").hexdigest()])

    def test_missing_and_duplicate_targets_reject_before_file_observation(self):
        good = self.binding(product_version="1.0.0")
        missing = self.binding(product_version="3.0.0")
        for bindings in ((good, missing), (good, good)):
            with (
                self.subTest(bindings=bindings),
                patch("ordivon_data.local_evidence.scoped_sha256") as observe,
            ):
                with self.assertRaises(ValueError):
                    project_catalog(self.sources(), bindings=bindings)
                observe.assert_not_called()

    def test_single_snapshot_direct_api_rejects_wrong_version(self):
        with patch("ordivon_data.local_evidence.scoped_sha256") as observe:
            with self.assertRaisesRegex(ValueError, "product version|product identity"):
                project_odps(
                    self.sources()[0], bindings=(self.binding(product_version="2.0.0"),)
                )
            observe.assert_not_called()

    def test_cli_exact_version_and_legacy_ambiguity(self):
        command = [
            sys.executable,
            str(ROOT / "packages/data/scripts/project_owned_products.py"),
        ]
        for i, source in enumerate(self.sources()):
            path = self.root / f"metadata-{i}.json"
            path.write_bytes(source)
            command.extend(["--product", str(path)])
        tail = ["corpusManifestRelativePath", "corpusManifestSha256", str(self.root)]
        legacy = subprocess.run(
            command + ["--bind-local", self.id, "episode-corpus-manifest-json", *tail],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(legacy.returncode, 2)
        self.assertIn("product version", legacy.stderr)
        self.assertEqual(legacy.stdout, "")
        exact = subprocess.run(
            command
            + [
                "--bind-local-versioned",
                self.id,
                "2.0.0",
                "episode-corpus-manifest-json",
                "1.0.0",
                *tail,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(exact.returncode, 0, exact.stderr)
        result = json.loads(exact.stdout)
        self.assertEqual(
            result,
            project_catalog(
                self.sources(), bindings=(self.binding(product_version="2.0.0"),)
            ),
        )

    def test_independent_versions_both_bind(self):
        bindings = tuple(self.binding(product_version=v) for v in ("1.0.0", "2.0.0"))
        result = project_catalog(self.sources(), bindings=bindings)
        self.assertEqual(
            result, project_catalog(self.sources()[::-1], bindings=bindings[::-1])
        )
        for entry in result["dcat:dataset"]:
            checksums = [
                d["spdx:checksum"]["spdx:checksumValue"]["@value"]
                for d in entry["dcat:distribution"]
                if "spdx:checksum" in d
            ]
            self.assertEqual(
                checksums, [hashlib.sha256(entry["dcat:version"].encode()).hexdigest()]
            )

    def test_all_targets_qualified_before_first_file_read(self):
        good = self.binding(product_version="1.0.0")
        bad_port = LocalEvidenceBinding(
            self.id,
            "nonexistent",
            good.path_property,
            good.digest_property,
            self.root,
            product_version="2.0.0",
        )
        with patch("ordivon_data.local_evidence.scoped_sha256") as observe:
            with self.assertRaisesRegex(ValueError, "named output port"):
                project_catalog(self.sources(), bindings=(good, bad_port))
            observe.assert_not_called()

    def test_uuid_alias_cannot_escape_ambiguity_check(self):
        self.versions[1]["id"] = self.id.upper()
        with patch("ordivon_data.local_evidence.scoped_sha256") as observe:
            with self.assertRaisesRegex(ValueError, "product version|product identity"):
                project_catalog(self.sources(), bindings=(self.binding(),))
            observe.assert_not_called()

    def test_producer_surrogate_path_rejected_before_native_read(self):
        product = self.versions[0]
        for prop in product["customProperties"]:
            if prop["property"] == "corpusManifestRelativePath":
                prop["value"] = "evidence-\udc80"
        with patch("ordivon_data.local_evidence.scoped_sha256") as observe:
            with self.assertRaisesRegex(ValueError, "non-Unicode scalar"):
                project_odps(
                    json.dumps(product).encode(),
                    bindings=(self.binding(product_version="1.0.0"),),
                )
            observe.assert_not_called()

    def test_all_metadata_declarations_qualified_before_any_file_read(self):
        bindings = tuple(self.binding(product_version=v) for v in ("1.0.0", "2.0.0"))
        invalid = (
            ("corpusManifestSha256", "not-a-digest"),
            ("corpusManifestRelativePath", "../escape.json"),
            ("corpusManifestRelativePath", "invalid\x00path"),
            ("corpusManifestRelativePath", "invalid\ud800path"),
            ("corpusManifestRelativePath", "/absolute.json"),
        )
        for property_name, value in invalid:
            for index in (0, 1):
                products = copy.deepcopy(self.versions)
                for prop in products[index]["customProperties"]:
                    if prop["property"] == property_name:
                        prop["value"] = value
                sources = [json.dumps(p).encode() for p in products]
                with (
                    self.subTest(
                        property_name=property_name, value=ascii(value), index=index
                    ),
                    patch(
                        "ordivon_data.local_evidence.scoped_sha256",
                        side_effect=lambda path, *args, **kwargs: (
                            hashlib.sha256(path.stem.encode()).hexdigest(),
                            "observed",
                        ),
                    ) as observe,
                ):
                    with self.assertRaises(ValueError):
                        project_catalog(sources, bindings=bindings)
                    observe.assert_not_called()

    def test_late_missing_or_duplicate_property_never_reads_earlier_product(self):
        bindings = tuple(self.binding(product_version=v) for v in ("1.0.0", "2.0.0"))
        for duplicate in (False, True):
            products = copy.deepcopy(self.versions)
            props = products[1]["customProperties"]
            found = next(p for p in props if p["property"] == "corpusManifestSha256")
            if duplicate:
                props.append(found.copy())
            else:
                props.remove(found)
            with (
                self.subTest(duplicate=duplicate),
                patch(
                    "ordivon_data.local_evidence.scoped_sha256",
                    return_value=(hashlib.sha256(b"1.0.0").hexdigest(), "observed"),
                ) as observe,
            ):
                with self.assertRaisesRegex(
                    ValueError, "missing or ambiguous producer property"
                ):
                    project_catalog(
                        [json.dumps(p).encode() for p in products], bindings=bindings
                    )
                observe.assert_not_called()

    def test_invalid_projected_unicode_is_rejected_before_file_io(self):
        fields = (
            ("id",),
            ("version",),
            ("name",),
            ("description", "purpose"),
            ("outputPorts", 0, "name"),
            ("outputPorts", 0, "id"),
            ("outputPorts", 0, "version"),
        )
        for fieldspec in fields:
            products = copy.deepcopy(self.versions)
            parent = products[1]
            for key in fieldspec[:-1]:
                parent = parent[key]
            parent[fieldspec[-1]] = "bad\ud800"
            with (
                self.subTest(fieldspec=fieldspec),
                patch(
                    "ordivon_data.local_evidence.scoped_sha256",
                    return_value=(hashlib.sha256(b"1.0.0").hexdigest(), "observed"),
                ) as observe,
            ):
                with self.assertRaisesRegex(ValueError, "non-Unicode scalar"):
                    project_catalog(
                        [json.dumps(p).encode() for p in products],
                        bindings=(self.binding(product_version="1.0.0"),),
                    )
                observe.assert_not_called()

    def test_invalid_governance_policy_unicode_is_rejected(self):
        product = copy.deepcopy(self.versions[0])
        for prop in product["customProperties"]:
            if prop["property"] == "governancePolicyUid":
                prop["value"] = "urn:bad:\ud800"
        with patch("ordivon_data.local_evidence.scoped_sha256") as observe:
            with self.assertRaisesRegex(ValueError, "non-Unicode scalar"):
                project_odps(
                    json.dumps(product).encode(),
                    bindings=(self.binding(product_version="1.0.0"),),
                )
            observe.assert_not_called()

    def test_projector_cli_invalid_text_rejects_and_valid_unicode_serializes(self):
        product = copy.deepcopy(self.versions[0])
        path = self.root / "unicode-metadata.json"
        command = [
            sys.executable,
            str(ROOT / "packages/data/scripts/project_owned_products.py"),
            "--product",
            str(path),
        ]
        product["name"] = "bad\ud800"
        path.write_text(json.dumps(product))
        bad = subprocess.run(
            command,
            capture_output=True,
            check=False,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "utf-8:strict"},
        )
        self.assertEqual(bad.returncode, 2, bad.stderr)
        self.assertNotIn(b"Traceback", bad.stderr)
        self.assertEqual(bad.stdout, b"")
        product["name"] = "数据产品"
        path.write_text(json.dumps(product))
        good = subprocess.run(
            command,
            capture_output=True,
            check=False,
            timeout=20,
            env={**os.environ, "PYTHONIOENCODING": "ascii:strict"},
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(
            json.loads(good.stdout)["dcat:dataset"][0]["dct:title"], product["name"]
        )
