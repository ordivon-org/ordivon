from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/repo/dependency_surface.py"
SPEC = importlib.util.spec_from_file_location("dependency_surface", MODULE)
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class DependencySurfaceTests(unittest.TestCase):
    def test_report_is_source_projection_with_explicit_nonclaims(self) -> None:
        value = M.build_report(ROOT)
        self.assertEqual(value["schemaVersion"], 1)
        self.assertEqual(value["kind"], "ordivon-dependency-surface-r1")
        self.assertEqual(value["truthRole"], M.TRUTH_ROLE)
        self.assertEqual(len(value["sourceCut"]), 40)
        self.assertTrue(value["nonClaims"])
        for name in M.MANIFEST_NAMES:
            self.assertIn(name, value["manifestCounts"])

    def test_all_declared_uv_consumers_follow_latest_channel(self) -> None:
        value = M.build_report(ROOT)
        self.assertTrue(value["toolPolicy"]["uv"])
        self.assertTrue(
            value["toolPolicy"]["allDeclaredUvUseLatest"],
            value["toolPolicy"]["uv"],
        )

    def test_artifact_delivery_is_exact_production_dependency_projection(self) -> None:
        value = M.artifact_python_projection(ROOT)
        self.assertTrue(value["directProductionDependenciesEqual"], value)
        self.assertTrue(value["deliveryThirdPartySubsetOfOwner"], value)
        self.assertEqual(value["deliveryThirdPartyDrift"], {})
        self.assertGreater(value["deliveryThirdPartyPackageCount"], 0)

    def test_runtime_legacy_detector_matches_native_cargo_features(self) -> None:
        value = M.runtime_legacy_surface(ROOT)
        core = tomllib.loads(
            (ROOT / "services/runtime/crates/ordivon-runtime-core/Cargo.toml").read_text()
        )
        mcp = tomllib.loads(
            (ROOT / "services/runtime/crates/ordivon-runtime-mcp/Cargo.toml").read_text()
        )
        self.assertEqual(
            value["transactionalRuntimeUsesRusqlite"],
            "dep:rusqlite" in core["features"].get("transactional-runtime", []),
        )
        self.assertEqual(
            value["legacyMcpReachTransactionalRuntime"],
            "ordivon-runtime-core/transactional-runtime"
            in mcp["features"].get("legacy-runtime", []),
        )
        self.assertFalse(value["sourceRetirementEligible"])
        self.assertIn("installed", value["retirementEligibilityReason"])


    def test_dirty_and_index_changes_do_not_mislabel_committed_projection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            def git(*args):
                return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)
            def write(path, value):
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(value, encoding="utf-8")
            git("init", "-q")
            git("config", "user.name", "Projection Fixture")
            git("config", "user.email", "fixture@example.invalid")
            write("mise.toml", '[tools]\nuv = "0.1"\n')
            for path in ("capabilities/artifact", "capabilities/artifact/artifact-delivery/python-uv"):
                write(path + "/pyproject.toml", '[project]\ndependencies = ["demo"]\n')
                write(path + "/uv.lock", '[[package]]\nname = "demo"\nversion = "1"\nsource = {registry = "https://example.invalid"}\n')
            for name in ("ordivon-runtime-core", "ordivon-runtime-mcp"):
                write("services/runtime/crates/" + name + "/Cargo.toml", "[features]\ndefault = []\n")
            git("add", ".")
            git("commit", "-qm", "baseline")
            first = M.build_report(root)
            write("mise.toml", '[tools]\nuv = "latest"\n')
            write("nested/mise.toml", '[tools]\nuv = "latest"\n')
            git("add", "nested/mise.toml")
            write("capabilities/artifact/artifact-delivery/python-uv/uv.lock", '[[package]]\nname = "demo"\nversion = "2"\nsource = {registry = "https://example.invalid"}\n')
            self.assertEqual(M.build_report(root), first)
            self.assertEqual(first["sourceMode"], "committed-git-tree")
            git("add", ".")
            git("commit", "-qm", "new source cut")
            second = M.build_report(root)
            self.assertNotEqual(second["sourceCut"], first["sourceCut"])
            self.assertEqual(second["manifestCounts"]["mise.toml"], 2)
            self.assertTrue(second["toolPolicy"]["allDeclaredUvUseLatest"])
            self.assertFalse(second["artifactPythonProjection"]["deliveryThirdPartySubsetOfOwner"])


if __name__ == "__main__":
    unittest.main()
