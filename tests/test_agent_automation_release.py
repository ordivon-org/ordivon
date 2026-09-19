from __future__ import annotations
import ast
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_automation_release as r  # noqa: E402

REAL_REQUIRE_OPERATOR_CARRIER_AVAILABLE = r.require_operator_carrier_available
REAL_REQUIRE_WORKER_RUNTIME_IMPORTABLE = r.require_worker_runtime_importable
REAL_REQUIRE_MCP_RUNTIME_IMPORTABLE = r.require_mcp_runtime_importable
REAL_REQUIRE_BROWSER_SECURITY_RELEASE_QUALIFICATION = (
    r.require_browser_security_release_qualification
)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self._admission_td = tempfile.TemporaryDirectory()
        root = Path(self._admission_td.name) / "admission"
        self._admission_patchers = [
            patch.object(r, "ADMISSION_ROOT", root),
            patch.object(r, "ADMISSION_LOCK", root / "release.lock"),
            patch.object(r, "ADMISSION_CLOSED", root / "closed.json"),
            patch.object(r, "require_operator_carrier_available", return_value=None),
            patch.object(r, "require_mcp_runtime_importable", return_value=None),
            patch.object(r, "require_worker_runtime_importable", return_value=None),
            patch.object(
                r,
                "require_browser_security_release_qualification",
                return_value={
                    "schemaVersion": 1,
                    "kind": "ordivon.agent-automation-browser-security-qualification",
                    "standing": "PASS",
                    "classificationStanding": "NO_OBSERVED_DRIFT",
                },
            ),
        ]
        for p in self._admission_patchers:
            p.start()

    def tearDown(self):
        for p in reversed(self._admission_patchers):
            p.stop()
        self._admission_td.cleanup()

    def test_units_execute_immutable_release_surface_not_shared_checkout(self):
        w = (ROOT / "systemd/ordivon-agent-temporal-worker.service").read_text()
        m = (ROOT / "systemd/ordivon-agent-automation-mcp.service").read_text()
        for x in (w, m):
            self.assertIn("/opt/ordivon/agent-automation/current", x)
            self.assertNotIn("WorkingDirectory=/root/workstation-lab", x)
        self.assertIn("--address 127.0.0.1:17233", w)
        self.assertIn("Requires=temporal.service", w)
        self.assertNotIn("/root/workstation-lab/scripts/temporal_agent_automation_worker.py", w)
        self.assertNotIn("/root/workstation-lab/scripts/agent_automation_mcp.py", m)

    def test_materialize_is_commit_addressed_and_reusable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = root / "r"
            releases = root / "releases"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "x@example.invalid"], check=True
            )
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "x"], check=True)
            (repo / "a").write_text("one\n")
            subprocess.run(["git", "-C", str(repo), "add", "a"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "one"], check=True)
            c = r.exact_commit(repo, "HEAD")
            with patch.object(r, "RELEASE_PATHS", ("a",)):
                a = r.materialize(repo, c, releases)
                b = r.materialize(repo, c, releases)
                self.assertEqual(a["disposition"], "materialized")
                self.assertEqual(b["disposition"], "existing")
                self.assertEqual(a["archiveDigest"], b["archiveDigest"])
                self.assertEqual((Path(a["path"]) / "a").read_text(), "one\n")
                self.assertEqual(json.loads((Path(a["path"]) / r.MARKER).read_text())["commit"], c)

    def test_operator_carrier_is_external_workstation_owned_executable_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            installed = Path(td) / "agent-automation"
            with patch.object(r, "OPERATOR_CLI", installed):
                self.assertFalse(r.operator_carrier_available())
                with self.assertRaisesRegex(r.ReleaseError, "Workstation-owned stable"):
                    REAL_REQUIRE_OPERATOR_CARRIER_AVAILABLE()
                installed.write_text("#!/bin/sh\nexit 0\n")
                installed.chmod(0o755)
                self.assertTrue(r.operator_carrier_available())
                REAL_REQUIRE_OPERATOR_CARRIER_AVAILABLE()
                installed.chmod(0o644)
                self.assertFalse(r.operator_carrier_available())

    def test_release_archive_does_not_duplicate_workstation_operator_carrier(self):
        self.assertNotIn("scripts/agent_automation_wrapper.py", r.RELEASE_PATHS)
        self.assertFalse((ROOT / "scripts/agent_automation_wrapper.py").exists())
        self.assertIn("scripts/browser_security_witness_source.py", r.RELEASE_PATHS)
        self.assertIn("scripts/browser_security_pool_runner.py", r.RELEASE_PATHS)
        self.assertIn("scripts/browser_security_browserless_canary.py", r.RELEASE_PATHS)
        self.assertIn("scripts/browserless_image_promotion.py", r.RELEASE_PATHS)

    def test_worker_runtime_import_preflight_uses_exact_temporal_worker_python(self):
        with tempfile.TemporaryDirectory() as td:
            release = Path(td)
            (release / "scripts").mkdir()
            completed = subprocess.CompletedProcess(
                [],
                0,
                stdout=json.dumps({"rfc8785": "0.1.4", "temporalio": "1.32.0"}) + "\n",
                stderr="",
            )
            with patch.object(r, "run", return_value=completed) as invoked:
                REAL_REQUIRE_WORKER_RUNTIME_IMPORTABLE(release)
            argv = invoked.call_args.args[0]
            self.assertEqual(argv[0], str(r.WORKER_PY))
            self.assertIn(str(release / "scripts"), argv)
            self.assertTrue(any("import temporal_agent_automation" in str(value) for value in argv))
            failed = subprocess.CompletedProcess([], 1, stdout="", stderr="ModuleNotFoundError: x")
            with patch.object(r, "run", return_value=failed):
                with self.assertRaisesRegex(r.ReleaseError, "exact Temporal worker runtime"):
                    REAL_REQUIRE_WORKER_RUNTIME_IMPORTABLE(release)

    def test_mcp_runtime_import_preflight_uses_exact_control_python(self):
        with tempfile.TemporaryDirectory() as td:
            release = Path(td)
            (release / "scripts").mkdir()
            completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            with patch.object(r, "run", return_value=completed) as invoked:
                REAL_REQUIRE_MCP_RUNTIME_IMPORTABLE(release)
            argv = invoked.call_args.args[0]
            self.assertEqual(argv[0], str(r.MCP_PY))
            self.assertIn(str(release / "scripts"), argv)
            self.assertTrue(
                any(
                    "agent_automation_registry" in str(value)
                    and "agent_automation_browserless" in str(value)
                    for value in argv
                )
            )
            failed = subprocess.CompletedProcess(
                [], 1, stdout="", stderr="ModuleNotFoundError: rfc8785"
            )
            with patch.object(r, "run", return_value=failed):
                with self.assertRaisesRegex(r.ReleaseError, "exact MCP control runtime"):
                    REAL_REQUIRE_MCP_RUNTIME_IMPORTABLE(release)

    def test_browser_security_release_qualification_pass_is_candidate_bound_and_persisted(self):
        with tempfile.TemporaryDirectory() as td:
            release = Path(td)
            (release / "scripts").mkdir()
            (release / "scripts/browser_security_pool_runner.py").write_text("# runner\n")
            (release / "scripts/browser_security_witness_source.py").write_text("# witness\n")
            commit = "a" * 40
            pool = {
                "schemaVersion": 1,
                "kind": "ordivon.browser-security-pool-run",
                "runId": "release-aaaaaaaaaaaa",
                "poolId": "browserless-prod-r2-20260918",
                "poolIndexSha256": "sha256:" + "b" * 64,
                "harnessRevision": commit,
                "securityRevision": "c" * 40,
                "carrierEvidence": [{}, {}, {}],
                "classification": {
                    "standing": "NO_OBSERVED_DRIFT",
                    "rootCauseEstablished": False,
                },
                "providerChallengeVisited": False,
                "providerSendAttempted": False,
            }
            completed = subprocess.CompletedProcess([], 0, stdout=json.dumps(pool), stderr="")
            with patch.object(r, "run", return_value=completed) as invoked:
                value = REAL_REQUIRE_BROWSER_SECURITY_RELEASE_QUALIFICATION(release, commit)
            self.assertEqual(value["standing"], "PASS")
            self.assertEqual(value["candidateCommit"], commit)
            self.assertEqual(value["classificationStanding"], "NO_OBSERVED_DRIFT")
            argv = invoked.call_args.args[0]
            self.assertEqual(argv[0], str(r.BROWSER_SECURITY_PY))
            self.assertEqual(argv[1], str(release / "scripts/browser_security_pool_runner.py"))
            receipt = r._browser_security_qualification_path(commit)
            self.assertTrue(receipt.is_file())
            self.assertEqual(json.loads(receipt.read_text())["standing"], "PASS")
            self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)

    def test_browser_security_release_qualification_drift_holds_and_persists(self):
        with tempfile.TemporaryDirectory() as td:
            release = Path(td)
            (release / "scripts").mkdir()
            (release / "scripts/browser_security_pool_runner.py").write_text("# runner\n")
            (release / "scripts/browser_security_witness_source.py").write_text("# witness\n")
            commit = "d" * 40
            pool = {
                "kind": "ordivon.browser-security-pool-run",
                "poolId": "browserless-prod-r2-20260918",
                "poolIndexSha256": "sha256:" + "e" * 64,
                "harnessRevision": commit,
                "securityRevision": "f" * 40,
                "carrierEvidence": [{}, {}, {}],
                "classification": {
                    "standing": "GLOBAL_DRIFT",
                    "rootCauseEstablished": False,
                },
                "providerChallengeVisited": False,
                "providerSendAttempted": False,
            }
            completed = subprocess.CompletedProcess([], 0, stdout=json.dumps(pool), stderr="")
            with patch.object(r, "run", return_value=completed):
                with self.assertRaisesRegex(r.ReleaseError, "qualification HOLD: GLOBAL_DRIFT"):
                    REAL_REQUIRE_BROWSER_SECURITY_RELEASE_QUALIFICATION(release, commit)
            value = json.loads(r._browser_security_qualification_path(commit).read_text())
            self.assertEqual(value["standing"], "HOLD")
            self.assertEqual(value["classificationStanding"], "GLOBAL_DRIFT")

    def test_browser_security_release_qualification_runner_failure_holds(self):
        with tempfile.TemporaryDirectory() as td:
            release = Path(td)
            (release / "scripts").mkdir()
            (release / "scripts/browser_security_pool_runner.py").write_text("# runner\n")
            (release / "scripts/browser_security_witness_source.py").write_text("# witness\n")
            commit = "1" * 40
            failed = subprocess.CompletedProcess([], 9, stdout="", stderr="carrier busy")
            with patch.object(r, "run", return_value=failed):
                with self.assertRaisesRegex(r.ReleaseError, "pool runner failed"):
                    REAL_REQUIRE_BROWSER_SECURITY_RELEASE_QUALIFICATION(release, commit)
            value = json.loads(r._browser_security_qualification_path(commit).read_text())
            self.assertEqual(value["standing"], "HOLD")
            self.assertIn("carrier busy", value["detail"])

    def test_browser_security_qualification_runs_after_drain_before_worker_stop_and_switch(self):
        tree = ast.parse((ROOT / "scripts/agent_automation_release.py").read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "activate")
        calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call)]
        observe = min(
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Name) and node.func.id == "running_workflows"
        )
        qualify = next(
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "require_browser_security_release_qualification"
        )
        worker_stop = next(
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "run"
            and node.args
            and isinstance(node.args[0], ast.List)
            and any(isinstance(elt, ast.Constant) and elt.value == "stop" for elt in node.args[0].elts)
            and any(isinstance(elt, ast.Name) and elt.id == "WORKER_UNIT" for elt in node.args[0].elts)
        )
        switch = next(
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Name) and node.func.id == "atomic_link"
        )
        self.assertLess(observe, qualify)
        self.assertLess(qualify, worker_stop)
        self.assertLess(worker_stop, switch)

    def test_operator_carrier_preflight_precedes_admission_fence_and_service_mutation(self):
        tree = ast.parse((ROOT / "scripts/agent_automation_release.py").read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "activate")
        calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call)]

        def named_call(name):
            return next(node for node in calls if isinstance(node.func, ast.Name) and node.func.id == name)

        def systemctl_stop(unit_name):
            for node in calls:
                if not (isinstance(node.func, ast.Name) and node.func.id == "run" and node.args):
                    continue
                arg = node.args[0]
                if not isinstance(arg, ast.List):
                    continue
                values = [elt.value if isinstance(elt, ast.Constant) else elt.id if isinstance(elt, ast.Name) else None for elt in arg.elts]
                if "stop" in values and unit_name in values:
                    return node
            raise AssertionError(f"missing systemctl stop for {unit_name}")

        check = named_call("require_operator_carrier_available").lineno
        mcp_runtime = named_call("require_mcp_runtime_importable").lineno
        worker_runtime = named_call("require_worker_runtime_importable").lineno
        fence = named_call("release_admission_fence").lineno
        stop = systemctl_stop("MCP_UNIT").lineno
        self.assertLess(check, mcp_runtime)
        self.assertLess(mcp_runtime, worker_runtime)
        self.assertLess(worker_runtime, fence)
        self.assertLess(fence, stop)

    def test_plan_does_not_materialize_candidate_as_a_side_effect(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases = root / "releases"
            with (
                patch.object(r, "RELEASE_ROOT", releases),
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(r, "current_release", return_value=None),
                patch.object(r, "running_workflows", return_value=[]),
                patch.object(r, "active", return_value=False),
                patch.object(r, "operator_carrier_available", return_value=False),
                patch.object(
                    r, "materialize", side_effect=AssertionError("plan must not materialize")
                ),
            ):
                row = r.plan(root, "HEAD")
            self.assertFalse(row["candidateMaterialized"])
            self.assertFalse(row["operatorCarrierAvailable"])
            self.assertFalse(row["candidateRuntimeImports"]["ready"])
            self.assertFalse(releases.exists())

    def test_mcp_runtime_import_failure_precedes_admission_and_service_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidate = root / "candidate"
            candidate.mkdir()
            with (
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(
                    r,
                    "materialize",
                    return_value={
                        "path": str(candidate),
                        "commit": "c" * 40,
                        "archiveDigest": "sha256:x",
                        "disposition": "materialized",
                    },
                ),
                patch.object(r, "require_operator_carrier_available", return_value=None),
                patch.object(
                    r,
                    "require_mcp_runtime_importable",
                    side_effect=r.ReleaseError("control import failed"),
                ),
                patch.object(
                    r, "release_admission_fence", side_effect=AssertionError("fence touched")
                ),
                patch.object(r, "active", side_effect=AssertionError("service touched")),
            ):
                with self.assertRaisesRegex(r.ReleaseError, "control import failed"):
                    r.activate(root, "HEAD")

    def test_running_workflow_query_is_scoped_to_production_task_queue(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "config.json"
            cfg.write_text(json.dumps({"temporalTaskQueue": "ordivon-agent-automation"}))
            completed = subprocess.CompletedProcess([], 0, stdout="[]", stderr="")
            with (
                patch.object(r, "CONFIG", cfg),
                patch.object(r, "run", return_value=completed) as invoked,
            ):
                self.assertEqual(r.running_workflows(), [])
            self.assertEqual(len(invoked.call_args_list), 1)
            argv = invoked.call_args.args[0]
            query = argv[argv.index("--query") + 1]
            self.assertEqual(
                query, 'ExecutionStatus="Running" AND TaskQueue="ordivon-agent-automation"'
            )
            self.assertEqual(argv[argv.index("--address") + 1], r.TEMPORAL_ADDRESS)

    def test_running_workflows_preserve_production_cluster_identity(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "config.json"
            cfg.write_text(json.dumps({"temporalTaskQueue": "ordivon-agent-automation"}))
            completed = subprocess.CompletedProcess(
                [], 0, stdout=json.dumps([{"workflowId": "production-running"}]), stderr=""
            )
            with patch.object(r, "CONFIG", cfg), patch.object(r, "run", return_value=completed):
                rows = r.running_workflows()
            self.assertEqual(
                rows, [{"workflowId": "production-running", "temporalAddress": "127.0.0.1:17233"}]
            )

    def test_running_workflow_scope_fails_closed_on_missing_or_unsafe_queue(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "config.json"
            cfg.write_text(json.dumps({"temporalTaskQueue": 'q" OR ExecutionStatus="Running'}))
            with patch.object(r, "CONFIG", cfg):
                with self.assertRaisesRegex(r.ReleaseError, "unavailable or unsafe"):
                    r.current_temporal_task_queue()

    def test_running_parser_fails_closed_on_non_list(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "config.json"
            cfg.write_text(json.dumps({"temporalTaskQueue": "ordivon-agent-automation"}))
            with (
                patch.object(r, "CONFIG", cfg),
                patch.object(
                    r,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, stdout="{}", stderr=""),
                ),
            ):
                with self.assertRaisesRegex(r.ReleaseError, "not a list"):
                    r.running_workflows()

    def test_quiescence_observation_failure_restores_admission_before_any_switch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidate = root / "candidate"
            candidate.mkdir()
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(tuple(str(x) for x in argv))
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            with (
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(
                    r,
                    "materialize",
                    return_value={
                        "path": str(candidate),
                        "commit": "c" * 40,
                        "archiveDigest": "sha256:x",
                        "disposition": "materialized",
                    },
                ),
                patch.object(
                    r, "active", side_effect=lambda unit: unit in {r.MCP_UNIT, r.WORKER_UNIT}
                ),
                patch.object(
                    r,
                    "running_workflows",
                    side_effect=r.ReleaseError("temporal observation unavailable"),
                ),
                patch.object(r, "run", side_effect=fake_run),
                patch.object(r, "atomic_link") as switch,
            ):
                with self.assertRaisesRegex(r.ReleaseError, "temporal observation unavailable"):
                    r.activate(root, "HEAD")
            switch.assert_not_called()
            flat = [" ".join(x) for x in calls]
            self.assertTrue(any(f"stop {r.MCP_UNIT}" in x for x in flat))
            self.assertTrue(any(f"start {r.MCP_UNIT}" in x for x in flat))
            self.assertFalse(r.ADMISSION_CLOSED.exists())

    def test_failed_activation_restores_previous_release_config_and_units(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old"
            candidate = root / "candidate"
            current = root / "current"
            systemd = root / "systemd"
            config = root / "config.json"
            old.mkdir()
            candidate.mkdir()
            systemd.mkdir()
            current.symlink_to(old)
            config.write_bytes(b"old-config")
            old_bytes = {r.WORKER_UNIT: b"old-worker", r.MCP_UNIT: b"old-mcp"}
            for name, raw in old_bytes.items():
                (systemd / name).write_bytes(raw)
            (candidate / "systemd").mkdir()
            (candidate / "scripts").mkdir()
            (candidate / "systemd" / r.WORKER_UNIT).write_bytes(b"new-worker")
            (candidate / "scripts" / "agent_automation_mcp_deploy.py").write_text("x")
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(tuple(str(x) for x in argv))
                if any("agent_automation_mcp_deploy.py" in str(x) for x in argv):
                    raise subprocess.CalledProcessError(1, argv)
                return subprocess.CompletedProcess(
                    argv, 0, stdout="[]" if "workflow" in argv else "", stderr=""
                )

            with (
                patch.object(r, "CURRENT", current),
                patch.object(r, "SYSTEMD", systemd),
                patch.object(r, "CONFIG", config),
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(
                    r,
                    "materialize",
                    return_value={
                        "path": str(candidate),
                        "commit": "c" * 40,
                        "archiveDigest": "sha256:x",
                        "disposition": "materialized",
                    },
                ),
                patch.object(r, "active", return_value=True),
                patch.object(r, "running_workflows", return_value=[]),
                patch.object(r, "run", side_effect=fake_run),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    r.activate(root, "HEAD")
            self.assertEqual(current.resolve(), old.resolve())
            self.assertEqual(config.read_bytes(), b"old-config")
            for name, raw in old_bytes.items():
                self.assertEqual((systemd / name).read_bytes(), raw, name)
            flattened = [" ".join(x) for x in calls]
            self.assertTrue(any(f"start {r.WORKER_UNIT}" in x for x in flattened))
            self.assertTrue(any(f"start {r.MCP_UNIT}" in x for x in flattened))

    def test_failed_activation_restores_preexisting_absence_not_candidate_residue(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old"
            candidate = root / "candidate"
            current = root / "current"
            systemd = root / "systemd"
            config = root / "config.json"
            old.mkdir()
            candidate.mkdir()
            systemd.mkdir()
            current.symlink_to(old)
            (candidate / "systemd").mkdir()
            (candidate / "scripts").mkdir()
            (candidate / "systemd" / r.WORKER_UNIT).write_bytes(b"new-worker")
            (candidate / "scripts" / "agent_automation_mcp_deploy.py").write_text("x")

            def fake_run(argv, **kwargs):
                if any("agent_automation_mcp_deploy.py" in str(x) for x in argv):
                    config.write_bytes(b"new-config")
                    (systemd / r.MCP_UNIT).write_bytes(b"new-mcp")
                    config.with_name(config.name + ".next").write_bytes(b"abandoned")
                    raise subprocess.CalledProcessError(1, argv)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            with (
                patch.object(r, "CURRENT", current),
                patch.object(r, "SYSTEMD", systemd),
                patch.object(r, "CONFIG", config),
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(
                    r,
                    "materialize",
                    return_value={
                        "path": str(candidate),
                        "commit": "c" * 40,
                        "archiveDigest": "sha256:x",
                        "disposition": "materialized",
                    },
                ),
                patch.object(r, "active", return_value=False),
                patch.object(r, "running_workflows", return_value=[]),
                patch.object(r, "run", side_effect=fake_run),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    r.activate(root, "HEAD")
            self.assertEqual(current.resolve(), old.resolve())
            self.assertFalse(config.exists())
            self.assertFalse(config.with_name(config.name + ".next").exists())
            for name in (r.WORKER_UNIT, r.MCP_UNIT):
                self.assertFalse((systemd / name).exists(), name)
                self.assertFalse((systemd / (name + ".next")).exists(), name + ".next")

    def test_activation_failure_matrix_restores_exact_previous_state(self):
        failure_points = (
            "daemon-reload",
            "start-worker",
            "mcp-deploy",
            "post-quiescence",
            "post-health",
        )
        for failure_point in failure_points:
            with self.subTest(failure_point=failure_point), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                old = root / "old"
                candidate = root / "candidate"
                current = root / "current"
                systemd = root / "systemd"
                config = root / "config.json"
                old.mkdir()
                candidate.mkdir()
                systemd.mkdir()
                current.symlink_to(old)
                config.write_bytes(b"old-config")
                old_bytes = {r.WORKER_UNIT: b"old-worker", r.MCP_UNIT: b"old-mcp"}
                for name, raw in old_bytes.items():
                    (systemd / name).write_bytes(raw)
                (candidate / "systemd").mkdir()
                (candidate / "scripts").mkdir()
                (candidate / "systemd" / r.WORKER_UNIT).write_bytes(b"new-worker")
                (candidate / "scripts" / "agent_automation_mcp_deploy.py").write_text("x")
                calls = []
                workflow_calls = 0
                active_calls = 0

                def fake_run(argv, **kwargs):
                    calls.append(tuple(str(x) for x in argv))
                    joined = " ".join(str(x) for x in argv)
                    if any("agent_automation_mcp_deploy.py" in str(x) for x in argv):
                        if failure_point == "mcp-deploy":
                            raise subprocess.CalledProcessError(1, argv)
                        config.write_bytes(b"new-config")
                        (systemd / r.MCP_UNIT).write_bytes(b"new-mcp")
                        return subprocess.CompletedProcess(
                            argv, 0, stdout='{"standing":"ready"}\n', stderr=""
                        )
                    if failure_point == "daemon-reload" and "daemon-reload" in joined:
                        raise subprocess.CalledProcessError(1, argv)
                    if failure_point == "start-worker" and f"start {r.WORKER_UNIT}" in joined:
                        raise subprocess.CalledProcessError(1, argv)
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

                def fake_workflows():
                    nonlocal workflow_calls
                    workflow_calls += 1
                    if failure_point == "post-quiescence" and workflow_calls == 2:
                        raise r.ReleaseError("post switch temporal unavailable")
                    return []

                def fake_active(unit):
                    nonlocal active_calls
                    active_calls += 1
                    if (
                        failure_point == "post-health"
                        and active_calls >= 3
                        and unit in {r.WORKER_UNIT, r.MCP_UNIT}
                    ):
                        return False
                    return True

                with (
                    patch.object(r, "CURRENT", current),
                    patch.object(r, "SYSTEMD", systemd),
                    patch.object(r, "CONFIG", config),
                    patch.object(r, "exact_commit", return_value="c" * 40),
                    patch.object(
                        r,
                        "materialize",
                        return_value={
                            "path": str(candidate),
                            "commit": "c" * 40,
                            "archiveDigest": "sha256:x",
                            "disposition": "materialized",
                        },
                    ),
                    patch.object(r, "active", side_effect=fake_active),
                    patch.object(r, "running_workflows", side_effect=fake_workflows),
                    patch.object(r, "run", side_effect=fake_run),
                ):
                    with self.assertRaises(Exception):
                        r.activate(root, "HEAD")
                self.assertEqual(current.resolve(), old.resolve(), failure_point)
                self.assertEqual(config.read_bytes(), b"old-config", failure_point)
                for name, raw in old_bytes.items():
                    self.assertEqual((systemd / name).read_bytes(), raw, f"{failure_point}:{name}")

    def test_release_exclusive_fence_waits_for_existing_mutating_cli_lease(self):
        root = r.ADMISSION_ROOT
        root.mkdir(parents=True, exist_ok=True)
        ready = root / "child-ready"
        code = (
            "import fcntl,sys,time; from pathlib import Path; "
            "r=Path(sys.argv[1]); lock=r/'release.lock'; "
            "h=lock.open('a+'); fcntl.flock(h.fileno(),fcntl.LOCK_SH); "
            "(r/'child-ready').write_text('ready'); time.sleep(0.35); "
            "fcntl.flock(h.fileno(),fcntl.LOCK_UN); h.close()"
        )
        child = subprocess.Popen(
            [sys.executable, "-c", code, str(root)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 3
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(ready.exists(), "child did not acquire shared CLI admission lease")
        started = time.monotonic()
        with r.release_admission_fence("c" * 40):
            elapsed = time.monotonic() - started
            self.assertTrue(r.ADMISSION_CLOSED.is_file())
        out, err = child.communicate(timeout=5)
        self.assertEqual(child.returncode, 0, err)
        self.assertGreaterEqual(
            elapsed, 0.20, "release fence did not wait for in-flight CLI admission"
        )

    def test_existing_closed_gate_is_candidate_bound_and_malformed_gate_stays_closed(self):
        r.ADMISSION_ROOT.mkdir(parents=True, exist_ok=True)
        first = "a" * 40
        second = "b" * 40
        with (
            patch.object(r, "source_repo_identity", return_value="/same/source"),
            patch.object(r, "candidate_fast_forwards_closed_gate", return_value=False),
        ):
            with r.release_admission_fence(first):
                pass
        self.assertTrue(r.ADMISSION_CLOSED.exists())
        with (
            patch.object(r, "source_repo_identity", return_value="/same/source"),
            patch.object(r, "candidate_fast_forwards_closed_gate", return_value=False),
        ):
            with self.assertRaisesRegex(r.ReleaseError, "non-ancestor candidate"):
                with r.release_admission_fence(second):
                    pass
        row = json.loads(r.ADMISSION_CLOSED.read_text())
        self.assertEqual(row["candidateCommit"], first)
        r.ADMISSION_CLOSED.write_text("{broken")
        with self.assertRaisesRegex(r.ReleaseError, "malformed"):
            with r.release_admission_fence(first):
                pass
        self.assertTrue(r.ADMISSION_CLOSED.exists(), "malformed closed gate must fail closed")

    def test_closed_gate_can_advance_only_to_fast_forward_repair_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "x@example.invalid"], check=True
            )
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "x"], check=True)
            (repo / "x").write_text("one\n")
            subprocess.run(["git", "-C", str(repo), "add", "x"], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "one"], check=True)
            old = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            (repo / "x").write_text("two\n")
            subprocess.run(["git", "-C", str(repo), "commit", "-qam", "two"], check=True)
            new = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            r.ADMISSION_ROOT.mkdir(parents=True, exist_ok=True)
            r._close_admission(old, repo)
            with patch.object(r, "SOURCE_REPO", repo):
                with r.release_admission_fence(new) as was_closed:
                    self.assertTrue(was_closed)
                    gate = json.loads(r.ADMISSION_CLOSED.read_text())
                    self.assertEqual(gate["candidateCommit"], new)
                    self.assertEqual(gate["schemaVersion"], 2)
                    self.assertEqual(gate["sourceRepo"], str(repo.resolve()))
            self.assertTrue(
                r.ADMISSION_CLOSED.exists(),
                "fast-forward supersession must preserve the closed gate",
            )

    def test_legacy_v1_closed_gate_requires_explicit_reconciliation_before_owner_migration(self):
        r.ADMISSION_ROOT.mkdir(parents=True, exist_ok=True)
        r.ADMISSION_CLOSED.write_text(
            json.dumps({"schemaVersion": 1, "standing": "HOLD_CLOSED", "candidateCommit": "a" * 40})
        )
        with self.assertRaisesRegex(
            r.ReleaseError, "legacy closed admission gate requires explicit reconciliation"
        ):
            with r.release_admission_fence("b" * 40):
                pass
        self.assertEqual(json.loads(r.ADMISSION_CLOSED.read_text())["schemaVersion"], 1)

    def test_hold_draining_keeps_cli_gate_closed_without_stopping_worker(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidate = root / "candidate"
            candidate.mkdir()
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(tuple(str(x) for x in argv))
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            with (
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(
                    r,
                    "materialize",
                    return_value={
                        "path": str(candidate),
                        "commit": "c" * 40,
                        "archiveDigest": "sha256:x",
                        "disposition": "materialized",
                    },
                ),
                patch.object(r, "active", return_value=True),
                patch.object(r, "running_workflows", return_value=[{"workflowId": "in-flight"}]),
                patch.object(r, "run", side_effect=fake_run),
            ):
                row = r.activate(root, "HEAD")
            self.assertEqual(row["standing"], "HOLD_DRAINING")
            self.assertTrue(row["cliAdmissionClosed"])
            self.assertTrue(r.ADMISSION_CLOSED.is_file())
            flat = [" ".join(x) for x in calls]
            self.assertTrue(any(f"stop {r.MCP_UNIT}" in x for x in flat))
            self.assertFalse(any(f"stop {r.WORKER_UNIT}" in x for x in flat))

    def test_worker_stop_failure_restores_pre_attempt_services_and_opens_new_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = root / "old"
            candidate = root / "candidate"
            current = root / "current"
            systemd = root / "systemd"
            config = root / "config.json"
            old.mkdir()
            candidate.mkdir()
            systemd.mkdir()
            current.symlink_to(old)
            (systemd / r.WORKER_UNIT).write_bytes(b"old-worker")
            (systemd / r.MCP_UNIT).write_bytes(b"old-mcp")
            config.write_bytes(b"old-config")
            calls = []

            def fake_run(argv, **kwargs):
                calls.append(tuple(str(x) for x in argv))
                joined = " ".join(str(x) for x in argv)
                if f"stop {r.WORKER_UNIT}" in joined and kwargs.get("check", True):
                    raise subprocess.CalledProcessError(1, argv)
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            with (
                patch.object(r, "CURRENT", current),
                patch.object(r, "SYSTEMD", systemd),
                patch.object(r, "CONFIG", config),
                patch.object(r, "exact_commit", return_value="c" * 40),
                patch.object(
                    r,
                    "materialize",
                    return_value={
                        "path": str(candidate),
                        "commit": "c" * 40,
                        "archiveDigest": "sha256:x",
                        "disposition": "materialized",
                    },
                ),
                patch.object(r, "active", return_value=True),
                patch.object(r, "running_workflows", return_value=[]),
                patch.object(r, "run", side_effect=fake_run),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    r.activate(root, "HEAD")
            self.assertEqual(current.resolve(), old.resolve())
            self.assertFalse(r.ADMISSION_CLOSED.exists())
            flat = [" ".join(x) for x in calls]
            self.assertTrue(any(f"start {r.WORKER_UNIT}" in x for x in flat))
            self.assertTrue(any(f"start {r.MCP_UNIT}" in x for x in flat))

    def test_activation_closes_admission_before_quiescence_and_switch(self):
        source = (ROOT / "scripts/agent_automation_release.py").read_text()
        tree = ast.parse(source)
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "activate")
        calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call)]
        stop = next(
            node.lineno
            for node in calls
            if isinstance(node.func, ast.Name)
            and node.func.id == "run"
            and node.args
            and isinstance(node.args[0], ast.List)
            and any(isinstance(elt, ast.Constant) and elt.value == "stop" for elt in node.args[0].elts)
            and any(isinstance(elt, ast.Name) and elt.id == "MCP_UNIT" for elt in node.args[0].elts)
        )
        observe = next(node.lineno for node in calls if isinstance(node.func, ast.Name) and node.func.id == "running_workflows")
        switch = next(node.lineno for node in calls if isinstance(node.func, ast.Name) and node.func.id == "atomic_link")
        self.assertLess(stop, observe)
        self.assertLess(observe, switch)
        self.assertIn("HOLD_DRAINING", source)
        self.assertNotIn("ordivon-browserless-netns-reconcile", source)
        self.assertIn("Network v2", source)


if __name__ == "__main__":
    unittest.main()

class MaterializationLedgerMigrationTests(unittest.TestCase):
    def _config_and_legacy_ledger(self, root: Path) -> tuple[Path, Path]:
        config = root / "config.json"
        state = root / "state"
        state.mkdir()
        config.write_text(json.dumps({"stateRoot": str(state)}))
        legacy = state / "birth-ledger.sqlite"
        import sqlite3

        db = sqlite3.connect(legacy)
        db.execute(
            """
            CREATE TABLE requests (
                request_id TEXT PRIMARY KEY,
                request_digest TEXT NOT NULL,
                request_json TEXT NOT NULL,
                standing TEXT NOT NULL,
                provider_coordinate TEXT,
                evidence_digest TEXT,
                detail TEXT,
                effect_generation INTEGER NOT NULL DEFAULT 0,
                created_at_ms INTEGER NOT NULL,
                updated_at_ms INTEGER NOT NULL
            )
            """
        )
        db.execute(
            "INSERT INTO requests VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                "effect:1",
                "sha256:" + "1" * 64,
                "{}",
                "unknown",
                None,
                None,
                "receipt lost",
                1,
                10,
                11,
            ),
        )
        db.commit()
        db.close()
        return config, legacy

    def test_prepare_and_finalize_migrates_one_authoritative_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config, legacy = self._config_and_legacy_ledger(Path(td))
            receipt = r.prepare_materialization_ledger_migration(legacy.parent)
            current = legacy.with_name("materialization-ledger.sqlite")
            self.assertTrue(legacy.is_file())
            self.assertTrue(current.is_file())
            self.assertEqual(receipt["standing"], "PREPARED")
            self.assertEqual(receipt["requestCount"], 1)
            r.finalize_materialization_ledger_migration(receipt)
            self.assertFalse(legacy.exists())
            self.assertTrue(current.is_file())

    def test_rollback_removes_only_new_copy_and_restores_legacy_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config, legacy = self._config_and_legacy_ledger(Path(td))
            receipt = r.prepare_materialization_ledger_migration(legacy.parent)
            current = legacy.with_name("materialization-ledger.sqlite")
            r.rollback_materialization_ledger_migration(receipt)
            self.assertTrue(legacy.is_file())
            self.assertFalse(current.exists())

class BrowserSecurityReadinessQualificationTests(unittest.TestCase):
    def _pool(self, standing: str) -> dict:
        return {
            "kind": "ordivon.browser-security-pool-run",
            "harnessRevision": "a" * 40,
            "securityRevision": "b" * 40,
            "poolIndexSha256": "sha256:" + "c" * 64,
            "carrierEvidence": [],
            "providerChallengeVisited": False,
            "providerSendAttempted": False,
            "classification": {
                "standing": standing,
                "rootCauseEstablished": False,
            },
        }

    def test_observer_unavailable_is_resampled_before_release_verdict(self):
        import json
        from unittest.mock import patch
        import scripts.agent_automation_release as release

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "browser_security_pool_runner.py").write_text("# runner\n")
            (scripts / "browser_security_witness_source.py").write_text("# witness\n")
            rows = [
                self._pool("OBSERVATION_INVALID"),
                self._pool("NO_OBSERVED_DRIFT"),
            ]
            completed = [
                subprocess.CompletedProcess([], 0, stdout=json.dumps(row), stderr="")
                for row in rows
            ]
            with (
                patch.object(release, "run", side_effect=completed) as invoked,
                patch.object(release, "_persist_browser_security_qualification"),
            ):
                out = release.require_browser_security_release_qualification(root, "a" * 40)
            self.assertEqual(out["standing"], "PASS")
            self.assertEqual(out["probeAttempts"], 2)
            self.assertEqual(invoked.call_count, 2)

    def test_real_drift_is_not_retried(self):
        import json
        from unittest.mock import patch
        import scripts.agent_automation_release as release

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "browser_security_pool_runner.py").write_text("# runner\n")
            (scripts / "browser_security_witness_source.py").write_text("# witness\n")
            completed = subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(self._pool("GLOBAL_DRIFT")), stderr=""
            )
            with (
                patch.object(release, "run", return_value=completed) as invoked,
                patch.object(release, "_persist_browser_security_qualification"),
            ):
                with self.assertRaises(release.ReleaseError):
                    release.require_browser_security_release_qualification(root, "a" * 40)
            self.assertEqual(invoked.call_count, 1)

    def test_repeated_observation_invalid_still_holds(self):
        import json
        from unittest.mock import patch
        import scripts.agent_automation_release as release

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "browser_security_pool_runner.py").write_text("# runner\n")
            (scripts / "browser_security_witness_source.py").write_text("# witness\n")
            completed = subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(self._pool("OBSERVATION_INVALID")), stderr=""
            )
            with (
                patch.object(release, "run", return_value=completed) as invoked,
                patch.object(release, "_persist_browser_security_qualification"),
            ):
                with self.assertRaises(release.ReleaseError):
                    release.require_browser_security_release_qualification(root, "a" * 40)
            self.assertEqual(invoked.call_count, 3)
