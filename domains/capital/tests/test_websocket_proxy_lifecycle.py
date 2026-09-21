from __future__ import annotations

import unittest

from websockets.client import ClientProtocol
from websockets.uri import parse_uri

from ordivon_capital.market.websocket_proxy_lifecycle import (
    NetworkV2ProxyClientConnection,
)


class NetworkV2ProxyClientConnectionTests(unittest.IsolatedAsyncioTestCase):
    def make_connection(self) -> NetworkV2ProxyClientConnection:
        protocol = ClientProtocol(parse_uri("wss://example.com/"))
        return NetworkV2ProxyClientConnection(protocol)

    async def test_connection_lost_before_connection_made_is_safe(self) -> None:
        connection = self.make_connection()
        self.assertFalse(hasattr(connection, "recv_messages"))
        self.assertFalse(hasattr(connection, "transport"))

        connection.connection_lost(ConnectionResetError("synthetic TLS loss"))

        self.assertTrue(connection.connection_lost_waiter.done())
        self.assertFalse(hasattr(connection, "recv_messages"))
        self.assertFalse(hasattr(connection, "transport"))

    async def test_eof_before_connection_made_is_safe(self) -> None:
        connection = self.make_connection()
        self.assertFalse(hasattr(connection, "transport"))

        self.assertIsNone(connection.eof_received())

        self.assertFalse(hasattr(connection, "transport"))

    async def test_normal_connection_made_delegates_to_upstream(self) -> None:
        connection = self.make_connection()

        class Transport:
            def pause_reading(self) -> None:
                pass

            def resume_reading(self) -> None:
                pass

            def set_write_buffer_limits(self, high: int | None, low: int | None) -> None:
                self.high = high
                self.low = low

        transport = Transport()
        connection.connection_made(transport)  # type: ignore[arg-type]

        self.assertTrue(hasattr(connection, "recv_messages"))
        self.assertIs(connection.transport, transport)


class WebsocketCallSiteTests(unittest.TestCase):
    def test_market_websocket_callers_use_guard_factory(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        for rel in (
            "src/ordivon_capital/market/crypto_public_streaming.py",
            "src/ordivon_capital/market/crypto_stream_resilience.py",
        ):
            source = (root / rel).read_text()
            self.assertIn(
                "create_connection=NetworkV2ProxyClientConnection",
                source,
            )


if __name__ == "__main__":
    unittest.main()


class R3PostInjectionEvidenceTests(unittest.TestCase):
    def test_reconnect_evidence_is_gated_after_injection(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        source = (
            root / "src/ordivon_capital/market/crypto_stream_resilience.py"
        ).read_text()
        self.assertIn("injected_generation: int | None = None", source)
        self.assertIn('int(event["monoNs"]) > injected_mono', source)
        self.assertIn('int(event["generation"]) > injected_generation', source)
        self.assertIn('"injectedGeneration": injected_generation', source)
