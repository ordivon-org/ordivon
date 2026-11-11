"""Scratch-PG-only semantic Contract corpus for Rust read-only takeover.

A correct SHA256 digest and consistent PG Event chain do not imply that the
versioned Contract can be consumed under HarnessRunContract.from_dict.
All writes below are intentionally scoped to isolated scratch PG fixtures.
"""
from __future__ import annotations

from copy import deepcopy
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


def semantic_counterexamples(valid_contract: dict) -> list[tuple[str, dict]]:
    """Make one focused mutation per category, preserving valid JSON bytes."""
    cases: list[tuple[str, dict]] = []

    def add(name: str, field: str, value: object) -> None:
        item = deepcopy(valid_contract)
        item[field] = value
        cases.append((name, item))

    add("provider_empty", "providerId", "")
    add("provider_control_whitespace", "providerId", "\u001cprovider:test")
    add("adapter_non_string", "adapterId", 7)
    add("requested_model_blank", "requestedModelId", " ")
    add("tool_catalog_bad_digest", "toolCatalogDigest", "sha256:not-a-real-digest")
    add("tool_grant_uppercase_digest", "toolGrantDigest", "sha256:" + "A" * 64)
    add("context_refs_empty", "contextRefs", [])
    add("context_refs_duplicate", "contextRefs", valid_contract["contextRefs"] * 2)
    add("objective_ref_empty", "objectiveRef", {
        **valid_contract["objectiveRef"], "ref": "",
    })
    add("source_ref_digest_malformed", "sourceRefs", [
        {"ref": "test:source", "kind": "test-only", "digest": "invalid"}
    ])
    add("privacy_metadata_capture", "privacy", {
        "contentPolicy": "metadata-only",
        "allowModelContent": True,
        "allowToolContent": False,
    })
    add("privacy_flag_wrong_type", "privacy", {
        "contentPolicy": "metadata-only",
        "allowModelContent": 1,
        "allowToolContent": False,
    })
    add("privacy_extra_field", "privacy", {
        **valid_contract["privacy"], "unboundedContentCapture": True,
    })
    add("budget_empty", "budget", {})
    add("completion_empty", "completionContract", {})
    add("completion_schema_missing", "completionContract", {
        "mode": "structured-result-v1",
    })
    add("completion_schema_invalid_type", "completionContract", {
        "mode": "structured-result-v1",
        "resultSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "not-a-json-schema-type",
        },
    })
    add("completion_unbound_conformance", "completionContract", {
        "mode": "text", "conformancePolicy": "unbound",
    })
    add("deadline_before_creation", "deadlineMs", valid_contract["createdAtMs"] - 1)
    add("created_at_boolean", "createdAtMs", True)
    add("unexpected_contract_field", "unexpectedField", "not-in-contract")
    add("v2_correlation_forbidden", "correlation", {
        "traceparent": None, "tracestate": None, "links": [],
    })
    add("v1_missing_correlation", "schemaVersion", 1)
    add("v1_bad_traceparent", "schemaVersion", 1)
    cases[-1][1]["correlation"] = {
        "traceparent": "00-" + "0" * 32 + "-" + "0" * 16 + "-01",
        "tracestate": None,
        "links": [],
    }
    return cases


def semantic_positive_variants(valid_contract: dict) -> list[tuple[str, dict]]:
    '''Valid legacy/current cases that an over-strict Rust port must keep.'''
    cases: list[tuple[str, dict]] = []

    def add(name: str, field: str, value: object) -> None:
        item = deepcopy(valid_contract)
        item[field] = value
        cases.append((name, item))

    add("bounded_private_model", "privacy", {
        "contentPolicy": "bounded-private-content",
        "allowModelContent": True,
        "allowToolContent": False,
    })
    add("bounded_private_tool", "privacy", {
        "contentPolicy": "bounded-private-content",
        "allowModelContent": False,
        "allowToolContent": True,
    })
    add("unicode_model_and_adapter", "requestedModelId", "model:测试-🧩")
    add("large_2048_digit_budget", "budget", {
        "maxTurns": 2,
        "countUpperBound": int("8" * 2048),
    })
    add("structured_current_schema", "completionContract", {
        "mode": "structured-result-v1",
        "resultSchema": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": {"status": {"type": "string"}},
            "required": ["status"],
            "additionalProperties": False,
        },
    })
    add("structured_legacy_profile", "completionContract", {
        "mode": "structured-result-v1",
        "conformancePolicy": "local-json-schema-draft-2020-12-profile-v1",
        "resultSchema": {
            "type": "object",
            "properties": {"count": {"type": "integer", "minimum": 0}},
            "additionalProperties": False,
        },
    })
    add("v1_none_correlation", "schemaVersion", 1)
    cases[-1][1]["correlation"] = {
        "traceparent": None, "tracestate": None, "links": [],
    }
    add("v1_real_traceparent", "schemaVersion", 1)
    cases[-1][1]["correlation"] = {
        "traceparent": "00-" + "1234567890abcdef" * 2 + "-1234567890abcdef-01",
        "tracestate": "vendor=value",
        "links": [{
            "ref": "test:trace-related",
            "kind": "test-only",
            "digest": valid_contract["toolCatalogDigest"],
        }],
    }
    add("valid_source_and_prior_artifact", "sourceRefs", [{
        "ref": "test:source-file", "kind": "test-only",
        "digest": valid_contract["toolCatalogDigest"],
    }])
    cases[-1][1]["priorArtifactRefs"] = [{
        "ref": "artifact:prior-file", "kind": "test-only",
        "digest": valid_contract["toolCatalogDigest"],
    }]
    add("valid_deadline", "deadlineMs", valid_contract["createdAtMs"] + 7000)
    return cases


with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
    valid = store.load_run(fixtures["valid"])
    template = store.get_object(valid.contract_object_digest, expected_kind="harness-run-contract")
    positive_cases: dict[str, str] = {}
    for name, variant in semantic_positive_variants(template):
        variant["harnessRunId"] = "harness-run:test-rust-pg-valid-" + name
        variant["callerRunRef"] = "test-run-valid-" + name
        contract = HarnessRunContract.from_dict(variant)
        assert store.create_run(contract).value == "created"
        store.validate_run_history(contract.harness_run_id)
        positive_cases[name] = contract.harness_run_id
    specs: list[tuple[str, str, dict, str, str, str]] = []
    for name, _ in semantic_counterexamples(template):
        template_run = deepcopy(template)
        template_run["harnessRunId"] = "harness-run:test-rust-pg-contract-" + name
        template_run["callerRunRef"] = "test-run-contract-" + name
        legitimate = HarnessRunContract.from_dict(template_run)
        assert store.create_run(legitimate).value == "created"
        created = store.list_run_events(legitimate.harness_run_id)[0]
        payload = store.get_object(
            created.payload_digest, expected_kind="ordivon.harness-run-event-payload"
        )
        specs.append((
            name, legitimate.harness_run_id, legitimate.to_dict(),
            created.event_id, created.payload_digest,
            json.dumps(payload, ensure_ascii=False),
        ))

cases: dict[str, str] = {}
with psycopg.connect(dsn, autocommit=True) as connection:
    connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
    for name, run_id, valid_contract, event_id, _, payload_json in specs:
        mutations = dict(semantic_counterexamples(valid_contract))
        malformed = mutations[name]
        try:
            HarnessRunContract.from_dict(malformed)
        except (ValueError, TypeError) as error:
            assert type(error) in {ValueError, TypeError}
        else:
            raise AssertionError(f"Python Contract unexpectedly accepted invalid case {name}")
        malformed_digest = canonical_digest(malformed)
        malformed_raw = canonical_bytes(malformed)
        new_payload = json.loads(payload_json)
        new_payload["data"] = {
            **new_payload["data"],
            "contractDigest": malformed_digest,
            "contractObjectDigest": malformed_digest,
        }
        payload_digest = canonical_digest(new_payload)
        payload_raw = canonical_bytes(new_payload)
        with connection.transaction():
            for digest, kind, raw in (
                (malformed_digest, "harness-run-contract", malformed_raw),
                (payload_digest, "ordivon.harness-run-event-payload", payload_raw),
            ):
                connection.execute(
                    "INSERT INTO objects(digest,kind,byte_length,content,first_seen_at_ms) "
                    "VALUES(%s,%s,%s,%s,%s) ON CONFLICT(digest) DO NOTHING",
                    (digest, kind, len(raw), raw, 1000),
                )
            connection.execute(
                "UPDATE runs SET contract_digest=%s,contract_object_digest=%s "
                "WHERE harness_run_id=%s",
                (malformed_digest, malformed_digest, run_id),
            )
            connection.execute(
                "UPDATE run_events SET payload_digest=%s WHERE event_id=%s",
                (payload_digest, event_id),
            )
            connection.execute(
                "UPDATE run_object_refs SET digest=%s WHERE event_id=%s AND role='payload'",
                (payload_digest, event_id),
            )
            connection.execute(
                "UPDATE run_object_refs SET digest=%s WHERE event_id=%s AND role='reference'",
                (malformed_digest, event_id),
            )
        cases[name] = run_id

    # Verify each probe with the *real* Python Store reader, not a local
    # imitation of its validation. This is the consumer source oracle.
    with PostgresHarnessStore(dsn, schema=schema, initialize=False) as store:
        for name, run_id in cases.items():
            try:
                store.validate_run_history(run_id)
            except (ValueError, HarnessObjectCorrupt):
                pass
            else:
                raise AssertionError(f"Python validated a semantically invalid Run: {name}")
            run = store.load_run(run_id)
            assert run.contract_digest == run.contract_object_digest
            assert len(store.list_run_events(run_id)) == run.revision == 1
        print(f"PYTHON_SEMANTIC_REJECTION={len(cases)}/{len(cases)}")

fixtures["positive_contract_cases"] = positive_cases
fixtures["invalid_contract"] = cases["provider_empty"]
fixtures["invalid_contract_cases"] = cases
path.write_text(json.dumps(fixtures, sort_keys=True), encoding="utf-8")
print("SCRATCH_PG_CONTRACT_SEMANTICS_CORPUS_READY", len(cases))
