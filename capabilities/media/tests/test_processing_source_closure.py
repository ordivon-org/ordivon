"""Qualify the declared local source closure, not the installed environment."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.agent_processing import processing_profiles
from ordivon_studio.agent_surface import execute_surface_action

ROOT = Path(__file__).resolve().parents[1]


class ProcessingSourceClosureTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        shutil.copytree(ROOT / "processing/bin", self.root / "processing/bin")
        shutil.copytree(ROOT / "processing/profiles", self.root / "processing/profiles")
        for name in ("mise.toml", ".python-version"):
            shutil.copyfile(ROOT / name, self.root / name)
        self.input = self.root / "input.ttml"
        self.input.write_bytes((ROOT / "productions/runtime-introduction/timed-text/standard/narration.en.ttml").read_bytes())

    def discover(self, kind="timed-text"):
        return next(row for row in processing_profiles(self.root)["profiles"]
                    if row["profileKind"] == f"ordivon.media.v2.{kind}-profile")

    def compile(self, row, *, select=True, bind_input=True, **overrides):
        args = {
            "profileId": row["id"], "expectedProfileDigest": row["profileDigest"],
            "expectedAdapterDigest": row["adapterDigest"], "inputPath": str(self.input),
            "evidenceDirectory": "out/attempt/evidence",
        }
        if select:
            args["expectedSourceClosureDigest"] = row["sourceClosureDigest"]
        if bind_input:
            args["expectedInputDigest"] = "sha256:" + hashlib.sha256(self.input.read_bytes()).hexdigest()
        return execute_surface_action("studio_processing_probe_plan", {**args, **overrides}, root=self.root)

    def test_wrapper_and_toolchain_drift_change_selected_source_not_entry_digest(self):
        row = self.discover()
        initial = self.compile(row)
        self.assertEqual(initial["sourceClosureBinding"]["status"], "caller-selected")
        expected_paths = {
            "processing/bin/probe-timed-text.sh", "processing/bin/ttconv-pinned.sh",
            "processing/profiles/timed-text-runtime-introduction-en.json", "mise.toml", ".python-version",
        }
        self.assertEqual({item["path"] for item in row["sourceDependencies"]}, expected_paths)
        native = {item["path"]: item["expectedDigest"] for item in initial["execution"]["hostDependencies"]}
        self.assertEqual(len(native), 6)
        for item in row["sourceDependencies"]:
            path = self.root / item["path"]
            self.assertEqual(native[str(path.resolve())], "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest())
        for relative in ("processing/bin/ttconv-pinned.sh", "mise.toml", ".python-version"):
            with self.subTest(relative=relative):
                old = self.discover()
                path = self.root / relative
                path.write_bytes(path.read_bytes() + b"\n# changed selection\n")
                new = self.discover()
                self.assertEqual(old["adapterDigest"], new["adapterDigest"])
                self.assertEqual(old["profileDigest"], new["profileDigest"])
                self.assertNotEqual(old["sourceClosureDigest"], new["sourceClosureDigest"])
                with self.assertRaisesRegex(ValueError, "source closure digest changed"):
                    self.compile(old)
                self.assertEqual(self.compile(new)["sourceClosureBinding"]["digest"], new["sourceClosureDigest"])
        with self.assertRaisesRegex(ValueError, "invalid arguments"):
            self.compile(row, expectedSourceClosureDigest="bad")

    def test_missing_dependency_is_visible_but_not_admissible(self):
        before = self.discover()
        (self.root / "processing/bin/ttconv-pinned.sh").unlink()
        after = self.discover()
        self.assertIsNone(after["sourceClosureDigest"])
        self.assertTrue(after["adapterPresent"])
        self.assertIn({"path": "processing/bin/ttconv-pinned.sh", "digest": None}, after["sourceDependencies"])
        for select in (True, False):
            with self.assertRaisesRegex(ValueError, "source closure unavailable"):
                self.compile(before, select=select)

    def test_legacy_compilation_observes_dependencies_without_claiming_selection(self):
        row = self.discover()
        old = self.compile(row, select=False)
        self.assertEqual(old["sourceClosureBinding"]["status"], "observed-at-compilation")
        self.assertEqual(len(old["execution"]["hostDependencies"]), 6)
        unbound = self.compile(row, select=False, bind_input=False)
        self.assertNotIn("hostDependencies", unbound["execution"])
        source_only = self.compile(row, bind_input=False)
        self.assertEqual(len(source_only["execution"]["hostDependencies"]), 5)
        self.assertNotIn("inputByteBinding", source_only)

    def test_closure_is_relocatable_and_scope_is_specific(self):
        for kind, count in (("av", 2), ("audio", 2), ("otio", 4), ("timed-text", 5)):
            with self.subTest(kind=kind):
                row = self.discover(kind)
                original = next(p for p in processing_profiles(ROOT)["profiles"]
                                if p["profileKind"] == row["profileKind"])
                self.assertEqual(row["sourceClosureDigest"], original["sourceClosureDigest"])
                self.assertEqual(len(row["sourceDependencies"]), count)
                self.assertEqual(row["externalToolReadiness"], "not-observed")
