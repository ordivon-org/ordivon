from __future__ import annotations

import json
import os
import subprocess
import tempfile
import textwrap
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import affected_owners
import ci_owner_shards


class ShardQueueTests(unittest.TestCase):
    def test_gateway_only_merge_queue_installs_security_native_opa(self) -> None:
        # Test the actual workflow's Owner-toolroot selection code. The
        # Gateway-only merge group must preinstall the Security-pinned OPA,
        # without adding unrelated Owner tools to other shards.
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        prefix = """python3 - "$selected_roots" <<'PYOWNERS'"""
        self.assertEqual(workflow.count(prefix), 1)
        source = textwrap.dedent(
            workflow.split(prefix + "\n", 1)[1].split("\n          PYOWNERS", 1)[0]
        )
        for selected, wanted in (
            (["gateway:verify"], 1),
            (["gateway:verify", "security:verify"], 1),
            (["security:verify"], 1),
            (["data:verify"], 0),
            ([], 0),
        ):
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as td:
                target = Path(td) / "toolroots.txt"
                env = os.environ.copy()
                env["OWNER_TASKS_JSON"] = json.dumps(selected)
                observed = subprocess.run(
                    [sys.executable, "-c", source, str(target)],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=12,
                    check=False,
                )
                self.assertEqual(observed.returncode, 0, observed.stderr)
                roots = target.read_text(encoding="utf-8").splitlines()
                self.assertEqual(roots.count("platform/security"), wanted)
                self.assertEqual(len(roots), len(set(roots)))

    def test_full_owner_closure_is_exactly_preserved(self) -> None:
        selected = [owner.queue_task for owner in affected_owners.OWNERS]
        result = ci_owner_shards.shard_queue(selected + ["formal:verify"])
        rows = result["include"]
        self.assertLessEqual(len(rows), 4)
        observed = [task for row in rows for task in row["tasks"]]
        self.assertEqual(len(observed), len(selected))
        self.assertCountEqual(observed, selected)
        self.assertNotIn("formal:verify", observed)
        self.assertEqual([row["shard"] for row in rows], list(range(len(rows))))

    def test_empty_selection_keeps_required_aggregate_present(self) -> None:
        self.assertEqual(
            ci_owner_shards.shard_queue([]),
            {"include": [{"shard": 0, "tasks": []}]},
        )
        self.assertEqual(
            ci_owner_shards.shard_queue(["formal:verify"]),
            {"include": [{"shard": 0, "tasks": []}]},
        )

    def test_single_owner_runs_exactly_once(self) -> None:
        self.assertEqual(
            ci_owner_shards.shard_queue(["data:verify"])["include"],
            [{"shard": 0, "tasks": ["data:verify"]}],
        )

    def test_duplicate_and_unknown_task_fail_closed(self) -> None:
        for tasks in (
            ["data:verify", "data:verify"],
            ["unknown:verify"],
            ["formal:verify", "formal:verify"],
        ):
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                ci_owner_shards.shard_queue(tasks)

    def test_measured_heavy_owners_do_not_share_a_runner(self) -> None:
        selected = [owner.queue_task for owner in affected_owners.OWNERS]
        matrix = ci_owner_shards.shard_queue(selected)
        by_task = {
            task: row["shard"] for row in matrix["include"] for task in row["tasks"]
        }
        self.assertNotEqual(by_task["runtime:verify"], by_task["game:verify"])
        self.assertNotEqual(by_task["runtime:verify"], by_task["capital:verify"])
        self.assertCountEqual(list(by_task), selected)
        estimates = [
            sum(
                ci_owner_shards.HISTORICAL_SECONDS.get(
                    task,
                    ci_owner_shards.DEFAULT_SECONDS,
                )
                for task in row["tasks"]
            )
            for row in matrix["include"]
        ]
        self.assertLessEqual(max(estimates), 320)
        self.assertEqual(matrix, ci_owner_shards.shard_queue(list(reversed(selected))))

    def test_machine_json_roundtrip_and_max_parallel(self) -> None:
        tasks = [owner.queue_task for owner in affected_owners.OWNERS]
        for count in (1, 2, 3, 4):
            plan = ci_owner_shards.shard_queue(tasks, count)
            matrix = json.loads(json.dumps(plan))
            self.assertLessEqual(len(matrix["include"]), count)
            self.assertCountEqual(
                [t for row in matrix["include"] for t in row["tasks"]],
                tasks,
            )
        with self.assertRaises(ValueError):
            ci_owner_shards.shard_queue(tasks, 5)


if __name__ == "__main__":
    unittest.main()
