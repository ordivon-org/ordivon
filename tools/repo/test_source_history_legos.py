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
            owner.write_text('[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n')
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
            self.assertEqual(records[local_patch]["patchRelation"], "PATCH_ID_EQUIVALENT")
            self.assertEqual(records[remote_patch]["patchRelation"], "PATCH_ID_EQUIVALENT")
            self.assertEqual(records[local_patch]["owners"], ["runtime"])
            self.assertEqual(records[local_patch]["pathRelations"], {"SAME_BLOB_AND_MODE": 1})
            for record in records.values():
                self.assertEqual(record["consumerQualification"], "UNKNOWN_REQUIRES_OWNER_CDC")
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
            manifest.write_text('[[owners]]\nname = "runtime"\nroot = "services/runtime/"\n')
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
            merges = [
                x for x in report["commits"] if x["kind"] == "merge-provenance"
            ]
            self.assertEqual(len(merges), 1)
            self.assertEqual(merges[0]["patchRelation"], "NOT_APPLICABLE")
            self.assertEqual(len(merges[0]["parents"]), 2)

    def test_invalid_reference_fails_not_reported_as_empty(self):
        with (
            tempfile.TemporaryDirectory(prefix="ordivon-history-invalid-") as temp,
            self.assertRaises(subprocess.CalledProcessError),
        ):
            history(Path(temp), "main", "nonexistent")


if __name__ == "__main__":
    unittest.main()
