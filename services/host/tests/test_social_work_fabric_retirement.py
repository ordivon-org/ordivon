from pathlib import Path

ROOT = Path(__file__).parents[1]
SRC = ROOT / "src" / "ordivon_host_v2"
MIGRATION = ROOT / "migrations" / "versions" / "0009_retire_legacy_task_board.py"


def test_retirement_removes_legacy_active_modules_and_exports() -> None:
    for name in ("board.py", "attention.py", "checkpoint_contract.py", "models.py"):
        assert not (SRC / name).exists()
    exports = (SRC / "__init__.py").read_text()
    for name in ("BoardStore", "TaskView", "TaskState", "CheckpointInput", "TaskNotFound"):
        assert name not in exports


def test_retirement_migration_drops_legacy_tables_and_is_irreversible() -> None:
    text = MIGRATION.read_text()
    assert 'revision = "0009"' in text
    assert 'down_revision = "0008"' in text
    for table in ("board_messages", "task_events", "checkpoints", "tasks"):
        assert f"DROP TABLE {table}" in text
    assert "schema_version=9" in text
    assert "destructive legacy-retirement boundary" in text


def test_active_service_has_no_legacy_storage_references() -> None:
    text = (SRC / "service.py").read_text()
    for fragment in ("board_messages", "task_events", "FROM tasks", "FROM checkpoints"):
        assert fragment not in text
    assert "REQUIRED_SCHEMA_VERSION = 9" in text


def test_historical_cutover_reader_is_not_active_host_authority() -> None:
    mcp = (SRC / "mcp_server.py").read_text() + (SRC / "social_work_mcp.py").read_text()
    assert "legacy_cutover" not in mcp
    assert "register_social_work_tools" in mcp
