"""Native selection, queue admission, and shard conservation for path sources."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import affected_owners
import ci_owner_shards
import convergence_plan


class PythonPathQueueTests(unittest.TestCase):
    def test_actual_consumers_reach_native_queue_and_shards(self):
        plan = convergence_plan.build_plan(
            changed_files=["packages/composition/pyproject.toml"]
        )
        self.assertEqual(plan["directOwners"], ["composition"])
        needed = {
            "composition:verify",
            "authority-catalog:verify",
            "experimental-episodes:verify",
        }
        self.assertTrue(needed <= set(plan["queueVerifyTasks"]))
        convergence_plan.validate_queue_task_selection(
            plan["verificationOwners"], plan["queueVerifyTasks"], plan["changedPaths"]
        )
        shards = ci_owner_shards.shard_queue(plan["queueVerifyTasks"])
        actual = [task for lane in shards["include"] for task in lane["tasks"]]
        self.assertCountEqual(
            actual, [t for t in plan["queueVerifyTasks"] if t != "formal:verify"]
        )
        for missing in needed:
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                convergence_plan.validate_queue_task_selection(
                    plan["verificationOwners"],
                    [t for t in plan["queueVerifyTasks"] if t != missing],
                    plan["changedPaths"],
                )
        study = convergence_plan.build_plan(
            changed_files=["studies/experimental-episodes/episode-store/uv.lock"]
        )
        self.assertEqual(study["directOwners"], ["experimental-episodes"])
        self.assertIn("experimental-episodes:verify", study["queueVerifyTasks"])

    def test_actual_git_range_removed_edge_and_forged_delta(self):
        # Use actual Git snapshots in a separate repository. Current owner
        # mapping is the existing repository mechanics, not a new fixture registry.
        previous_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args], text=True
                ).strip()

            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "fixture")
            provider = repo / "packages/composition"
            consumer = repo / "catalogs/authorities"
            provider.mkdir(parents=True)
            consumer.mkdir(parents=True)
            (provider / "pyproject.toml").write_text(
                '[project]\nname="ordivon-composition"\n'
            )
            (consumer / "pyproject.toml").write_text(
                '[project]\nname="authority"\n[tool.uv.sources]\nordivon-composition={path="../../packages/composition"}\n'
            )
            (provider / "source.py").write_text("value=0\n")
            git("add", ".")
            git("commit", "-qm", "before")
            before = git("rev-parse", "HEAD")
            (consumer / "pyproject.toml").write_text('[project]\nname="authority"\n')
            (provider / "source.py").write_text("value=1\n")
            git("add", ".")
            git("commit", "-qm", "after")
            after = git("rev-parse", "HEAD")
            # The source-derived edge survives removal in the old graph.
            observed = affected_owners.path_consumer_owners(
                ["packages/composition/source.py"],
                tuple(o for o in affected_owners.OWNERS if o.name == "composition"),
                repo=repo,
                before=before,
                after=after,
            )
            self.assertIn("authority-catalog", {o.name for o in observed})
            try:
                os.chdir(repo)
                plan = convergence_plan.build_plan(base=before, head=after)
                self.assertIn("authority-catalog:verify", plan["queueVerifyTasks"])
                with self.assertRaisesRegex(ValueError, "exact Git range"):
                    convergence_plan.validate_queue_task_selection(
                        plan["verificationOwners"],
                        plan["queueVerifyTasks"],
                        [],
                        base=before,
                        head=after,
                    )
            finally:
                os.chdir(previous_cwd)


if __name__ == "__main__":
    unittest.main()
