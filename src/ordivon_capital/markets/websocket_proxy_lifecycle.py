from __future__ import annotations

import asyncio

from websockets.asyncio.client import ClientConnection


class NetworkV2ProxyClientConnection(ClientConnection):
    """Guard websockets' HTTP-proxy TLS pre-connection callback window.

    websockets 17.1 hands an HTTP CONNECT transport to ClientConnection before
    asyncio.start_tls() completes, while ClientConnection.recv_messages and
    .transport are initialized only by connection_made(). If TLS setup loses
    the transport in that window, asyncio may call connection_lost() or
    eof_received() on a partially initialized connection.

    This subclass uses websockets' documented create_connection extension
    point. It changes only callbacks that arrive before connection_made();
    normal WebSocket protocol handling is delegated unchanged to upstream.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._ordivon_connection_made = False

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._ordivon_connection_made = True
        super().connection_made(transport)

    def connection_lost(self, exc: Exception | None) -> None:
        if self._ordivon_connection_made:
            super().connection_lost(exc)
            return

        # start_tls() failed after transport.set_protocol(self), but before
        # websockets called connection_made(). The upstream callback assumes
        # recv_messages exists; finalize only state that is already initialized.
        self.protocol.receive_eof()
        self.set_recv_exc(exc)
        self.terminate_pending_pings()
        if self.keepalive_task is not None:
            self.keepalive_task.cancel()
            self.keepalive_task = None
        if not self.connection_lost_waiter.done():
            self.connection_lost_waiter.set_result(None)

    def eof_received(self) -> None:
        if self._ordivon_connection_made:
            super().eof_received()
            return

        # Upstream eof_received() calls send_data(), which assumes .transport
        # exists. Before connection_made(), receive_eof() is the only valid
        # state transition.
        self.protocol.receive_eof()
