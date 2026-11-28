"""Natural Work query facet: unchanged public store, no second authority."""

from ordivon_host_v2.work_queries import WorkReadQueries
from ordivon_host_v2.work_store import WorkStore


def test_work_query_facet_accepts_explicit_connection_factory() -> None:
    def forbidden():
        raise AssertionError("validation must precede checkout")

    import pytest

    with pytest.raises(ValueError, match="positive PostgreSQL BIGINT"):
        WorkReadQueries(forbidden).get_work("work:test", True)


def test_work_read_rejects_revision_outside_json_safe_integer_before_connection() -> None:
    """The actual store rejects a nonrepresentable revision, not the DB driver."""
    import pytest

    with pytest.raises(ValueError, match="positive PostgreSQL BIGINT"):
        WorkStore("postgresql://unreachable").get_work("work:outside", (1 << 53))


def test_native_mcp_work_revision_types_reject_unrepresentable_values() -> None:
    """MCP read and CAS ingress have distinct representable revision domains."""
    import pytest
    from pydantic import TypeAdapter, ValidationError

    from ordivon_host_v2.mcp_work_tools import AdvancableWorkRevision, PositiveWorkRevision

    read = TypeAdapter(PositiveWorkRevision)
    write = TypeAdapter(AdvancableWorkRevision)
    assert read.validate_python((1 << 53) - 1) == (1 << 53) - 1
    assert write.validate_python((1 << 53) - 2) == (1 << 53) - 2
    with pytest.raises(ValidationError):
        read.validate_python(1 << 53)
    with pytest.raises(ValidationError):
        write.validate_python((1 << 53) - 1)
