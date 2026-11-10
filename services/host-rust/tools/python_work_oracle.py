"""Python legacy Host seed/readback on a disposable PostgreSQL 18 test database."""
import os
import sys

from ordivon_host_v2.work_inputs import (
    ActorKind, ActorRefInput, WorkCreateInput, WorkSnapshotInput,
)
from ordivon_host_v2.work_store import WorkStore
from ordivon_host_v2.canonical_json import canonical_digest
import psycopg

if len(sys.argv) != 2 or sys.argv[1] not in {"seed", "verify"}:
    raise SystemExit("mode must be seed or verify")
dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
if not dsn or "127.0.0.1" not in dsn or os.environ.get("ORDIVON_HOST_V2_DSN") != dsn:
    raise SystemExit("REFUSE_NON_DISPOSABLE_DATABASE")
store = WorkStore(dsn)
work_ref = "work:test:rust-mcp-stdio"
if sys.argv[1] == "seed":
    store.declare_actor(
        ActorRefInput(actor_ref="actor:test:rust-mcp", actor_kind=ActorKind.AGENT),
        client_request_id="test-seed-rust-mcp-actor",
    )
    work = store.create_work(
        WorkCreateInput(
            work_ref=work_ref,
            kind="migration-smoke",
            actor_ref="actor:test:rust-mcp",
            initial_snapshot=WorkSnapshotInput(
                objective="Rust Host live MCP CAS 🌍",
                frontier="created-by-original-python-host",
            ),
        ),
        client_request_id="test-seed-rust-mcp-work",
    )
    assert work["revision"] == 1 and work["state"] == "open"
    print("PYTHON_HOST_SEED_PASS work_revision=1")
else:
    work = store.get_work(work_ref)
    assert work["revision"] == 2 and work["state"] == "completed", work
    assert work["snapshot"]["frontier"] == "committed-via-rust-mcp", work
    prior = store.get_work(work_ref, 1)
    assert prior["state"] == "historical_state_unknown", prior
    # Tool request-id identity must match Python's actual MCP adapter, not merely
    # produce a locally repeatable Rust identity.
    snapshot = WorkSnapshotInput(
        objective="Rust Host live MCP CAS 🌍",
        frontier="committed-via-rust-mcp",
        established=["PG18 CAS", "MCP wire parity"],
        nextActions=["verify Python recovery"],
    )
    payload = {
        "workRef": work_ref,
        "expectedRevision": 1,
        "snapshot": snapshot.canonical_payload(),
        "actorRef": "actor:test:rust-mcp",
        "continuityDisposition": "complete",
    }
    request_id = f"work-snapshot-commit:{canonical_digest(payload).removeprefix('sha256:')}"
    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT operation, response FROM command_receipts WHERE client_request_id=%s",
            (request_id,),
        ).fetchone()
        assert row is not None, "Rust receipt identity differs from Python MCP"
        assert row[0] == "work.snapshot.commit" and row[1]["revision"] == 2, row
    print("PYTHON_HOST_READBACK_PASS work_revision=2 terminal=completed receipt_identity=EXACT")
