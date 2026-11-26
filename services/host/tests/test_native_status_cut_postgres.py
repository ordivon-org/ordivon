"""Public status is one read-only authority cut, even under concurrent writers."""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from ordivon_host_v2.collaboration_inputs import MessageInput, SpaceInput, TopicInput
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.service import HostV2
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires disposable native PostgreSQL"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def test_summary_is_one_native_projection_at_a_consistent_cut(monkeypatch):
    assert DSN
    token = uuid4().hex
    actor, space, topic, message = (
        f"{kind}:status-cut:{token}" for kind in ("actor", "space", "topic", "message")
    )
    ActorReferenceStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{token}",
    )
    host = HostV2(DSN)
    baseline = host.status()["authority"]
    execute = psycopg.Connection.execute
    reader = None
    reads = []
    settings = []
    injected = False

    def observe(conn, query, *args, **kwargs):
        nonlocal injected, reader
        result = execute(conn, query, *args, **kwargs)
        if not isinstance(query, str):
            return result
        if reader is None:
            reader = conn
        if conn is reader and query.lstrip().upper().startswith("SELECT"):
            reads.append(query)
            isolation = execute(conn, "SHOW transaction_isolation").fetchone()[
                "transaction_isolation"
            ]
            readonly = execute(conn, "SHOW transaction_read_only").fetchone()[
                "transaction_read_only"
            ]
            settings.append((isolation, readonly))
            if not injected:
                injected = True
                social = SocialStore(DSN)
                social.create_space(
                    SpaceInput(
                        space_ref=space, purpose="concurrent status witness", actor_ref=actor
                    ),
                    client_request_id=f"space:{token}",
                )
                social.create_topic(
                    TopicInput(
                        topic_ref=topic, space_ref=space, title="status cut", actor_ref=actor
                    ),
                    client_request_id=f"topic:{token}",
                )
                social.post_message(
                    MessageInput(
                        message_ref=message,
                        client_request_id=f"post:{token}",
                        space_ref=space,
                        topic_ref=topic,
                        author_actor_ref=actor,
                        body="later cut",
                        recorded_at_ms=1,
                    )
                )
        return result

    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Connection, "execute", observe)
        earlier = host.status()
    assert injected
    assert earlier["authority"] == baseline, "summary mixed facts from different MVCC cuts"
    assert len(reads) == 1
    assert settings == [("repeatable read", "on")]
    assert earlier["doctor"] is None
    after = host.status()["authority"]
    for key in ("spaces", "topics", "messages"):
        assert after[key] == baseline[key] + 1
    assert after["changeHighSequence"] > baseline["changeHighSequence"]
    assert after["works"] == sum(after["worksByState"].values())


@pytest.mark.parametrize("detail", ["summary", "integrity", "history"])
def test_native_status_rejects_indirect_write(monkeypatch, detail):
    assert DSN
    execute = psycopg.Connection.execute
    injected = False

    def observe(conn, query, *args, **kwargs):
        nonlocal injected
        result = execute(conn, query, *args, **kwargs)
        if not injected and isinstance(query, str) and query.lstrip().upper().startswith("SELECT"):
            injected = True
            execute(conn, "UPDATE works SET current_revision=current_revision WHERE false")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Connection, "execute", observe)
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            HostV2(DSN).status(detail=detail)
    assert injected
    assert HostV2(DSN).status(detail="integrity")["doctor"]["healthy"]
