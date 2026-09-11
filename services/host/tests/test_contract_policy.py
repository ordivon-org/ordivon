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
