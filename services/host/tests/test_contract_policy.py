from pathlib import Path


def test_historical_alembic_migrations_do_not_import_mutable_runtime_schema() -> None:
    root = Path(__file__).parents[1] / "migrations" / "versions"
    for migration in root.glob("*.py"):
        text = migration.read_text()
        assert "from ordivon_host_v2.schema import SCHEMA_SQL" not in text


def test_board_search_preserves_non_authoritative_negative_result_contract() -> None:
    text = (Path(__file__).parents[1] / "src" / "ordivon_host_v2" / "board.py").read_text()
    assert '"negativeResultAuthoritative": False' in text


def test_running_service_does_not_own_schema_ddl() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
    assert "SCHEMA_SQL" not in service
    assert not (root / "schema.py").exists()
    assert "alembic upgrade head" in service


def _v2_checkpoint(task_id: str) -> dict[str, object]:
    return {
        "schemaVersion": 2,
        "kind": "ordivon.host-working-checkpoint",
        "truthRole": "semantic-working-claim",
        "taskId": task_id,
        "objective": "preserve exact continuity claim",
        "frontier": "before",
        "established": ["fact"],
        "unresolved": ["next"],
        "rejected": [],
        "constraints": ["claim-only"],
        "nextActions": ["continue"],
        "runtime": None,
        "workStanding": {
            "schemaVersion": 1,
            "truthRole": "checkpoint-authored-work-standing",
            "attention": "WAIT",
            "executionAdmission": "REENTRY_REQUIRED",
            "valueNow": "POSITIVE_VALUE_NOW",
            "progress": "OPEN_FRONTIER",
            "lineage": "SELF_STANDING",
            "relatedTaskIds": ["task:related"],
            "blockerKinds": ["OWNER"],
            "wake": {"mode": "ANY", "conditions": ["owner changes"]},
            "carrier": "RETAIN",
        },
    }


def test_work_standing_has_no_runtime_consumer_outside_checkpoint_contract() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    consumers = []
    for source in root.glob("*.py"):
        if source.name == "checkpoint_contract.py":
            continue
        text = source.read_text()
        if "workStanding" in text:
            consumers.append(source.name)
    assert consumers == []


def test_work_standing_round_trips_as_claim_only_checkpoint_data() -> None:
    from ordivon_host_v2.checkpoint_contract import (
        merge_checkpoint_update,
        validate_full_checkpoint,
    )

    task_id = "task:contract-policy:claim-only"
    original = _v2_checkpoint(task_id)
    validated = validate_full_checkpoint(task_id, original)
    assert validated["workStanding"] == original["workStanding"]

    patched = merge_checkpoint_update(
        task_id=task_id,
        base=validated,
        update={"frontier": "after"},
        terminal=False,
    )
    assert patched["frontier"] == "after"
    assert patched["workStanding"] == validated["workStanding"]


def test_work_standing_truth_role_stays_caller_authored() -> None:
    from ordivon_host_v2.checkpoint_contract import full_checkpoint_schema

    schema_text = str(full_checkpoint_schema())
    assert "checkpoint-authored-work-standing" in schema_text
    assert "caller-authored workStanding" in schema_text


def test_board_search_binds_results_to_reported_snapshot_high_water() -> None:
    text = (Path(__file__).parents[1] / "src" / "ordivon_host_v2" / "board.py").read_text()
    search = text.split("    def search(self, *, query: str, limit: int = 20)", 1)[1]
    assert "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY" in search
    assert '"WHERE sequence<=%s AND ("' in search
