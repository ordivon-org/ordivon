"""Consumer proof: PG cutover must not silently fall back to legacy wake writes."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("psycopg", reason="PG provider is owned by the Temporal worker")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_automation_browserless as browserless  # noqa: E402
import postgres_wake_turn_map  # noqa: E402

CAMPAIGN_REF = "sha256:" + "a" * 64
TURN_ID = "019a9af0-7b00-7000-8000-000000000011"


def _service(tmp_path: Path) -> browserless.BrowserlessAutomationService:
    service = object.__new__(browserless.BrowserlessAutomationService)
    service.config = SimpleNamespace(turn_ledger=tmp_path / "old-turn-ledger.sqlite")
    service.conversation_affinity = lambda *_: {"placementAction": "CONTINUE"}
    service.launch_continue = lambda *_, **__: {"standing": "admitted"}
    return service


def test_postgres_selected_only_after_source_retirement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    monkeypatch.setenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", "host=disposable-pg")
    calls: list[str] = []

    class ProofOwner:
        def __init__(self, dsn: str) -> None:
            assert dsn == "host=disposable-pg"
            calls.append("PG")

        def assert_legacy_sealed(self, source: Path, *, fresh_bootstrap: bool = False) -> None:
            assert source == service.config.turn_ledger
            calls.append("sealed")

        def allocate(self, **kwargs: str):
            assert kwargs["wake_intent_id"] == "wake:task-1"
            calls.append("allocate")
            return {"turnRequestId": TURN_ID}

    monkeypatch.setattr(postgres_wake_turn_map, "PostgresWakeTurnMap", ProofOwner)
    monkeypatch.setattr(browserless, "SQLiteWakeTurnMap", Mock(side_effect=AssertionError("SQLite fallback")))
    result = service.launch_wake(
        tmp_path / "spec.json", CAMPAIGN_REF, "A01", wake_intent_id="wake:task-1", prompt="hello"
    )
    assert calls == ["PG", "sealed", "allocate"]
    assert result["turnRequestId"] == TURN_ID
    assert result["promptSent"] is True


def test_unsealed_legacy_state_fails_closed_before_any_pg_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    monkeypatch.setenv("ORDIVON_WAKE_TURN_POSTGRES_DSN", "host=disposable-pg")

    class Unsealed:
        def __init__(self, dsn: str) -> None:
            assert dsn == "host=disposable-pg"

        def assert_legacy_sealed(self, source: Path, *, fresh_bootstrap: bool = False) -> None:
            raise postgres_wake_turn_map.WakeTurnConflict("legacy source not retired")

        def allocate(self, **kwargs: str):
            raise AssertionError("must not allocate until source sealing")

    monkeypatch.setattr(postgres_wake_turn_map, "PostgresWakeTurnMap", Unsealed)
    with pytest.raises(browserless.BrowserlessAutomationConflict, match="not retired"):
        service.launch_wake(
            tmp_path / "spec.json", CAMPAIGN_REF, "A01", wake_intent_id="wake:task-1", prompt="hello"
        )
