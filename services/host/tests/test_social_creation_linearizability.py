from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest

from ordivon_host_v2.collaboration_inputs import SpaceInput
from ordivon_host_v2.coordination_inputs import CoordinationIntentInput
from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.social_store import SocialStore
from ordivon_host_v2.work_inputs import ActorKind, ActorRefInput
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="ORDIVON_HOST_V2_TEST_DSN not set"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


def _actor() -> str:
    assert DSN is not None
    actor = f"actor:agent:concurrent-social-create:{uuid4().hex}"
    WorkStore(DSN).declare_actor(
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
