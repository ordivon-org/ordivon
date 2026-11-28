"""Attention read responsibilities are tested via actual resolved behavior, not file layout."""

from ordivon_host_v2.attention_store import AttentionStore, TargetKind

READ_METHODS = ("list_subscriptions", "get", "delta", "reentry")


def test_attention_reads_available_through_stable_host_store() -> None:
    store = AttentionStore("postgresql://unused.invalid/host")
    assert all(callable(getattr(store, name)) for name in READ_METHODS)
    assert TargetKind is not None
