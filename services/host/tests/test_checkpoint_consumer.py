from __future__ import annotations

import copy
import json

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_host_v2.canonical_json import canonical_digest
from ordivon_host_v2.social_message_records import message_content
from ordivon_host_v2.work_inputs import WorkSnapshotInput
from tools.host_checkpoint_verify import verify_checkpoint


def wire(ref, body):
    content = message_content(
        message_ref=ref,
        space_ref="space:test",
        topic_ref="topic:test",
        author_actor_ref="actor:test",
        message_kind="handoff",
        body=json.dumps(body, ensure_ascii=False),
        recorded_at_ms=1,
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.host-message-read",
        **content,
        "messageDigest": canonical_digest(content),
    }


def fixture(refs, *, full=True, note="汉𠀀"):
    snapshot = WorkSnapshotInput(
        objective="objective", frontier=note, reference_refs=refs
    ).canonical_payload()
    coord = {"workRef": "work:test", "revision": 2, "snapshotDigest": canonical_digest(snapshot)}
    work = {"schemaVersion": 1, "kind": "ordivon.host-work", **coord, "snapshot": snapshot}
    parts = []
    if full:
        payload = json.dumps(snapshot, ensure_ascii=False)
        cut = len(payload) // 2
        for n, text in enumerate((payload[:cut], payload[cut:]), 1):
            parts.append(
                wire(
                    f"message:part:{n}",
                    {
                        **coord,
                        "kind": "work-snapshot-checkpoint-part-v1",
                        "part": n,
                        "total": 2,
                        "payload": text,
                    },
                )
            )
        body = {
            **coord,
            "kind": "work-snapshot-checkpoint-manifest-v1",
            "encoding": "ordered concatenation of part.payload, JSON.parse",
            "chars": len(payload.encode("utf-16-le")) // 2,
            "parts": [{k: p[k] for k in ("messageRef", "messageDigest")} for p in parts],
        }
    else:
        body = {
            **coord,
            "kind": "ordered-reference-checkpoint-v1",
            "referenceRefs": refs,
            "count": len(refs),
            "previousFullCheckpoint": "message:previous",
            "previousFullCheckpointDigest": "sha256:" + "b" * 64,
        }
    manifest = wire("message:manifest", body)
    pin = {
        **coord,
        "manifestRef": manifest["messageRef"],
        "manifestDigest": manifest["messageDigest"],
    }
    return pin, work, manifest, parts


@given(
    st.lists(st.sampled_from(["a", "b", "汉𠀀", "ref:1", "ref:2"]), max_size=256),
    st.text(alphabet="abc汉𠀀🙂", min_size=1, max_size=40),
)
@settings(max_examples=100)
def test_both_existing_formats_preserve_order_and_multiplicity(refs, note):
    for full in (True, False):
        result = verify_checkpoint(*fixture(refs, full=full, note=note))
        assert result["referenceCount"] == len(refs)
        assert result["snapshotVerified"] is full
        assert result["retentionPinVerified"] is False
        assert result["currentnessVerified"] is False


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "extra",
        "order",
        "payload",
        "scope",
        "work",
        "revision",
        "manifest",
        "wrong_snapshot",
    ],
)
def test_corrupt_readbacks_fail_closed(change):
    pin, work, manifest, parts = copy.deepcopy(fixture(["a", "b", "a"]))
    if change == "missing":
        parts.pop()
    elif change == "extra":
        parts.append(parts[0])
    elif change == "order":
        parts.reverse()
    elif change == "payload":
        parts[0]["body"] += " "
    elif change == "scope":
        parts[0]["topicRef"] = "topic:other"
    elif change == "work":
        work["workRef"] = "work:other"
    elif change == "revision":
        work["revision"] = 2.0
    elif change == "manifest":
        manifest["messageDigest"] = "sha256:" + "0" * 64
    elif change == "wrong_snapshot":
        work["snapshot"]["referenceRefs"] = ["b", "a", "a"]
    with pytest.raises(ValueError):
        verify_checkpoint(pin, work, manifest, parts)


def rebind_manifest(pin, manifest, body):
    updated = wire(manifest["messageRef"], body)
    return {**pin, "manifestDigest": updated["messageDigest"]}, updated


@pytest.mark.parametrize("change", ["reorder", "deduplicate", "count", "bad_previous"])
def test_consistently_rehashed_wrong_reference_archive_is_not_evidence(change):
    pin, work, manifest, parts = fixture(["a", "b", "a"], full=False)
    body = json.loads(manifest["body"])
    if change == "reorder":
        body["referenceRefs"] = ["b", "a", "a"]
    elif change == "deduplicate":
        body["referenceRefs"] = ["a", "b"]
        body["count"] = 2
    elif change == "count":
        body["count"] = 3.0
    elif change == "bad_previous":
        body["previousFullCheckpointDigest"] = "unknown"
    pin, manifest = rebind_manifest(pin, manifest, body)
    with pytest.raises(ValueError):
        verify_checkpoint(pin, work, manifest, parts)


def test_rehashed_duplicate_json_and_wrong_part_scope_rejected():
    pin, work, manifest, parts = fixture(["a"])
    body = json.loads(manifest["body"])
    # Even when the supplied message pin is internally consistent, a duplicate
    # JSON key must not be silently discarded by the consumer.
    manifest["body"] = manifest["body"][:-1] + ', "revision": 2}'
    content = {
        k: manifest[k]
        for k in (
            "messageRef",
            "spaceRef",
            "topicRef",
            "authorActorRef",
            "messageKind",
            "body",
            "recordedAtMs",
        )
    }
    manifest["messageDigest"] = canonical_digest(content)
    with pytest.raises(ValueError, match="duplicate"):
        verify_checkpoint(
            {**pin, "manifestDigest": manifest["messageDigest"]}, work, manifest, parts
        )
    pin, work, manifest, parts = fixture(["a"])
    parts[0]["topicRef"] = "topic:other"
    content = {k: parts[0][k] for k in content}
    parts[0]["messageDigest"] = canonical_digest(content)
    body["parts"][0]["messageDigest"] = parts[0]["messageDigest"]
    pin, manifest = rebind_manifest(pin, manifest, body)
    with pytest.raises(ValueError, match="scope"):
        verify_checkpoint(pin, work, manifest, parts)


@pytest.mark.usefixtures("host_test_db_ready")
def test_native_checkpoint_consumer_reads_real_historical_work_and_messages():
    import os
    import subprocess
    import sys
    from uuid import uuid4

    from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
    from ordivon_host_v2.references.actor_store import ActorReferenceStore
    from ordivon_host_v2.social_store import SocialStore
    from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput, WorkCreateInput
    from ordivon_host_v2.work_store import WorkStore

    dsn = os.environ["ORDIVON_HOST_V2_TEST_DSN"]
    token = uuid4().hex
    actor, work_ref, space, topic = (
        f"{kind}:checkpoint:{token}" for kind in ("actor", "work", "space", "topic")
    )
    a, w, s = ActorReferenceStore(dsn), WorkStore(dsn), SocialStore(dsn)
    a.declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    original = WorkSnapshotInput(
        objective="historical checkpoint",
        frontier="汉𠀀🙂",
        established=["immutable"],
        unresolved=["still open"],
        reference_refs=["ref:a", "ref:b", "ref:a"],
    )
    w.create_work(
        WorkCreateInput(
            work_ref=work_ref, kind="qualification", actor_ref=actor, initial_snapshot=original
        ),
        client_request_id=f"create:{token}",
    )
    w.commit_snapshot(
        work_ref,
        expected_revision=1,
        snapshot=WorkSnapshotInput(objective="historical checkpoint", frontier="new"),
        actor_ref=actor,
        client_request_id=f"advance:{token}",
    )
    historical = w.get_work(work_ref, 1)
    coord = {k: historical[k] for k in ("workRef", "revision", "snapshotDigest")}
    s.create_space(
        SpaceInput(space_ref=space, purpose="checkpoint verification", actor_ref=actor),
        client_request_id=f"space:{token}",
    )
    s.create_topic(
        TopicInput(topic_ref=topic, space_ref=space, title="checkpoint", actor_ref=actor),
        client_request_id=f"topic:{token}",
    )

    def post(name, body):
        ref = f"message:checkpoint:{token}:{name}"
        result = s.post_message(
            MessageInput(
                message_ref=ref,
                client_request_id=ref,
                space_ref=space,
                topic_ref=topic,
                author_actor_ref=actor,
                message_kind="handoff",
                body=json.dumps(body, ensure_ascii=False),
                recorded_at_ms=1,
            )
        )
        return s.get_message(ref, expected_digest=result["messageDigest"])

    payload = json.dumps(historical["snapshot"], ensure_ascii=False)
    cut = len(payload) // 2
    parts = [
        post(
            f"part:{n}",
            {
                **coord,
                "kind": "work-snapshot-checkpoint-part-v1",
                "part": n,
                "total": 2,
                "payload": chunk,
            },
        )
        for n, chunk in enumerate((payload[:cut], payload[cut:]), 1)
    ]
    full = post(
        "full",
        {
            **coord,
            "kind": "work-snapshot-checkpoint-manifest-v1",
            "encoding": "ordered concatenation of part.payload, JSON.parse",
            "chars": len(payload.encode("utf-16-le")) // 2,
            "parts": [{k: p[k] for k in ("messageRef", "messageDigest")} for p in parts],
        },
    )
    ordered = post(
        "ordered",
        {
            **coord,
            "kind": "ordered-reference-checkpoint-v1",
            "count": 3,
            "referenceRefs": ["ref:a", "ref:b", "ref:a"],
            "previousFullCheckpoint": full["messageRef"],
            "previousFullCheckpointDigest": full["messageDigest"],
        },
    )
    for manifest, supplied_parts in ((full, parts), (ordered, [])):
        pin = {
            **coord,
            "manifestRef": manifest["messageRef"],
            "manifestDigest": manifest["messageDigest"],
        }
        bundle = {"pin": pin, "work": historical, "manifest": manifest, "parts": supplied_parts}
        expected = verify_checkpoint(pin, historical, manifest, supplied_parts)
        actual = subprocess.run(
            [sys.executable, "tools/host_checkpoint_verify.py"],
            input=json.dumps(bundle, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )
        assert json.loads(actual.stdout) == expected
        assert expected["referenceCount"] == 3
    assert w.get_work(work_ref)["revision"] == 2
