from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import playwright_browserless_turn_once as turn  # noqa: E402
from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    BrowserlessAutomationHold,
    BrowserlessAutomationService,
)

CAMPAIGN_REF = "sha256:" + "a" * 64
SESSION_ID = "019a9af0-7b00-7000-8000-000000000001"
TURN_ID = "019a9af0-7b00-7000-8000-000000000011"


def config(root: Path) -> dict:
    token = root / "browserless.token"
    token.write_text("secret-token-value-long-enough-for-test")
    return {
        "schemaVersion": 1,
        "stateRoot": str(root / "state"),
        "playwrightPython": "/venv/bin/python",
        "browserlessSubmitScript": str(ROOT / "scripts/playwright_browserless_chatgpt_submit.py"),
        "browserlessReconcileScript": str(
            ROOT / "scripts/playwright_browserless_binding_reconcile.py"
        ),
        "browserlessTurnScript": str(ROOT / "scripts/playwright_browserless_turn_once.py"),
        "browserlessPreflightScript": str(
            ROOT / "scripts/playwright_browserless_provider_preflight.py"
        ),
        "temporalPython": "/temporal/bin/python",
        "temporalLaunchScript": str(ROOT / "scripts/temporal_agent_automation_launch.py"),
        "browserSubstrate": {
            "kind": "browserless",
            "endpoints": [
                {
                    "id": "carrier-a",
                    "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                    "httpEndpoint": "http://127.0.0.1:3011",
                    "tokenFile": str(token),
                }
            ],
        },
    }


def spec_path(root: Path) -> Path:
    path = root / "spec.json"
    path.write_text(
        json.dumps(
            {
                "campaignId": "campaign:wake",
                "sharedPrompt": "bootstrap",
                "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
            }
        )
    )
    return path


def test_turn_connector_accepts_exact_loopback_cft_session() -> None:
    args = SimpleNamespace(
        browserless_endpoint=None,
        browserless_token_file=None,
        endpoint_id=None,
        cdp_endpoint="http://127.0.0.1:19241",
        session_id=SESSION_ID,
    )
    value = turn.connector_spec(args)
    assert value == {
        "connectorKind": "cft-human-session",
        "connectionEndpoint": "http://127.0.0.1:19241",
        "receiptIdentity": {"sessionId": SESSION_ID},
    }


def test_turn_connector_rejects_nonloopback_cft_endpoint() -> None:
    args = SimpleNamespace(
        browserless_endpoint=None,
        browserless_token_file=None,
        endpoint_id=None,
        cdp_endpoint="http://10.0.0.8:9222",
        session_id=SESSION_ID,
    )
    with pytest.raises(ValueError, match="loopback"):
        turn.connector_spec(args)


def test_turn_connector_preserves_browserless_mode(tmp_path: Path) -> None:
    token = tmp_path / "token"
    token.write_text("secret-token")
    args = SimpleNamespace(
        browserless_endpoint="ws://127.0.0.1:3011/chromium",
        browserless_token_file=token,
        endpoint_id="carrier-a",
        cdp_endpoint=None,
        session_id=None,
    )
    value = turn.connector_spec(args)
    assert value["connectorKind"] == "browserless"
    assert "token=secret-token" in value["connectionEndpoint"]
    assert value["receiptIdentity"] == {"browserlessEndpointId": "carrier-a"}


def test_launch_continue_uses_adopted_affinity_without_browserless_preflight(
    tmp_path: Path,
) -> None:
    svc = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    path = spec_path(tmp_path)
    affinity = {
        "standing": "READY",
        "placementAction": "CONTINUE",
        "affinityKind": "DURABLE_CFT_SESSION",
        "providerResource": "https://chatgpt.com/c/adopted",
        "sessionId": SESSION_ID,
    }
    admitted = {
        "workflowId": TURN_ID,
        "workflowType": "ordivon.agent.continue",
        "disposition": "started",
    }
    with (
        mock.patch.object(svc, "conversation_affinity", return_value=affinity),
        mock.patch.object(svc, "provider_preflight") as preflight,
        mock.patch.object(svc, "_temporal_admit", return_value=admitted) as temporal,
    ):
        value = svc.launch_continue(
            path, "A01", campaign_ref=CAMPAIGN_REF, prompt="continue", turn_request_id=TURN_ID
        )
    preflight.assert_not_called()
    temporal.assert_called_once_with(
        path, "continue", agent_id="A01", prompt="continue", turn_request_id=TURN_ID
    )
    assert value["affinityKind"] == "DURABLE_CFT_SESSION"


def test_launch_continue_holds_stale_explicit_affinity(tmp_path: Path) -> None:
    svc = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    path = spec_path(tmp_path)
    affinity = {
        "standing": "STALE",
        "placementAction": "HOLD_EXISTING_AFFINITY",
        "affinityKind": "DURABLE_CFT_SESSION",
    }
    with mock.patch.object(svc, "conversation_affinity", return_value=affinity):
        with pytest.raises(BrowserlessAutomationHold, match="existing conversation affinity"):
            svc.launch_continue(
                path, "A01", campaign_ref=CAMPAIGN_REF, prompt="continue", turn_request_id=TURN_ID
            )


def test_wake_continue_reuses_stable_turn_identity(tmp_path: Path) -> None:
    svc = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    path = spec_path(tmp_path)
    affinity = {
        "standing": "READY",
        "placementAction": "CONTINUE",
        "affinityKind": "DURABLE_CFT_SESSION",
        "providerResource": "https://chatgpt.com/c/a",
        "sessionId": SESSION_ID,
    }
    with (
        mock.patch.object(svc, "conversation_affinity", return_value=affinity),
        mock.patch.object(
            svc, "launch_continue", return_value={"kind": "continue", "turnRequestId": TURN_ID}
        ) as cont,
        mock.patch(
            "sqlite_wake_turn_map.uuid.uuid7", return_value=__import__("uuid").UUID(TURN_ID)
        ),
    ):
        first = svc.launch_wake(path, CAMPAIGN_REF, "A01", wake_intent_id="wake:1", prompt="next")
        second = svc.launch_wake(path, CAMPAIGN_REF, "A01", wake_intent_id="wake:1", prompt="next")
    assert first["turnRequestId"] == second["turnRequestId"] == TURN_ID
    assert cont.call_count == 2
    assert all(call.kwargs["turn_request_id"] == TURN_ID for call in cont.call_args_list)


def test_wake_without_affinity_admits_materialization_fallback_and_does_not_continue(
    tmp_path: Path,
) -> None:
    svc = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(tmp_path)))
    path = spec_path(tmp_path)
    affinity = {
        "standing": "NONE",
        "placementAction": "MATERIALIZE_FALLBACK",
        "affinityKind": "NONE",
    }
    with (
        mock.patch.object(svc, "conversation_affinity", return_value=affinity),
        mock.patch.object(
            svc, "launch_reconcile", return_value={"temporal": {"workflowId": "mat-1"}}
        ) as materialize,
        mock.patch.object(svc, "launch_continue") as cont,
        mock.patch(
            "sqlite_wake_turn_map.uuid.uuid7", return_value=__import__("uuid").UUID(TURN_ID)
        ),
    ):
        value = svc.launch_wake(path, CAMPAIGN_REF, "A01", wake_intent_id="wake:1", prompt="next")
    materialize.assert_called_once_with(path, "A01")
    cont.assert_not_called()
    assert value["placementAction"] == "MATERIALIZE_FALLBACK"
    assert value["turnRequestId"] == TURN_ID
    assert value["promptSent"] is False
