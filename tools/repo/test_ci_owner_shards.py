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

    def test_explicit_cost_scenario_changes_placement_not_obligations(self) -> None:
        tasks = ["runtime:verify", "game:verify", "capital:verify"]
        weights = dict(zip(tasks, (100, 900, 300)))
        result = ci_owner_shards.shard_queue(tasks, 2, task_weights=weights)
        self.assertEqual(result["include"], [
            {"shard": 0, "tasks": ["game:verify"]},
            {"shard": 1, "tasks": ["capital:verify", "runtime:verify"]},
        ])
        self.assertEqual(result, ci_owner_shards.shard_queue(
            list(reversed(tasks)) + ["formal:verify"], 2, task_weights=weights))
        for bad in ({}, {**weights, "formal:verify": 1},
                    {**weights, "runtime:verify": True},
                    {**weights, "runtime:verify": -1},
                    {**weights, "runtime:verify": 0},
                    {**weights, "runtime:verify": 1.0}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ci_owner_shards.shard_queue(tasks, 2, task_weights=bad)

    def test_cost_frontier_known_dominance_and_empty_sentinel(self) -> None:
        from ci_owner_cost_frontier import cost_frontier
        weights = {"runtime:verify": 285, "capital:verify": 89,
                   "harness:queue": 79, "host:queue": 54}
        report = cost_frontier(list(weights), weights, 93)
        self.assertEqual(report["frontierCaps"], [1, 2])
        self.assertEqual(report["candidates"][1]["modeledLatencyMs"], 378)
        self.assertEqual(report["candidates"][1]["modeledTotalMs"], 693)
        self.assertEqual(report["candidates"][3]["modeledTotalMs"], 879)
        self.assertEqual(report["scope"], "ADVISORY_LPT_SCENARIO_NOT_DISPATCH")
        empty = cost_frontier(["formal:verify"], {}, 93)
        self.assertEqual(empty["candidates"][0]["activeLanes"], 0)
        self.assertEqual(empty["candidates"][0]["modeledTotalMs"], 0)
        self.assertEqual(empty["candidates"][0]["matrix"], {"include": [{"shard": 0, "tasks": []}]})

    def test_cost_frontier_independent_finite_oracle(self) -> None:
        from itertools import product
        from ci_owner_cost_frontier import cost_frontier
        tasks = ["runtime:verify", "game:verify", "capital:verify", "host:queue"]
        for values in product((1, 2, 7), repeat=4):
            weights = dict(zip(tasks, values))
            for fixed in (0, 1, 9):
                report = cost_frontier(tasks, weights, fixed)
                self.assertEqual(report, cost_frontier(list(reversed(tasks)), weights, fixed))
                rows = report["candidates"]
                self.assertEqual([r["cap"] for r in rows], [1, 2, 3, 4])
                points = []
                for row in rows:
                    lanes = [r["tasks"] for r in row["matrix"]["include"]]
                    self.assertCountEqual([t for lane in lanes for t in lane], tasks)
                    self.assertTrue(all(lanes))
                    loads = [sum(weights[t] for t in lane) for lane in lanes]
                    self.assertEqual(row["activeLanes"], len(lanes))
                    self.assertEqual(row["laneWorkMs"], loads)
                    self.assertEqual(row["modeledLatencyMs"], max(loads) + fixed)
                    self.assertEqual(row["modeledTotalMs"], sum(values) + len(lanes)*fixed)
                    # Independent exhaustive assignment oracle: LPT is an
                    # approximation; check its classical makespan bound.
                    m = row["cap"]
                    optimum = min(max(sum(v for v, k in zip(values, assignment) if k == j)
                                      for j in range(m))
                                  for assignment in product(range(m), repeat=len(values)))
                    self.assertGreaterEqual(max(loads), optimum)
                    self.assertLessEqual(3*m*max(loads), (4*m-1)*optimum)
                    points.append((row["modeledLatencyMs"], row["modeledTotalMs"], m))
                expected = [m for a,b,m in points if not any(
                    x<=a and y<=b and (x<a or y<b) for x,y,_ in points)]
                self.assertEqual(report["frontierCaps"], expected)

    def test_cost_scenario_rejects_invalid_fixed_overhead(self) -> None:
        from ci_owner_cost_frontier import cost_frontier
        for bad in (-1, True, 1.5, float("nan"), "93", None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                cost_frontier(["data:verify"], {"data:verify": 100}, bad)

    def test_native_cli_explicit_cap_preserves_selected_tasks(self) -> None:
        root = Path(__file__).resolve().parents[2]
        selected = [owner.queue_task for owner in affected_owners.OWNERS] + ["formal:verify"]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/"tasks.txt"
            path.write_text("\n".join(selected)+"\n")
            cmd = [sys.executable, str(root/"tools/repo/ci_owner_shards.py"), str(path)]
            def invoke(*args):
                return subprocess.run(cmd+list(args),capture_output=True,text=True,timeout=10)
            default = invoke()
            self.assertEqual(default.returncode,0,default.stderr)
            self.assertEqual(json.loads(default.stdout),ci_owner_shards.shard_queue(selected))
            for cap in (1,2,3,4):
                explicit = invoke("--max-shards",str(cap))
                self.assertEqual(explicit.returncode,0,explicit.stderr)
                rows = json.loads(explicit.stdout)["include"]
                self.assertEqual(len(rows),cap)
                self.assertCountEqual([t for row in rows for t in row["tasks"]],
                                      selected[:-1])
                self.assertEqual(json.loads(explicit.stdout),ci_owner_shards.shard_queue(selected,cap))
            for bad in ("0","5","true","3.0","-1"):
                result = invoke("--max-shards",bad)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,"")
            path.write_text("formal:verify\n")
            self.assertEqual(json.loads(invoke("--max-shards","3").stdout),
                             {"include":[{"shard":0,"tasks":[]}]})

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


class WorkflowShardExperimentTests(unittest.TestCase):
    def test_actual_dispatch_cap_is_isolated_from_protected_events(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/ci.yml").read_text()
        marker = "          # Begin native shard experiment projection"
        end = "          # End native shard experiment projection"
        self.assertEqual(workflow.count(marker), 1)
        self.assertEqual(workflow.count(end), 1)
        script = textwrap.dedent(workflow.split(marker + "\n", 1)[1].split(end, 1)[0])
        tasks = [owner.queue_task for owner in affected_owners.OWNERS]
        tasks.append("formal:verify")
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            (temp / "tasks").write_text("\n".join(tasks) + "\n")
            env = dict(os.environ, RUNNER_TEMP=str(temp))
            cases = [(event, value, 4) for event in
                     ("pull_request", "merge_group", "push", "schedule")
                     for value in ("", "3", "4", "2", "3; exit 0")]
            cases += [("workflow_dispatch", "", 4), ("workflow_dispatch", "3", 3),
                      ("workflow_dispatch", "4", 4)]
            for event, value, cap in cases:
                with self.subTest(event=event, value=value):
                    result = subprocess.run(
                        ["bash", "-euo", "pipefail", "-c",
                         'tasks_file="$RUNNER_TEMP/tasks"\n' + script],
                        cwd=root, env=dict(env, EVENT_NAME=event, MANUAL_SHARD_CAP=value),
                        capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    matrix = json.loads((temp / "ordivon-owner-shards.json").read_text())
                    self.assertEqual(matrix, ci_owner_shards.shard_queue(tasks, cap))
                    self.assertCountEqual([t for row in matrix["include"] for t in row["tasks"]],
                                          tasks[:-1])
                    self.assertIn(f"effective_owner_shard_cap={cap}", result.stdout)
            for value in ("2", "5", "03", "3; exit 0", "4\n3", "unknown"):
                with self.subTest(value=value):
                    out = temp / "ordivon-owner-shards.json"
                    out.unlink(missing_ok=True)
                    result = subprocess.run(
                        ["bash", "-euo", "pipefail", "-c",
                         'tasks_file="$RUNNER_TEMP/tasks"\n' + script],
                        cwd=root, env=dict(env, EVENT_NAME="workflow_dispatch", MANUAL_SHARD_CAP=value),
                        capture_output=True, text=True, timeout=15,
                    )
                    self.assertEqual(result.returncode, 43, result.stderr)
                    self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
