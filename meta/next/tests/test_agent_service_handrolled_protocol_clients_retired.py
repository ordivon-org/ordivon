from __future__ import annotations

import unittest

import agent_service
import agent_service.provider_adapters as providers


class HandRolledProtocolClientsRetiredTests(unittest.TestCase):
    def test_agent_service_does_not_export_transport_clients(self) -> None:
        for name in ("A2AJsonRpcHttpClient", "MCPTasksHttpClient"):
            with self.subTest(name=name):
                self.assertFalse(hasattr(providers, name))
                self.assertFalse(hasattr(agent_service, name))

    def test_retired_transport_helpers_remain_absent(self) -> None:
        for name in (
            "_parse_json_rpc_response",
            "_safe_http_endpoint",
            "_merge_headers",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(providers, name))

    def test_semantic_provider_adapters_remain(self) -> None:
        self.assertTrue(hasattr(providers, "A2AQuiescenceAdapter"))
        self.assertTrue(hasattr(providers, "MCPTaskQuiescenceAdapter"))
        self.assertTrue(hasattr(providers, "EffectLedgerReplaySafetyAdapter"))


if __name__ == "__main__":
    unittest.main()
