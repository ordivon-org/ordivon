"""Live Python PostgreSQL v1 lease oracle for the experimental Rust lease port.

Commands:
    prepare: create source-valid Runs in an isolated PostgreSQL18 schema.
    verify:  re-acquire Rust-written tuples through the real Python Store.
This never initializes/drops a schema or touches the configured production DSN.
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
import re
from pathlib import Path
import sys

from psycopg import sql

import psycopg

from ordivon_harness.core_contracts import HarnessRunContract
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import HarnessEventWrite, HarnessEventAdmission

command = sys.argv[1]
assert command in {"prepare", "verify"}
dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
root = Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"])
assert re.fullmatch(r"hpg_rust_isolated_a_[a-z0-9_]+", schema), "never contact production"
assert root.is_file() and root.parent.as_posix().startswith("/tmp/")
manifest = json.loads(root.read_text())

if command == "prepare":
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        source = store.load_run(manifest["valid"])
        template = store.get_object(
            source.contract_object_digest, expected_kind="harness-run-contract"
        )
        runs = {}
        for name in ("rust", "python", "handoff", "race", "revision", "tamper"):
            item = deepcopy(template)
            item["harnessRunId"] = f"harness-run:pg-lease-source-{name}"
            item["callerRunRef"] = f"pg-lease-source-{name}"
            contract = HarnessRunContract.from_dict(item)
            assert store.create_run(contract) is HarnessEventAdmission.CREATED
            store.validate_run_history(contract.harness_run_id)
            runs[name] = contract.harness_run_id

        # Have Python create a live owner tuple BEFORE Rust acquires.
        seeded = store.acquire_run_lease(
            runs["python"], owner_id="python:source-owner", ttl_ms=1000,
            now_ms=1000, expected_run_revision=1
        )
        assert seeded.lease_revision == 1
        assert seeded.expires_at_ms == 2000

        # Python changes a revision using the real transactional Journal Writer,
        # so a later Rust expectedRevision=1 must fail and 2 may succeed.
        rev_lease = store.acquire_run_lease(
            runs["revision"], owner_id="python:rev-writer", ttl_ms=1000,
            now_ms=1100, expected_run_revision=1
        )
        assert store.append_events(
            harness_run_id=runs["revision"], expected_revision=1,
            events=(HarnessEventWrite(
                "event:lease-source-revision-advance",
                "harness.trace-recorded", {"tag": "revision-two"}, 1200
            ),), lease=rev_lease, lease_checked_at_ms=1200
        ) is HarnessEventAdmission.CREATED
        assert store.load_run(runs["revision"]).revision == 2
        store.validate_run_history(runs["revision"])

    # Deliberately malformed projection. Never grant a lease merely because
    # the row physically exists and PostgreSQL lacks an enum CHECK.
    with psycopg.connect(dsn, autocommit=True) as con:
        con.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        con.execute(
            "UPDATE runs SET status='not_a_harness_status' WHERE harness_run_id=%s",
            (runs["tamper"],),
        )
    manifest["lease_rust_fixture"] = runs
    root.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    print("PYTHON_PG_LEASE_SOURCE_FIXTURE_CREATED", len(runs))
else:
    runs = manifest["lease_rust_fixture"]
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        # Rust's live committed row must be read EXACTLY as Python's own
        # acquire_run_lease semantics: no TTL extension for same owner.
        handoff = store.acquire_run_lease(
            runs["handoff"], owner_id="rust:handoff",
            now_ms=1200, ttl_ms=100, expected_run_revision=1
        )
        assert handoff.lease_revision == 1
        assert handoff.run_revision == 1
        assert handoff.expires_at_ms == 5000
        # Real Python Journal Writer must be able to consume the Rust-owned
        # EXACT lease tuple in one Event/CAS+projection+lease transaction.
        # A trace event is intentionally non-effectful: this is not Tool
        # dispatch or a claim of external semantic success.
        assert store.append_events(
            harness_run_id=runs["handoff"], expected_revision=1,
            events=(HarnessEventWrite(
                "event:rust-lease-python-journal-consumer",
                "harness.trace-recorded", {"source": "rust-native-lease"}, 1300
            ),), lease=handoff, lease_checked_at_ms=1250
        ) is HarnessEventAdmission.CREATED
        assert store.release_run_lease(handoff) is False
        store.validate_run_history(runs["handoff"])
        assert store.load_run(runs["handoff"]).revision == 2

        py = store.acquire_run_lease(
            runs["python"], owner_id="rust:after-expiry",
            now_ms=2200, ttl_ms=100, expected_run_revision=1
        )
        assert py.lease_revision == 2
        assert py.expires_at_ms == 2800
        assert store.release_run_lease(py) is True

        # Readback of the Python-owned revision never regresses after Rust
        # acquired/released a lease on its current revision.
        store.validate_run_history(runs["revision"])
        assert store.load_run(runs["revision"]).revision == 2

        # Run is still not terminal nor physically executed by these leases.
        assert store.load_run(runs["handoff"]).revision == 2
    print("PYTHON_REOBSERVED_RUST_PG_LEASE_TUPLES_EXACT_PASS")
