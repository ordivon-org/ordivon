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

def test_active_source_has_no_legacy_route_anchor_runtime_compatibility() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    active = "\n".join((root / name).read_text() for name in ("board.py", "attention.py"))
    assert "is_legacy_task_route_anchor" not in active
    assert "task-route-anchor-v1" not in active


def test_compact_task_inventory_is_the_only_list_implementation() -> None:
    text = (Path(__file__).parents[1] / "src" / "ordivon_host_v2" / "service.py").read_text()
    assert "def list_task_summaries_page(" in text
    assert "def list_tasks(" not in text
    assert "def list_tasks_page(" not in text

def test_release_python_is_owned_by_uv_and_project_pin() -> None:
    root = Path(__file__).parents[1]
    install = (root / "packaging" / "install_release.sh").read_text()
    assert "/usr/bin/python3.14" not in install
    assert '.python-version' in install
    assert 'UV_PYTHON_INSTALL_DIR' in install
    assert 'python install' in install
    assert 'python find' in install
    assert '--managed-python' in install


def test_python_pin_matches_project_requirement() -> None:
    import tomllib

    root = Path(__file__).parents[1]
    pinned = (root / ".python-version").read_text().strip()
    project = tomllib.loads((root / "pyproject.toml").read_text())
    assert project["project"]["requires-python"] == f"=={pinned}"

def test_host_status_does_not_duplicate_foreign_or_mcp_authorities() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
    contracts = (root / "contracts.py").read_text()
    for retired in (
        '"interface":',
        '"surfaceVersion":',
        '"toolNames":',
        '"leases": 0',
        '"deployment": {',
        '"continuity": {',
        '"recentActivity":',
        '"terminalTasks":',
    ):
        assert retired not in service
    assert "HostInterfaceWire" not in contracts

def test_psycopg_owns_jsonb_adaptation() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
    assert "from psycopg.types.json import Jsonb" in service
    assert "Jsonb(" in service
    assert "json.dumps" not in service
    assert "json.loads" not in service
    assert "%s::jsonb" not in service


def test_dead_host_status_model_is_absent() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    models = (root / "models.py").read_text()
    exports = (root / "__init__.py").read_text()
    assert "class HostStatus(" not in models
    assert "HostStatus" not in exports
