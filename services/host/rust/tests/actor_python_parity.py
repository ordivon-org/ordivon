"""Python reads the exact PG18 ActorDeclare receipt written by Rust.

Requires the same disposable schema13 database after Rust work_pg tests.
Never provides an implicit production DSN fallback.
"""

from __future__ import annotations

import os

import psycopg

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput
from ordivon_host_v2.work_store import WorkStore

dsn = os.environ.get("HOST_RUST_TEST_DSN")
assert dsn and dsn == os.environ.get("ORDIVON_HOST_V2_DSN"), (
    "requires explicit shared disposable PG18 test DSN"
)
actor_ref = "actor:test:rust:actor-declare"
request_id = "request:test:actor:declare-v1"
request = {"operation": "actor.declare", "actor_ref": actor_ref, "actor_kind": "agent"}

with psycopg.connect(dsn) as conn:
    row = conn.execute(
        "SELECT operation,request_digest,response FROM command_receipts WHERE client_request_id=%s",
        (request_id,),
    ).fetchone()
    assert row is not None, "Rust receipt is not in same disposable PG"
    operation, digest, original = row
    assert operation == "actor.declare"
    assert digest == canonical_digest(request), "Python and Rust request digests differ"
    assert original["admission"] == "committed"
    assert original["actorRef"] == actor_ref
    assert original["actorKind"] == "agent"

work = WorkStore(dsn)
replayed = work.declare_actor(
    ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
    client_request_id=request_id,
)
assert replayed == {**original, "admission": "existing"}, (
    "Python cannot replay the exact Rust ActorDeclare receipt"
)

another_request = work.declare_actor(
    ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.AGENT),
    client_request_id="request:test:actor:python-different-id",
)
assert another_request == {**original, "admission": "existing"}
try:
    work.declare_actor(
        ActorRefInput(actor_ref=actor_ref, actor_kind=ActorKind.HUMAN),
        client_request_id="request:test:actor:python-different-kind",
    )
except ConflictError:
    pass
else:
    raise AssertionError("Python accepted mismatched actor_kind against Rust insert")
print("ACTOR_PYTHON_RUST_RECEIPT_PARITY_PASS")
