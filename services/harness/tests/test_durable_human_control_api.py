from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_browserless import BrowserlessAutomationConfig  # noqa:E402
from agent_automation_browserless_effects import BrowserlessEffectAdapter  # noqa:E402

SESSION_ID = "019a9af0-7b00-7000-8000-000000000001"


def config(root: Path) -> dict:
    token = root / "token"
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
    p = root / "spec.json"
    p.write_text(
        json.dumps(
            {
                "campaignId": "campaign:human-control",
                "sharedPrompt": "bootstrap",
                "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
            }
        )
    )
    return p


def session() -> dict:
    return {
        "standing": "READY",
        "sessionId": SESSION_ID,
        "sessionActive": True,
        "cdpEndpoint": "http://127.0.0.1:19241",
        "operatorURL": "http://127.0.0.1:19441/vnc.html",
        "browserExecutableDigest": "sha256:" + "8" * 64,
    }


def auth_observation(effects: BrowserlessEffectAdapter) -> dict:
    endpoint = effects.config.browserless_pool.endpoints[0]
    return {
        "standing": "AUTH_REQUIRED",
        "endpointId": endpoint.endpoint_id,
        "providerEffectAttempted": False,
        "clicked": False,
        "composerFilled": False,
        "sendAttempted": False,
        "assistantOutputRead": False,
        "substrateHealth": {"healthy": True},
    }


def arrange(tmp_path: Path):
    cfg = BrowserlessAutomationConfig.from_dict(config(tmp_path))
    effects = BrowserlessEffectAdapter(cfg)
    path = spec_path(tmp_path)
    with (
        mock.patch("agent_automation_browserless_effects.DurableSessionAuthority") as authority,
        mock.patch("agent_automation_browserless_effects.prepare_chatgpt_human_session"),
    ):
        authority.return_value.open.return_value = session()
        result = effects.materialize(
            path, "A01", endpoint_id="carrier-a", provider_preflight=auth_observation(effects)
        )
    return cfg, effects.context, path, result


def test_handoff_info_projects_durable_cft_operator_url(tmp_path: Path) -> None:
    _cfg, service, path, result = arrange(tmp_path)
    with mock.patch("agent_automation_browserless.resolve_session", return_value=session()):
        value = service.human_handoff_info(path, "A01")
    assert value["mode"] == "durable-cft-session"
    assert value["sessionId"] == SESSION_ID
    assert value["handoffURL"] == session()["operatorURL"]
    assert value["handoffDigest"] == result["humanHandoff"]["handoffDigest"]
    assert value["sessionActive"] is True
    assert value["providerEffectAttempted"] is False


def test_census_projects_durable_handoff_without_exposing_url(tmp_path: Path) -> None:
    _cfg, service, path, _result = arrange(tmp_path)
    with mock.patch("agent_automation_browserless.resolve_session", return_value=session()):
        value = service.census(path)
    row = value["materializations"][0]
    assert row["humanHandoffAvailable"] is True
    assert row["humanHandoffMode"] == "durable-cft-session"
    assert "operatorURL" not in json.dumps(value)
    assert value["activeHumanHandoffs"] == 1


def test_human_resume_updates_same_workflow_while_durable_session_is_active(tmp_path: Path) -> None:
    _cfg, service, path, result = arrange(tmp_path)
    temporal = {"workflowId": "effect-1", "disposition": "updated"}
    with (
        mock.patch("agent_automation_browserless.resolve_session", return_value=session()),
        mock.patch.object(service, "_temporal_admit", return_value=temporal) as admit,
    ):
        value = service.launch_human_resume(path, "A01")
    admit.assert_called_once_with(
        path, "human-resume", agent_id="A01", resume_id=result["humanHandoff"]["handoffDigest"]
    )
    assert value["temporal"] == temporal


def test_stale_durable_session_handoff_holds_without_falling_back_to_legacy(tmp_path: Path) -> None:
    _cfg, service, path, _result = arrange(tmp_path)
    with mock.patch(
        "agent_automation_browserless.resolve_session", side_effect=RuntimeError("not READY")
    ):
        try:
            service.human_handoff_info(path, "A01")
        except Exception as error:
            assert "durable" in str(error).lower() or "session" in str(error).lower()
        else:
            raise AssertionError("stale durable session must HOLD")
