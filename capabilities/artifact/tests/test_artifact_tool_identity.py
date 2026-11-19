"""Negative and positive controls for post-run executable observations."""
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from artifact_verification.tool_identity import assess_native_tool_paths


class NativeToolIdentityTests(unittest.TestCase):
    def test_reported_executable_digest_matches_independent_postrun_fact(self):
        with tempfile.TemporaryDirectory() as d:
            binary = Path(d) / "decoder"
            binary.write_bytes(b"first-version")
            sha = hashlib.sha256(binary.read_bytes()).hexdigest()
            report = assess_native_tool_paths({
                "tools": {"decoder": {"path": str(binary), "sha256": sha}},
            })
            self.assertEqual(report["status"], "OBSERVED_POSTRUN_CONSISTENT")
            self.assertFalse(report["rejected"])
            self.assertFalse(report["dependenciesComplete"])
            self.assertEqual(report["observed"]["decoder"]["size"], binary.stat().st_size)

    def test_replaced_executable_is_a_contradiction(self):
        with tempfile.TemporaryDirectory() as d:
            binary = Path(d) / "decoder"
            binary.write_bytes(b"first-version")
            sha = hashlib.sha256(binary.read_bytes()).hexdigest()
            binary.write_bytes(b"replaced-version")
            report = assess_native_tool_paths({
                "tools": {"decoder": {"path": str(binary), "sha256": sha}},
            })
            self.assertTrue(report["rejected"])
            self.assertEqual(report["status"], "CONTRADICTORY")
            self.assertIn(
                "native tool digest drift after verification: decoder", report["issues"]
            )

    def test_package_root_manifest_is_observed_without_claiming_dependency_closure(self):
        with tempfile.TemporaryDirectory() as d:
            package_root = Path(d) / "playwright"
            package_root.mkdir()
            manifest = package_root / "package.json"
            manifest.write_bytes(b'{"version":"1.63.0"}')
            original = hashlib.sha256(manifest.read_bytes()).hexdigest()
            fact = {"path": str(package_root), "packageJsonSha256": original}

            result = assess_native_tool_paths({"tools": {"nodePackageRoot": fact}})
            self.assertFalse(result["rejected"], result)
            self.assertEqual(result["status"], "OBSERVED_POSTRUN_CONSISTENT")
            self.assertFalse(result["dependenciesComplete"])
            self.assertEqual(
                result["observed"]["nodePackageRoot"]["identityScope"], "PACKAGE_JSON_ONLY"
            )
            self.assertEqual(
                result["observed"]["nodePackageRoot"]["path"], str(manifest)
            )

            manifest.write_bytes(b'{"version":"changed"}')
            drift = assess_native_tool_paths({"tools": {"nodePackageRoot": fact}})
            self.assertTrue(drift["rejected"])
            self.assertIn(
                "native tool digest drift after verification: nodePackageRoot",
                drift["issues"],
            )

    def test_unknown_and_malformed_tool_evidence(self):
        for native in ({}, {"tools": None}, {"tools": {}}):
            report = assess_native_tool_paths(native)
            self.assertEqual(report["status"], "NOT_EVALUATED")
            self.assertFalse(report["rejected"])
        for native in (
            {"tools": []},
            {"tools": {"decoder": {"path": "relative", "sha256": "0" * 64}}},
            {"tools": {"decoder": {"path": "/missing/tool"}}},
            {"tools": {"decoder": "not-a-fact"}},
            {"tools": {1: {"path": "/missing/tool"}, "decoder": {"path": "/missing/tool"}}},
        ):
            with self.subTest(native=native):
                report = assess_native_tool_paths(native)
                self.assertTrue(report["rejected"])
                self.assertEqual(report["status"], "CONTRADICTORY")


if __name__ == "__main__":
    unittest.main()
