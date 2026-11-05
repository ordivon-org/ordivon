"""Single natural Attention write owner and a read projection facet."""

import ast
from pathlib import Path

from ordivon_host_v2.attention_projections import AttentionReadProjections
from ordivon_host_v2.social_attention import AttentionStore, TargetKind


def test_attention_reads_inherited_by_stable_host_store() -> None:
    query_names = {"list_subscriptions", "get", "delta", "reentry"}
    assert issubclass(AttentionStore, AttentionReadProjections)
    assert all(name in AttentionReadProjections.__dict__ for name in query_names)
    assert all(name not in AttentionStore.__dict__ for name in query_names)
    assert TargetKind is not None


def test_attention_query_facet_has_no_mutation_or_command_receipts() -> None:
    p = Path(__file__).parents[1] / "src/ordivon_host_v2/attention_projections.py"
    source = p.read_text()
    tree = ast.parse(source)
    assert "claim_command_receipt" not in source
    assert "record_command_receipt" not in source
    sql_literals = " ".join(
        str(n.value).lower()
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )
    for forbidden in ("insert into ", "update subscriptions ", "delete from ", "on conflict "):
        assert forbidden not in sql_literals
