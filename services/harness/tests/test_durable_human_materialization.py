from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_browserless import BrowserlessAutomationConfig  # noqa:E402
from agent_automation_browserless_effects import BrowserlessEffectAdapter  # noqa:E402
from campaign_materialization import campaign_census  # noqa:E402

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
                "campaignId": "campaign:human",
                "sharedPrompt": "bootstrap",
                "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
            }
        )
    )
    return p


def auth_preflight(effects: BrowserlessEffectAdapter) -> dict:
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


def session() -> dict:
    return {
        "standing": "READY",
        "sessionId": SESSION_ID,
        "sessionActive": True,
        "cdpEndpoint": "http://127.0.0.1:19241",
        "operatorURL": "http://127.0.0.1:19441/vnc.html",
        "browserExecutableDigest": "sha256:" + "8" * 64,
    }


def test_auth_required_enters_durable_cft_handoff_before_browserless_binding(
    tmp_path: Path,
) -> None:
    cfg = BrowserlessAutomationConfig.from_dict(config(tmp_path))
    effects = BrowserlessEffectAdapter(cfg)
    path = spec_path(tmp_path)
    with (
        mock.patch("agent_automation_browserless_effects.DurableSessionAuthority") as authority,
        mock.patch("agent_automation_browserless_effects.prepare_chatgpt_human_session") as prepare,
        mock.patch.object(effects, "_write_binding") as write_binding,
        mock.patch.object(effects, "_target") as browserless_target,
    ):
        authority.return_value.open.return_value = session()
        value = effects.materialize(
            path, "A01", endpoint_id="carrier-a", provider_preflight=auth_preflight(effects)
        )
    write_binding.assert_not_called()
    browserless_target.assert_not_called()
    prepare.assert_called_once_with(session())
    authority.return_value.open.assert_called_once()
    assert value["receipt"]["standing"] == "human-required"
    assert value["humanHandoff"]["sessionId"] == SESSION_ID
    assert value["humanHandoff"]["operatorURL"] == session()["operatorURL"]
    assert value["humanHandoff"]["providerEffectAttempted"] is False
    assert "cdpEndpoint" not in value["humanHandoff"]
    census = campaign_census(effects.context.load_spec(path), cfg.ledger)
    assert census["materializations"][0]["materializationStanding"] == "human-required"


def test_durable_handoff_replay_reuses_same_session_request_identity(tmp_path: Path) -> None:
    cfg = BrowserlessAutomationConfig.from_dict(config(tmp_path))
    effects = BrowserlessEffectAdapter(cfg)
    path = spec_path(tmp_path)
    with (
        mock.patch("agent_automation_browserless_effects.DurableSessionAuthority") as authority,
        mock.patch("agent_automation_browserless_effects.prepare_chatgpt_human_session"),
    ):
        authority.return_value.open.return_value = session()
        first = effects.materialize(
            path, "A01", endpoint_id="carrier-a", provider_preflight=auth_preflight(effects)
        )
        second = effects.materialize(
            path, "A01", endpoint_id="carrier-a", provider_preflight=auth_preflight(effects)
        )
    assert first["receipt"]["standing"] == second["receipt"]["standing"] == "human-required"
    assert authority.return_value.open.call_count == 1


def test_handoff_receipt_is_private_and_verifiable(tmp_path: Path) -> None:
    from cft_human_materialization import create_handoff, load_verified_handoff

    path = tmp_path / "handoff.json"
    value = create_handoff(
        path,
        effect_id="effect-1",
        request_digest="sha256:" + "1" * 64,
        session=session(),
        blocker="auth-required",
    )
    assert path.stat().st_mode & 0o777 == 0o600
    assert load_verified_handoff(path, expected_digest=value["handoffDigest"]) == value
    assert "cdpEndpoint" not in value
    assert "cookie" not in json.dumps(value).lower()


def test_durable_human_resume_uses_cft_target_without_browserless_binding(tmp_path: Path) -> None:
    from sqlite_conversation_materializer import TargetMaterializationObservation
    from conversation_relay_carrier import MaterializationStanding

    cfg = BrowserlessAutomationConfig.from_dict(config(tmp_path))
    effects = BrowserlessEffectAdapter(cfg)
    path = spec_path(tmp_path)
    with (
        mock.patch("agent_automation_browserless_effects.DurableSessionAuthority") as authority,
        mock.patch("agent_automation_browserless_effects.prepare_chatgpt_human_session"),
    ):
        authority.return_value.open.return_value = session()
        first = effects.materialize(
            path, "A01", endpoint_id="carrier-a", provider_preflight=auth_preflight(effects)
        )
    assert first["receipt"]["standing"] == "human-required"

    fake_target = mock.Mock()
    fake_target.resume_after_human.return_value = TargetMaterializationObservation(
        standing=MaterializationStanding.BOUND,
        provider_conversation_coordinate="https://chatgpt.com/c/resumed-1",
        evidence_digest="sha256:" + "5" * 64,
        detail="CfT authenticated bootstrap submitted and provider-bound",
    )
    with (
        mock.patch(
            "agent_automation_browserless_effects.CftAuthenticatedSendTarget",
            return_value=fake_target,
        ) as target,
        mock.patch.object(effects.context, "_current_binding") as current_binding,
        mock.patch.object(effects, "_target") as browserless_target,
    ):
        value = effects.resume_after_human(path, "A01")
    current_binding.assert_not_called()
    browserless_target.assert_not_called()
    target.assert_called_once()
    assert value["kind"] == "ordivon.durable-human-resume"
    assert value["receipt"]["standing"] == "bound"
    assert value["receipt"]["providerResource"] == "https://chatgpt.com/c/resumed-1"


def test_cft_authenticated_send_target_invokes_loopback_resume_script(tmp_path: Path) -> None:
    from campaign_materialization import compile_campaign
    from cft_human_materialization import (
        CftAuthenticatedSendTarget,
        create_handoff,
    )

    cfg = BrowserlessAutomationConfig.from_dict(config(tmp_path))
    effects = BrowserlessEffectAdapter(cfg)
    spec = effects.context.load_spec(spec_path(tmp_path))
    request = compile_campaign(spec)["A01"]
    handoff_path = tmp_path / "handoff.json"
    handoff = create_handoff(
        handoff_path,
        effect_id=request.request_id,
        request_digest=request.request_digest,
        session=session(),
        blocker="auth-required",
    )
    script = tmp_path / "resume.py"
    script.write_text("# witness")
    python = tmp_path / "python"
    python.write_text("# witness")
    completed = mock.Mock(
        returncode=0,
        stdout=json.dumps(
            {
                "effectId": request.request_id,
                "providerResource": "https://chatgpt.com/c/resumed-1",
                "generationStarted": True,
                "composerCleared": True,
                "bindingDigest": "sha256:" + "6" * 64,
            }
        )
        + "\n",
        stderr="",
    )
    with (
        mock.patch("cft_human_materialization.resolve_session", return_value=session()),
        mock.patch("cft_human_materialization.subprocess.run", return_value=completed) as run,
    ):
        target = CftAuthenticatedSendTarget(
            handoff_path=handoff_path,
            state_dir=tmp_path / "state",
            playwright_python=python,
            resume_script=script,
            wait_stable_seconds=150,
        )
        observation = target.resume_after_human(request)
    command = run.call_args.args[0]
    assert "--cdp-endpoint" in command and session()["cdpEndpoint"] in command
    assert "--session-id" in command and SESSION_ID in command
    assert "--browserless-token-file" not in command
    assert "--expected-handoff-digest" in command and handoff["handoffDigest"] in command
    assert observation.standing.value == "bound"
    assert observation.provider_conversation_coordinate == "https://chatgpt.com/c/resumed-1"


def test_cft_resume_script_has_no_cookie_or_browserless_reconnect_surface() -> None:
    text = (ROOT / "scripts/playwright_cft_chatgpt_resume.py").read_text().lower()
    assert "--cdp-endpoint" in text
    assert "--session-id" in text
    assert "browserless.reconnect" not in text
    assert "cookie" not in text
    assert "storage_state" not in text
