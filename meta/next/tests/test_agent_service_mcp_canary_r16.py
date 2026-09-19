from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


MCP_AVAILABLE = importlib.util.find_spec("mcp") is not None


@unittest.skipUnless(MCP_AVAILABLE, "mcp deployment dependency is tested in the deployment venv")
class AgentServiceMcpCanaryR16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import scripts.agent_service_mcp as module
        cls.module = module

    def _token(self, root: Path) -> Path:
        path = root / "token"
        path.write_text("x" * 48, encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
        return path

    def test_settings_reject_non_loopback_bind(self):
        with tempfile.TemporaryDirectory() as tmp:
            token = self._token(Path(tmp))
            with self.assertRaises(ValueError):
                self.module.McpSettings(
                    source_root=Path.cwd().resolve(),
                    token_file=token.resolve(),
                    bind_host="0.0.0.0",
                )

    def test_contract_is_read_only_and_production_blocked(self):
        value = self.module._contract(Path.cwd().resolve())
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["compositionRoot"], "open_agent_service")
        self.assertFalse(value["writeSurfaceEnabled"])
        self.assertFalse(value["providerEffectSurfaceEnabled"])
        self.assertFalse(value["runtimeMutationSurfaceEnabled"])
        self.assertFalse(value["hostMutationSurfaceEnabled"])
        self.assertEqual(value["productionDeployment"], "NOT_ADMITTED")

    def test_server_exposes_exactly_four_read_only_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = self.module.McpSettings(
                source_root=Path.cwd().resolve(),
                token_file=self._token(Path(tmp)).resolve(),
                port=8894,
            )
            server = self.module.build_server(settings)
            tools = server._tool_manager.list_tools()
            self.assertEqual(
                sorted(tool.name for tool in tools),
                ["architecture.identity", "deployment.snapshot", "service.contract", "service.doctor"],
            )
            for tool in tools:
                self.assertTrue(tool.annotations.read_only_hint)
                self.assertFalse(tool.annotations.destructive_hint)
                self.assertTrue(tool.annotations.idempotent_hint)
                self.assertFalse(tool.annotations.open_world_hint)

    def test_check_mode_needs_no_database_or_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            token = self._token(Path(tmp))
            env = dict(os.environ)
            env["ORDIVON_AGENT_SERVICE_SOURCE_ROOT"] = str(Path.cwd().resolve())
            proc = subprocess.run(
                [
                    os.sys.executable,
                    "scripts/agent_service_mcp.py",
                    "--source-root",
                    str(Path.cwd().resolve()),
                    "--token-file",
                    str(token.resolve()),
                    "--bind",
                    "127.0.0.1",
                    "--port",
                    "8894",
                    "--check",
                ],
                cwd=Path.cwd(),
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('"toolCount": 4', proc.stdout)
            self.assertIn('"readOnlyCanary": true', proc.stdout)
            self.assertIn('"productionDeployment": "NOT_ADMITTED"', proc.stdout)

    def test_deployment_uses_standard_opentelemetry_zero_code_boundary(self):
        requirements = Path("config/agent-service-mcp-requirements.txt").read_text(encoding="utf-8")
        unit = Path("systemd/ordivon-agent-service-canary-mcp.service").read_text(encoding="utf-8")
        self.assertIn("opentelemetry-distro[otlp]==0.65b0", requirements)
        self.assertIn("opentelemetry-instrumentation-starlette==0.65b0", requirements)
        self.assertIn(".venv/bin/opentelemetry-instrument", unit)
        self.assertIn("Environment=OTEL_SERVICE_NAME=ordivon-agent-service-canary", unit)
        self.assertIn("Environment=OTEL_TRACES_EXPORTER=none", unit)
        self.assertIn("Environment=OTEL_METRICS_EXPORTER=none", unit)
        self.assertIn("Environment=OTEL_LOGS_EXPORTER=none", unit)
        self.assertIn("EnvironmentFile=-/etc/ordivon/agent-service-otel.env", unit)
        self.assertNotIn("opentelemetry", Path("agent_service/evidence.py").read_text(encoding="utf-8"))

    def test_token_permissions_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "token"
            path.write_text("x" * 48, encoding="utf-8")
            path.chmod(0o644)
            with self.assertRaises(RuntimeError):
                self.module._read_token(path)


if __name__ == "__main__":
    unittest.main()
