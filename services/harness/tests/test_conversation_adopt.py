from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    BrowserlessAutomationConflict,
    BrowserlessAutomationHold,
    BrowserlessAutomationService,
)


def config(root: Path) -> dict:
    token = root / "browserless.token"
    token.write_text("secret-token-value-long-enough-for-test")
    return {
        "schemaVersion": 1,
        "stateRoot": str(root / "state"),
        "playwrightPython": "/venv/bin/python",
        "browserlessSubmitScript": str(ROOT / "scripts/playwright_browserless_chatgpt_submit.py"),
        "browserlessReconcileScript": str(ROOT / "scripts/playwright_browserless_binding_reconcile.py"),
        "browserlessTurnScript": str(ROOT / "scripts/playwright_browserless_turn_once.py"),
        "browserlessPreflightScript": str(ROOT / "scripts/playwright_browserless_provider_preflight.py"),
        "temporalPython": "/temporal/bin/python",
        "temporalLaunchScript": str(ROOT / "scripts/temporal_agent_automation_launch.py"),
        "browserSubstrate": {
            "kind": "browserless",
            "endpoints": [{
                "id": "carrier-a",
                "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                "httpEndpoint": "http://127.0.0.1:3011",
                "tokenFile": str(token),
            }],
        },
    }


def spec_path(root: Path) -> Path:
    path = root / "spec.json"
    path.write_text(json.dumps({
        "campaignId": "campaign:adopt",
        "sharedPrompt": "Do one task.",
        "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
    }))
    return path


def proof() -> dict[str, str]:
    return {
        "sessionId": "cft-session-01",
        "cdpEndpoint": "http://127.0.0.1:9222",
        "markerDigest": "sha256:" + "3" * 64,
    }


def exact_match() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.chatgpt-conversation-discovery",
        "standing": "EXACT_MATCH",
        "matchCount": 1,
        "providerResource": "https://chatgpt.com/c/existing-1",
        "evidenceDigest": "sha256:" + "4" * 64,
        "providerEffectAttempted": False,
        "sendAttempted": False,
        "sideEffectsAttempted": False,
    }


def test_exact_match_adopts_binding_without_materialize_or_continue(tmp_path: Path) -> None:
    service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    with (
        mock.patch("agent_automation_browserless.discover_exact_marker", return_value=exact_match()) as discover,
        mock.patch.object(service, "launch_campaign") as materialize,
        mock.patch.object(service, "launch_continue") as cont,
    ):
        value = service.adopt_conversation(
            spec_path(tmp_path),
            "sha256:" + "a" * 64,
            "A01",
            adoption_request_id="adoption:1",
            marker_proof=proof(),
        )
    discover.assert_called_once()
    materialize.assert_not_called()
    cont.assert_not_called()
    assert value["standing"] == "ADOPTED"
    assert value["providerResource"] == "https://chatgpt.com/c/existing-1"
    assert value["providerEffectAttempted"] is False
    assert value["sendAttempted"] is False
    assert "cdpEndpoint" not in json.dumps(value)


def test_zero_match_holds_without_binding(tmp_path: Path) -> None:
    service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    row = {**exact_match(), "standing": "NO_MATCH", "matchCount": 0}
    row.pop("providerResource")
    with mock.patch("agent_automation_browserless.discover_exact_marker", return_value=row):
        with pytest.raises(BrowserlessAutomationHold, match="no exact provider conversation"):
            service.adopt_conversation(
                spec_path(tmp_path), "sha256:" + "a" * 64, "A01",
                adoption_request_id="adoption:1", marker_proof=proof(),
            )


def test_multiple_matches_conflict_without_binding(tmp_path: Path) -> None:
    service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    row = {**exact_match(), "standing": "AMBIGUOUS_MATCH", "matchCount": 2}
    row.pop("providerResource")
    with mock.patch("agent_automation_browserless.discover_exact_marker", return_value=row):
        with pytest.raises(BrowserlessAutomationConflict, match="multiple exact provider conversations"):
            service.adopt_conversation(
                spec_path(tmp_path), "sha256:" + "a" * 64, "A01",
                adoption_request_id="adoption:1", marker_proof=proof(),
            )


def test_unknown_agent_fails_before_provider_discovery(tmp_path: Path) -> None:
    service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    with mock.patch("agent_automation_browserless.discover_exact_marker") as discover:
        with pytest.raises(BrowserlessAutomationConflict, match="agentId"):
            service.adopt_conversation(
                spec_path(tmp_path), "sha256:" + "a" * 64, "A99",
                adoption_request_id="adoption:1", marker_proof=proof(),
            )
    discover.assert_not_called()


def test_exact_adoption_replay_converges(tmp_path: Path) -> None:
    service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    path = spec_path(tmp_path)
    with mock.patch("agent_automation_browserless.discover_exact_marker", return_value=exact_match()):
        first = service.adopt_conversation(
            path, "sha256:" + "a" * 64, "A01", adoption_request_id="adoption:1", marker_proof=proof()
        )
        second = service.adopt_conversation(
            path, "sha256:" + "a" * 64, "A01", adoption_request_id="adoption:1", marker_proof=proof()
        )
    assert first["bindingDigest"] == second["bindingDigest"]
