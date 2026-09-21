from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib.metadata as metadata
import json
import struct
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import websockets
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK, InvalidStatus

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


@dataclass(frozen=True)
class Frame:
    opcode: int
    payload: bytes
    masked: bool


async def _read_http_headers(reader: asyncio.StreamReader) -> dict[str, str]:
    raw = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=2)
    lines = raw.decode("iso-8859-1").split("\r\n")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


async def _handshake(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> dict[str, str]:
    headers = await _read_http_headers(reader)
    key = headers["sec-websocket-key"]
    accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    writer.write(
        (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n"
            "\r\n"
        ).encode("ascii")
    )
    await writer.drain()
    return headers


async def _read_frame(reader: asyncio.StreamReader) -> Frame:
    first, second = await reader.readexactly(2)
    opcode = first & 0x0F
    masked = bool(second & 0x80)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    mask = await reader.readexactly(4) if masked else b""
    payload = await reader.readexactly(length)
    if masked:
        payload = bytes(byte ^ mask[i % 4] for i, byte in enumerate(payload))
    return Frame(opcode=opcode, payload=payload, masked=masked)


def _server_frame(opcode: int, payload: bytes = b"") -> bytes:
    first = 0x80 | opcode
    size = len(payload)
    if size < 126:
        return bytes([first, size]) + payload
    if size < 65536:
        return bytes([first, 126]) + struct.pack("!H", size) + payload
    return bytes([first, 127]) + struct.pack("!Q", size) + payload


async def _with_server(
    handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]],
    client: Callable[[str], Awaitable[None]],
) -> None:
    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    sockets = server.sockets or []
    assert len(sockets) == 1
    port = int(sockets[0].getsockname()[1])
    try:
        async with server:
            await client(f"ws://127.0.0.1:{port}/wire")
    finally:
        server.close()
        await server.wait_closed()


async def _protocol_roundtrip() -> dict[str, bool]:
    observed: dict[str, bool] = {}

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        headers = await _handshake(reader, writer)
        observed["upgradeHeaders"] = (
            headers.get("upgrade", "").lower() == "websocket"
            and "upgrade" in headers.get("connection", "").lower()
        )
        frame = await _read_frame(reader)
        observed["clientTextMasked"] = (
            frame.opcode == 0x1
            and frame.masked
            and frame.payload.decode("utf-8") == "hello-α"
        )

        writer.write(_server_frame(0x1, "world-现货".encode()))
        await writer.drain()

        writer.write(_server_frame(0x9, b"ping-r17"))
        await writer.drain()
        pong = await asyncio.wait_for(_read_frame(reader), timeout=2)
        observed["automaticPong"] = (
            pong.opcode == 0xA and pong.masked and pong.payload == b"ping-r17"
        )

        close_payload = struct.pack("!H", 1000) + b"done"
        writer.write(_server_frame(0x8, close_payload))
        await writer.drain()
        close = await asyncio.wait_for(_read_frame(reader), timeout=2)
        observed["closeHandshake"] = close.opcode == 0x8 and close.masked
        writer.close()
        await writer.wait_closed()

    async def client(uri: str) -> None:
        async with connect(
            uri,
            proxy=None,
            open_timeout=1,
            ping_interval=None,
            close_timeout=1,
            max_size=64,
        ) as ws:
            await ws.send("hello-α")
            message = await ws.recv()
            observed["serverTextReceived"] = message == "world-现货"
            try:
                await ws.recv()
            except ConnectionClosedOK:
                observed["cleanCloseObserved"] = True

    await _with_server(handler, client)
    return observed


async def _max_size_rejection() -> bool:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _handshake(reader, writer)
        writer.write(_server_frame(0x1, b"x" * 256))
        await writer.drain()
        try:
            await asyncio.wait_for(_read_frame(reader), timeout=2)
        except (TimeoutError, asyncio.IncompleteReadError):
            pass
        writer.close()
        await writer.wait_closed()

    outcome = False

    async def client(uri: str) -> None:
        nonlocal outcome
        try:
            async with connect(uri, proxy=None, open_timeout=1, max_size=32) as ws:
                await ws.recv()
        except ConnectionClosedError as exc:
            outcome = exc.sent is not None and exc.sent.code == 1009

    await _with_server(handler, client)
    return outcome


async def _invalid_status_rejection() -> bool:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _read_http_headers(reader)
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    outcome = False

    async def client(uri: str) -> None:
        nonlocal outcome
        try:
            async with connect(uri, proxy=None, open_timeout=1):
                pass
        except InvalidStatus:
            outcome = True

    await _with_server(handler, client)
    return outcome


async def _opening_timeout() -> bool:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await _read_http_headers(reader)
        await asyncio.sleep(0.5)
        writer.close()
        await writer.wait_closed()

    outcome = False

    async def client(uri: str) -> None:
        nonlocal outcome
        try:
            async with connect(uri, proxy=None, open_timeout=0.05):
                pass
        except TimeoutError:
            outcome = True

    await _with_server(handler, client)
    return outcome


def _footprint() -> tuple[int, int]:
    dist = metadata.distribution("websockets")
    files = list(dist.files or [])
    total = 0
    for item in files:
        path = dist.locate_file(item)
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            pass
    return len(files), total


async def _main() -> None:
    if websockets.__version__ != "17.1":
        raise SystemExit(f"unexpected websockets version: {websockets.__version__}")
    protocol = await _protocol_roundtrip()
    required = {
        "upgradeHeaders",
        "clientTextMasked",
        "serverTextReceived",
        "automaticPong",
        "closeHandshake",
        "cleanCloseObserved",
    }
    if set(protocol) != required or not all(protocol.values()):
        raise SystemExit(f"protocol falsification failed: {protocol}")

    max_size = await _max_size_rejection()
    invalid_status = await _invalid_status_rejection()
    opening_timeout = await _opening_timeout()
    if not (max_size and invalid_status and opening_timeout):
        raise SystemExit(
            f"failure-path falsification failed: "
            f"max_size={max_size} invalid_status={invalid_status} timeout={opening_timeout}"
        )

    files, bytes_ = _footprint()
    dist = metadata.distribution("websockets")
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.markets.websockets-owner-requalification-r17",
        "standing": "PASS_RETAIN_WEBSOCKETS_NARROW_PROTOCOL_OWNER",
        "contract": "contracts/websocket-client-mechanics-v1.json",
        "version": websockets.__version__,
        "python3147ExecutableQualification": "PASS",
        "requiresPython": dist.metadata.get("Requires-Python"),
        "thirdPartyDependencies": len(dist.requires or []),
        "installedFileCount": files,
        "installedFootprintBytes": bytes_,
        "rawWireFalsification": {
            **protocol,
            "maxSizeFailClosed": max_size,
            "invalidHandshakeStatusRejected": invalid_status,
            "openingHandshakeTimeout": opening_timeout,
        },
        "localBaseline": {
            "stdlibWebSocketClientAvailable": False,
            "contractEquivalentLocalBaselineCredible": False,
            "reason": (
                "stdlib has asyncio/socket/TLS/HTTP primitives but no RFC 6455 client; "
                "a substitute would need to implement handshake, masking, control frames, "
                "close semantics, message limits, and proxy/TLS integration"
            ),
        },
        "externalOwnerAdmitted": True,
        "externalFinancialWriteAttempted": False,
    }
    print(json.dumps(result, sort_keys=True))


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
