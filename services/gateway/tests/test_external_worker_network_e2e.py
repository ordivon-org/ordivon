from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import socket
import threading
import time
from urllib.request import Request, urlopen

import uvicorn
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from ordivon_gateway.external_worker import ExternalPullWorkerTransport
from ordivon_gateway.mcp_server import build_http_app, build_server
from ordivon_gateway.service import GatewayService


class NoOwnerCaller:
    def is_configured(self, owner_id: str) -> bool:
        return False

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict):
        raise AssertionError((owner_id, tool_name, arguments))


def signed_headers(private, worker_id, generation, nonce, path, body):
    body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    digest = "sha256:" + hashlib.sha256(body_bytes).hexdigest()
    now = time.time_ns() // 1_000_000
    canonical = "\n".join(
        [worker_id, str(generation), str(now), nonce, "POST", path, digest]
    ).encode()
    return {
        "X-Ordivon-Worker": worker_id,
        "X-Ordivon-Generation": str(generation),
        "X-Ordivon-Timestamp-Ms": str(now),
        "X-Ordivon-Nonce": nonce,
        "X-Ordivon-Signature": base64.b64encode(private.sign(canonical)).decode(),
        "Content-Type": "application/json",
    }


def test_real_http_mcp_submit_to_signed_worker_completion(tmp_path) -> None:
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3")
    private = Ed25519PrivateKey.generate()
    public = base64.b64encode(private.public_key().public_bytes_raw()).decode()
    transport.enroll(
        worker_id="fake-http-worker",
        provider_id="test",
        generation=1,
        public_key_b64=public,
        capabilities=["muse.shell.echo"],
    )
    service = GatewayService(NoOwnerCaller(), external_workers=transport)
    app = build_http_app(
        build_server(service),
        host="127.0.0.1",
        path="/mcp",
        public_origin=None,
        access_verifier=None,
        external_workers=transport,
    )

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="on"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.02)
    assert server.started

    async def submit_and_finish() -> None:
        transport_io = streamable_http_client(f"http://127.0.0.1:{port}/mcp")
        async with Client(transport_io, raise_exceptions=True) as client:
            submitted = await client.call_tool(
                "execution.submit",
                {
                    "capability": "muse.shell.echo",
                    "requestId": "req-network-e2e",
                    "workspaceId": "ws-external",
                    "executable": "echo",
                    "args": ["hello"],
                },
            )
            receipt = submitted.structured_content
            assert receipt is not None
            operation_ref = receipt["operation_ref"]

            claim_path = "/v1/workers/fake-http-worker/claim"
            claim_body = {}
            claim_request = Request(
                f"http://127.0.0.1:{port}{claim_path}",
                data=json.dumps(claim_body, sort_keys=True, separators=(",", ":")).encode(),
                headers=signed_headers(
                    private, "fake-http-worker", 1, "claim-network", claim_path, claim_body
                ),
                method="POST",
            )
            with urlopen(claim_request, timeout=5) as response:
                parcel = json.loads(response.read())["parcel"]

            complete_path = f"/v1/operations/{parcel['operation_id']}/complete"
            complete_body = {
                "attempt_id": parcel["attempt_id"],
                "lease_id": parcel["lease_id"],
                "exit_code": 0,
                "result": {"text": "hello"},
                "artifacts": [{"artifact_id": "result.txt", "content": "hello"}],
            }
            complete_request = Request(
                f"http://127.0.0.1:{port}{complete_path}",
                data=json.dumps(complete_body, sort_keys=True, separators=(",", ":")).encode(),
                headers=signed_headers(
                    private,
                    "fake-http-worker",
                    1,
                    "complete-network",
                    complete_path,
                    complete_body,
                ),
                method="POST",
            )
            with urlopen(complete_request, timeout=5) as response:
                assert response.status == 200

            observed = await client.call_tool("execution.get", {"operationRef": operation_ref})
            value = observed.structured_content
            assert value is not None
            assert value["terminal"] is True
            assert value["state"] == "completed"
            assert value["artifact_ids"] == ["result.txt"]

    try:
        asyncio.run(submit_and_finish())
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
    assert not thread.is_alive()
