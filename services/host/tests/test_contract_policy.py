from pathlib import Path


def test_historical_alembic_migrations_do_not_import_mutable_runtime_schema() -> None:
    root = Path(__file__).parents[1] / "migrations" / "versions"
    for migration in root.glob("*.py"):
        text = migration.read_text()
        assert "from ordivon_host_v2.schema import SCHEMA_SQL" not in text


def test_running_service_does_not_own_schema_ddl() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
    assert "SCHEMA_SQL" not in service
    assert not (root / "schema.py").exists()
    assert "alembic upgrade head" in service


def test_legacy_task_board_runtime_modules_are_physically_retired() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    for name in ("board.py", "attention.py", "checkpoint_contract.py", "models.py"):
        assert not (root / name).exists()
    service = (root / "service.py").read_text()
    for legacy in (
        "def adopt(",
        "def checkpoint(",
        "def resume(",
        "def observe(",
        "list_task_summaries_page",
        "board_messages",
        "task_events",
        "FROM tasks",
        "FROM checkpoints",
    ):
        assert legacy not in service


def test_unclaimed_work_standing_ontology_is_retired_from_active_source() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    text = "\n".join(
        source.read_text() for source in root.glob("*.py") if source.name != "legacy_cutover.py"
    )
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


def test_release_python_is_owned_by_uv_and_project_pin() -> None:
    root = Path(__file__).parents[1]
    install = (root / "packaging" / "install_release.sh").read_text()
    assert "/usr/bin/python3.14" not in install
    assert ".python-version" in install
    assert "UV_PYTHON_INSTALL_DIR" in install
    assert "python install" in install
    assert "python find" in install
    assert "--managed-python" in install


def test_python_pin_matches_project_requirement() -> None:
    import tomllib

    root = Path(__file__).parents[1]
    pinned = (root / ".python-version").read_text().strip()
    project = tomllib.loads((root / "pyproject.toml").read_text())
    assert project["project"]["requires-python"] == f"=={pinned}"


def test_host_status_does_not_duplicate_foreign_or_mcp_authorities() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    service = (root / "service.py").read_text()
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


def test_psycopg_owns_jsonb_adaptation_in_active_stores() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    text = "\n".join(
        (root / name).read_text()
        for name in ("work_store.py", "social_store.py", "social_attention.py")
    )
    assert "Jsonb(" in text
    assert "%s::jsonb" not in text


def test_one_shot_legacy_reader_is_not_registered_as_active_mcp_surface() -> None:
    root = Path(__file__).parents[1] / "src" / "ordivon_host_v2"
    mcp = (root / "mcp_server.py").read_text() + (root / "social_work_mcp.py").read_text()
    assert "legacy_cutover" not in mcp
    assert 'name="task.' not in mcp
    assert 'name="board.' not in mcp
