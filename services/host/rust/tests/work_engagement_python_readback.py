"""Independent original Python Host reader for Rust Work engagement history.

No production writes, no new Postgres tables. Python's original WorkStore reads
immutable Rust snapshots and receipt digests from the same disposable database.
"""

from __future__ import annotations

import os

import psycopg
from pydantic import ValidationError

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.work_inputs import WorkSnapshotInput, WorkState
from ordivon_host_v2.work_store import WorkStore

dsn = os.getenv("HOST_RUST_TEST_DSN")
assert dsn and dsn == os.getenv("ORDIVON_HOST_V2_DSN"), "requires explicit disposable PG18 test DSN"
store = WorkStore(dsn)
work = "work:test:engagement:lifecycle-r7"
current = store.get_work(work)
assert current["state"] == "completed", current
assert current["revision"] == 8, current
engagement = current["snapshot"]["engagement"]
assert engagement["schemaVersion"] == 1, engagement
assert engagement["phase"] == "accepted", engagement
assert engagement["claimEpoch"] == 2, engagement
assert engagement["requestedByActorRef"] == "actor:test:engagement-requester"
assert engagement["consumerActorRef"] == "actor:test:engagement-consumer"
assert engagement["review"]["verificationRefs"] == ["evidence:consumer:review"]
assert current["snapshotDigest"] == canonical_digest(current["snapshot"])
# Legacy Python input is intentionally strict. New engagement is a different
# versioned operation, not an unsafe broadening of old Work.snapshot.commit.
try:
    WorkSnapshotInput.model_validate(current["snapshot"])
except ValidationError as error:
    assert any(
        entry["type"] == "extra_forbidden" and "engagement" in entry["loc"]
        for entry in error.errors()
    ), error
else:
    raise AssertionError("old WorkSnapshotInput silently accepted new engagement")

for version in range(1, 9):
    observed = store.get_work(work, revision=version)
    assert observed["revision"] == version, observed
    assert observed["snapshotDigest"] == canonical_digest(observed["snapshot"])
    if version < 8:
        assert observed["state"] == "historical_state_unknown", observed
assert "engagement" not in store.get_work(work, revision=1)["snapshot"]
assert store.get_work(work, revision=4)["snapshot"]["engagement"]["phase"] == "submitted"
assert store.get_work(work, revision=5)["snapshot"]["engagement"]["phase"] == "returned"
assert store.get_work(work, revision=6)["snapshot"]["engagement"]["claimEpoch"] == 2

cancelled = store.get_work("work:test:engagement:cancel-r7")
assert cancelled["state"] == "abandoned"
assert cancelled["snapshot"]["engagement"]["phase"] == "cancelled"
assert cancelled["snapshot"]["engagement"]["claimEpoch"] == 2

with psycopg.connect(dsn) as conn:
    row = conn.execute(
        "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=%s",
        ("request:test:engagement:offer",),
    ).fetchone()
    assert row is not None, "no persisted offer receipt"
    operation, digest, response = row
    assert operation == "work.engagement.advance"
    offer_request = {
        "operation": "work.engagement.advance",
        "workRef": work,
        "expectedRevision": 1,
        "actorRef": "actor:test:engagement-requester",
        "action": {
            "type": "offer",
            "consumerActorRef": "actor:test:engagement-consumer",
            "acceptanceCriteria": ["Consumer independently checks referenced result and receipt"],
        },
    }
    assert digest == canonical_digest(offer_request), (digest, offer_request)
    assert response["snapshot"]["engagement"]["phase"] == "offered"

# DTO strictness alone is not enough: the old Python writer must not erase
# current Rust-owned engagement from an already-open, versioned Work.
legacy_ref = "work:test:engagement:inventory-00"
before_legacy_attempt = store.get_work(legacy_ref)
assert before_legacy_attempt["state"] == "open"
assert before_legacy_attempt["revision"] == 2
assert before_legacy_attempt["snapshot"]["engagement"]["phase"] == "offered"
legacy_request_id = "request:test:python-generic-erases-rust-engagement-r11"
try:
    store.commit_snapshot(
        legacy_ref,
        expected_revision=2,
        snapshot=WorkSnapshotInput(
            objective="Legacy API must preserve versioned Work engagement",
            frontier="Old writer attempt to downgrade accountable Work",
        ),
        actor_ref="actor:test:engagement-requester",
        state=WorkState.OPEN,
        client_request_id=legacy_request_id,
    )
except ConflictError:
    pass
else:
    raise AssertionError("legacy Python erased active Rust Work engagement")
after_legacy_attempt = store.get_work(legacy_ref)
assert after_legacy_attempt == before_legacy_attempt
with psycopg.connect(dsn) as conn:
    assert (
        conn.execute(
            "SELECT 1 FROM command_receipts WHERE client_request_id=%s",
            (legacy_request_id,),
        ).fetchone()
        is None
    )

print("R11_LEGACY_WRITER_CAS_PRESERVES_RUST_ENGAGEMENT_PASS unchanged=true receipt=absent")

print("R7_ORIGINAL_PYTHON_READS_RUST_CLAIM_DELIVERY_REVIEW_EXACT_PASS")
