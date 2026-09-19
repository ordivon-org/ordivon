from __future__ import annotations

import unittest
from pathlib import Path

import agent_service
import agent_service.provider_adapters as providers


class HandRolledProtocolClientsRetiredTests(unittest.TestCase):
    def test_agent_service_does_not_export_transport_clients(self) -> None:
        for name in ("A2AJsonRpcHttpClient", "MCPTasksHttpClient"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(providers, name))
                self.assertFalse(hasattr(agent_service, name))

    def test_provider_adapters_do_not_own_http_or_json_rpc_transport(self) -> None:
        source = Path("agent_service/provider_adapters.py").read_text()
        for forbidden in (
            "urllib.request",
            "urllib.error",
            "_parse_json_rpc_response",
            "_safe_http_endpoint",
            "_merge_headers",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_semantic_provider_adapters_remain(self) -> None:
        self.assertTrue(hasattr(providers, "A2AQuiescenceAdapter"))
        self.assertTrue(hasattr(providers, "MCPTaskQuiescenceAdapter"))
        self.assertTrue(hasattr(providers, "EffectLedgerReplaySafetyAdapter"))


if __name__ == "__main__":
    unittest.main()
