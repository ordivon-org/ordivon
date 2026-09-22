from __future__ import annotations

import base64
import hashlib
import json

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from starlette.applications import Starlette
from starlette.testclient import TestClient

from ordivon_gateway.external_worker import ExternalPullWorkerTransport
from ordivon_gateway.worker_http import attach_worker_routes


def _body_bytes(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def _signed_headers(
    private: Ed25519PrivateKey,
    *,
    worker_id: str,
    generation: int,
    timestamp_ms: int,
    nonce: str,
    path: str,
    body: dict,
) -> dict[str, str]:
    digest = "sha256:" + hashlib.sha256(_body_bytes(body)).hexdigest()
    canonical = "\n".join(
        [worker_id, str(generation), str(timestamp_ms), nonce, "POST", path, digest]
    ).encode()
    return {
        "X-Ordivon-Worker": worker_id,
        "X-Ordivon-Generation": str(generation),
        "X-Ordivon-Timestamp-Ms": str(timestamp_ms),
        "X-Ordivon-Nonce": nonce,
        "X-Ordivon-Signature": base64.b64encode(private.sign(canonical)).decode(),
        "Content-Type": "application/json",
    }


def test_worker_http_enrollment_signed_claim_and_completion(tmp_path) -> None:
    now = 1_800_000_000_000
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3", clock_ms=lambda: now)
    token_file = tmp_path / "enroll.token"
    token_file.write_text("one-time-staging-token\n")
    app = Starlette()
    attach_worker_routes(app, transport, enrollment_token_file=str(token_file))
    client = TestClient(app)

    private = Ed25519PrivateKey.generate()
    public = base64.b64encode(private.public_key().public_bytes_raw()).decode()
    enrollment = {
        "worker_id": "muse-http-r3",
        "provider_id": "muse",
        "generation": 1,
        "public_key": public,
        "capabilities": ["muse.shell.echo"],
    }
    denied = client.post("/v1/workers/enroll", json=enrollment)
    assert denied.status_code == 401
    accepted = client.post(
        "/v1/workers/enroll",
        json=enrollment,
        headers={"Authorization": "Bearer one-time-staging-token"},
    )
    assert accepted.status_code == 201

    operation = transport.submit(
        capability="muse.shell.echo",
        request_id="req-http-r3",
        parcel={"fixed_action": "echo", "args": ["hello"]},
    )

    claim_body: dict = {}
    claim_path = "/v1/workers/muse-http-r3/claim"
    claim_response = client.post(
        claim_path,
        content=_body_bytes(claim_body),
        headers=_signed_headers(
            private,
            worker_id="muse-http-r3",
            generation=1,
            timestamp_ms=now,
            nonce="claim-1",
            path=claim_path,
            body=claim_body,
        ),
    )
    assert claim_response.status_code == 200
    claim = claim_response.json()["parcel"]
    assert claim["operation_id"] == operation.operation_id

    started_body = {
        "attempt_id": claim["attempt_id"],
        "lease_id": claim["lease_id"],
    }
    started_path = f"/v1/operations/{operation.operation_id}/started"
    started = client.post(
        started_path,
        content=_body_bytes(started_body),
        headers=_signed_headers(
            private,
            worker_id="muse-http-r3",
            generation=1,
            timestamp_ms=now,
            nonce="start-1",
            path=started_path,
            body=started_body,
        ),
    )
    assert started.status_code == 200

    complete_body = {
        "attempt_id": claim["attempt_id"],
        "lease_id": claim["lease_id"],
        "exit_code": 0,
        "result": {"text": "hello"},
        "artifacts": [{"artifact_id": "result.txt", "content": "hello"}],
    }
    complete_path = f"/v1/operations/{operation.operation_id}/complete"
    complete = client.post(
        complete_path,
        content=_body_bytes(complete_body),
        headers=_signed_headers(
            private,
            worker_id="muse-http-r3",
            generation=1,
            timestamp_ms=now,
            nonce="complete-1",
            path=complete_path,
            body=complete_body,
        ),
    )
    assert complete.status_code == 200
    assert transport.get(operation.operation_id).state == "completed"


def test_worker_http_replayed_signature_is_rejected(tmp_path) -> None:
    now = 1_800_000_000_000
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3", clock_ms=lambda: now)
    private = Ed25519PrivateKey.generate()
    public = base64.b64encode(private.public_key().public_bytes_raw()).decode()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public,
        capabilities=["muse.shell.echo"],
    )
    app = Starlette()
    attach_worker_routes(app, transport)
    client = TestClient(app)

    body = {"capabilities": ["muse.shell.echo"]}
    path = "/v1/workers/worker-1/heartbeat"
    headers = _signed_headers(
        private,
        worker_id="worker-1",
        generation=1,
        timestamp_ms=now,
        nonce="same-nonce",
        path=path,
        body=body,
    )
    assert client.post(path, content=_body_bytes(body), headers=headers).status_code == 200
    replay = client.post(path, content=_body_bytes(body), headers=headers)
    assert replay.status_code == 401
    assert replay.json()["error"] == "worker request replay detected"
