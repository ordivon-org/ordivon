"""Create exactly two Python Harness Runs in an isolated PG test schema.

Invoked only with HARNESS_RUST_TEST_PG_DSN pointing to an isolated PG18 instance;
it never selects a production DSN and never drops any schema.
"""
import json
import os
from pathlib import Path
import sys
import uuid

import psycopg
from psycopg import sql
from anc_canonical import digest_bytes
from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventWrite


def new_contract(suffix: str) -> HarnessRunContract:
    d = digest_bytes(b"isolated-harness-rust-readonly-test-object")
    reference = HarnessBoundReference(
        ref="test:objective:" + suffix,
        kind="test-only",
        digest=d,
    )
    return HarnessRunContract(
        harness_run_id="harness-run:test-rust-pg-" + suffix,
        harness_implementation_id="test:rustrun-reader",
        caller_id="caller:test-rust-pg",
        caller_run_ref="test-run-" + suffix,
        objective_ref=reference,
        context_refs=(HarnessBoundReference("test:context:" + suffix, "test-only", d),),
        provider_id="provider:test",
        adapter_id="adapter:test",
        requested_model_id="model:test",
        tool_catalog_digest=d,
        tool_grant_digest=d,
        budget={"maxTurns": 2},
        completion_contract={"mode": "text"},
        system_manifest_ref=HarnessBoundReference("test:manifest:" + suffix, "test-only", d),
        created_at_ms=1000,
    )


dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ.get("HARNESS_RUST_TEST_SCHEMA", "hpg_rust_" + uuid.uuid4().hex[:16])
assert schema.startswith("hpg_rust_")
valid, corrupt, bad_revision, bad_edge = (new_contract(suffix) for suffix in ("valid", "corrupt", "badrev", "badedge"))

with PostgresHarnessStore(dsn, schema=schema, initialize=True) as store:
    for contract in [valid, corrupt, bad_revision, bad_edge]:
        assert store.create_run(contract).value == "created"
    # Exercise real Python PG append_events and its exact lease/revision path.
    lease = store.acquire_run_lease(
        valid.harness_run_id, owner_id="rust-pg-readonly-fixture",
        ttl_ms=100000, now_ms=1200, expected_run_revision=1,
    )
    assert store.append_events(
        harness_run_id=valid.harness_run_id,
        expected_revision=1,
        events=(
            HarnessEventWrite("event:rust-test-provider-unknown", "harness.provider-call-unknown",
                              {"providerCallId": "provider-call:unknown", "state": "unknown"}, 1200),
            HarnessEventWrite("event:rust-test-run-completed", "harness.run-completed",
                              {"conclusionRef": "test:conclusion", "reason": "fixture"}, 1300,
                              caused_by_event_id="event:rust-test-provider-unknown"),
        ),
        lease=lease,
        lease_checked_at_ms=1250,
    ).value == "created"
    store.validate_run_history(valid.harness_run_id)
    store.validate_run_history(corrupt.harness_run_id)
    store.validate_run_history(bad_revision.harness_run_id)
    store.validate_run_history(bad_edge.harness_run_id)

# Deliberately corrupt only the second run's object within the isolated schema.
with psycopg.connect(dsn, autocommit=True) as conn:
    conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
    conn.execute(
        "UPDATE objects SET content = content || %s::bytea WHERE digest = %s",
        (b" ", corrupt.digest),
    )
    bad = conn.execute(
        "SELECT length(content) > byte_length AS bad FROM objects WHERE digest=%s",
        (corrupt.digest,),
    ).fetchone()[0]
    assert bad is True
    conn.execute("UPDATE runs SET revision=2 WHERE harness_run_id=%s", (bad_revision.harness_run_id,))
    conn.execute(
        "DELETE FROM run_object_refs WHERE harness_run_id=%s AND role='payload'",
        (bad_edge.harness_run_id,),
    )

out = Path(os.environ.get("HARNESS_RUST_TEST_FIXTURE_PATH", "/tmp/harness-rust-pg-fixture.json"))
out.write_text(json.dumps({
    "schema": schema, "valid": valid.harness_run_id,
    "corrupt": corrupt.harness_run_id,
    "bad_revision": bad_revision.harness_run_id,
    "bad_edge": bad_edge.harness_run_id,
}), encoding="utf-8")
print("PYTHON_PG_FIXTURE_READY schema=" + schema, "valid_revision=3", "corrupt_object=1 bad_projection=1 bad_edge=1")
