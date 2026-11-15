from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import affected_owners
import ci_owner_shards


class ShardQueueTests(unittest.TestCase):
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
