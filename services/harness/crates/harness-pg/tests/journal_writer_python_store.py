"""Real Python PostgresHarnessStore oracle for native Rust Journal Writer.

Uses only the disposable PG18 schema created by run_isolated_pg18.sh.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys

from ordivon_harness.core_contracts import HarnessRunContract
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store import (
    HarnessEventAdmission, HarnessEventWrite, HarnessRunLease, StoredHarnessObject,
)

action = sys.argv[1]
assert action in {"prepare", "verify"}
dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
fixture = Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"])
assert schema.startswith("hpg_rust_isolated_a_")
assert fixture.parent.as_posix().startswith("/tmp/")
manifest = json.loads(fixture.read_text(encoding="utf-8"))
if action == "prepare":
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        base = store.load_run(manifest["valid"])
        root_contract = store.get_object(
            base.contract_object_digest, expected_kind="harness-run-contract"
        )
        runs = {}
        for name in ("rust", "race", "rollback", "terminal", "readonly", "bounded", "expired", "reference"):
            item = dict(root_contract)
            item["harnessRunId"] = "harness-run:rust-writer-source-" + name
            item["callerRunRef"] = "rust-writer-source-" + name
            contract = HarnessRunContract.from_dict(item)
            assert store.create_run(contract) is HarnessEventAdmission.CREATED
            store.validate_run_history(contract.harness_run_id)
            runs[name] = contract.harness_run_id
        obj = store.put_object(
            {"artifact": "source-owned", "visible": False},
            kind="test-source-artifact",
        )
        manifest["rust_writer_fixture"] = {
            "runs": runs,
            "referenced": obj.to_dict(),
            "foreignEventId": store.list_run_events(manifest["valid"])[0].event_id,
        }
    fixture.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    print("PYTHON_SOURCE_RUNS_FOR_NATIVE_RUST_JOURNAL", len(runs))
else:
    entries = manifest["rust_writer_fixture"]
    runs = entries["runs"]
    source_ref = entries["referenced"]
    artifact = StoredHarnessObject(
        source_ref["digest"], source_ref["byteLength"], source_ref["kind"]
    )
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        store.validate_run_history(runs["rust"])
        live = store.load_run(runs["rust"])
        assert (live.status.value, live.revision) == ("active", 3)
        events = store.list_run_events(runs["rust"])
        assert [e.event_kind for e in events] == [
            "harness.run-created", "harness.tool-step-unknown", "harness.trace-recorded"
        ]
        assert events[1].data == {"reason": "unknown-effect", "attempt": 1}
        assert events[2].caused_by_event_id == events[1].event_id
        assert events[2].data == {"consumer": "python-source", "recoverable": True}
        assert store.get_object(artifact.digest, expected_kind=artifact.kind) == {
            "artifact": "source-owned", "visible": False
        }
        # Source-authoritative idempotency after Rust consumed the lease.
        saved_lease = HarnessRunLease(runs["rust"], "rust:journal", 1, 1, 5500)
        assert store.append_events(
            harness_run_id=runs["rust"],
            expected_revision=1,
            lease=saved_lease,
            lease_checked_at_ms=1600,
            events=(
                HarnessEventWrite(
                    "event:rust-native-writer-unknown", "harness.tool-step-unknown",
                    {"reason": "unknown-effect", "attempt": 1}, 1700
                ),
                HarnessEventWrite(
                    "event:rust-native-writer-trace", "harness.trace-recorded",
                    {"consumer": "python-source", "recoverable": True}, 1800,
                    caused_by_event_id="event:rust-native-writer-unknown",
                    referenced_objects=(artifact,),
                ),
            ),
        ) is HarnessEventAdmission.EXISTING
        assert store.release_run_lease(saved_lease) is False
        assert store.load_run(runs["rust"]).revision == 3
        store.validate_run_history(runs["terminal"])
        terminal = store.load_run(runs["terminal"])
        assert terminal.status.value == "completed"
        assert terminal.terminal_event_id == "event:rust-native-terminal"
        assert terminal.revision == 2
        store.validate_run_history(runs["rollback"])
        assert store.load_run(runs["rollback"]).revision == 2
        store.validate_run_history(runs["race"])
        assert store.load_run(runs["race"]).revision == 2
        assert len(store.list_run_events(runs["race"])) == 2
        store.validate_run_history(runs["bounded"])
        bounded = store.load_run(runs["bounded"])
        assert (bounded.status.value, bounded.revision) == ("created", 257)
        assert len(store.list_run_events(runs["bounded"])) == 257
        store.validate_run_history(runs["expired"])
        assert store.load_run(runs["expired"]).revision == 1
        store.validate_run_history(runs["reference"])
        assert store.load_run(runs["reference"]).revision == 1
        print("PYTHON_VALIDATED_RUST_NATIVE_CAS_JOURNAL_REPLAY_PASS")
