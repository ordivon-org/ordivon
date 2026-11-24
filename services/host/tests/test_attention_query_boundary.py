"""Attention read responsibilities are tested via actual resolved behavior, not file layout."""

import ast
import inspect
import textwrap

from ordivon_host_v2.attention_delta_queries import AttentionDeltaQueries
from ordivon_host_v2.attention_reentry_queries import AttentionReentryQueries
from ordivon_host_v2.attention_store import AttentionStore, TargetKind
from ordivon_host_v2.attention_subscription_queries import AttentionSubscriptionQueries

READ_METHODS = ("list_subscriptions", "get", "delta", "reentry")
READ_CAPABILITIES = (
    (AttentionSubscriptionQueries, ("list_subscriptions",)),
    (AttentionDeltaQueries, ("get", "delta", "_delta_in_tx")),
    (AttentionReentryQueries, ("reentry",)),
)


def test_attention_reads_available_through_stable_host_store() -> None:
    store = AttentionStore("postgresql://unused.invalid/host")
    assert all(callable(getattr(store, name)) for name in READ_METHODS)
    assert TargetKind is not None


def test_attention_read_methods_do_not_issue_direct_mutation_sql() -> None:
    # Inspect actual explicit query consumers. PG integration tests separately
    # qualify transaction read-only and cursor behavior.
    source = "\n".join(
        textwrap.dedent(inspect.getsource(getattr(capability, name)))
        for capability, methods in READ_CAPABILITIES for name in methods
    )
    tree = ast.parse(textwrap.dedent(source))
    sql_literals = " ".join(
        str(n.value).lower()
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    )
    for forbidden in ("insert into ", "update subscriptions ", "delete from ", "on conflict "):
        assert forbidden not in sql_literals
    assert "claim_command_receipt" not in source
    assert "record_command_receipt" not in source
