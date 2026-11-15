"""Prove cold-CI provisioning and offline Host/Gateway MCP consumer are distinct.

The integration consumer depends on the Gateway's *locked* dependency set.
Stub the native Mise/OPA tool locator and uv, without contacting network
or building Rust; the real PG18/OPA consumer executes in Host queue.
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
            # GitHub cold runners do not install mise under /usr/bin.
            # The wrapper must resolve the *existing PATH* tool, with OPA
            # provisioned by Security Owner's pinned mise profile.
            opa = root / "opa"
            opa.write_text("#!/usr/bin/bash\nexit 0\n", encoding="utf-8")
            opa.chmod(0o755)
            mise = root / "mise"
            mise_log = root / "mise_calls"
            mise.write_text(
                '#!/usr/bin/bash\n'
                'printf "%s\\n" "$*" >> "$MISE_FAKE_LOG"\n'
                'if [[ "$*" == *"which opa" ]]; then printf "%s\\n" "$OPA_FAKE_BINARY"; fi\n',
                encoding="utf-8",
            )
            mise.chmod(0o755)
            # This test checks provisioning order, not whether CI built Rust.
            # Supply an executable fixture so cold CI never depends on Cargo's
            # target_dir, private fd paths, or a prebuilt Host binary.
            rust_binary = root / "ordivon-host-rust"
            rust_binary.write_text("#!/usr/bin/bash\nexit 0\n", encoding="utf-8")
            rust_binary.chmod(0o755)
            env = dict(os.environ)
            env["PATH"] = str(root) + os.pathsep + env["PATH"]
            env["UV_FAKE_LOG"] = str(log)
            env["MISE_FAKE_LOG"] = str(mise_log)
            env["OPA_FAKE_BINARY"] = str(opa)
            env["HOST_RUST_BINARY"] = str(rust_binary)
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
            pinned = mise_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                pinned,
                [
                    f"-C {ROOT / 'platform/security'} install opa",
                    f"-C {ROOT / 'platform/security'} which opa",
                ],
            )


if __name__ == "__main__":
    unittest.main()
