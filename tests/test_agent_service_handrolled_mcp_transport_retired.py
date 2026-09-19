from __future__ import annotations

import unittest
from pathlib import Path

import agent_service
from agent_service import host_board, runtime_mcp


class HandRolledMcpTransportRetiredTests(unittest.TestCase):
    def test_http_transport_clients_are_absent(self) -> None:
        self.assertFalse(hasattr(runtime_mcp, "RuntimeMcpHttpClient"))
        self.assertFalse(hasattr(agent_service, "RuntimeMcpHttpClient"))
        self.assertFalse(hasattr(host_board, "HostBoardMcpHttpClient"))

    def test_semantic_adapters_do_not_offer_env_bound_transport_factories(self) -> None:
        self.assertFalse(hasattr(runtime_mcp.RuntimeMcpAdapter, "from_local_runtime_env"))
        self.assertFalse(hasattr(runtime_mcp.RuntimeMcpArtifactReader, "from_local_runtime_env"))
        self.assertFalse(hasattr(host_board.HostBoardMcpAdapter, "from_local_host_env"))

    def test_semantic_modules_do_not_own_http_transport(self) -> None:
        for module_path in (
            Path("agent_service/runtime_mcp.py"),
            Path("agent_service/host_board.py"),
        ):
            source = module_path.read_text()
            with self.subTest(module=module_path.name):
                self.assertNotIn("urllib.request", source)
                self.assertNotIn("urllib.error", source)

    def test_semantic_adapters_remain(self) -> None:
        self.assertTrue(hasattr(runtime_mcp, "RuntimeMcpAdapter"))
        self.assertTrue(hasattr(runtime_mcp, "RuntimeMcpArtifactReader"))
        self.assertTrue(hasattr(host_board, "HostBoardMcpAdapter"))


if __name__ == "__main__":
    unittest.main()
