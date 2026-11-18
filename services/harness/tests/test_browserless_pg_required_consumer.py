"""Real consumer admission for the existing Browserless PG binding/wake/effect seams."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts import agent_automation_browserless as browserless
from scripts import playwright_browserless_turn_once as sender


@pytest.mark.parametrize(
    "variable",
    [
        "ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN",
        "ORDIVON_WAKE_TURN_POSTGRES_DSN",
        "ORDIVON_TURN_EFFECT_POSTGRES_DSN",
    ],
)
def test_required_pg_identity_effect_owner_never_falls_back(
    monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setenv("ORDIVON_BROWSERLESS_PG_IDENTITIES_EFFECTS_REQUIRED", "1")
    monkeypatch.delenv(variable, raising=False)
    with pytest.raises(browserless.BrowserlessAutomationConflict, match="SQLite fallback prohibited"):
        browserless.BrowserlessAutomationService._postgres_seam_dsn(variable)


@pytest.mark.parametrize(
    "variable",
    [
        "ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN",
        "ORDIVON_WAKE_TURN_POSTGRES_DSN",
        "ORDIVON_TURN_EFFECT_POSTGRES_DSN",
    ],
)
def test_selected_pg_owners_reuse_existing_dsn(
    monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setenv("ORDIVON_BROWSERLESS_PG_IDENTITIES_EFFECTS_REQUIRED", "1")
    monkeypatch.setenv(variable, "host=disposable-pg")
    assert (
        browserless.BrowserlessAutomationService._postgres_seam_dsn(variable)
        == "host=disposable-pg"
    )


def test_fresh_role_binding_without_dsn_fails_before_sqlite(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ORDIVON_CONVERSATION_BINDING_POSTGRES_DSN", raising=False)
    monkeypatch.delenv("ORDIVON_BROWSERLESS_PG_IDENTITIES_EFFECTS_REQUIRED", raising=False)
    monkeypatch.setenv("ORDIVON_CONVERSATION_BINDING_FRESH_BOOTSTRAP", "1")
    with pytest.raises(browserless.BrowserlessAutomationConflict, match="SQLite fallback prohibited"):
        browserless.BrowserlessAutomationService._pg_conversation_binding_owner(
            object.__new__(browserless.BrowserlessAutomationService)
        )


def test_sender_missing_required_pg_dsn_rejects_before_token_or_file_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ORDIVON_BROWSERLESS_PG_IDENTITIES_EFFECTS_REQUIRED", "1")
    monkeypatch.delenv("ORDIVON_TURN_EFFECT_POSTGRES_DSN", raising=False)
    monkeypatch.setattr(sender, "connector_spec", Mock(side_effect=AssertionError("token must not be read")))
    monkeypatch.setattr(sender, "sync_playwright", Mock(side_effect=AssertionError("browser must not launch")))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "playwright_browserless_turn_once.py",
            "--target-resource",
            "https://chatgpt.com/c/11111111-1111-4111-8111-111111111111",
            "--prompt-file",
            str(tmp_path / "missing-prompt"),
            "--turn-request-id",
            "019a9af0-7b00-7000-8000-000000000011",
            "--ledger",
            str(tmp_path / "would-create-legacy.sqlite"),
            "--receipt-out",
            str(tmp_path / "would-create-receipt.json"),
        ],
    )
    with pytest.raises(SystemExit, match="SQLite fallback prohibited"):
        sender.main()
    assert list(tmp_path.iterdir()) == []
