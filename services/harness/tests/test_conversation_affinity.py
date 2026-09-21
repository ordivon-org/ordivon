from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_automation_browserless import BrowserlessAutomationConfig, BrowserlessAutomationService  # noqa: E402
from sqlite_conversation_binding import SQLiteConversationBindingStore  # noqa: E402

SESSION_ID = "019a9af0-7b00-7000-8000-000000000001"
CAMPAIGN_REF = "sha256:" + "a" * 64


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
                "campaignId": "campaign:affinity",
                "sharedPrompt": "Do one task.",
                "roster": [{"agentId": "A01", "roleCard": "Verifier."}],
            }
        )
    )
    return path


def service(root: Path) -> BrowserlessAutomationService:
    return BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(config(root)))


def adopt(root: Path) -> None:
    SQLiteConversationBindingStore(root / "state" / "materialization-ledger.sqlite").adopt_binding(
        campaign_ref=CAMPAIGN_REF,
        agent_id="A01",
        provider_resource="https://chatgpt.com/c/adopted",
        session_id=SESSION_ID,
        evidence_digest="sha256:" + "2" * 64,
        request_id="adoption:1",
    )


def test_adopted_ready_session_has_highest_affinity(tmp_path: Path) -> None:
    svc = service(tmp_path)
    path = spec_path(tmp_path)
    adopt(tmp_path)
    session = {
        "standing": "READY",
        "sessionId": SESSION_ID,
        "cdpEndpoint": "http://127.0.0.1:19241",
    }
    census = {
        "materializations": [
            {
                "agentId": "A01",
                "materializationStanding": "bound",
                "providerResource": "https://chatgpt.com/c/materialized",
            }
        ]
    }
    with (
        mock.patch("agent_automation_browserless.resolve_session", return_value=session),
        mock.patch("agent_automation_browserless.campaign_census", return_value=census),
        mock.patch.object(svc, "_current_binding") as carrier,
    ):
        value = svc.conversation_affinity(path, CAMPAIGN_REF, "A01")
    carrier.assert_not_called()
    assert value["standing"] == "READY"
    assert value["placementAction"] == "CONTINUE"
    assert value["affinityKind"] == "DURABLE_CFT_SESSION"
    assert value["providerResource"] == "https://chatgpt.com/c/adopted"
    assert value["sessionId"] == SESSION_ID
    assert "cdpEndpoint" not in value
    assert value["providerEffectAttempted"] is False


def test_stale_adopted_affinity_holds_instead_of_materializing_duplicate(tmp_path: Path) -> None:
    svc = service(tmp_path)
    path = spec_path(tmp_path)
    adopt(tmp_path)
    with (
        mock.patch(
            "agent_automation_browserless.resolve_session", side_effect=RuntimeError("not READY")
        ),
        mock.patch("agent_automation_browserless.campaign_census") as census,
    ):
        value = svc.conversation_affinity(path, CAMPAIGN_REF, "A01")
    census.assert_not_called()
    assert value["standing"] == "STALE"
    assert value["placementAction"] == "HOLD_EXISTING_AFFINITY"
    assert value["affinityKind"] == "DURABLE_CFT_SESSION"


def test_browserless_materialization_is_second_priority(tmp_path: Path) -> None:
    svc = service(tmp_path)
    path = spec_path(tmp_path)
    materialization = svc._materialization(svc.load_spec(path), "A01")
    census = {
        "materializations": [
            {
                "agentId": "A01",
                "materializationStanding": "bound",
                "providerResource": "https://chatgpt.com/c/materialized",
            }
        ]
    }
    binding = {
        "effectId": materialization.request_id,
        "endpointId": "carrier-a",
        "endpointIdentityDigest": svc.config.browserless_pool.endpoints[0].identity_digest,
    }
    with (
        mock.patch("agent_automation_browserless.campaign_census", return_value=census),
        mock.patch.object(svc, "_current_binding", return_value=binding),
    ):
        value = svc.conversation_affinity(path, CAMPAIGN_REF, "A01")
    assert value["standing"] == "READY"
    assert value["placementAction"] == "CONTINUE"
    assert value["affinityKind"] == "BROWSERLESS_MATERIALIZATION"
    assert value["endpointId"] == "carrier-a"


def test_bound_materialization_without_current_carrier_holds(tmp_path: Path) -> None:
    svc = service(tmp_path)
    path = spec_path(tmp_path)
    census = {
        "materializations": [
            {
                "agentId": "A01",
                "materializationStanding": "bound",
                "providerResource": "https://chatgpt.com/c/materialized",
            }
        ]
    }
    with (
        mock.patch("agent_automation_browserless.campaign_census", return_value=census),
        mock.patch.object(svc, "_current_binding", return_value=None),
    ):
        value = svc.conversation_affinity(path, CAMPAIGN_REF, "A01")
    assert value["standing"] == "STALE"
    assert value["placementAction"] == "HOLD_EXISTING_AFFINITY"
    assert value["affinityKind"] == "BROWSERLESS_MATERIALIZATION"


def test_no_affinity_projects_materialize_fallback(tmp_path: Path) -> None:
    svc = service(tmp_path)
    path = spec_path(tmp_path)
    census = {
        "materializations": [
            {"agentId": "A01", "materializationStanding": "unrecorded", "providerResource": None}
        ]
    }
    with mock.patch("agent_automation_browserless.campaign_census", return_value=census):
        value = svc.conversation_affinity(path, CAMPAIGN_REF, "A01")
    assert value["standing"] == "NONE"
    assert value["placementAction"] == "MATERIALIZE_FALLBACK"
    assert value["affinityKind"] == "NONE"


def test_affinity_projection_is_read_only(tmp_path: Path) -> None:
    svc = service(tmp_path)
    path = spec_path(tmp_path)
    adopt(tmp_path)
    before = svc.config.ledger.read_bytes()
    with mock.patch(
        "agent_automation_browserless.resolve_session",
        return_value={
            "standing": "READY",
            "sessionId": SESSION_ID,
            "cdpEndpoint": "http://127.0.0.1:19241",
        },
    ):
        svc.conversation_affinity(path, CAMPAIGN_REF, "A01")
    assert svc.config.ledger.read_bytes() == before
