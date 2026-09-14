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
        self.assertEqual(value, expected)
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


if __name__ == "__main__":
    unittest.main()
