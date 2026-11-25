"""Generated codec contracts; separate from actual PostgreSQL lifecycle tests."""

from __future__ import annotations

import hashlib
from copy import deepcopy

import pytest
import rfc8785
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_host_v2.work_receipts import (
    encode_work_receipt,
    replay_pinned_work_receipt,
    replay_work_receipt,
)

MAX_EXACT = (1 << 53) - 1
TEXT = st.text(alphabet=st.characters(exclude_categories=("Cs",)), max_size=40)
SNAPSHOT = st.fixed_dictionaries(
    {
        "objective": TEXT,
        "frontier": TEXT,
        "established": st.lists(TEXT, max_size=8),
        "nextActions": st.lists(TEXT, max_size=8),
    }
)
REVISION = st.one_of(st.sampled_from([1, 2, MAX_EXACT]), st.integers(1, MAX_EXACT))


def digest(value):
    # Direct canonical library + independent hash, not the production helper.
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def response(snapshot, revision, state, admission):
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-work",
        "workRef": "work:generated",
        "workKind": "test",
        "state": state,
        "revision": revision,
        "snapshotDigest": digest(snapshot),
        "snapshot": snapshot,
        "writerActorRef": "actor:agent:writer",
        "createdByActorRef": "actor:agent:creator",
        "createdAt": "2026-11-25T00:00:00Z",
        "updatedAt": "2026-11-25T00:00:01Z",
        "admission": admission,
    }


def target(value):
    return {
        "snapshot_digest": value["snapshotDigest"],
        "payload": deepcopy(value["snapshot"]),
        "writer_actor_ref": value["writerActorRef"],
    }


class Lookup:
    """A narrow query seam; the separate native tests prove actual SQL/FK."""

    def __init__(self, row):
        self.row = row
        self.keys = []

    def execute(self, _sql, params):
        self.keys.append(params)
        return self

    def fetchone(self):
        return self.row


@given(
    SNAPSHOT,
    REVISION,
    st.sampled_from(["open", "completed"]),
    st.sampled_from(["committed", "existing"]),
)
@settings(max_examples=120, derandomize=True, deadline=None)
def test_generated_exact_replay_and_legacy_no_lookup(snapshot, revision, state, admission):
    original = response(snapshot, revision, state, admission)
    before = deepcopy(original)
    expected = {**original, "admission": "existing"}
    tag = encode_work_receipt(original)
    assert original == before
    assert "snapshot" not in tag["envelope"]
    assert tag["responseDigest"] == digest(expected)
    lookup = Lookup(target(original))
    assert replay_work_receipt(lookup, tag, work_ref=original["workRef"]) == expected
    assert (
        replay_pinned_work_receipt(
            tag, work_ref=original["workRef"], revision=revision, target=target(original)
        )
        == expected
    )
    # Matching target bytes do not authorize a different native coordinate.
    with pytest.raises(RuntimeError, match="reference differs"):
        replay_pinned_work_receipt(
            tag, work_ref=original["workRef"], revision=revision + 1, target=target(original)
        )
    with pytest.raises(RuntimeError, match="reference differs"):
        replay_pinned_work_receipt(
            tag, work_ref="work:other", revision=revision, target=target(original)
        )
    assert lookup.keys == [(original["workRef"], revision)]
    assert replay_work_receipt(lookup, expected, work_ref=original["workRef"]) == expected
    assert len(lookup.keys) == 1


@given(
    SNAPSHOT,
    REVISION,
    st.sampled_from(["work_ref", "work_kind", "revision", "snapshot_digest", "actor_ref", "state"]),
)
@settings(max_examples=120, derandomize=True, deadline=None)
def test_generated_wrong_committed_context_rejected_without_lookup(snapshot, revision, field):
    original = response(snapshot, revision, "open", "committed")
    context = {
        "work_ref": original["workRef"],
        "work_kind": original["workKind"],
        "revision": revision,
        "snapshot_digest": original["snapshotDigest"],
        "actor_ref": original["writerActorRef"],
        "state": original["state"],
    }
    context[field] = revision + 1 if field == "revision" else "different"
    lookup = Lookup(target(original))
    with pytest.raises(RuntimeError, match="reference differs"):
        replay_work_receipt(lookup, encode_work_receipt(original), **context)
    assert lookup.keys == []


@given(SNAPSHOT, REVISION, st.sampled_from(["missing", "payload", "digest", "writer", "response"]))
@settings(max_examples=120, derandomize=True, deadline=None)
def test_generated_mutated_target_or_response_never_replays(snapshot, revision, mutation):
    original = response(snapshot, revision, "open", "committed")
    tag = encode_work_receipt(original)
    row = target(original)
    if mutation == "missing":
        row = None
    elif mutation == "payload":
        row["payload"]["objective"] += "!"
    elif mutation == "digest":
        row["snapshot_digest"] = "different"
    elif mutation == "writer":
        row["writer_actor_ref"] = "actor:agent:other"
    else:
        tag["envelope"]["updatedAt"] = "different"
    lookup = Lookup(row)
    with pytest.raises(
        RuntimeError,
        match="response digest differs"
        if mutation == "response"
        else "target is missing or changed",
    ):
        replay_work_receipt(lookup, tag, work_ref=original["workRef"])
    assert lookup.keys == [(original["workRef"], revision)]
