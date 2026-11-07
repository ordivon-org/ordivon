"""Fault-injected external-worker readback: never commit an unobservable effect."""

from __future__ import annotations

import base64
from contextlib import contextmanager

import psycopg
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ordivon_gateway.external_worker import ExternalPullWorkerTransport, WorkerConflict


class _MissingReadback:
    def fetchone(self) -> None:
        return None


class _ReadbackFaultConnection:
    """One read is unavailable; real PostgreSQL still performs all writes and rollback."""

    def __init__(self, connection: psycopg.Connection, missing_lookup: int) -> None:
        self.connection = connection
        self.missing_lookup = missing_lookup
        self.lookups = 0

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, *args):
        return self.connection.__exit__(*args)

    def execute(self, sql: str, parameters=()):
        cursor = self.connection.execute(sql, parameters)
        if sql.strip().startswith("SELECT * FROM operations WHERE operation_id=%s"):
            self.lookups += 1
            if self.lookups == self.missing_lookup:
                return _MissingReadback()
        return cursor

    def __getattr__(self, name: str):
        return getattr(self.connection, name)


def _mask_lookup(monkeypatch, store: ExternalPullWorkerTransport, lookup: int) -> None:
    real_connect = store._connect

    @contextmanager
    def fault_injected_connection():
        # Preserve the real connection's rollback/close lifecycle while masking
        # only the one readback; _connect now owns the context, not the caller.
        with real_connect() as connection:
            yield _ReadbackFaultConnection(connection, lookup)

    monkeypatch.setattr(store, "_connect", fault_injected_connection)


def test_submit_must_rollback_if_written_row_is_not_readable(pg_dsn, monkeypatch) -> None:
    store = ExternalPullWorkerTransport(pg_dsn)
    _mask_lookup(monkeypatch, store, 1)

    with pytest.raises(WorkerConflict, match="persisted operation is missing"):
        store.submit(capability="example.echo", request_id="req-1", parcel={"value": 1})

    assert store.resolve("example.echo", "req-1") is None


def test_cancel_must_rollback_if_updated_row_is_not_readable(pg_dsn, monkeypatch) -> None:
    store = ExternalPullWorkerTransport(pg_dsn)
    operation = store.submit(
        capability="example.echo", request_id="req-cancel", parcel={"value": 1}
    )
    _mask_lookup(monkeypatch, store, 2)

    with pytest.raises(WorkerConflict, match="persisted operation is missing"):
        store.cancel(operation.operation_id)

    assert store.get(operation.operation_id).state == "queued"


def test_complete_must_rollback_attempt_and_artifacts_on_missing_readback(
    pg_dsn, monkeypatch
) -> None:
    store = ExternalPullWorkerTransport(pg_dsn)
    private = Ed25519PrivateKey.generate()
    key = base64.b64encode(private.public_key().public_bytes_raw()).decode("ascii")
    store.enroll(
        worker_id="worker-1",
        provider_id="example",
        generation=1,
        public_key_b64=key,
        capabilities=["example.echo"],
    )
    op = store.submit(capability="example.echo", request_id="req-complete", parcel={"value": 1})
    claim = store.claim("worker-1", generation=1)
    assert claim is not None
    store.started(
        worker_id="worker-1",
        generation=1,
        operation_id=claim["operation_id"],
        attempt_id=claim["attempt_id"],
        lease_id=claim["lease_id"],
    )

    _mask_lookup(monkeypatch, store, 3)
    with pytest.raises(WorkerConflict, match="persisted operation is missing"):
        store.complete(
            worker_id="worker-1",
            generation=1,
            operation_id=claim["operation_id"],
            attempt_id=claim["attempt_id"],
            lease_id=claim["lease_id"],
            exit_code=0,
            result={"ok": True},
            artifacts=[{"artifact_id": "evidence", "content": "raw"}],
        )

    after = store.get(op.operation_id)
    assert after.terminal is False
    assert after.state == "started"
    with store._connect() as db:
        assert db.execute("SELECT count(*) FROM artifacts").fetchone()["count"] == 0
        assert (
            db.execute(
                "SELECT state FROM attempts WHERE attempt_id=%s", (claim["attempt_id"],)
            ).fetchone()["state"]
            == "started"
        )
