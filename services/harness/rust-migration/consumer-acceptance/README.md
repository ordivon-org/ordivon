# Consumer qualification: digest-valid, semantically invalid Run Contract

Status: **confirmed RED counterexample** against experimental Rust PG Reader
at commit 6d97f2a08265152a2771addb87877f85e2338c40.
This is not a production-data corruption report or a deployed cutover.

The Python HarnessRunContract.from_dict checks more than the identities
currently verified by the Rust PG Reader. It rejects an empty providerId.
An internally consistent, digest-valid PG v1 Run with this invalid Contract
is a legal integrity-falsification fixture. Hashes, references, revisions,
Run identities and creation event metadata can all remain consistent.

The opt-in test deliberately fails until Rust performs semantic Contract
validation. It is ignored by default, so normal Cargo runs remain green.

To reproduce with PostgreSQL 18, Cargo, uv and Python available, set
HARNESS_CONSUMER_FALSIFY_CONTRACT=1 and execute:
  bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh

The standard original five PG cases execute first. Then the Python script
make_invalid_contract_fixture.py copies a genuinely Python-created Run in
the disposable test DB and rewrites the Contract and creation-event CAS
contents consistently while setting providerId to an empty string.
Python validate_run_history rejects the Run. The separate Rust test
contract_semantic_falsifier.rs --ignored currently shows Rust accepts it.

The test creates a fresh PG data directory under /tmp, a temporary schema
beginning hpg_rust_isolated_, and a SELECT-only Rust role. It does not use
the configured production PG DSN. The runner shuts down/cleans the temp PG.

Required repair is NOT a one-off empty-provider check. The promotion gate
is Rust/Python parity for the complete versioned HarnessRunContract:
exact fields, identities, bound refs, privacy, budget, completion, deadline,
schema-v1 correlation and schema-v2 restrictions. Test-only code is handed
to A for a real Contract validator; C/consumers must still independently
accept the fix before Rust history takeover or PR merge.
