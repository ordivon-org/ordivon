"""Python legacy Host seed/readback on a disposable PostgreSQL 18 test database."""

import os
import sys

import psycopg

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
)
from ordivon_host_v2.work_store import WorkStore

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
    # Python's original Pydantic model_dump request id must retrieve the exact
    # Rust Work.create receipt (snake_case aliases and default Snapshot lists).
    from ordivon_host_v2.mcp_tool_registration import _request_id

    new_ref = "work:test:rust-mcp-created"
    created_snapshot = WorkSnapshotInput(
        objective="Rust MCP Work.create 🌍",
        frontier="created-with-rust",
        nextActions=["verify Python receipt"],
    )
    new_work = WorkCreateInput(
        work_ref=new_ref,
        kind="migration-smoke",
        actor_ref="actor:test:rust-mcp",
        initial_snapshot=created_snapshot,
    )
    created_from_python = store.get_work(new_ref)
    assert created_from_python["state"] == "open", created_from_python
    assert created_from_python["revision"] == 1, created_from_python
    create_req = _request_id("work-create", new_work.model_dump(mode="json"))
    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT operation,response FROM command_receipts WHERE client_request_id=%s",
            (create_req,),
        ).fetchone()
        assert row is not None, "Rust Work.create identity differs from original Python MCP"
        assert row[0] == "work.create" and row[1]["workRef"] == new_ref, row
    actor_value = ActorRefInput(
        actor_ref="actor:test:rust-mcp-declared",
        actor_kind=ActorKind.AGENT,
    )
    original_id = _request_id("actor-declare", actor_value.model_dump(mode="json"))
    with psycopg.connect(dsn) as conn:
        row = conn.execute(
            "SELECT operation,response FROM command_receipts WHERE client_request_id=%s",
            (original_id,),
        ).fetchone()
        assert row is not None and row[0] == "actor.declare", row
        actor_rust_response = row[1]
        assert actor_rust_response["actorKind"] == "agent", actor_rust_response
    actor_python_replay = store.declare_actor(actor_value, client_request_id=original_id)
    assert actor_python_replay["admission"] == "existing", actor_python_replay
    assert actor_python_replay["createdAt"] == actor_rust_response["createdAt"]
    print("PYTHON_MCP_ACTOR_DECLARATION_PARITY_PASS receipt=EXACT replay=existing")
    print("PYTHON_HOST_READBACK_PASS work_revision=2 terminal=completed receipt_identity=EXACT")
