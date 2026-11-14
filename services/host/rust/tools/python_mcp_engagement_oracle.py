"""Python original WorkStore reads exactly the Rust R7 official MCP effects."""
from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg
from pydantic import ValidationError

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.work_inputs import WorkSnapshotInput
from ordivon_host_v2.work_store import WorkStore

dsn = os.environ.get("HOST_RUST_TEST_DSN", "")
assert dsn and "127.0.0.1" in dsn and os.environ.get("ORDIVON_HOST_V2_DSN") == dsn
path = os.environ.get("HOST_RUST_ENGAGEMENT_OBSERVED_PATH")
assert path
observed = json.loads(Path(path).read_text(encoding="utf-8"))
store = WorkStore(dsn)
work_ref = observed["workRef"]
assert work_ref == "work:test:r7-mcp-engagement-lifecycle"
assert len(observed["revisions"]) == 8
for rev in range(1, 9):
    original = store.get_work(work_ref, rev)
    published = observed["revisions"][str(rev)]
    assert original == published, (rev, original, published)
    assert original["snapshotDigest"] == canonical_digest(original["snapshot"])
    if rev >= 2:
        try:
            WorkSnapshotInput.model_validate(original["snapshot"])
        except ValidationError:
            pass
        else:
            raise AssertionError(
                "Original Python WorkSnapshotInput must reject new versioned engagement"
            )
assert store.get_work(work_ref)["revision"] == 8
assert store.get_work(work_ref)["state"] == "completed"
assert store.get_work("work:test:r7-mcp-engagement-cancellation")["state"] == "abandoned"
with psycopg.connect(dsn) as conn:
    for request_id, record in observed["receipts"].items():
        fields = record["request"]
        expected = canonical_digest({
            "operation": "work.engagement.advance",
            "workRef": fields["workRef"],
            "expectedRevision": fields["expectedRevision"],
            "actorRef": fields["actorRef"],
            "action": fields["action"],
        })
        row = conn.execute(
            "SELECT operation,request_digest,response FROM command_receipts "
            "WHERE client_request_id=%s", (request_id,)
        ).fetchone()
        assert row is not None, request_id
        assert row[0] == "work.engagement.advance" and row[1] == expected
        assert row[2] == record["response"], (request_id, row[2], record["response"])

    offered_http = conn.execute(
        "SELECT current_revision FROM works WHERE work_ref=%s",
        ("work:test:r7-mcp-http",),
    ).fetchone()
    assert offered_http is not None and offered_http[0] == 3
    http = store.get_work("work:test:r7-mcp-http")
    assert http["snapshot"]["engagement"]["phase"] == "claimed"
    assert http["snapshot"]["engagement"]["claimEpoch"] == 1

print(
    "R7_ORIGINAL_PYTHON_WORKSTORE_MCP_READBACK_PASS "
    "revisions=8 digests=8 old_strict_rejection=7 native_receipts="
    f"{len(observed['receipts'])} http_roundtrip=YES"
)
