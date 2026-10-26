"""The read and adopt consumers must select the same PG role binding authority."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from tests.test_conversation_adopt import config, exact_match, proof, session, spec_path

import agent_automation_browserless as browserless


def test_conversation_affinity_reads_pg_without_legacy_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    observed: list[str] = []

    class PG:
        def get_binding(self, campaign_ref: str, agent_id: str):
            observed.append(f"pg:{agent_id}")
            return {
                "sessionId": session()["sessionId"],
                "providerResource": "https://chatgpt.com/c/current",
                "bindingDigest": "sha256:" + "a" * 64,
            }

    monkeypatch.setattr(svc, "_pg_conversation_binding_owner", lambda: PG())
    monkeypatch.setattr(svc, "_materialization", lambda *_: None)
    monkeypatch.setattr(
        browserless,
        "read_conversation_binding",
        Mock(side_effect=AssertionError("legacy binding read forbidden")),
    )
    monkeypatch.setattr(browserless, "resolve_session", lambda _: session())
    result = svc.conversation_affinity(spec_path(tmp_path), "sha256:" + "a" * 64, "A01")
    assert observed == ["pg:A01"]
    assert result["providerResource"] == "https://chatgpt.com/c/current"
    assert result["affinityKind"] == "DURABLE_CFT_SESSION"


def test_conversation_adoption_writes_pg_without_legacy_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    observed: list[str] = []

    class PG:
        def adopt_binding(self, **data):
            observed.append("pg-adopt")
            assert data["provider_resource"] == exact_match()["providerResource"]
            return {
                "providerResource": data["provider_resource"],
                "sessionId": data["session_id"],
                "bindingDigest": "sha256:" + "b" * 64,
            }

    monkeypatch.setattr(svc, "_pg_conversation_binding_owner", lambda: PG())
    monkeypatch.setattr(
        browserless,
        "SQLiteConversationBindingStore",
        Mock(side_effect=AssertionError("legacy binding write forbidden")),
    )
    monkeypatch.setattr(browserless, "resolve_session", lambda _: session())
    monkeypatch.setattr(browserless, "discover_exact_marker", lambda *_: exact_match())
    receipt = svc.adopt_conversation(
        spec_path(tmp_path),
        "sha256:" + "a" * 64,
        "A01",
        adoption_request_id="adoption:123",
        marker_proof=proof(),
    )
    assert observed == ["pg-adopt"]
    assert receipt["standing"] == "ADOPTED"
    assert receipt["providerEffectAttempted"] is False
    assert receipt["sendAttempted"] is False


@pytest.mark.parametrize("consumer", ["read", "adopt"])
def test_unsealed_pg_role_cannot_revert_to_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, consumer: str
) -> None:
    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )

    def reject_pg():
        raise browserless.ConversationBindingConflict("source not sealed")

    monkeypatch.setattr(svc, "_pg_conversation_binding_owner", reject_pg)
    monkeypatch.setattr(svc, "_materialization", lambda *_: None)
    monkeypatch.setattr(
        browserless,
        "SQLiteConversationBindingStore",
        Mock(side_effect=AssertionError("unsafe fallback")),
    )
    monkeypatch.setattr(
        browserless,
        "read_conversation_binding",
        Mock(side_effect=AssertionError("unsafe fallback")),
    )
    monkeypatch.setattr(browserless, "resolve_session", lambda _: session())
    monkeypatch.setattr(browserless, "discover_exact_marker", lambda *_: exact_match())
    with pytest.raises(browserless.BrowserlessAutomationConflict, match="not sealed"):
        if consumer == "read":
            svc.conversation_affinity(spec_path(tmp_path), "sha256:" + "a" * 64, "A01")
        else:
            svc.adopt_conversation(
                spec_path(tmp_path),
                "sha256:" + "a" * 64,
                "A01",
                adoption_request_id="adoption:123",
                marker_proof=proof(),
            )


@pytest.mark.parametrize("fresh_bootstrap", [False, True])
def test_pg_binding_real_consumer_passes_exact_legacy_source_and_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fresh_bootstrap: bool
) -> None:
    """PG-enabled consumers must satisfy the real PG constructor contract.

    Using _pg_conversation_binding_owner instead of stubbing the entire method
    catches a cutover bug even when read/write behavior mocks remain green.
    """
    import postgres_conversation_binding as pg_binding

    svc = browserless.BrowserlessAutomationService(
        browserless.BrowserlessAutomationConfig.from_dict(config(tmp_path))
    )
    monkeypatch.setenv("ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN", "postgresql://test/no-effect")
    if fresh_bootstrap:
        monkeypatch.setenv("ORDIVON_CONVERSATION_BINDING_FRESH_BOOTSTRAP", "1")
    else:
        monkeypatch.delenv("ORDIVON_CONVERSATION_BINDING_FRESH_BOOTSTRAP", raising=False)
    observed = []

    class PG:
        def __init__(self, dsn: str, *, legacy_source: Path, fresh_bootstrap: bool = False):
            observed.append(("open", dsn, legacy_source, fresh_bootstrap))

        def assert_legacy_sealed(self, source: Path, *, fresh_bootstrap: bool = False):
            observed.append(("sealed", source, fresh_bootstrap))

    monkeypatch.setattr(pg_binding, "PostgresConversationBindingStore", PG)
    owner = svc._pg_conversation_binding_owner()
    assert isinstance(owner, PG)
    assert observed == [
        ("open", "postgresql://test/no-effect", svc.config.ledger, fresh_bootstrap),
        ("sealed", svc.config.ledger, fresh_bootstrap),
    ]
