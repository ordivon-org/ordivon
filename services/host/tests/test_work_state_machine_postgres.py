"""Generated sequential histories against the real PostgreSQL Work authority.

The model tracks logical transitions and immutable receipts independently of
WorkStore's branching and SQL. It is not a concurrent linearizability proof.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import psycopg
import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule, run_state_machine_as_test

from ordivon_host_v2.errors import ConflictError, WorkRevisionUnavailable
from ordivon_host_v2.references.actor_store import ActorReferenceStore
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkSnapshotInput,
    WorkState,
)
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
pytestmark = [
    pytest.mark.skipif(not DSN, reason="requires isolated PostgreSQL Work history"),
    pytest.mark.usefixtures("host_test_db_ready"),
]


@dataclass(frozen=True)
class Transition:
    predecessor: int
    value: str
    actor: int
    state: str


def payload(value: str) -> dict[str, Any]:
    # Independent expected wire shape, not WorkSnapshotInput.canonical_payload.
    return {
        "objective": "generated history",
        "frontier": value,
        "established": ["a", "a", "汉𠀀"],
        "unresolved": ["retain"],
        "rejected": [],
        "constraints": [],
        "nextActions": [],
        "referenceRefs": ["ref:b", "ref:a", "ref:b"],
    }


def snapshot(value: str) -> WorkSnapshotInput:
    return WorkSnapshotInput.model_validate(payload(value))


class History(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        assert DSN
        self.dsn = DSN
        self.prefix = "generated-work-" + uuid4().hex
        self.ref = "work:" + self.prefix
        self.actors = [f"actor:{self.prefix}:{i}" for i in range(2)]
        self.store = WorkStore(DSN)
        registry = ActorReferenceStore(DSN)
        for i, actor in enumerate(self.actors):
            registry.declare_actor(
                ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
                client_request_id=f"actor:{self.prefix}:{i}",
            )
        self.initial = WorkCreateInput(
            work_ref=self.ref,
            kind="generated",
            actor_ref=self.actors[0],
            initial_snapshot=snapshot("initial"),
        )
        self.history = [("initial", 0)]
        self.state = "open"
        self.last: Transition | None = None
        self.receipts: dict[str, tuple[Transition | None, dict[str, Any]]] = {}
        self.key_counter = 0
        self.create()

    def key(self) -> str:
        self.key_counter += 1
        return f"{self.prefix}:{self.key_counter}"

    def check_result(self, result, revision, state, admission):
        value, actor = self.history[revision - 1]
        assert result["workRef"] == self.ref
        assert result["revision"] == revision
        assert result["snapshot"] == payload(value)
        assert result["writerActorRef"] == self.actors[actor]
        assert result["state"] == state
        assert result["admission"] == admission

    def create(self):
        key = self.key()
        result = self.store.create_work(self.initial, client_request_id=key)
        self.check_result(
            result, len(self.history), self.state, "committed" if not self.receipts else "existing"
        )
        self.receipts[key] = (None, result)

    def call(self, command, key):
        return self.store.commit_snapshot(
            self.ref,
            expected_revision=command.predecessor,
            snapshot=snapshot(command.value),
            actor_ref=self.actors[command.actor],
            state=WorkState(command.state),
            client_request_id=key,
        )

    def transition(self, command: Transition):
        key = self.key()
        revision = len(self.history)
        # Fresh command may be the exact immediately preceding transition,
        # or a new transition at the open head. No other command is admitted.
        if command == self.last:
            expected = "existing"
        elif self.state == "open" and command.predecessor == revision:
            expected = "committed"
        else:
            with pytest.raises(ConflictError):
                self.call(command, key)
            return
        result = self.call(command, key)
        if expected == "committed":
            self.history.append((command.value, command.actor))
            self.state = command.state
            self.last = command
        self.check_result(result, len(self.history), self.state, expected)
        self.receipts[key] = (command, result)

    @rule(
        value=st.sampled_from(["A", "B", "汉𠀀"]),
        actor=st.integers(0, 1),
        offset=st.sampled_from([-1, 0, 0, 0, 1]),
        state=st.sampled_from(["open", "open", "completed", "abandoned"]),
    )
    def commit(self, value, actor, offset, state):
        self.transition(Transition(max(1, len(self.history) + offset), value, actor, state))

    @rule()
    def repeat_create(self):
        self.create()

    @rule()
    def fresh_duplicate(self):
        if self.last is not None:
            self.transition(self.last)

    @rule(data=st.data())
    def replay(self, data):
        key = data.draw(st.sampled_from(tuple(self.receipts)))
        command, original = self.receipts[key]
        result = (
            self.store.create_work(self.initial, client_request_id=key)
            if command is None
            else self.call(command, key)
        )
        assert result == {**original, "admission": "existing"}

    @rule(data=st.data())
    def conflicting_key(self, data):
        key = data.draw(st.sampled_from(tuple(self.receipts)))
        command, _ = self.receipts[key]
        if command is None:
            with pytest.raises(ConflictError):
                self.call(Transition(1, "different", 0, "open"), key)
        else:
            with pytest.raises(ConflictError):
                self.call(
                    Transition(
                        command.predecessor, command.value + "!", command.actor, command.state
                    ),
                    key,
                )

    @rule(data=st.data())
    def historical_read(self, data):
        revision = data.draw(st.integers(1, len(self.history)))
        row = self.store.get_work(self.ref, revision)
        value, actor = self.history[revision - 1]
        assert row["snapshot"] == payload(value)
        assert row["revision"] == revision
        assert row["writerActorRef"] == self.actors[actor]
        assert row["state"] == (
            self.state if revision == len(self.history) else "historical_state_unknown"
        )

    @rule()
    def future_read(self):
        with pytest.raises(WorkRevisionUnavailable):
            self.store.get_work(self.ref, len(self.history) + 1)

    @invariant()
    def durable_state(self):
        row = self.store.get_work(self.ref)
        value, actor = self.history[-1]
        assert row["revision"] == len(self.history)
        assert row["snapshot"] == payload(value)
        assert row["writerActorRef"] == self.actors[actor]
        assert row["state"] == self.state
        # Independent native table observation, including failed-command
        # transaction rollback; not a count inferred from the command response.
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute(
                "SELECT revision,payload,writer_actor_ref FROM work_snapshots "
                "WHERE work_ref=%s ORDER BY revision",
                (self.ref,),
            ).fetchall()
            receipts = conn.execute(
                "SELECT client_request_id,response IS NOT NULL FROM command_receipts "
                "WHERE client_request_id LIKE %s",
                (self.prefix + ":%",),
            ).fetchall()
        assert rows == [(i, payload(v), self.actors[a]) for i, (v, a) in enumerate(self.history, 1)]
        assert dict(receipts) == {key: True for key in self.receipts}


def test_generated_native_work_histories():
    run_state_machine_as_test(
        History,
        settings=settings(
            max_examples=16,
            stateful_step_count=14,
            deadline=None,
            derandomize=True,
        ),
    )


def test_native_duplicate_transition_distinguishes_actor_and_terminal_state():
    h = History()
    h.transition(Transition(1, "A", 0, "open"))
    h.transition(Transition(1, "A", 0, "open"))
    h.transition(Transition(1, "A", 1, "open"))
    h.transition(Transition(1, "A", 0, "completed"))
    h.durable_state()
    h.transition(Transition(2, "B", 1, "completed"))
    h.transition(Transition(2, "B", 1, "completed"))
    h.transition(Transition(3, "C", 0, "open"))
    h.create()
    for key, (command, original) in h.receipts.items():
        result = (
            h.store.create_work(h.initial, client_request_id=key)
            if command is None
            else h.call(command, key)
        )
        assert result == {**original, "admission": "existing"}
    h.durable_state()
