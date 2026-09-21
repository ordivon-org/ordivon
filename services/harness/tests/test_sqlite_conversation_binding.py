from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sqlite_conversation_binding import (  # noqa: E402
    ConversationBindingConflict,
    SQLiteConversationBindingStore,
)


EVIDENCE = "sha256:" + "2" * 64


def store(tmp_path: Path) -> SQLiteConversationBindingStore:
    return SQLiteConversationBindingStore(tmp_path / "materialization-ledger.sqlite")


def adopt(
    s: SQLiteConversationBindingStore,
    *,
    campaign_ref: str = "sha256:" + "a" * 64,
    agent_id: str = "A01",
    provider_resource: str = "https://chatgpt.com/c/conversation-1",
    evidence_digest: str = EVIDENCE,
    request_id: str = "adoption:1",
):
    return s.adopt_binding(
        campaign_ref=campaign_ref,
        agent_id=agent_id,
        provider_resource=provider_resource,
        evidence_digest=evidence_digest,
        request_id=request_id,
    )


def test_exact_replay_returns_existing_binding(tmp_path: Path) -> None:
    s = store(tmp_path)
    first = adopt(s)
    second = adopt(s)
    assert second == first
    assert first["providerResource"] == "https://chatgpt.com/c/conversation-1"
    assert first["bindingDigest"].startswith("sha256:")
    assert first["bindingStanding"] == "ADOPTED"


def test_chatgpt_resource_is_canonicalized_before_binding(tmp_path: Path) -> None:
    s = store(tmp_path)
    value = adopt(
        s, provider_resource="https://chatgpt.com/c/conversation-1?utm=ignored#fragment"
    )
    assert value["providerResource"] == "https://chatgpt.com/c/conversation-1"


def test_same_request_changed_provider_resource_conflicts(tmp_path: Path) -> None:
    s = store(tmp_path)
    adopt(s)
    with pytest.raises(ConversationBindingConflict, match="request identity"):
        adopt(s, provider_resource="https://chatgpt.com/c/conversation-2")


def test_same_role_different_adoption_request_conflicts(tmp_path: Path) -> None:
    s = store(tmp_path)
    adopt(s)
    with pytest.raises(ConversationBindingConflict, match="role already has"):
        adopt(
            s,
            provider_resource="https://chatgpt.com/c/conversation-2",
            request_id="adoption:2",
        )


def test_same_request_id_cannot_bind_different_role(tmp_path: Path) -> None:
    s = store(tmp_path)
    adopt(s)
    with pytest.raises(ConversationBindingConflict, match="request identity"):
        adopt(s, agent_id="A02")


def test_get_and_resolve_are_read_only(tmp_path: Path) -> None:
    s = store(tmp_path)
    expected = adopt(s)
    before = s.path.read_bytes()
    assert s.get_binding(expected["campaignRef"], "A01") == expected
    assert s.resolve_binding(expected["campaignRef"], "A01") == expected
    assert s.get_binding(expected["campaignRef"], "missing") is None
    assert s.path.read_bytes() == before


def test_binding_table_lives_beside_existing_materialization_requests(tmp_path: Path) -> None:
    ledger = tmp_path / "materialization-ledger.sqlite"
    db = sqlite3.connect(ledger)
    db.execute("CREATE TABLE requests (request_id TEXT PRIMARY KEY)")
    db.execute("INSERT INTO requests VALUES ('effect-1')")
    db.commit()
    db.close()

    s = SQLiteConversationBindingStore(ledger)
    adopt(s)

    db = sqlite3.connect(ledger)
    try:
        assert db.execute("SELECT request_id FROM requests").fetchone()[0] == "effect-1"
        count = db.execute("SELECT COUNT(*) FROM conversation_bindings").fetchone()[0]
        assert count == 1
    finally:
        db.close()


@pytest.mark.parametrize(
    "field,value",
    [
        ("campaign_ref", ""),
        ("agent_id", " A01"),
        ("request_id", ""),
        ("evidence_digest", "sha256:abc"),
        ("provider_resource", "chatgpt-conversation:private"),
    ],
)
def test_invalid_binding_input_fails_closed(tmp_path: Path, field: str, value: str) -> None:
    s = store(tmp_path)
    kwargs = {field: value}
    with pytest.raises(ValueError):
        adopt(s, **kwargs)


def test_module_has_no_provider_effect_dependencies() -> None:
    text = (ROOT / "scripts/sqlite_conversation_binding.py").read_text()
    for forbidden in ("playwright", "browserless", "send.click", "composer.fill", "TemporalClient"):
        assert forbidden not in text
