"""Create real Python Harness Runs in an isolated PG test schema.

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
from anc_canonical import canonical_digest, digest_bytes
from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventWrite
from ordivon_harness.ordivon.run_continuity import EventSourcedRunContinuity


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
valid, corrupt, bad_revision, bad_edge, deep = (new_contract(suffix) for suffix in ("valid", "corrupt", "badrev", "badedge", "deep996"))

def legacy_boolean_contract(suffix: str) -> HarnessRunContract:
    raw = new_contract(suffix).to_dict()
    raw.update(
        schemaVersion=1,
        correlation={"traceparent": None, "tracestate": None, "links": []},
    )
    contract = HarnessRunContract.from_dict(raw)
    # Scratch fixture reproduces a historically admitted exact wire value.
    # Do not loosen the current public constructor or decoder.
    object.__setattr__(contract, "_schema_version", True)
    return contract


legacy_boolean = legacy_boolean_contract("legacy-bool")
legacy_bad_edge = legacy_boolean_contract("legacy-bool-bad-edge")

with PostgresHarnessStore(dsn, schema=schema, initialize=True) as store:
    for contract in [valid, corrupt, bad_revision, bad_edge, deep, legacy_boolean, legacy_bad_edge]:
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
            HarnessEventWrite("event:rust-test-trace", "harness.trace-recorded",
                              {"source": "fixture"}, 1200),
            HarnessEventWrite("event:rust-test-run-completed", "harness.run-completed",
                              {"conclusionRef": "test:conclusion", "reason": "fixture"}, 1300,
                              caused_by_event_id="event:rust-test-trace"),
        ),
        lease=lease,
        lease_checked_at_ms=1250,
    ).value == "created"
    store.validate_run_history(valid.harness_run_id)
    store.validate_run_history(corrupt.harness_run_id)
    store.validate_run_history(bad_revision.harness_run_id)
    store.validate_run_history(bad_edge.harness_run_id)

    # UNKNOWN must have the real current typed Provider record. A normal
    # terminal event over that unresolved effect is intentionally not legal.
    # Reuse the existing Provider consumer fixtures; do not synthesize a
    # Provider outcome or weaken the production terminal admission rule.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from tests.test_p0_sqlite_provider_store import (
        MutableClock, contract as provider_contract, failure, state,
    )

    unknown_run = provider_contract()
    assert store.create_run(unknown_run).value == "created"
    clock = MutableClock()
    continuity = EventSourcedRunContinuity(store, unknown_run, clock_ms=clock)
    continuity.bind_state(state())
    claim = continuity.claim_provider_call(
        source=continuity.assignment_provider_source(),
        turn_id="turn:rust-pg-unknown",
        turn_sequence=1,
        request_digest=canonical_digest({"request": "rust-pg-unknown"}),
        provider_request_digest=canonical_digest({"wire": "rust-pg-unknown"}),
        adapter_id=unknown_run.adapter_id,
        requested_model_id=unknown_run.requested_model_id,
        holder_id="holder:rust-pg-unknown",
        ttl_ms=10_000,
    )
    dispatching = continuity.mark_provider_call_dispatching(claim)
    ambiguous = failure(
        dispatching.record.provider_call_id,
        dispatching.record.request_digest,
        dispatching.record.provider_request_digest,
        safety="dispatch_ambiguous",
        suffix="rust-pg-unknown",
    )
    continuity.bind_state(state(elapsed=5, wall_time_ms=29_995))
    unknown = continuity.fail_provider_call(dispatching, failure=ambiguous)
    assert unknown.record.status.value == "unknown"
    assert not store.load_run(unknown_run.harness_run_id).status.terminal
    store.validate_run_history(unknown_run.harness_run_id)

    # An explicitly configured legacy Python runtime can accept this depth.
    # Default CPython recursion_limit=1000 fails inside nested Store calls;
    # this fixture is a *cross-configuration* compatibility counterexample,
    # not evidence that today's default production Run contains such content.
    sys.setrecursionlimit(2000)
    nested = 0
    for _ in range(996):
        nested = [nested]
    deep_object = store.put_object(nested, kind="legacy-python-depth-996")
    assert store.get_object(deep_object.digest, expected_kind="legacy-python-depth-996") == nested
    deep_lease = store.acquire_run_lease(
        deep.harness_run_id, owner_id="test-rust-legacy-depth",
        ttl_ms=100000, now_ms=1100, expected_run_revision=1,
    )
    assert store.append_events(
        harness_run_id=deep.harness_run_id,
        expected_revision=1,
        events=(HarnessEventWrite(
            "event:rust-test-legit-legacy-depth", "harness.trace-recorded",
            {"source": "python-valid-depth996"}, 1200,
            referenced_objects=(deep_object,),
        ),),
        lease=deep_lease, lease_checked_at_ms=1200,
    ).value == "created"
    store.validate_run_history(deep.harness_run_id)

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
    conn.execute(
        "DELETE FROM run_object_refs WHERE harness_run_id=%s AND role='payload'",
        (legacy_bad_edge.harness_run_id,),
    )

out = Path(os.environ.get("HARNESS_RUST_TEST_FIXTURE_PATH", "/tmp/harness-rust-pg-fixture.json"))
out.write_text(json.dumps({
    "schema": schema, "valid": valid.harness_run_id,
    "corrupt": corrupt.harness_run_id,
    "bad_revision": bad_revision.harness_run_id,
    "bad_edge": bad_edge.harness_run_id,
    "deep": deep.harness_run_id,
    "legacy_boolean": legacy_boolean.harness_run_id,
    "legacy_bad_edge": legacy_bad_edge.harness_run_id,
    "unknown": unknown_run.harness_run_id,
}), encoding="utf-8")
print("PYTHON_PG_FIXTURE_READY schema=" + schema, "valid_revision=3", "corrupt_object=1 bad_projection=1 bad_edge=1")
