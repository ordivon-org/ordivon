from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
os.environ["ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT"] = str(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
import agent_automation_mcp_deploy as d  # noqa: E402
import browserless_podman_deploy as browserless_deploy  # noqa: E402


class DeployTests(unittest.TestCase):
    def test_runtime_check_rejects_old_python_even_if_pinned_packages_match(self):
        versions = {
            "mcp": "2.0.0",
            "mcp-types": "2.0.0",
            "uvicorn": "0.52.1",
            "pydantic": "2.14.1",
            "jsonschema": "4.26.0",
            "rfc8785": "0.1.4",
        }
        with tempfile.TemporaryDirectory() as td:
            py = Path(td) / "python"
            py.write_bytes(b"runtime-carrier")
            c = {
                "mcp_runtime_python": str(py),
                "mcp_python_version": "3.15.1",
                "mcp_sqlite_version": "3.54.0",
            }
            old_runtime = {
                "versions": versions,
                "forbidden": {"ordivon-protocol": None},
                "pythonVersion": "3.12.13",
                "sqliteVersion": "3.53.1",
            }
            with patch.object(d, "_runtime_versions", return_value=old_runtime):
                with self.assertRaisesRegex(RuntimeError, "MCP Python runtime mismatch"):
                    d.runtime_check(c)

    def test_runtime_check_rejects_old_embedded_sqlite_at_latest_python(self):
        versions = {
            "mcp": "2.0.0",
            "mcp-types": "2.0.0",
            "uvicorn": "0.52.1",
            "pydantic": "2.14.1",
            "jsonschema": "4.26.0",
            "rfc8785": "0.1.4",
        }
        with tempfile.TemporaryDirectory() as td:
            py = Path(td) / "python"
            py.write_bytes(b"runtime-carrier")
            c = {
                "mcp_runtime_python": str(py),
                "mcp_python_version": "3.15.1",
                "mcp_sqlite_version": "3.54.0",
            }
            old_sqlite = {
                "versions": versions,
                "forbidden": {"ordivon-protocol": None},
                "pythonVersion": "3.15.1",
                "sqliteVersion": "3.53.1",
            }
            with patch.object(d, "_runtime_versions", return_value=old_sqlite):
                with self.assertRaisesRegex(RuntimeError, "MCP embedded SQLite mismatch"):
                    d.runtime_check(c)

    def test_runtime_check_admits_only_matching_latest_python_and_sqlite(self):
        versions = {
            "mcp": "2.0.0",
            "mcp-types": "2.0.0",
            "uvicorn": "0.52.1",
            "pydantic": "2.14.1",
            "jsonschema": "4.26.0",
            "rfc8785": "0.1.4",
        }
        with tempfile.TemporaryDirectory() as td:
            py = Path(td) / "python"
            py.write_bytes(b"runtime-carrier")
            c = {
                "mcp_runtime_python": str(py),
                "mcp_python_version": "3.15.1",
                "mcp_sqlite_version": "3.54.0",
            }
            current = {
                "versions": versions,
                "forbidden": {"ordivon-protocol": None},
                "pythonVersion": "3.15.1",
                "sqliteVersion": "3.54.0",
            }
            with patch.object(d, "_runtime_versions", return_value=current):
                observed = d.runtime_check(c)
            self.assertEqual(observed["pythonVersion"], "3.15.1")
            self.assertEqual(observed["sqliteVersion"], "3.54.0")
            self.assertEqual(observed["versions"], versions)

    def test_loaded_mcp_unit_rejects_stale_systemd_projection(self):
        import subprocess

        unit = "ordivon-agent-automation-mcp.service"
        source_unit = b"[Service]\nType=exec\nExecStart=/bin/true\n"
        path = f"/etc/systemd/system/{unit}"
        current = f"NeedDaemonReload=no\nType=exec\nFragmentPath={path}\nDropInPaths=\n"
        cases = [
            (current, False),
            (current.replace("NeedDaemonReload=no", "NeedDaemonReload=yes"), True),
            (current.replace("Type=exec", "Type=simple"), True),
            (current.replace(path, "/tmp/forged.service"), True),
            (current.replace("DropInPaths=", "DropInPaths=/etc/systemd/system/extra.conf"), True),
            (current.replace("NeedDaemonReload=no\n", ""), True),
            (current + "Type=exec\n", True),
            ("NeedDaemonReload=no\nType=exec\n", True),
        ]
        for observation, should_fail in cases:
            with self.subTest(observation=observation):
                process = subprocess.CompletedProcess(
                    ["/usr/bin/systemctl", "show"], 0, stdout=observation
                )
                with patch.object(d.subprocess, "run", return_value=process):
                    if should_fail:
                        with self.assertRaises(RuntimeError):
                            d.check_loaded_unit(unit, source_unit)
                    else:
                        result = d.check_loaded_unit(unit, source_unit)
                        self.assertEqual(result["loadedType"], "exec")
                        self.assertEqual(result["daemonReloadRequired"], False)

    def test_loaded_mcp_unit_rejects_failed_systemctl_readback(self):
        import subprocess

        process = subprocess.CompletedProcess(
            ["/usr/bin/systemctl", "show"], 1, stdout="", stderr="failure"
        )
        with patch.object(d.subprocess, "run", return_value=process):
            with self.assertRaises(subprocess.CalledProcessError):
                d.check_loaded_unit(
                    "ordivon-agent-automation-mcp.service", b"[Service]\nType=exec\n"
                )

    def test_mcp_convergence_never_deletes_unresolved_backup_or_staging(self):
        for ext in ("previous", "staging"):
            with self.subTest(ext=ext), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                venv = root / "active"
                venv.mkdir()
                artifact = root / f"active.{ext}"
                artifact.mkdir()
                sentinel = artifact / "unique-recovery-record"
                sentinel.write_text("retain these bytes")
                c = {
                    "mcp_runtime_python": str(venv / "bin/python"),
                    "mcp_python_version": "3.15.1",
                    "mcp_requirements": "config/agent-automation-mcp-requirements.txt",
                }
                with (
                    patch.object(d, "runtime_check", side_effect=RuntimeError("old runtime")),
                    patch.object(d, "owner_uv_executable", return_value="/bin/false"),
                    patch.object(d.subprocess, "run") as run,
                ):
                    with self.assertRaisesRegex(RuntimeError, "unresolved MCP runtime"):
                        d.converge_runtime(c)
                self.assertEqual(sentinel.read_text(), "retain these bytes")
                run.assert_not_called()

    def test_mcp_convergence_rejects_missing_explicit_python_before_effects(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = {
                "mcp_runtime_python": str(root / "active" / "bin/python"),
                "mcp_python_version": "3.15.1",
                "mcp_python_executable": str(root / "missing-official-python"),
                "mcp_requirements": "config/agent-automation-mcp-requirements.txt",
            }
            with (
                patch.object(d, "runtime_check", side_effect=RuntimeError("old runtime")),
                patch.object(d, "owner_uv_executable", return_value="/bin/false"),
                patch.object(d.subprocess, "run") as run,
            ):
                with self.assertRaisesRegex(RuntimeError, "configured MCP Python executable"):
                    d.converge_runtime(c)
            run.assert_not_called()
            self.assertFalse((root / "active.staging").exists())
            self.assertFalse((root / "active.previous").exists())

    def test_mcp_convergence_keeps_rollback_until_process_consumer_proves_release(self):
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            venv = root / "active"
            old = venv / "bin/python"
            old.parent.mkdir(parents=True)
            old.write_text("old version with possible live consumers")
            c = {
                "mcp_runtime_python": str(old),
                "mcp_python_version": "3.15.1",
                "mcp_requirements": "config/agent-automation-mcp-requirements.txt",
            }

            def fake_run(args, **_kwargs):
                if args[1] == "venv":
                    target = Path(args[-1]) / "bin/python"
                    target.parent.mkdir(parents=True)
                    target.write_text("new qualified version")
                return subprocess.CompletedProcess(args, 0)

            def fake_runtime_check(data):
                candidate = Path(data["mcp_runtime_python"])
                if candidate.is_file() and candidate.read_text() == "new qualified version":
                    return {"pythonVersion": "3.15.1"}
                raise RuntimeError("previous runtime does not satisfy new contract")

            with (
                patch.object(d, "runtime_check", side_effect=fake_runtime_check),
                patch.object(d, "owner_uv_executable", return_value="/bin/false"),
                patch.object(d.subprocess, "run", side_effect=fake_run),
            ):
                result = d.converge_runtime(c)
            self.assertEqual(result["disposition"], "materialized")
            self.assertTrue(result["previousRuntimePreserved"])
            self.assertEqual(old.read_text(), "new qualified version")
            self.assertEqual(
                (root / "active.previous/bin/python").read_text(),
                "old version with possible live consumers",
            )
            self.assertFalse((root / "active.staging").exists())

    def test_mcp_convergence_cleans_only_its_failed_new_staging(self):
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            c = {
                "mcp_runtime_python": str(root / "active" / "bin/python"),
                "mcp_python_version": "3.15.1",
                "mcp_requirements": "config/agent-automation-mcp-requirements.txt",
            }

            def failing_venv(args, **_kwargs):
                staging = Path(args[-1])
                staging.mkdir()
                (staging / "partial").write_text("owned by this failed invocation")
                raise subprocess.CalledProcessError(2, args)

            with (
                patch.object(d, "runtime_check", side_effect=RuntimeError("old runtime")),
                patch.object(d, "owner_uv_executable", return_value="/bin/false"),
                patch.object(d.subprocess, "run", side_effect=failing_venv),
            ):
                with self.assertRaises(subprocess.CalledProcessError):
                    d.converge_runtime(c)
            self.assertFalse((root / "active.staging").exists())
            self.assertFalse((root / "active.previous").exists())

    def test_private_token_receipt_has_no_secret_derived_digest_and_preserves_existing(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "token"
            p.write_text("A" * 64 + "\n")
            p.chmod(0o600)
            before = p.read_bytes()
            receipt = d.private_token(p, True)
            self.assertEqual(p.read_bytes(), before)
            self.assertEqual(receipt, {"path": str(p), "mode": "0600", "present": True})
            self.assertNotIn("digest", receipt)

    def test_private_token_generation_is_private(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "token"
            receipt = d.private_token(p, True)
            self.assertEqual(oct(p.stat().st_mode & 0o777), "0o600")
            self.assertTrue(receipt["present"])
            self.assertGreaterEqual(len(p.read_text().strip()), 32)

    def test_runtime_config_is_the_browserless_authoritative_config(self):
        c = d.cfg()
        binding = {
            "kind": "network-v2",
            "name": "browserless-prod",
            "namespace": "nv2-browserless-prod",
            "generationDigest": "sha256:" + "a" * 64,
            "serviceUnit": "network-v2-browserless.target",
            "receiptPath": "/var/lib/network-v2/browserless-cutover/production-cutover.json",
        }
        with patch.object(browserless_deploy, "resolve_network_binding", return_value=binding):
            value = d.runtime_config(c)
            expected = d.render_browserless_config()
        for key, expected_value in expected.items():
            self.assertEqual(value[key], expected_value, key)
        self.assertEqual(value["materializationCarrier"], "windows-user-browser")
        self.assertEqual(
            value["windowsUserBrowser"]["workspaceId"],
            "ws-user-browser-prod-r1-20260922",
        )
        self.assertEqual(
            value["browserSubstrate"]["endpoints"][0]["networkNamespace"], "nv2-browserless-prod"
        )
        self.assertEqual(
            value["browserNetworkAuthority"],
            {k: binding[k] for k in ("kind", "name", "generationDigest", "serviceUnit")},
        )
        for key in (
            "playwrightPython",
            "browserlessSubmitScript",
            "browserlessReconcileScript",
            "browserlessTurnScript",
            "browserlessPreflightScript",
            "browserlessHumanResumeScript",
            "temporalPython",
            "temporalLaunchScript",
        ):
            self.assertTrue(Path(value[key]).is_absolute(), key)
        self.assertEqual(value["browserSubstrate"]["kind"], "browserless")
        self.assertEqual(value["temporalTaskQueue"], "ordivon-agent-automation")
        self.assertEqual(value["browserlessHumanHandoffMode"], "self-hosted-vnc")
        self.assertEqual(value["browserlessHumanHandoffMs"], 300000)
        self.assertEqual(value["browserlessSessionTimeoutMs"], 480000)

    def test_requirements_are_fully_frozen_and_retired_protocol_is_absent(self):
        c = d.cfg()
        req = (d.ROOT / str(c["mcp_requirements"])).read_text().splitlines()
        active = [row for row in req if row.strip()]
        self.assertGreaterEqual(len(active), 20)
        for row in active:
            self.assertTrue("==" in row and row.split("==", 1)[0] and row.split("==", 1)[1], row)
        self.assertIn("mcp==2.0.0", req)
        self.assertIn("uvicorn==0.52.1", req)
        self.assertFalse(any(row.startswith("ordivon-protocol") for row in active))

    def test_runtime_config_writable_roots_are_absolute(self):
        c = d.cfg()
        self.assertTrue(Path(c["state_root"]).is_absolute())
        self.assertEqual(c["mcp_config"], "/etc/ordivon/agent-automation-browserless.json")
        for retired in (
            "profile_templates",
            "profile_root",
            "display_range",
            "cdp_port_range",
            "browser_runtime_seconds",
            "network_namespace",
            "playwright_python",
            "wait_stable_seconds",
            "mcp_body_limit_bytes",
        ):
            self.assertNotIn(retired, c)

    def test_service_keeps_host_tmp_visible_for_display_census(self):
        unit = (d.ROOT / "systemd/ordivon-agent-automation-mcp.service").read_text()
        # An exec-synchronized start catches missing binaries before ExecStartPost.
        self.assertIn("Type=exec", unit)
        self.assertNotIn("Type=simple", unit)
        self.assertNotIn("PrivateTmp=true", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn(
            "ReadWritePaths=/root/.local/state/ordivon-workstation/agent-automation", unit
        )
        self.assertNotIn("/root/.cache/ordivon-agent-automation-v0-profiles", unit)
        self.assertIn(
            "agent_automation_browserless.py --config /etc/ordivon/agent-automation-browserless.json doctor",
            unit,
        )
        self.assertIn("RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_NETLINK", unit)
        self.assertNotIn("ordivon-host-mcp.service", unit)
        self.assertNotIn("ordivon-runtime.service", unit)

    def test_gateway_effect_credential_belongs_to_temporal_worker_not_mcp(self):
        """MCP transport must not inherit the Gateway credential used by effects."""
        mcp = (ROOT / "systemd/ordivon-agent-automation-mcp.service").read_text()
        worker = (ROOT / "systemd/ordivon-agent-temporal-worker.service").read_text()
        self.assertNotIn("LoadCredential=gateway-local-bearer:", mcp)
        self.assertNotIn("ORDIVON_AGENT_GATEWAY_BEARER_TOKEN_FILE", mcp)
        self.assertIn(
            "LoadCredential=gateway-local-bearer:/etc/ordivon/gateway/local-client-bearer",
            worker,
        )
        self.assertIn(
            "Environment=ORDIVON_AGENT_GATEWAY_BEARER_TOKEN_FILE=%d/gateway-local-bearer",
            worker,
        )

    def test_declared_path_tool_bootstraps_repo_scripts_when_materialized(self):
        import subprocess
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as td:
            installed = Path(td) / "agent-automation-mcp-deploy"
            shutil.copyfile(ROOT / "scripts/agent_automation_mcp_deploy.py", installed)
            installed.chmod(0o755)
            env = dict(os.environ)
            env["ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT"] = str(ROOT)
            env.pop("PYTHONPATH", None)
            proc = subprocess.run(
                [str(installed), "--help"],
                cwd=td,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("--check", proc.stdout)

    def test_source_revision_reads_immutable_release_marker_without_git_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            commit = "a" * 40
            (root / ".ordivon-agent-automation-release.json").write_text(
                json.dumps(
                    {"schemaVersion": 1, "commit": commit, "archiveDigest": "sha256:" + "b" * 64}
                )
            )
            with patch.object(d, "ROOT", root):
                self.assertEqual(d.source_revision(), commit)

    def test_mcp_release_includes_its_canonical_uv_tool_pin(self):
        import agent_automation_release as release

        self.assertIn("mise.toml", release.RELEASE_PATHS)

    def test_mcp_materialization_selects_one_project_mise_uv_not_global_venv(self):
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mise.toml").write_text('[tools]\nuv = "0.13.5"\n')
            selected = root / "versioned-uv"
            selected.write_text("#!/bin/sh\nexit 0\n")
            selected.chmod(0o755)
            process = subprocess.CompletedProcess(
                ["/usr/bin/mise", "which", "uv"], 0, stdout=str(selected) + "\n"
            )
            with (
                patch.object(d, "ROOT", root),
                patch.object(d.subprocess, "run", return_value=process) as invoked,
            ):
                self.assertEqual(d.owner_uv_executable(), str(selected))
            self.assertEqual(invoked.call_args.args[0], ["/usr/bin/mise", "which", "uv"])
            self.assertEqual(invoked.call_args.kwargs["cwd"], root)
            self.assertEqual(invoked.call_args.kwargs["env"]["MISE_OFFLINE"], "1")
            self.assertEqual(invoked.call_args.kwargs["env"]["MISE_AUTO_INSTALL"], "false")
            source = (ROOT / "scripts/agent_automation_mcp_deploy.py").read_text()
            self.assertNotIn('"/usr/bin/uv"', source)
            self.assertIn("uv = owner_uv_executable()", source)

    def test_mcp_owner_uv_fails_without_exact_release_pin_or_executable(self):
        import subprocess

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            selected = root / "not-executable"
            fake = subprocess.CompletedProcess(
                ["/usr/bin/mise", "which", "uv"], 0, stdout=str(selected) + "\n"
            )
            with (
                patch.object(d, "ROOT", root),
                patch.object(d.subprocess, "run", return_value=fake),
            ):
                with self.assertRaisesRegex(RuntimeError, "owner uv"):
                    d.owner_uv_executable()
                (root / "mise.toml").write_text('[tools]\nuv = "0.13.5"\n')
                with self.assertRaisesRegex(RuntimeError, "owner uv"):
                    d.owner_uv_executable()
                selected.write_text("inert")
                selected.chmod(0o600)
                with self.assertRaisesRegex(RuntimeError, "owner uv"):
                    d.owner_uv_executable()


if __name__ == "__main__":
    unittest.main()
