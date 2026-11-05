"""Natural Work query facet: unchanged public store, no second authority."""

import ast
from pathlib import Path

from ordivon_host_v2.work_queries import WorkReadQueries
from ordivon_host_v2.work_store import WorkStore


def test_work_reads_inherited_without_duplicate_write_paths() -> None:
    queries = {"get_work", "list_works", "_get_work_in_tx", "_state_at_revision"}
    assert issubclass(WorkStore, WorkReadQueries)
    assert all(name in WorkReadQueries.__dict__ for name in queries)
    assert all(name not in WorkStore.__dict__ for name in queries)


def test_work_queries_have_no_mutation_commands_or_receipts() -> None:
    path = Path(__file__).parents[1] / "src/ordivon_host_v2/work_queries.py"
    tree = ast.parse(path.read_text())
    source = path.read_text().lower()
    assert "claim_command_receipt" not in source
    assert "record_command_receipt" not in source
    literals = " ".join(
        str(node.value).lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    for forbidden in ("insert into ", "update works ", "delete from ", "on conflict "):
        assert forbidden not in literals
