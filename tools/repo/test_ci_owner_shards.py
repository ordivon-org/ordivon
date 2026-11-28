from __future__ import annotations

import json
import os
import subprocess
import shutil
import textwrap
import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import affected_owners
import ci_owner_shards
import ci_owner_toolroots


def task_group_fixture():
    run = {"id": 7, "run_attempt": 2, "head_sha": "a"*40,
           "path": ".github/workflows/ci.yml", "status": "completed", "conclusion": "success"}
    job = {"id": 8, "run_id": 7, "run_attempt": 2, "head_sha": "a"*40,
           "name": "owner-shard-0", "status": "completed", "conclusion": "success",
           "started_at": "2026-11-26T00:00:00Z", "completed_at": "2026-11-26T00:00:08Z",
           "steps": [{"number": 12, "name": "Verify affected owners",
                      "status": "completed", "conclusion": "success",
                      "started_at": "2026-11-26T00:00:02Z",
                      "completed_at": "2026-11-26T00:00:07Z"}]}
    plan = {"shard": 0, "tasks": ["data:verify", "web:verify"]}
    log = (b"2026-11-26T00:00:02.0000000Z ##[group]mise run data:verify\n"
           b"2026-11-26T00:00:02.5000000Z private sentinel\n"
           b"2026-11-26T00:00:03.2500000Z ##[endgroup]\n"
           b"2026-11-26T00:00:03.2500000Z ##[group]mise run web:verify\n"
           b"2026-11-26T00:00:06.0000000Z ##[endgroup]\n")
    return run, job, plan, log


class ShardQueueTests(unittest.TestCase):
    def test_native_task_group_observation_exact_scope(self) -> None:
        from ci_owner_task_observation import observe_task_groups
        run, job, plan, log = task_group_fixture()
        result = observe_task_groups(run, job, plan, log)
        self.assertEqual(result["standing"], "DESCRIPTIVE_GROUP_SPANS_NOT_RECEIPTS")
        self.assertEqual(result["taskMilliseconds"], {"data:verify": 1250, "web:verify": 2750})
        self.assertEqual(result["fixedObservedMs"], 3000)
        self.assertEqual(result["namedStepMs"], 5000)
        self.assertEqual(result["groupObservedMs"], 4000)
        self.assertEqual(result["providerHeadSha"], "a"*40)
        self.assertEqual(result["jobId"], 8)
        self.assertEqual(result["runAttempt"], 2)
        self.assertEqual(result["expectedTasks"], plan["tasks"])
        import hashlib
        self.assertEqual(result["logSha256"], hashlib.sha256(log).hexdigest())
        self.assertNotIn("private sentinel", json.dumps(result))

    def test_native_task_group_observation_rejects_unqualified_frames(self) -> None:
        from ci_owner_task_observation import observe_task_groups
        for fault in ("run-alias", "job-attempt", "head", "workflow", "job-name",
                      "step-duplicate", "step-skipped", "job-failed", "step-outside",
                      "missing", "duplicate", "nested-task", "order", "reverse",
                      "unclosed", "late", "naive", "wrong-plan", "formal",
                      "bad-utf8", "foreign-group", "truncated-marker", "malformed-end", "empty-label"):
            with self.subTest(fault=fault):
                run, job, plan, log = task_group_fixture()
                a = b"2026-11-26T00:00:02.0000000Z ##[group]mise run data:verify"
                b = b"2026-11-26T00:00:03.2500000Z ##[endgroup]"
                c = b"2026-11-26T00:00:03.2500000Z ##[group]mise run web:verify"
                if fault == "run-alias": run["id"] = True
                elif fault == "job-attempt": job["run_attempt"] = 1
                elif fault == "head": job["head_sha"] = "b"*40
                elif fault == "workflow": run["path"] = ".github/workflows/other.yml"
                elif fault == "job-name": job["name"] = "owner-shard-1"
                elif fault == "step-duplicate": job["steps"].append(dict(job["steps"][0]))
                elif fault == "step-skipped": job["steps"][0]["conclusion"] = "skipped"
                elif fault == "job-failed": job["conclusion"] = "failure"
                elif fault == "step-outside": job["steps"][0]["started_at"] = "2026-11-25T00:00:00Z"
                elif fault == "missing": log = log.replace(c, c.replace(b"mise run web:verify", b"ordinary group"))
                elif fault == "duplicate": log = log.replace(c, c.replace(b"web:verify", b"data:verify"))
                elif fault == "nested-task": log = log.replace(b, c+b"\n"+b)
                elif fault == "order": plan["tasks"].reverse()
                elif fault == "reverse": log = log.replace(b, b.replace(b"03.250", b"01.999"))
                elif fault == "unclosed": log = log.rsplit(b"##[endgroup]", 1)[0]
                elif fault == "late": log = log.replace(b"06.0000000Z", b"08.0000000Z")
                elif fault == "naive": log = log.replace(a, a.replace(b"Z ", b" "))
                elif fault == "wrong-plan": plan["tasks"].append("data:verify")
                elif fault == "formal": plan["tasks"].append("formal:verify")
                elif fault == "bad-utf8": log += bytes([255])
                elif fault == "foreign-group": log = log.replace(c, c.replace(b"web:verify", b"gateway:verify"))
                elif fault == "truncated-marker": log = log.replace(a, a.replace(b"data:verify", b"data:verify extra"))
                elif fault == "malformed-end": log = log.replace(b, b+b" unexpected")
                elif fault == "empty-label": log = log.replace(a, a.replace(b"mise run data:verify", b"mise run"))
                with self.assertRaises(ValueError):
                    observe_task_groups(run, job, plan, log)

    def test_native_task_group_observation_nested_nontask_and_precision(self) -> None:
        from ci_owner_task_observation import observe_task_groups
        run, job, plan, log = task_group_fixture()
        # Provider REST step times have whole-second precision, whereas log
        # events include fractional seconds. Completion within the reported
        # completion second is observable, not silently rounded to zero.
        log = log.replace(b"06.0000000Z", b"07.0010000Z")
        result = observe_task_groups(run, job, plan, log)
        self.assertEqual(result["taskMilliseconds"]["web:verify"], 3751)
        self.assertEqual(result["timestampScope"], "REST_SECOND_BUCKET_LOG_MICROSECOND")
        nested = b"2026-11-26T00:00:02.1000000Z ##[group]ordinary group\n" + \
                 b"2026-11-26T00:00:02.2000000Z ##[endgroup]\n"
        log = log.replace(b"2026-11-26T00:00:03.2500000Z ##[endgroup]", nested+
                          b"2026-11-26T00:00:03.2500000Z ##[endgroup]", 1)
        self.assertEqual(observe_task_groups(run, job, plan, log)["taskMilliseconds"],
                         result["taskMilliseconds"])

    def test_native_task_group_finite_microsecond_oracle(self) -> None:
        from datetime import datetime, timedelta, timezone
        from itertools import product
        from ci_owner_task_observation import observe_task_groups
        base = datetime(2026, 11, 26, tzinfo=timezone.utc)
        def stamp(micros, zone):
            return (base + timedelta(microseconds=micros)).astimezone(zone).isoformat()
        for offset, first, second, gap, zone_offset in product(
            (0, 1, 999), (1, 1000, 1001), (1, 1000, 1999), (0, 1, 1001), (0, 8)
        ):
            run, job, plan, _ = task_group_fixture()
            zone = timezone(timedelta(hours=zone_offset))
            a = 2_000_000 + offset
            b = a + first
            c = b + gap
            d = c + second
            raw = ("\n".join([
                stamp(a, zone) + " ##[group]mise run data:verify",
                stamp(b, zone) + " ##[endgroup]",
                stamp(c, zone) + " ##[group]mise run web:verify",
                stamp(d, zone) + " ##[endgroup]",
            ])+"\n").encode()
            report = observe_task_groups(run, job, plan, raw)
            expected = {"data:verify": (first+999)//1000, "web:verify": (second+999)//1000}
            self.assertEqual(report["taskMilliseconds"], expected)
            self.assertEqual(report["groupObservedMs"], sum(expected.values()))
            # ANSI decoration changes the byte digest, not the group semantics.
            decorated = raw.replace(b"mise run", b"\x1b[32mmise run").replace(b":verify", b":verify\x1b[0m")
            other = observe_task_groups(run, job, plan, decorated)
            self.assertEqual(other["groups"], report["groups"])
            self.assertNotEqual(other["logSha256"], report["logSha256"])

    def test_native_task_group_cli_context_and_bounds(self) -> None:
        from ci_owner_task_observation import MAX_CONTEXT_BYTES, observe_task_groups
        run, job, plan, log = task_group_fixture()
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            context, log_path = folder/"context.json", folder/"log.txt"
            original = json.dumps({"run":run, "job":job, "plan":plan})
            context.write_text(original)
            log_path.write_bytes(log)
            command = [sys.executable, str(root/"tools/repo/ci_owner_task_observation.py"),
                       str(context), str(log_path)]
            def invoke():
                return subprocess.run(command, capture_output=True, text=True, timeout=10)
            result = invoke()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), observe_task_groups(run, job, plan, log))
            context.write_text(original[:-1]+',"run":null}')
            self.assertNotEqual(invoke().returncode, 0)
            context.write_bytes(b" "*(MAX_CONTEXT_BYTES+1))
            self.assertNotEqual(invoke().returncode, 0)
            context.write_text(original)
            log_path.write_bytes(b"")
            self.assertNotEqual(invoke().returncode, 0)

    def test_native_task_group_fractional_positive_oracle(self) -> None:
        from ci_owner_task_observation import observe_task_groups
        run, job, plan, log = task_group_fixture()
        log = log.replace(b"03.2500000Z", b"03.2500010Z")
        report = observe_task_groups(run, job, plan, log)
        self.assertEqual(report["taskMilliseconds"], {"data:verify":1251,"web:verify":2750})

    def test_native_cohort_conserves_tasks_and_produces_explicit_scenario(self) -> None:
        from ci_owner_task_observation import observe_task_cohort
        run, job, plan, log = task_group_fixture()
        second = {**job, "id":9, "name":"owner-shard-1",
                  "completed_at":"2026-11-26T00:00:10Z"}
        matrix = {"include":[plan, {"shard":1,"tasks":["gateway:verify","network:ci"]}]}
        second_log = log.replace(b"data:verify",b"gateway:verify").replace(b"web:verify",b"network:ci")
        result = observe_task_cohort(run, [second,job], matrix, {8:log,9:second_log})
        self.assertEqual(result["standing"], "DESCRIPTIVE_COHORT_NOT_EXECUTION_ATTESTATION")
        self.assertEqual(result["scenario"], {
            "tasks":["data:verify","web:verify","gateway:verify","network:ci"],
            "taskMilliseconds":{"data:verify":1250,"web:verify":2750,
                                "gateway:verify":1250,"network:ci":2750},
            "fixedMilliseconds":4000,
        })
        self.assertEqual(result["fixedObservedMs"], [3000,5000])
        self.assertEqual([row["jobId"] for row in result["shards"]], [8,9])
        self.assertNotIn("private sentinel",json.dumps(result))
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            context = folder/"context.json"
            context.write_text(json.dumps({"run":run,"jobs":[second,job],"matrix":matrix}))
            (folder/"8.log").write_bytes(log)
            (folder/"9.log").write_bytes(second_log)
            command = [sys.executable,str(root/"tools/repo/ci_owner_task_observation.py"),
                       str(context),str(folder)]
            process = subprocess.run(command,capture_output=True,text=True,timeout=10)
            self.assertEqual(process.returncode,0,process.stderr)
            self.assertEqual(json.loads(process.stdout),result)
        for fault in ("duplicate-task","missing-job","extra-job","duplicate-job-id",
                      "missing-log","extra-log","wrong-shard","empty-shard","duplicate-shard"):
            with self.subTest(fault=fault):
                import copy
                jobs, m, logs = [copy.deepcopy(job),copy.deepcopy(second)],copy.deepcopy(matrix),{8:log,9:second_log}
                if fault=="duplicate-task":
                    m["include"][1]["tasks"][0]="data:verify"
                    logs[9]=second_log.replace(b"gateway:verify",b"data:verify")
                elif fault=="missing-job": jobs.pop()
                elif fault=="extra-job": jobs.append({**second,"id":10,"name":"owner-shard-2"})
                elif fault=="duplicate-job-id": jobs[1]["id"]=8
                elif fault=="missing-log": logs.pop(9)
                elif fault=="extra-log": logs[10]=log
                elif fault=="wrong-shard": m["include"][1]["shard"]=2
                elif fault=="empty-shard": m["include"][1]["tasks"]=[]
                elif fault=="duplicate-shard": m["include"][1]["shard"]=0
                with self.assertRaises(ValueError):
                    observe_task_cohort(run,jobs,m,logs)

    def test_gateway_only_merge_queue_installs_security_native_opa(self) -> None:
        # Test the actual workflow's Owner-toolroot selection code. The
        # Gateway-only merge group must preinstall the Security-pinned OPA,
        # without adding unrelated Owner tools to other shards.
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        prefix = 'python3 tools/repo/ci_owner_toolroots.py "$selected_roots"'
        self.assertEqual(workflow.count(prefix), 1)
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
                    [sys.executable, "tools/repo/ci_owner_toolroots.py", str(target)],
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

    def test_toolroot_projection_contract(self) -> None:
        by_task = {"a:verify": "a", "b:verify": "b", "gateway:verify": "gateway"}
        manifests = {
            "a": {"tasks": {"verify": {"run": ["echo hello", "cd ../../tools/formal"]}}},
            "b": {"tasks": {"verify": {"run": "echo b"}}},
            "tools/formal": {"tools": {"lean": "current"}},
            "platform/security": {"tools": {"opa": "current"}},
        }
        read = manifests.get
        for tasks, expected in (
            ([], []),
            (["b:verify"], ["b"]),
            (["a:verify", "b:verify"], ["a", "tools/formal", "b"]),
            (["gateway:verify"], ["platform/security"]),
            (["gateway:verify", "a:verify"], ["a", "tools/formal", "platform/security"]),
        ):
            with self.subTest(tasks=tasks):
                self.assertEqual(ci_owner_toolroots.project(tasks, by_task, read), expected)
        for tasks in ({}, ["a:verify", "a:verify"], ["unknown"], [True]):
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                ci_owner_toolroots.project(tasks, by_task, read)
        for root, task in (("tools/formal", "a:verify"), ("platform/security", "gateway:verify")):
            missing = dict(manifests)
            del missing[root]
            with self.subTest(root=root), self.assertRaises(ValueError):
                ci_owner_toolroots.project([task], by_task, missing.get)
        for opa in ("", None, []):
            bad = dict(manifests, **{"platform/security": {"tools": {"opa": opa}}})
            with self.subTest(opa=opa), self.assertRaises(ValueError):
                ci_owner_toolroots.project(["gateway:verify"], by_task, bad.get)

    def test_toolroot_actual_git_source_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "a").mkdir()
            manifest = repo / "a/mise.toml"
            original = b'[tools]\npython = "current"\n'
            manifest.write_bytes(original)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                            "-c", "user.email=test@local.invalid", "commit", "-qm", "fixture"],
                           check=True)
            head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            tracked = {"a/mise.toml": b"100644"}
            read = lambda root: ci_owner_toolroots.read_at_checkout(repo, head, tracked, root)
            self.assertEqual(read("a"), {"tools": {"python": "current"}})
            self.assertIsNone(read("missing"))
            with self.assertRaises(ValueError):
                ci_owner_toolroots.read_at_checkout(
                    repo, head, {"a/mise.toml": b"120000"}, "a"
                )
            for variant in ("dirty", "missing", "symlink", "untracked"):
                with self.subTest(variant=variant):
                    if manifest.exists() or manifest.is_symlink():
                        manifest.unlink()
                    if variant == "dirty":
                        manifest.write_bytes(original + b"# drift")
                    elif variant == "symlink":
                        target = repo / "original.toml"
                        target.write_bytes(original)
                        manifest.symlink_to(target)
                    elif variant == "untracked":
                        manifest.write_bytes(original)
                    with self.assertRaises(ValueError):
                        if variant == "untracked":
                            ci_owner_toolroots.read_at_checkout(repo, head, {}, "a")
                        else:
                            read("a")

    def test_actual_preinstall_rejects_drift_before_native_install(self) -> None:
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        section = workflow.split("      - name: Preinstall selected Owner tools with native mise\n", 1)[1]
        script = textwrap.dedent(section.split("        run: |\n", 1)[1].split(
            "\n      - name: Verify affected owners", 1
        )[0])
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            repo = temp / "repo"
            registry = repo / "tools/repo"
            registry.mkdir(parents=True)
            for name in ("ci_owner_toolroots.py", "affected_owners.py", "owners.toml"):
                shutil.copy2(root / "tools/repo" / name, registry / name)
            runtime = repo / "services/runtime/mise.toml"
            runtime.parent.mkdir(parents=True)
            runtime.write_text('[tools]\npython = "current"\n')
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                            "-c", "user.email=test@local.invalid", "commit", "-qm", "fixture"],
                           check=True)
            binary = temp / "bin"
            binary.mkdir()
            mock = binary / "mise"
            mock.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "$TRACE"\n')
            mock.chmod(0o755)
            trace = temp / "trace"
            env = dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"],
                       RUNNER_TEMP=str(temp), TRACE=str(trace),
                       OWNER_TASKS_JSON=json.dumps(["runtime:verify"]))
            env.pop("GITHUB_SHA", None)
            def invoke():
                trace.write_text("")
                result = subprocess.run(["bash", "-c", script], cwd=repo, env=env,
                                        capture_output=True, text=True, timeout=12)
                return result, trace.read_text().splitlines()
            result, calls = invoke()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(calls, ["--cd services/runtime install"])
            for path in (runtime, registry / "ci_owner_toolroots.py",
                         registry / "affected_owners.py", registry / "owners.toml"):
                with self.subTest(path=path.name):
                    original = path.read_bytes()
                    try:
                        path.write_bytes(original + b"\n# source drift\n")
                        result, calls = invoke()
                        self.assertEqual(result.returncode, 43, result.stderr)
                        self.assertEqual(calls, [])
                    finally:
                        path.write_bytes(original)
            env["GITHUB_SHA"] = "0" * 40
            result, calls = invoke()
            self.assertEqual(result.returncode, 43, result.stderr)
            self.assertEqual(calls, [])

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
