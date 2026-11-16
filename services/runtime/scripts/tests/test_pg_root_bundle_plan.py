"""Root-bundle source-vs-installed plan, deliberately without any release effect."""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
loader = importlib.machinery.SourceFileLoader(
    "runtime_deploy_root_bundle_plan", str(SCRIPTS / "ordivon-runtime-deploy")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
deploy = importlib.util.module_from_spec(spec)
loader.exec_module(deploy)


class RootOperatorBundlePlanTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="ordivon-root-plan-")
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.repo = self.temp / "repo"
        self.owner = self.repo / "services" / "runtime"
        self.scripts = self.owner / "scripts"
        self.scripts.mkdir(parents=True)
        self.installed = self.temp / "installed"
        self.installed.mkdir()
        self.git("init", "-q", "--initial-branch=main")
        self.git("config", "user.email", "root-bundle-plan@example.invalid")
        self.git("config", "user.name", "Root Bundle Plan Fixture")
        for name, mode in deploy.ROOT_OPERATOR_BUNDLE:
            source = self.scripts / name
            source.write_bytes(("source:" + name + "\n").encode())
            source.chmod(mode)
            installed = self.installed / name
            shutil.copyfile(source, installed)
            installed.chmod(mode)
        self.commit("initial bundle")

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["/usr/bin/git", "-C", str(self.repo), *args],
            text=True, capture_output=True, check=True,
        )
        return result.stdout.strip()

    def commit(self, label: str) -> None:
        self.git("add", "--", ".")
        self.git("commit", "-qm", label)
        self.head = self.git("rev-parse", "HEAD")
        self.tree = self.git("rev-parse", "HEAD:services/runtime")
        self.git("update-ref", "refs/remotes/origin/main", self.head)

    def plan(self, **overrides: object) -> dict[str, object]:
        data = {
            "git": Path("/usr/bin/git"),
            "source_repo": self.owner,
            "commit": self.head,
            "require_ref": "origin/main",
            "expected_owner_tree": self.tree,
            "install_dir": self.installed,
        }
        data.update(overrides)
        native_stat = Path.stat

        def root_owned_test_fixture(path: Path, *args: object, **kwargs: object):
            metadata = native_stat(path, *args, **kwargs)
            # CI is deliberately unprivileged. Only fixtures under our unique
            # isolated install directory represent production Root-owned files.
            if path == self.installed or path.parent == self.installed:
                fields = list(metadata)
                fields[4] = 0
                return os.stat_result(fields)
            return metadata

        with patch.object(Path, "stat", root_owned_test_fixture):
            return deploy.root_operator_bundle_plan(argparse.Namespace(**data))

    def test_five_git_sources_match_root_owned_installation(self) -> None:
        before = [(p.name, p.read_bytes()) for p in sorted(self.installed.iterdir())]
        plan = self.plan()
        self.assertTrue(plan["sourceAuthorized"])
        self.assertTrue(plan["eligibleForRootOwnerReview"])
        self.assertEqual(plan["currentCount"], 5)
        self.assertEqual(plan["drifted"], [])
        self.assertFalse(plan["productionInstallExecuted"])
        self.assertEqual(
            before,
            [(p.name, p.read_bytes()) for p in sorted(self.installed.iterdir())],
        )

    def test_three_actual_drifted_paths_are_explicit(self) -> None:
        names = ("ordivon-runtime-deploy", "ordivon-runtime-pg-release-dispatch",
                 "ordivon_runtime_pg_operator.py")
        for name in names:
            (self.installed / name).write_text("old root version", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(plan["currentCount"], 2)
        self.assertEqual(set(plan["drifted"]), set(names))
        self.assertTrue(plan["eligibleForRootOwnerReview"])
        self.assertFalse(plan["productionInstallExecuted"])

    def test_symlink_is_unsafe_not_a_missing_or_qualified_bundle(self) -> None:
        file = self.installed / "mcp_probe.py"
        file.unlink()
        file.symlink_to(self.scripts / file.name)
        plan = self.plan()
        self.assertEqual(plan["unsafe"], ["mcp_probe.py"])
        self.assertFalse(plan["eligibleForRootOwnerReview"])

    def test_hardlink_root_script_is_unsafe_for_a_snapshot(self) -> None:
        import os

        source = self.installed / "ordivon-runtime-deploy"
        os.link(source, self.temp / "other-root-hardlink")
        plan = self.plan()
        self.assertEqual(plan["unsafe"], ["ordivon-runtime-deploy"])
        self.assertFalse(plan["eligibleForRootOwnerReview"])

    def test_writable_root_bundle_directory_is_not_a_trusted_preimage(self) -> None:
        self.installed.chmod(0o777)
        with self.assertRaisesRegex(RuntimeError, "root-owned"):
            self.plan()

    def test_wrong_installed_mode_is_not_safe_drift(self) -> None:
        (self.installed / "ordivon-runtime-deploy").chmod(0o777)
        plan = self.plan()
        self.assertEqual(plan["unsafe"], ["ordivon-runtime-deploy"])
        self.assertEqual(plan["drifted"], [])
        self.assertFalse(plan["eligibleForRootOwnerReview"])

    def test_required_git_tree_is_an_independent_exact_pin(self) -> None:
        plan = self.plan(expected_owner_tree="a" * 40)
        self.assertFalse(plan["sourceAuthorized"])
        self.assertFalse(plan["eligibleForRootOwnerReview"])

    def test_unrelated_monorepo_commit_may_keep_same_owner_tree(self) -> None:
        expected_tree = self.tree
        (self.repo / "README.md").write_text("unrelated owner changed", encoding="utf-8")
        self.commit("unrelated root readme")
        self.assertEqual(self.tree, expected_tree)
        plan = self.plan()
        self.assertTrue(plan["requiredRefAuthority"]["authorized"])
        self.assertEqual(plan["sourceOwnerTree"], expected_tree)
        self.assertEqual(plan["currentCount"], 5)

    def test_outdated_owner_commit_is_not_authorized_after_source_change(self) -> None:
        old_head, old_tree = self.head, self.tree
        (self.scripts / "ordivon-runtime-deploy").write_text(
            "new source revision", encoding="utf-8",
        )
        self.commit("change owner")
        plan = self.plan(commit=old_head, expected_owner_tree=old_tree)
        self.assertFalse(plan["requiredRefAuthority"]["authorized"])
        self.assertFalse(plan["eligibleForRootOwnerReview"])

    def test_git_symlink_source_is_rejected_before_any_installer_plan(self) -> None:
        file = self.scripts / "mcp_probe.py"
        file.unlink()
        file.symlink_to(self.scripts / "ordivon-runtime-deploy")
        self.commit("invalid source symlink")
        with self.assertRaisesRegex(RuntimeError, "regular expected-mode blob"):
            self.plan()

    def test_missing_file_can_be_reported_for_root_owner_review(self) -> None:
        (self.installed / "ordivon-runtime-pg-release-dispatch").unlink()
        plan = self.plan()
        self.assertEqual(plan["missing"], ["ordivon-runtime-pg-release-dispatch"])
        self.assertTrue(plan["eligibleForRootOwnerReview"])

    def test_alias_install_directory_is_rejected(self) -> None:
        alias = self.temp / "symlink-root"
        alias.symlink_to(self.installed)
        with self.assertRaisesRegex(RuntimeError, "without aliases"):
            self.plan(install_dir=alias)


if __name__ == "__main__":
    unittest.main()
