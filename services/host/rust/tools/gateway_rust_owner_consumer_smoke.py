"""Real Gateway SDK -> real Rust Host HTTP -> disposable PG18 consumer proof.

This uses the production Gateway MCP client transport and Gateway server SDK.
Only the Rust Host endpoint is redirected to a loopback, disposable test owner.
No production Gateway config, broker, extra protocol, or database is created.
"""
from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys

from mcp import Client
from ordivon_gateway.mcp_server import build_server
from ordivon_gateway.service import GatewayService
from ordivon_gateway.upstream import McpOwnerCaller, OwnerCallError, OwnerEndpoint


def require_disposable_pg18() -> None:
    dsn = os.environ.get("HOST_RUST_TEST_DSN")
    if not dsn or "127.0.0.1" not in dsn or dsn != os.environ.get("ORDIVON_HOST_V2_DSN"):
        raise RuntimeError("Gateway→Rust owner consumer requires the same disposable loopback PG18")
    if os.environ.get("ORDIVON_GATEWAY_HOST_URL"):
        # Prevent an installed production Host config from being mistaken for a
        # disposable owner in the test process, even though we inject an explicit endpoint.
        raise RuntimeError("Gateway→Rust smoke refuses inherited production Host URL")


async def consume_owner(url: str, child: subprocess.Popen) -> None:
    # This is exactly the existing Gateway's production upstream implementation,
    # not an ad hoc requests/httpx proxy and not a stub Owner caller.
    owner = McpOwnerCaller({"host": OwnerEndpoint(url=url)})
    gateway = GatewayService(owner)
    try:
        for attempt in range(90):
            if child.poll() is not None:
                raise RuntimeError("Rust Host process exited before real Gateway owner connect")
            try:
                await owner.call_tool("host", "host.status", {"detail": "summary"})
                break
            except OwnerCallError:
                if attempt == 89:
                    raise
                await asyncio.sleep(0.15)
        async with Client(build_server(gateway), raise_exceptions=False) as agent:
            registered = {tool.name for tool in (await agent.list_tools()).tools}
            # Gateway is intentionally a thinner 29-tool Host projection; the
            # versioned Work engagement extension has not been installed here.
            assert {"work.get", "host.status", "space.list", "topic.resume"} <= registered
            assert "work.engagement.advance" not in registered
            assert "work.engagement.list" not in registered
            assert "host.pool.stats" not in registered
            assert "message.get" not in registered

            async def roundtrip(name: str, args: dict) -> dict:
                expected = await owner.call_tool("host", name, args)
                result = await agent.call_tool(name, args)
                assert not result.is_error, (name, result)
                actual = result.structured_content
                assert isinstance(actual, dict), (name, "Gateway lost structured output")
                if name == "host.status":
                    # Independent Host reads are two distinct observations, so
                    # their volatile observedAtMs can legitimately differ.
                    # Compare every stable field; never hide Doctor or authority drift.
                    assert type(actual.get("observedAtMs")) is int
                    assert type(expected.get("observedAtMs")) is int
                    actual = {key: val for key, val in actual.items() if key != "observedAtMs"}
                    expected_stable = {
                        key: val for key, val in expected.items() if key != "observedAtMs"
                    }
                    assert actual == expected_stable, (
                        name, "Gateway changed stable Host status/Doctor semantics",
                    )
                else:
                    assert actual == expected, (name, "Gateway changed Host payload")
                return expected

            current = await roundtrip(
                "work.get", {"workRef": "work:test:rust-mcp-stdio", "revision": 2},
            )
            assert current["revision"] == 2
            listing = await roundtrip(
                "space.list", {"limit": 2, "maxBytes": 262144},
            )
            assert isinstance(listing["spaces"], list)
            status = await roundtrip("host.status", {"detail": "integrity"})
            assert status["detail"] == "integrity"
            assert status["authority"]["journalSchema"] == 13
            topic = await roundtrip(
                "topic.resume",
                {"topicRef": "topic:test:rust-mcp-social", "afterSequence": 0},
            )
            assert len(topic["messages"]) >= 2

            missing = await agent.call_tool(
                "work.get", {"workRef": "work:r9:missing:never-created"},
            )
            assert missing.is_error, missing
            envelope = missing.structured_content
            assert isinstance(envelope, dict), missing
            assert envelope.get("error", {}).get("code") == "NOT_FOUND", envelope
            assert envelope.get("error", {}).get("resourceKind") == "work", envelope
            assert envelope.get("error", {}).get("resourceRef") == (
                "work:r9:missing:never-created"
            ), envelope
            assert envelope["gatewayOwnerId"] == "host"
            assert envelope["gatewayOwnerTool"] == "work.get"

            print(
                "GATEWAY_REAL_RUST_OWNER_CONSUMER_PASS"
                " sdk_gateway=true sdk_upstream=true rust_http=true"
                " actual_payloads=4 typed_missing=1"
                " installed_gateway=false production_effect=false",
                flush=True,
            )
    finally:
        await gateway.aclose()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("expected Rust Host executable")
    require_disposable_pg18()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(os.environ)
    env.update(
        ORDIVON_HOST_V2_TRANSPORT="streamable-http",
        ORDIVON_HOST_V2_HOST="127.0.0.1",
        ORDIVON_HOST_V2_PORT=str(port),
        ORDIVON_HOST_V2_PATH="/mcp",
    )
    child = subprocess.Popen(
        [sys.argv[1]],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        asyncio.run(consume_owner(f"http://127.0.0.1:{port}/mcp", child))
    finally:
        child.terminate()
        try:
            child.wait(timeout=6)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=6)


if __name__ == "__main__":
    main()
