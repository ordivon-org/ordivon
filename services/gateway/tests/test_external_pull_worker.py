from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from dataclasses import dataclass

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ordivon_gateway.external_worker import (
    ExternalPullWorkerTransport,
    WorkerAuthError,
    WorkerConflict,
)
from ordivon_gateway.service import GatewayService


class NoOwnerCaller:
    def is_configured(self, owner_id: str) -> bool:
        return False

    async def call_tool(self, owner_id: str, tool_name: str, arguments: dict):
        raise AssertionError((owner_id, tool_name, arguments))


@dataclass
class Clock:
    now: int = 1_800_000_000_000

    def __call__(self) -> int:
        return self.now


def keypair() -> tuple[Ed25519PrivateKey, str]:
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes_raw()
    return private, base64.b64encode(public).decode("ascii")


def sign(
    private: Ed25519PrivateKey,
    *,
    worker_id: str,
    generation: int,
    timestamp_ms: int,
    nonce: str,
    method: str,
    path: str,
    body: dict,
) -> dict[str, str]:
    body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    digest = "sha256:" + hashlib.sha256(body_bytes).hexdigest()
    canonical = "\n".join(
        [
            worker_id,
            str(generation),
            str(timestamp_ms),
            nonce,
            method.upper(),
            path,
            digest,
        ]
    ).encode()
    signature = base64.b64encode(private.sign(canonical)).decode("ascii")
    return {
        "X-Ordivon-Worker": worker_id,
        "X-Ordivon-Generation": str(generation),
        "X-Ordivon-Timestamp-Ms": str(timestamp_ms),
        "X-Ordivon-Nonce": nonce,
        "X-Ordivon-Signature": signature,
    }


def test_external_pull_execution_round_trip_and_artifact(tmp_path) -> None:
    clock = Clock()
    transport = ExternalPullWorkerTransport(
        tmp_path / "workers.sqlite3", clock_ms=clock, lease_ms=5_000
    )
    private, public_key = keypair()
    transport.enroll(
        worker_id="muse-test-r3",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    service = GatewayService(NoOwnerCaller(), external_workers=transport)

    projection = asyncio.run(service.capability_describe())
    external = {item.capability: item for item in projection.capabilities}["muse.shell.echo"]
    assert external.available is True
    assert external.owner_id == "external.pull"
    assert external.owner_node_ids == ["muse-test-r3"]

    receipt = asyncio.run(
        service.execution_submit(
            capability="muse.shell.echo",
            request_id="req-muse-1",
            workspace_id="ws-external",
            executable="echo",
            args=["hello"],
        )
    )
    assert receipt.owner_id == "external.pull"
    assert receipt.state == "queued"
    assert receipt.terminal is False

    claim = transport.claim("muse-test-r3", generation=1)
    assert claim is not None
    assert claim["capability"] == "muse.shell.echo"
    assert claim["attempt_id"]
    assert transport.claim("muse-test-r3", generation=1) is None

    transport.started(
        worker_id="muse-test-r3",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
    )
    transport.complete(
        worker_id="muse-test-r3",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
        exit_code=0,
        result={"text": "hello"},
        artifacts=[{"artifact_id": "result.txt", "content": "hello"}],
    )

    observed = asyncio.run(service.execution_get(receipt.operation_ref))
    assert observed.terminal is True
    assert observed.state == "completed"
    assert observed.exit_code == 0
    assert observed.artifact_ids == ["result.txt"]

    chunk = asyncio.run(service.artifact_read(receipt.operation_ref, "result.txt"))
    assert chunk.content == "hello"
    assert chunk.eof is True


def test_expired_attempt_cannot_commit_and_operation_is_reclaimed(tmp_path) -> None:
    clock = Clock()
    transport = ExternalPullWorkerTransport(
        tmp_path / "workers.sqlite3", clock_ms=clock, lease_ms=1_000
    )
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    operation = transport.submit(
        capability="muse.shell.echo",
        request_id="req-expire",
        parcel={"fixed_action": "echo"},
    )
    first = transport.claim("worker-1", generation=1)
    assert first is not None

    clock.now += 1_001
    second = transport.claim("worker-1", generation=1)
    assert second is not None
    assert second["operation_id"] == operation.operation_id
    assert second["attempt_id"] != first["attempt_id"]

    with pytest.raises(WorkerConflict, match="stale"):
        transport.complete(
            worker_id="worker-1",
            generation=1,
            operation_id=first["operation_id"],
            attempt_id=first["attempt_id"],
            lease_id=first["lease_id"],
            exit_code=0,
            result={},
            artifacts=[],
        )


def test_duplicate_completion_is_idempotent_but_changed_completion_conflicts(tmp_path) -> None:
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3")
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    transport.submit(
        capability="muse.shell.echo",
        request_id="req-idempotent",
        parcel={"fixed_action": "echo"},
    )
    claim = transport.claim("worker-1", generation=1)
    assert claim is not None
    kwargs = dict(
        worker_id="worker-1",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
        exit_code=0,
        result={"text": "same"},
        artifacts=[],
    )
    first = transport.complete(**kwargs)
    second = transport.complete(**kwargs)
    assert first == second

    with pytest.raises(WorkerConflict, match="terminal result"):
        transport.complete(**{**kwargs, "result": {"text": "different"}})


def test_worker_generation_and_revocation_fence_claims(tmp_path) -> None:
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3")
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=2,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    transport.submit(
        capability="muse.shell.echo",
        request_id="req-generation",
        parcel={"fixed_action": "echo"},
    )
    with pytest.raises(WorkerAuthError, match="generation"):
        transport.claim("worker-1", generation=1)

    transport.revoke("worker-1")
    with pytest.raises(WorkerAuthError, match="revoked"):
        transport.claim("worker-1", generation=2)


def test_signed_request_verification_rejects_replay(tmp_path) -> None:
    clock = Clock()
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3", clock_ms=clock)
    private, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    body = {"capabilities": ["muse.shell.echo"]}
    headers = sign(
        private,
        worker_id="worker-1",
        generation=1,
        timestamp_ms=clock.now,
        nonce="nonce-1",
        method="POST",
        path="/v1/workers/worker-1/heartbeat",
        body=body,
    )
    transport.verify_signed_request(
        method="POST",
        path="/v1/workers/worker-1/heartbeat",
        body=body,
        headers=headers,
    )
    with pytest.raises(WorkerAuthError, match="replay"):
        transport.verify_signed_request(
            method="POST",
            path="/v1/workers/worker-1/heartbeat",
            body=body,
            headers=headers,
        )


def test_system_description_marks_external_transport_configured(tmp_path) -> None:
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3")
    service = GatewayService(NoOwnerCaller(), external_workers=transport)
    owners = {owner.owner_id: owner for owner in service.system_describe().owners}
    assert owners["external.pull"].configured is True


def test_heartbeat_cannot_expand_operator_admitted_capability_ceiling(tmp_path) -> None:
    transport = ExternalPullWorkerTransport(tmp_path / "workers.sqlite3")
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    with pytest.raises(WorkerAuthError, match="capability"):
        transport.heartbeat(
            "worker-1",
            generation=1,
            capabilities=["muse.shell.echo", "execution.windows"],
        )
    assert transport.capability_projection() == {"muse.shell.echo": ["worker-1"]}


def test_transport_migrates_pre_ceiling_worker_schema(tmp_path) -> None:
    import sqlite3

    db_path = tmp_path / "workers.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute(
            """
            CREATE TABLE workers (
                worker_id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                generation INTEGER NOT NULL,
                public_key_b64 TEXT NOT NULL,
                capabilities_json TEXT NOT NULL,
                enrolled_at_ms INTEGER NOT NULL,
                last_heartbeat_ms INTEGER NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0
            )
            """
        )
    transport = ExternalPullWorkerTransport(db_path)
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-after-migration",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    assert transport.capability_projection() == {"muse.shell.echo": ["worker-after-migration"]}


def test_heartbeat_renews_live_started_attempt_lease(tmp_path) -> None:
    clock = Clock()
    transport = ExternalPullWorkerTransport(
        tmp_path / "workers.sqlite3", clock_ms=clock, lease_ms=1_000
    )
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    transport.submit(
        capability="muse.shell.echo",
        request_id="req-heartbeat-renew",
        parcel={"fixed_action": "echo"},
    )
    claim = transport.claim("worker-1", generation=1)
    assert claim is not None
    transport.started(
        worker_id="worker-1",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
    )

    clock.now += 900
    transport.heartbeat("worker-1", generation=1)
    clock.now += 200
    assert transport.claim("worker-1", generation=1) is None
    assert transport.get(claim["operation_id"]).state == "started"


def test_expired_started_attempt_requires_reconciliation_and_is_not_duplicated(tmp_path) -> None:
    clock = Clock()
    transport = ExternalPullWorkerTransport(
        tmp_path / "workers.sqlite3", clock_ms=clock, lease_ms=1_000
    )
    _, public_key = keypair()
    transport.enroll(
        worker_id="worker-1",
        provider_id="muse",
        generation=1,
        public_key_b64=public_key,
        capabilities=["muse.shell.echo"],
    )
    operation = transport.submit(
        capability="muse.shell.echo",
        request_id="req-started-expire",
        parcel={"fixed_action": "echo"},
    )
    claim = transport.claim("worker-1", generation=1)
    assert claim is not None
    transport.started(
        worker_id="worker-1",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
    )

    clock.now += 1_001
    assert transport.claim("worker-1", generation=1) is None
    unknown = transport.get(operation.operation_id)
    assert unknown.state == "reconcile_required"
    assert unknown.terminal is False

    service = GatewayService(NoOwnerCaller(), external_workers=transport)
    observed = asyncio.run(service.execution_get(f"ordivon-exec:v1:external.pull:{operation.operation_id}"))
    assert observed.state == "reconcile_required"
    assert observed.recovery_required is True
    assert observed.delivery_disposition == "unknown"

    # A late terminal report from the same fenced attempt is safe to accept because
    # no replacement attempt was ever issued.
    completed = transport.complete(
        worker_id="worker-1",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
        exit_code=0,
        result={"text": "late but same attempt"},
        artifacts=[],
    )
    assert completed.state == "completed"
    assert completed.terminal is True
