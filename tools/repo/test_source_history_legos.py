"""Native source graph LEGO: two-sided exact patch classes and no false consumer claims."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repo.source_history_legos import history


def git(p: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(p), *args], text=True).strip()


class SourceHistoryLegosTests(unittest.TestCase):
    def test_complete_graph_and_patch_equivalence_no_automatic_retirement(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-legos-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            owner = root / "tools/repo/owners.toml"
            owner.parent.mkdir(parents=True)
            owner.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            (root / "README").write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            tracked = root / "services/runtime/contract.txt"
            tracked.parent.mkdir(parents=True)
            tracked.write_text("same property\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local property")
            local_patch = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            tracked.parent.mkdir(parents=True, exist_ok=True)
            tracked.write_text("same property\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "equivalent remote property")
            remote_patch = git(root, "rev-parse", "HEAD")
            (root / "remote-only.txt").write_text("remote unique\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote unique")

            projection = history(root, "main", "remote-main")
            self.assertEqual(projection["counts"], {"local": 1, "remote": 2})
            records = {record["commit"]: record for record in projection["commits"]}
            self.assertEqual(
                records[local_patch]["patchRelation"], "PATCH_ID_EQUIVALENT"
            )
            self.assertEqual(
                records[remote_patch]["patchRelation"], "PATCH_ID_EQUIVALENT"
            )
            self.assertEqual(records[local_patch]["owners"], ["runtime"])
            self.assertEqual(
                records[local_patch]["pathRelations"], {"SAME_BLOB_AND_MODE": 1}
            )
            for record in records.values():
                self.assertEqual(
                    record["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC"
                )
            self.assertEqual(
                sum(projection["patchClasses"].values()),
                sum(projection["counts"].values()),
            )

    def test_merge_connectors_are_preserved_not_mistaken_for_patch_proofs(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-merge-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            (root / "README").write_text("base")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            (root / "local.txt").write_text("left")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local")
            git(root, "switch", "-q", "remote-main")
            git(root, "switch", "-q", "-c", "feature")
            (root / "remote.txt").write_text("remote")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote feature")
            git(root, "switch", "-q", "remote-main")
            git(root, "merge", "--no-ff", "-qm", "remote merge", "feature")
            report = history(root, "main", "remote-main")
            self.assertEqual(report["counts"], {"local": 1, "remote": 2})
            merges = [x for x in report["commits"] if x["kind"] == "merge-provenance"]
            self.assertEqual(len(merges), 1)
            self.assertEqual(merges[0]["patchRelation"], "NOT_APPLICABLE")
            self.assertEqual(len(merges[0]["parents"]), 2)
            # Merge connectors are not blank: their first-parent transition
            # can contain the only surviving consumer implementation.
            self.assertEqual(merges[0]["changedPaths"], ["remote.txt"])
            self.assertEqual(merges[0]["owners"], ["ROOT_UNOWNED"])
            self.assertEqual(merges[0]["resultDistinctFromAllParentsPaths"], [])

    def test_merge_conflict_resolution_has_real_owner_and_nonpatch_effect(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-resolution-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            consumer = root / "services/runtime/consumer.txt"
            consumer.parent.mkdir(parents=True)
            consumer.write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            consumer.write_text("local behavior\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local consumer")
            git(root, "switch", "-q", "remote-main")
            consumer.write_text("remote behavior\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote consumer")
            git(root, "branch", "feature", "main")
            merge = subprocess.run(
                ["git", "-C", str(root), "merge", "--no-ff", "feature"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(merge.returncode, 0)
            consumer.write_text("resolved behavior unique to merge\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "resolved provider contract")
            merged_oid = git(root, "rev-parse", "HEAD")
            report = history(root, "main", "remote-main")
            record = next(
                row for row in report["commits"] if row["commit"] == merged_oid
            )
            self.assertEqual(record["kind"], "merge-provenance")
            self.assertEqual(record["patchRelation"], "NOT_APPLICABLE")
            self.assertEqual(record["changedPaths"], ["services/runtime/consumer.txt"])
            self.assertEqual(record["owners"], ["runtime"])
            self.assertEqual(
                record["resultDistinctFromAllParentsPaths"],
                ["services/runtime/consumer.txt"],
            )
            self.assertEqual(
                record["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC"
            )

    def test_newline_paths_and_header_like_names_keep_exact_git_identity(self):
        # Git paths are byte strings: line splitting or C-quoting changes owner identity.
        with tempfile.TemporaryDirectory(prefix="ordivon-history-weird-path-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            expected = [
                "services/runtime/part\nbroken.txt",
                "services/runtime/\nleading.txt",
                "__ORDIVON_HISTORY_RECORD__< " + "0" * 40,
            ]
            for name in expected:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "unusual paths")
            left = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            (root / "remote-only").write_text("remote")
            git(root, "add", ".")
            git(root, "commit", "-qm", "independent remote")
            result = history(root, "main", "remote-main")
            record = next(row for row in result["commits"] if row["commit"] == left)
            self.assertEqual(sorted(record["changedPaths"]), sorted(expected))
            self.assertEqual(record["owners"], ["ROOT_UNOWNED", "runtime"])
            self.assertEqual(
                record["pathRelations"], {"OPPOSITE_TIP_ABSENT": len(expected)}
            )

    def test_owner_type_universe_is_bound_to_right_source_not_worktree(self):
        with tempfile.TemporaryDirectory(prefix="ordivon-history-owners-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")
            runtime_file = root / "services/runtime/contract.txt"
            runtime_file.parent.mkdir(parents=True)
            runtime_file.write_text("local change\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "local runtime owner")
            left = git(root, "rev-parse", "HEAD")
            git(root, "switch", "-q", "remote-main")
            (root / "remote.txt").write_text("remote change\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote")
            remote = git(root, "rev-parse", "HEAD")
            before = history(root, "main", "remote-main")
            # Workspace materialization may be dirty or checked out at a
            # different ref. Its manifest must not change historical evidence.
            manifest.write_text(
                '[[owners]]\nname = "fake"\nroot = "services/runtime/"\n'
            )
            after = history(root, "main", "remote-main")
            first = next(x for x in before["commits"] if x["commit"] == left)
            second = next(x for x in after["commits"] if x["commit"] == left)
            self.assertEqual(first["owners"], ["runtime"])
            self.assertEqual(second["owners"], ["runtime"])
            self.assertEqual(after["ownerMappingSourceCut"], remote)

    def test_invalid_reference_fails_not_reported_as_empty(self):
        with (
            tempfile.TemporaryDirectory(prefix="ordivon-history-invalid-") as temp,
            self.assertRaises(subprocess.CalledProcessError),
        ):
            history(Path(temp), "main", "nonexistent")


    def test_repo_mechanics_owner_is_distinct_from_unknown_root(self):
        # tools/repo is the existing natural owner in Formal Issue Census,
        # despite not being a domain entry in owners.toml.
        with tempfile.TemporaryDirectory(prefix="ordivon-history-repo-owner-") as temp:
            root = Path(temp)
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Ordivon Test")
            git(root, "config", "user.email", "test@example.invalid")
            manifest = root / "tools/repo/owners.toml"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                '[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n'
            )
            (root / "README").write_text("base\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "base")
            git(root, "branch", "remote-main")

            local_file = root / "tools/repo/selected_consumer.py"
            local_file.write_text("consumer = 1\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "native repo consumer")
            local_commit = git(root, "rev-parse", "HEAD")

            git(root, "switch", "-q", "remote-main")
            (root / "unattributed-root.txt").write_text("remote\n")
            git(root, "add", ".")
            git(root, "commit", "-qm", "remote independent")
            report = history(root, "main", "remote-main")
            row = next(r for r in report["commits"] if r["commit"] == local_commit)
            self.assertEqual(row["owners"], ["tools/repo"])
            self.assertEqual(row["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC")



if __name__ == "__main__":
    unittest.main()
