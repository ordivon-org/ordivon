"""Finite native PostgreSQL CDC for transitive Work DAG cycle exclusion.

This is a bounded three-vertex graph oracle, not a proof of unbounded
PostgreSQL concurrency, liveness or external EffectAuthority.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from itertools import permutations
from threading import Barrier
from uuid import uuid4

import psycopg
import pytest

from ordivon_host_v2.errors import ConflictError
from ordivon_host_v2.work_inputs import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkRelationInput,
    WorkRelationKind,
    WorkSnapshotInput,
)
from ordivon_host_v2.work_store import WorkStore

DSN = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
TRIANGLE = ((0, 1), (1, 2), (2, 0))


def _has_cycle(edges: list[tuple[str, str]]) -> bool:
    outgoing: dict[str, list[str]] = {}
    for source, target in edges:
        outgoing.setdefault(source, []).append(target)
    seen: dict[str, int] = {}

    def visit(vertex: str) -> bool:
        state = seen.get(vertex, 0)
        if state == 1:
            return True
        if state == 2:
            return False
        seen[vertex] = 1
        for nxt in outgoing.get(vertex, []):
            if visit(nxt):
                return True
        seen[vertex] = 2
        return False

    return any(visit(vertex) for vertex in outgoing if seen.get(vertex, 0) == 0)


def test_triangle_negative_control_and_acyclic_prefix() -> None:
    """The independent test oracle must distinguish a true counterexample."""
    edges = [("a", "b"), ("b", "c"), ("c", "a")]
    assert not _has_cycle(edges[:2])
    assert _has_cycle(edges)


def _three_works(store: WorkStore) -> tuple[str, list[str]]:
    token = uuid4().hex
    actor = f"actor:agent:dag3:{token}"
    works = [f"work:dag3:{token}:{i}" for i in range(3)]
    store.declare_actor(
        ActorRefInput(actor_ref=actor, actor_kind=ActorKind.AGENT),
        client_request_id=f"declare:{actor}",
    )
    snapshot = WorkSnapshotInput(
        objective="prove transitive graph safety",
        frontier="three-node finite cycle admission",
        established=[],
        unresolved=[],
        rejected=[],
        constraints=["no same-kind Work relation cycle"],
        next_actions=[],
        reference_refs=[],
    )
    for ref in works:
        store.create_work(
            WorkCreateInput(
                work_ref=ref, kind="investigation",
                actor_ref=actor, initial_snapshot=snapshot,
            ),
            client_request_id=f"create:{ref}",
        )
    return actor, works


def _committed_edges(works: list[str]) -> list[tuple[str, str]]:
    assert DSN is not None
    with psycopg.connect(DSN) as conn:
        return [
            (str(row[0]), str(row[1]))
            for row in conn.execute(
                "SELECT source_work_ref,target_work_ref FROM work_relations "
                "WHERE source_work_ref=ANY(%s)",
                (works,),
            ).fetchall()
        ]


@pytest.mark.skipif(not DSN, reason="isolated PostgreSQL DSN required")
@pytest.mark.usefixtures("host_test_db_ready")
@pytest.mark.parametrize("relation", [WorkRelationKind.PARENT_OF, WorkRelationKind.DEPENDS_ON])
def test_every_three_edge_permutation_preserves_native_dag(relation: WorkRelationKind) -> None:
    """Exhaust six source admission orders, checking true SQL state each time."""
    assert DSN is not None
    store = WorkStore(DSN)
    for order in permutations(TRIANGLE):
        actor, works = _three_works(store)
        committed = 0
        rejected = 0
        for source, target in order:
            try:
                store.add_relation(
                    WorkRelationInput(
                        source_work_ref=works[source], relation=relation,
                        target_work_ref=works[target], actor_ref=actor,
                    ),
                    client_request_id=f"dag3:{relation.value}:{works[source]}:{works[target]}",
                )
                committed += 1
            except ConflictError:
                rejected += 1
            assert not _has_cycle(_committed_edges(works))
        assert (committed, rejected) == (2, 1)
        assert len(_committed_edges(works)) == 2


@pytest.mark.skipif(not DSN, reason="isolated PostgreSQL DSN required")
@pytest.mark.usefixtures("host_test_db_ready")
@pytest.mark.parametrize("relation", [WorkRelationKind.PARENT_OF, WorkRelationKind.DEPENDS_ON])
def test_parallel_three_way_cycle_has_single_native_rejection(relation: WorkRelationKind) -> None:
    """Three contenders cannot commit a cycle through concurrent READ COMMITTED gaps."""
    assert DSN is not None
    store = WorkStore(DSN)
    actor, works = _three_works(store)
    barrier = Barrier(3)

    def add(pair: tuple[int, int]) -> str:
        source, target = pair
        barrier.wait(timeout=15)
        try:
            store.add_relation(
                WorkRelationInput(
                    source_work_ref=works[source], relation=relation,
                    target_work_ref=works[target], actor_ref=actor,
                ),
                client_request_id=f"parallel:{relation.value}:{works[source]}:{works[target]}",
            )
            return "committed"
        except ConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = sorted(executor.map(add, TRIANGLE))
    assert results == ["committed", "committed", "conflict"]
    persisted = _committed_edges(works)
    assert len(persisted) == 2
    assert not _has_cycle(persisted)
