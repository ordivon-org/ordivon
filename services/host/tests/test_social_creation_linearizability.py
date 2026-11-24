from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from ordivon_host_v2.collaboration_inputs import SpaceInput
from ordivon_host_v2.coordination_inputs import CoordinationIntentInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def _actor() -> str:
    assert DSN is not None
    actor = f"actor:agent:concurrent-social-create:{uuid4().hex}"
    ActorReferenceStore(DSN).declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"actor:{actor}",
    )
    return actor


def _racing_requests(fn, count: int) -> list[str]:
    barrier = Barrier(count)

    def invoke(index: int) -> str:
        barrier.wait(timeout=15)
        try:
            return fn(index)
        except ConflictError:
            return "conflict"
        except Exception as error:
            return type(error).__name__

    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(invoke, range(count)))


def test_parallel_identical_space_creation_has_one_winner_and_no_storage_errors() -> None:
    assert DSN is not None
    actor = _actor()
    space = f"space:create-race:{uuid4().hex}"
    store = SocialStore(DSN)
    payload = SpaceInput(
        space_ref=space, purpose="same canonical social scope", actor_ref=actor,
        subject_refs=["subject:one", "subject:two"],
    )
    outcomes = _racing_requests(
        lambda index: store.create_space(
            payload, client_request_id=f"space:create-race:{space}:{index}"
        )["admission"],
        12,
    )
    assert sorted(outcomes) == ["committed", *(["existing"] * 11)], outcomes
    assert store.get_space(space)["subjectRefs"] == ["subject:one", "subject:two"]


def test_parallel_incompatible_space_semantics_are_domain_conflicts() -> None:
    assert DSN is not None
    actor = _actor()
    space = f"space:create-incompatible:{uuid4().hex}"
    store = SocialStore(DSN)
    outcomes = _racing_requests(
        lambda index: store.create_space(
            SpaceInput(
                space_ref=space, actor_ref=actor,
                purpose=f"distinct initial semantic {index}", subject_refs=[],
            ),
            client_request_id=f"space:incompatible:{space}:{index}",
        )["admission"],
        2,
    )
    assert sorted(outcomes) == ["committed", "conflict"], outcomes


def test_parallel_identical_intent_declaration_has_one_winner() -> None:
    assert DSN is not None
    actor = _actor()
    intent = f"intent:create-race:{uuid4().hex}"
    store = SocialStore(DSN)
    payload = CoordinationIntentInput(
        intent_ref=intent, actor_ref=actor, subject_ref="subject:shared",
        operation="review", observed_at_ms=1000, expires_at_ms=2000,
    )
    outcomes = _racing_requests(
        lambda index: store.declare_intent(
            payload, client_request_id=f"intent:create-race:{intent}:{index}"
        )["admission"],
        12,
    )
    assert sorted(outcomes) == ["committed", *(["existing"] * 11)], outcomes


def test_parallel_incompatible_intent_semantics_are_domain_conflicts() -> None:
    assert DSN is not None
    actor = _actor()
    intent = f"intent:create-incompatible:{uuid4().hex}"
    store = SocialStore(DSN)
    outcomes = _racing_requests(
        lambda index: store.declare_intent(
            CoordinationIntentInput(
                intent_ref=intent, actor_ref=actor,
                subject_ref=f"subject:distinct:{index}",
                operation="review", observed_at_ms=1000, expires_at_ms=2000,
            ),
            client_request_id=f"intent:incompatible:{intent}:{index}",
        )["admission"],
        2,
    )
    assert sorted(outcomes) == ["committed", "conflict"], outcomes


def test_space_create_reads_new_subjects_in_same_uncommitted_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An independent PG reader cannot see the row until creation commits.

    Create's own response must already include subject rows that were inserted
    within that same transaction; never replace the shared conn with a second
    checkout or infer success from an unrelated committed snapshot.
    """
    assert DSN is not None
    import psycopg

    from ordivon_host_v2 import social_space_commands
    from ordivon_host_v2.social_space_records import read_space_in_tx

    actor = _actor()
    ref = f"space:create-readback:{uuid4().hex}"
    observed = []

    def witnessed_readback(conn, space_ref, **kwargs):
        assert space_ref == ref
        own_space = conn.execute(
            "SELECT space_ref FROM spaces WHERE space_ref=%s", (ref,)
        ).fetchone()
        assert own_space is not None
        own_subjects = conn.execute(
            "SELECT subject_ref FROM space_subjects WHERE space_ref=%s ORDER BY subject_ref",
            (ref,),
        ).fetchall()
        assert [row["subject_ref"] for row in own_subjects] == ["subject:a", "subject:z"]

        with psycopg.connect(DSN) as outside:
            assert outside.execute(
                "SELECT 1 FROM spaces WHERE space_ref=%s", (ref,)
            ).fetchone() is None, "newly created Space leaked before transaction commit"
        observed.append(True)
        return read_space_in_tx(conn, space_ref, **kwargs)

    monkeypatch.setattr(social_space_commands, "read_space_in_tx", witnessed_readback)
    social = SocialStore(DSN)
    created = social.create_space(
        SpaceInput(
            space_ref=ref,
            purpose="one-owner same-transaction Space projection",
            actor_ref=actor,
            subject_refs=["subject:z", "subject:a"],
        ),
        client_request_id=f"create:{ref}",
    )
    assert observed == [True]
    assert created["admission"] == "committed"
    assert created["spaceRef"] == ref
    assert created["subjectRefs"] == ["subject:a", "subject:z"]
    assert created["subjectCount"] == 2
    assert created["subjectHasMore"] is False
    assert social.get_space(ref)["subjectRefs"] == created["subjectRefs"]
