from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_browserless import BrowserlessAutomationConfig  # noqa: E402
from agent_automation_browserless_effects import BrowserlessEffectAdapter  # noqa: E402

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
                "campaignId": "campaign:continue",
                "sharedPrompt": "bootstrap",
                "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
            }
        )
    )
    return path


def affinity() -> dict:
    return {
        "standing": "READY",
        "placementAction": "CONTINUE",
        "affinityKind": "DURABLE_CFT_SESSION",
        "providerResource": "https://chatgpt.com/c/adopted",
        "sessionId": SESSION_ID,
    }


def test_effect_adapter_uses_same_turn_script_for_durable_cft(tmp_path: Path) -> None:
    cfg = BrowserlessAutomationConfig.from_dict(config(tmp_path))
    effects = BrowserlessEffectAdapter(cfg)
    path = spec_path(tmp_path)
    completed = mock.Mock(
        returncode=0,
        stdout=json.dumps(
            {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-turn-run",
                "turnRequestId": TURN_ID,
                "standing": "COMPLETED",
                "safeToResend": False,
            }
        )
        + "\n",
        stderr="",
    )
    session = {
        "standing": "READY",
        "sessionId": SESSION_ID,
        "cdpEndpoint": "http://127.0.0.1:19241",
    }
    with (
        mock.patch.object(effects.context, "conversation_affinity", return_value=affinity()),
        mock.patch("agent_automation_browserless_effects.resolve_session", return_value=session),
        mock.patch(
            "agent_automation_browserless_effects.subprocess.run", return_value=completed
        ) as run,
    ):
        value = effects.send_adopted_turn(
            path, CAMPAIGN_REF, "A01", turn_request_id=TURN_ID, prompt="continue"
        )
    command = run.call_args.args[0]
    assert "--cdp-endpoint" in command and "http://127.0.0.1:19241" in command
    assert "--session-id" in command and SESSION_ID in command
    assert "--target-resource" in command and "https://chatgpt.com/c/adopted" in command
    assert "--browserless-token-file" not in command
    assert value["standing"] == "COMPLETED"


def test_temporal_launcher_carries_campaign_ref_into_continue_input() -> None:
    text = (ROOT / "scripts/temporal_agent_automation_launch.py").read_text()
    block = text[
        text.index("value = AgentContinueInput(") : text.index('if a.operation == "continue-retry"')
    ]
    assert "campaign_ref=a.campaign_ref" in block
