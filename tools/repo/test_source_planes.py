#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("source_planes.py")
SPEC = importlib.util.spec_from_file_location("source_planes", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


class SourcePlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "user.name", "Ordivon Test")
        (self.repo / "a").write_text("0\n")
        git(self.repo, "add", "a")
        git(self.repo, "commit", "-q", "-m", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def commit(self, name: str, value: str) -> str:
        (self.repo / name).write_text(value)
        git(self.repo, "add", name)
        git(self.repo, "commit", "-q", "-m", name)
        return git(self.repo, "rev-parse", "HEAD")

    def test_same(self) -> None:
        p = M.project(self.base, self.base, cwd=str(self.repo))
        self.assertEqual(p.relationship, "SAME")
        self.assertFalse(p.reconciliationRequired)
        self.assertEqual((p.localOnlyCount, p.providerOnlyCount), (0, 0))

    def test_local_ahead(self) -> None:
        local = self.commit("local", "1\n")
        p = M.project(local, self.base, cwd=str(self.repo))
        self.assertEqual(p.relationship, "LOCAL_AHEAD")
        self.assertEqual((p.localOnlyCount, p.providerOnlyCount), (1, 0))

    def test_provider_ahead(self) -> None:
        provider = self.commit("provider", "1\n")
        p = M.project(self.base, provider, cwd=str(self.repo))
        self.assertEqual(p.relationship, "PROVIDER_AHEAD")
        self.assertEqual((p.localOnlyCount, p.providerOnlyCount), (0, 1))

    def test_diverged(self) -> None:
        git(self.repo, "branch", "provider", self.base)
        local = self.commit("local", "1\n")
        git(self.repo, "checkout", "-q", "provider")
        provider = self.commit("provider", "2\n")
        p = M.project(local, provider, cwd=str(self.repo))
        self.assertEqual(p.relationship, "DIVERGED")
        self.assertTrue(p.reconciliationRequired)
        self.assertEqual((p.localOnlyCount, p.providerOnlyCount), (1, 1))
        self.assertEqual(p.mergeBase, self.base)


if __name__ == "__main__":
    unittest.main()
