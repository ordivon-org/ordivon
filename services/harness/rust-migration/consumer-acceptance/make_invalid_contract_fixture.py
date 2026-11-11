"""Scratch-PG-only falsifier: CAS-correct but semantically invalid Harness Contract.

Consumes the test-only PG writer fixture; it never connects to production.
Mutating the contract is deliberate, to distinguish byte-integrity from
HarnessRunContract.from_dict semantic acceptance.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from psycopg import sql

from anc_canonical import canonical_bytes, canonical_digest
from ordivon_harness.core_contracts import HarnessRunContract
from ordivon_harness.postgres_store import PostgresHarnessStore
from ordivon_harness.store_errors import HarnessObjectCorrupt

dsn = os.environ["HARNESS_RUST_TEST_PG_DSN"]
schema = os.environ["HARNESS_RUST_TEST_SCHEMA"]
path = Path(os.environ["HARNESS_RUST_TEST_FIXTURE_PATH"])
assert schema.startswith("hpg_rust_isolated_"), "never touch production PG schema"
fixtures = json.loads(path.read_text(encoding="utf-8"))

with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
    valid = store.load_run(fixtures["valid"])
    valid_contract = store.get_object(
        valid.contract_object_digest, expected_kind="harness-run-contract"
    )
    copied = dict(valid_contract)
    copied["harnessRunId"] = "harness-run:test-rust-pg-invalid-contract-semantic"
    copied["callerRunRef"] = "test-run-invalid-contract-semantic"
    legitimate = HarnessRunContract.from_dict(copied)
    assert store.create_run(legitimate).value == "created"
    created = store.list_run_events(legitimate.harness_run_id)[0]
    payload = store.get_object(
        created.payload_digest, expected_kind="ordivon.harness-run-event-payload"
    )
    assert payload["data"]["contractDigest"] == legitimate.digest
    # The same Python source that owns production admission must reject it.
    malformed = legitimate.to_dict()
    malformed["providerId"] = ""
    try:
        HarnessRunContract.from_dict(malformed)
    except ValueError as error:
        assert "Provider identity" in str(error), str(error)
    else:
        raise AssertionError("Python Contract unexpectedly accepted empty providerId")
    malformed_digest = canonical_digest(malformed)
    malformed_raw = canonical_bytes(malformed)

    new_payload = dict(payload)
    new_data = dict(payload["data"])
    new_data["contractDigest"] = malformed_digest
    new_data["contractObjectDigest"] = malformed_digest
    new_payload["data"] = new_data
    payload_digest = canonical_digest(new_payload)
    payload_raw = canonical_bytes(new_payload)

with psycopg.connect(dsn, autocommit=True) as connection:
    connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
    with connection.transaction():
        for digest, kind, raw in (
            (malformed_digest, "harness-run-contract", malformed_raw),
            (payload_digest, "ordivon.harness-run-event-payload", payload_raw),
        ):
            connection.execute(
                "INSERT INTO objects(digest,kind,byte_length,content,first_seen_at_ms) "
                "VALUES(%s,%s,%s,%s,%s)",
                (digest, kind, len(raw), raw, 1000),
            )
        connection.execute(
            "UPDATE runs SET contract_digest=%s,contract_object_digest=%s "
            "WHERE harness_run_id=%s",
            (malformed_digest, malformed_digest, legitimate.harness_run_id),
        )
        connection.execute(
            "UPDATE run_events SET payload_digest=%s WHERE event_id=%s",
            (payload_digest, created.event_id),
        )
        connection.execute(
            "UPDATE run_object_refs SET digest=%s "
            "WHERE event_id=%s AND role='payload'",
            (payload_digest, created.event_id),
        )
        connection.execute(
            "UPDATE run_object_refs SET digest=%s "
            "WHERE event_id=%s AND role='reference'",
            (malformed_digest, created.event_id),
        )
    # Python authoritative reader validates identity AND semantic contract;
    # distinguish this from a CAS corruption or hash mismatch.
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        try:
            store.validate_run_history(legitimate.harness_run_id)
        except (ValueError, HarnessObjectCorrupt) as error:
            assert "contract" in str(error).lower(), str(error)
            print(f"PYTHON_SEMANTIC_REJECTION={type(error).__name__}")
        else:
            raise AssertionError("Python unexpectedly accepted invalid stored Contract")
    row = connection.execute(
        "SELECT contract_digest,contract_object_digest FROM runs WHERE harness_run_id=%s",
        (legitimate.harness_run_id,),
    ).fetchone()
    assert row == (malformed_digest, malformed_digest)

fixtures["invalid_contract"] = legitimate.harness_run_id
path.write_text(json.dumps(fixtures, sort_keys=True), encoding="utf-8")
print("SCRATCH_PG_CONTRACT_SEMANTICS_COUNTEREXAMPLE_READY", legitimate.harness_run_id)
