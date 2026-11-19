"""Natural Work query facet: unchanged public store, no second authority."""

import ast
from pathlib import Path

from ordivon_host_v2.work_queries import WorkReadQueries
from ordivon_host_v2.work_store import WorkStore


def test_work_reads_and_mutations_share_one_explicit_same_transaction_readback() -> None:
    """WorkStore keeps its public read API, but command readback is no longer an MRO hook."""
    import inspect

    from ordivon_host_v2.work_queries import read_work_in_tx

    assert callable(WorkStore.get_work)
    assert callable(WorkStore.list_works)
    assert callable(read_work_in_tx)
    assert "read_work_in_tx(conn, work_ref, revision)" in inspect.getsource(
        WorkReadQueries.get_work
    )
    assert "read_work_in_tx(conn, work_ref, next_revision)" in inspect.getsource(
        WorkStore.commit_snapshot
    )
    assert not hasattr(WorkStore, "_get_work_in_tx")


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


def test_work_read_rejects_revision_outside_postgres_bigint_before_connection() -> None:
    """The actual store rejects a nonrepresentable revision, not the DB driver."""
    import pytest

    with pytest.raises(ValueError, match="positive PostgreSQL BIGINT"):
        WorkStore("postgresql://unreachable").get_work("work:outside", (1 << 63))


def test_native_mcp_work_revision_types_reject_unrepresentable_values() -> None:
    """MCP read and CAS ingress have distinct representable revision domains."""
    import pytest
    from pydantic import TypeAdapter, ValidationError

    from ordivon_host_v2.mcp_work_tools import AdvancableWorkRevision, PositiveWorkRevision

    read = TypeAdapter(PositiveWorkRevision)
    write = TypeAdapter(AdvancableWorkRevision)
    assert read.validate_python((1 << 63) - 1) == (1 << 63) - 1
    assert write.validate_python((1 << 63) - 2) == (1 << 63) - 2
    with pytest.raises(ValidationError):
        read.validate_python(1 << 63)
    with pytest.raises(ValidationError):
        write.validate_python((1 << 63) - 1)
