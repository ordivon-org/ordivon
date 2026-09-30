from pathlib import Path

import pytest

from ordivon_host_v2.social_work import (
    ActorKind,
    ActorRefInput,
    WorkCreateInput,
    WorkRelationInput,
    WorkRelationKind,
    WorkSnapshotInput,
)

ROOT = Path(__file__).parents[1]


def _snapshot() -> WorkSnapshotInput:
    return WorkSnapshotInput(
        objective="prove Work Graph semantics",
        frontier="SWF10-SWF13",
        established=["stable identity"],
        unresolved=["database vertical"],
        constraints=["no authority leakage"],
        next_actions=["run destroyers"],
        reference_refs=["runtime:job:example"],
    )


def test_actor_ref_is_stable_reference_not_identity_claim() -> None:
    actor = ActorRefInput(actor_ref="actor:agent:a17", actor_kind=ActorKind.AGENT)
    assert actor.actor_ref == "actor:agent:a17"
    with pytest.raises(ValueError):
        ActorRefInput(actor_ref="anonymous", actor_kind=ActorKind.AGENT)


def test_work_snapshot_uses_complete_explicit_shape() -> None:
    payload = _snapshot().canonical_payload()
    assert payload["objective"] == "prove Work Graph semantics"
    assert payload["nextActions"] == ["run destroyers"]
    assert payload["referenceRefs"] == ["runtime:job:example"]
    assert "priority" not in payload
    assert "owner" not in payload
    assert "authority" not in payload


def test_work_create_does_not_embed_social_space() -> None:
    value = WorkCreateInput(
        work_ref="work:paper2:pilot-r6",
        kind="investigation",
        actor_ref="actor:agent:a17",
        initial_snapshot=_snapshot(),
    )
    dumped = value.model_dump(mode="json")
    assert "space" not in dumped
    assert "participants" not in dumped
    assert "messages" not in dumped


def test_work_relation_rejects_self_relation() -> None:
    relation = WorkRelationInput(
        source_work_ref="work:x",
        relation=WorkRelationKind.DEPENDS_ON,
        target_work_ref="work:x",
        actor_ref="actor:agent:a17",
    )
    with pytest.raises(ValueError):
        relation.validate_not_self_relation()


def test_work_relation_vocabulary_stays_small_and_non_authoritative() -> None:
    assert {item.value for item in WorkRelationKind} == {
        "parent_of",
        "depends_on",
        "blocks",
        "relates_to",
    }


def test_work_graph_migration_has_no_legacy_task_or_board_dependency() -> None:
    text = (ROOT / "migrations" / "versions" / "0006_social_work_fabric_work_graph.py").read_text()
    schema = text.split('_SCHEMA_V6_DELTA = r"""', 1)[1].split('"""', 1)[0]
    assert "REFERENCES tasks" not in schema
    assert "REFERENCES board_messages" not in schema
    assert "CREATE TABLE actor_refs" in schema
    assert "CREATE TABLE works" in schema
    assert "CREATE TABLE work_snapshots" in schema
    assert "CREATE TABLE work_relations" in schema


def test_work_store_contract_never_claims_priority_assignment_or_effect_authority() -> None:
    text = (ROOT / "src" / "ordivon_host_v2" / "work_store.py").read_text()
    forbidden_sql_fields = ("priority", "assignee", "winner", "vote_count", "effect_authority")
    sql_lines = [
        line.lower()
        for line in text.splitlines()
        if "select " in line.lower() or "insert " in line.lower() or "update " in line.lower()
    ]
    sql = "\n".join(sql_lines)
    for field in forbidden_sql_fields:
        assert field not in sql
