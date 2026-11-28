"""Independent original Python Store consumer of native PG birth."""
import os
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.core_contracts import HarnessRunContract
from anc_canonical import canonical_digest

with PostgresHarnessStore(os.environ["HARNESS_RUST_TEST_PG_DSN"], schema=os.environ["HARNESS_RUST_TEST_SCHEMA"]) as store:
    run = "harness-run:rust-native-birth"
    projection = store.load_run(run)
    contract = HarnessRunContract.from_dict(store.get_object(projection.contract_object_digest, expected_kind="harness-run-contract"))
    store.validate_run_history(run)
    assert store.create_run(contract).value == "existing"
    event = store.list_run_events(run)[0]
    assert event.event_id == "event:harness-run-created:" + canonical_digest({"harnessRunId": run, "contractDigest": contract.digest})[7:]
    assert store.load_run(run).revision == 1
    print("PYTHON_ORIGINAL_STORE_NATIVE_BIRTH_EXACT_REPLAY_PASS")
