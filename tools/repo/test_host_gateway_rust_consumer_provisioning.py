"""Prove cold-CI provisioning and offline Host/Gateway MCP consumer are distinct.

The integration consumer depends on the Gateway's *locked* dependency set.
Mock only the uv executable; the real PG18/SDK consumer executes in Host queue.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/repo/run_host_gateway_rust_consumer.sh"


class HostGatewayProvisioningTests(unittest.TestCase):
    def test_locked_sync_precedes_offline_sdk_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            uv = root / "uv"
            log = root / "uv_calls"
            uv.write_text(
                '#!/usr/bin/bash\nprintf "%s\\n" "$*" >> "$UV_FAKE_LOG"\n',
                encoding="utf-8",
            )
            uv.chmod(0o755)
            env = dict(os.environ)
            env["PATH"] = str(root) + os.pathsep + env["PATH"]
            env["UV_FAKE_LOG"] = str(log)
            subprocess.run(
                ["/usr/bin/bash", str(RUNNER)],
                cwd=ROOT,
                env=env,
                check=True,
                timeout=30,
                capture_output=True,
                text=True,
            )
            lines = log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0].split(), ["sync", "--locked", "--quiet"])
            self.assertTrue(lines[1].startswith("run --offline python "))
            self.assertIn("native_rust_host_consumer_smoke.py", lines[1])
            self.assertIn("ordivon-host-rust", lines[1])
            self.assertNotIn("--offline", lines[0])


if __name__ == "__main__":
    unittest.main()
