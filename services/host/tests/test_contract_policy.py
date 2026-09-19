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


def test_checkpoint_contract_has_no_custom_partial_patch_language() -> None:
    text = (
        Path(__file__).parents[1] / "src" / "ordivon_host_v2" / "checkpoint_contract.py"
    ).read_text()
    assert "merge_checkpoint_update" not in text
    assert "checkpoint_patch_schema" not in text
    assert "WorkingCheckpointUpdate" not in text


def test_unclaimed_work_standing_ontology_is_retired_from_active_source() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    text = "\n".join(source.read_text() for source in root.glob("*.py"))
    for retired in (
        "workStanding",
        "WorkingCheckpointStanding",
        "WorkingCheckpointWake",
        "executionAdmission",
        "valueNow",
        "blockerKinds",
        "DIRTY_HANDOFF",
    ):
        assert retired not in text


def test_checkpoint_schema_is_one_complete_v1_contract() -> None:
    from ordivon_host_v2.checkpoint_contract import full_checkpoint_schema

    schema = full_checkpoint_schema()
    assert "oneOf" not in schema
    assert schema["properties"]["schemaVersion"]["const"] == 1
    assert "workStanding" not in schema["properties"]
    assert schema["additionalProperties"] is False


def test_board_search_binds_results_to_reported_snapshot_high_water() -> None:
    text = (Path(__file__).parents[1] / "src" / "ordivon_host_v2" / "board.py").read_text()
    search = text.split("    def search(self, *, query: str, limit: int = 20)", 1)[1]
    assert "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY" in search
    assert '"WHERE sequence<=%s AND ("' in search
