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

    def stage(self, **overrides: object) -> dict[str, object]:
        data = {
            "git": Path("/usr/bin/git"),
            "source_repo": self.owner,
            "commit": self.head,
            "require_ref": "origin/main",
            "expected_owner_tree": self.tree,
            "install_dir": self.installed,
            "candidate_dir": self.temp / "staged",
        }
        data.update(overrides)
        native_stat = Path.stat

        def root_owned_test_fixture(path: Path, *args: object, **kwargs: object):
            metadata = native_stat(path, *args, **kwargs)
            if path == self.installed or path.parent == self.installed:
                fields = list(metadata)
                fields[4] = 0
                return os.stat_result(fields)
            return metadata

        with patch.object(Path, "stat", root_owned_test_fixture):
            return deploy.stage_root_operator_bundle(argparse.Namespace(**data))

    def test_exact_git_bundle_is_staged_without_install_effect(self) -> None:
        import json

        before = [(p.name, p.read_bytes()) for p in sorted(self.installed.iterdir())]
        result = self.stage()
        self.assertEqual(result["artifactCount"], 5)
        self.assertTrue(result["rootOwnerApprovalRequired"])
        self.assertFalse(result["productionInstallExecuted"])
        path = self.temp / "staged" / "ordivon-root-bundle-candidate.json"
        self.assertEqual(result["candidateManifestDigest"], deploy.sha256(path))
        manifest = json.loads(path.read_text())
        self.assertEqual(manifest["sourceOwnerTree"], self.tree)
        self.assertFalse(manifest["trustedRollbackPreimageCaptured"])
        self.assertFalse(manifest["physicalServiceQuiesced"])
        self.assertFalse(manifest["releaseAdmissionFenced"])
        self.assertEqual(
            {entry["name"] for entry in manifest["artifacts"]},
            {name for name, _ in deploy.ROOT_OPERATOR_BUNDLE},
        )
        for entry in manifest["artifacts"]:
            source = self.scripts / entry["name"]
            staged = self.temp / "staged" / entry["name"]
            self.assertEqual(staged.read_bytes(), source.read_bytes())
            self.assertEqual(entry["digest"], deploy.sha256(staged))
        self.assertEqual(
            before,
            [(p.name, p.read_bytes()) for p in sorted(self.installed.iterdir())],
        )

    def test_stage_existing_candidate_is_never_overwritten(self) -> None:
        self.stage()
        candidate = self.temp / "staged"
        before = sorted((p.name,p.read_bytes()) for p in candidate.iterdir())
        with self.assertRaisesRegex(RuntimeError,"already exists"):
            self.stage()
        self.assertEqual(
            sorted((p.name,p.read_bytes()) for p in candidate.iterdir()),
            before,
        )

    def test_stage_refuses_candidate_inside_or_parent_of_live_root(self) -> None:
        for destination in (
            self.installed / "staged",
            self.temp,
            self.installed,
        ):
            with self.subTest(destination=destination):
                with self.assertRaisesRegex(RuntimeError,"separate from"):
                    self.stage(candidate_dir=destination)

    def test_stage_refuses_changed_required_owner_tree(self) -> None:
        old_head, old_tree = self.head,self.tree
        (self.scripts/"ordivon-runtime-deploy").write_text("new",encoding="utf-8")
        self.commit("new protected owner tree")
        with self.assertRaisesRegex(RuntimeError,"not Git-qualified"):
            self.stage(commit=old_head,expected_owner_tree=old_tree)
        self.assertFalse((self.temp/"staged").exists())

    def test_stage_refuses_ref_drift_after_candidate_bytes_were_copied(self) -> None:
        original = deploy.required_ref_authority
        call_count = [0]

        def changed_ref(*args: object, **kwargs: object) -> dict[str, object]:
            call_count[0] += 1
            qualification = original(*args, **kwargs)
            if call_count[0] > 1:
                qualification = dict(qualification)
                qualification["authorized"] = False
            return qualification

        with patch.object(deploy, "required_ref_authority", side_effect=changed_ref):
            with self.assertRaisesRegex(RuntimeError, "required Git ref"):
                self.stage()
        self.assertGreaterEqual(call_count[0], 2)
        self.assertFalse((self.temp / "staged").exists())

    def test_stage_refuses_unsafe_live_preimage_without_staging(self) -> None:
        (self.installed/"ordivon-runtime-deploy").chmod(0o777)
        with self.assertRaisesRegex(RuntimeError,"not Git-qualified"):
            self.stage()
        self.assertFalse((self.temp/"staged").exists())

    def test_stage_failure_removes_only_newly_created_candidate(self) -> None:
        original = deploy.sha256

        def fail_candidate_only(path: Path) -> str:
            result = original(path)
            if path.parent == self.temp/"staged" and path.name == "ordivon-runtime-pg-operator":
                return "sha256:" + "0" * 64
            return result

        with patch.object(deploy,"sha256",side_effect=fail_candidate_only):
            with self.assertRaisesRegex(RuntimeError,"stage bytes changed"):
                self.stage()
        self.assertFalse((self.temp/"staged").exists())
        self.assertEqual(
            {p.name for p in self.installed.iterdir()},
            {n for n,_ in deploy.ROOT_OPERATOR_BUNDLE},
        )

    def test_stage_rejects_untrusted_symlink_candidate_parent(self) -> None:
        actual = self.temp/"candidate-parent"
        actual.mkdir()
        alias = self.temp/"candidate-parent-link"
        alias.symlink_to(actual)
        with self.assertRaisesRegex(RuntimeError,"aliases a symlink"):
            self.stage(candidate_dir=alias/"staged")
        self.assertFalse((actual/"staged").exists())

    def exchanged_directories(self) -> tuple[
        Path, dict[str, str], dict[str, str],
    ]:
        import json

        old = {
            row["name"]: row["installedSha256"]
            for row in self.plan()["bundle"]
        }
        self.stage()
        # A current=current test cannot distinguish PREPARED from EXCHANGED
        # by bytes, and would give vacuous evidence of a successful switch.
        for name in (
            "ordivon-runtime-deploy",
            "ordivon-runtime-pg-release-dispatch",
            "ordivon_runtime_pg_operator.py",
        ):
            (self.installed / name).write_text("legacy-root:" + name)
            old[name] = deploy.sha256(self.installed / name)
        new = {
            row["name"]: row["digest"]
            for row in json.loads(
                (self.temp / "staged" / "ordivon-root-bundle-candidate.json").read_text()
            )["artifacts"]
        }
        return self.temp / "staged", old, new

    def test_linux_atomic_directory_exchange_is_one_reversible_five_file_switch(self) -> None:
        candidate, old, new = self.exchanged_directories()
        # Real native Linux renameat2, not a patched os.rename or mock.
        for name in old:
            (self.installed / name).write_text("preimage:" + name)
            old[name] = deploy.sha256(self.installed / name)
        self.assertEqual(
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts=old,candidate_artifacts=new,
            ), "PREPARED",
        )
        deploy.linux_exchange_sibling_root_bundle_directories(
            self.installed, candidate,
        )
        self.assertEqual(
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts=old,candidate_artifacts=new,
            ),"EXCHANGED",
        )
        for name in new:
            self.assertEqual(deploy.sha256(self.installed / name),new[name])
            self.assertEqual(deploy.sha256(candidate / name),old[name])
        deploy.linux_exchange_sibling_root_bundle_directories(
            self.installed, candidate,
        )
        self.assertEqual(
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts=old,candidate_artifacts=new,
            ),"PREPARED",
        )

    def test_readback_never_qualifies_mixed_or_damaged_root_directory(self) -> None:
        candidate, old, new = self.exchanged_directories()
        name = "ordivon-runtime-pg-release-dispatch"
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"PREPARED")
        (self.installed/name).write_bytes(b"mixed-wrong-live-operator")
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"UNKNOWN")
        (self.installed/name).chmod(0o777)
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"UNKNOWN")

    def test_identical_old_and_new_bytes_are_not_an_exchange_receipt(self) -> None:
        candidate,old,new=self.exchanged_directories()
        for name,mode in deploy.ROOT_OPERATOR_BUNDLE:
            (self.installed/name).write_bytes((candidate/name).read_bytes())
            (self.installed/name).chmod(mode)
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=new,candidate_artifacts=new,
        ),"UNKNOWN")

    def test_readback_rejects_missing_blob_or_incomplete_journal(self) -> None:
        candidate, old, new = self.exchanged_directories()
        with self.assertRaisesRegex(RuntimeError,"exactly the five"):
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts={name:value for name,value in old.items()
                               if name!="mcp_probe.py"},
                candidate_artifacts=new,
            )
        with self.assertRaisesRegex(RuntimeError,"invalid artifact digest"):
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts=old,
                candidate_artifacts={**new,"mcp_probe.py":"corrupt"},
            )
        (candidate/"mcp_probe.py").unlink()
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"UNKNOWN")

    def test_native_exchange_rejects_symlink_sibling_and_missing_directory(self) -> None:
        candidate, old, new = self.exchanged_directories()
        alias = self.temp/"symlink-candidate"
        alias.symlink_to(candidate,target_is_directory=True)
        with self.assertRaises((OSError,RuntimeError)):
            deploy.linux_exchange_sibling_root_bundle_directories(
                self.installed,alias,
            )
        with self.assertRaises((OSError,RuntimeError)):
            deploy.linux_exchange_sibling_root_bundle_directories(
                self.installed,self.temp/"missing",
            )
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"PREPARED")

    def test_native_exchange_rejects_same_directory_and_parent_child_paths(self) -> None:
        candidate, old, new = self.exchanged_directories()
        with self.assertRaisesRegex(RuntimeError,"two distinct direct sibling"):
            deploy.linux_exchange_sibling_root_bundle_directories(
                self.installed,self.installed,
            )
        with self.assertRaisesRegex(RuntimeError,"two distinct direct sibling"):
            deploy.linux_exchange_sibling_root_bundle_directories(
                self.installed,self.installed/"child",
            )
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"PREPARED")

    def test_post_effect_directory_fsync_failure_requires_reconciliation(self) -> None:
        candidate, old, new = self.exchanged_directories()
        native_fsync = deploy.os.fsync
        calls = [0]

        def fail_after_exchange(descriptor: int) -> None:
            calls[0] += 1
            # Initial two directory fsyncs succeed; parent fsync happens
            # AFTER the Linux atomic exchange and now fails.
            if calls[0] == 3:
                raise OSError("injected post-rename parent fsync failure")
            native_fsync(descriptor)

        with patch.object(deploy.os, "fsync", side_effect=fail_after_exchange):
            with self.assertRaisesRegex(RuntimeError,"RECONCILIATION_REQUIRED"):
                deploy.linux_exchange_sibling_root_bundle_directories(
                    self.installed,candidate,
                )
        self.assertEqual(calls[0], 3)
        self.assertEqual(
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts=old,candidate_artifacts=new,
            ),"EXCHANGED",
            "a failing post-effect flush must not license another exchange",
        )

    def test_exchange_parent_symlink_is_rejected_without_effect(self) -> None:
        candidate,old,new=self.exchanged_directories()
        parent_link=self.temp.parent/("link-"+self.temp.name)
        parent_link.symlink_to(self.temp,target_is_directory=True)
        self.addCleanup(parent_link.unlink)
        with self.assertRaisesRegex(RuntimeError,"two distinct direct sibling"):
            deploy.linux_exchange_sibling_root_bundle_directories(
                parent_link/self.installed.name,
                parent_link/candidate.name,
            )
        self.assertEqual(
            deploy.root_bundle_exchange_readback(
                self.installed,candidate,
                old_artifacts=old,candidate_artifacts=new,
            ),"PREPARED",
        )

    def test_missing_linux_renameat2_fails_without_nonatomic_fallback(self) -> None:
        candidate, old, new = self.exchanged_directories()
        with patch.object(deploy.ctypes,"CDLL",return_value=object()):
            with self.assertRaisesRegex(RuntimeError,"unavailable"):
                deploy.linux_exchange_sibling_root_bundle_directories(
                    self.installed,candidate,
                )
        self.assertEqual(deploy.root_bundle_exchange_readback(
            self.installed,candidate,
            old_artifacts=old,candidate_artifacts=new,
        ),"PREPARED")

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
