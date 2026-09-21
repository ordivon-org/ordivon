from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "contracts" / "agent-admission-v1" / "evaluate.py"
FIXTURE = ROOT / "fixtures" / "agent-admission" / "v0-allow.json"


def _run(payload: dict[str, object]) -> dict[str, object]:
    result = subprocess.run(
        ["/usr/bin/python3", str(EVALUATOR)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_public_contract_composes_agent_and_effect_admission() -> None:
    payload = json.loads(FIXTURE.read_text())
    result = _run(payload)

    assert result["kind"] == "ordivon.security.agent-admission-chain"
    assert result["agent"]["outcome"] == "ALLOW"
    assert result["agent"]["reason"] == "admitted"
    assert result["effect"]["admitted"] is True
    assert result["effect"]["requestId"] == payload["effect"]["effectId"]


def test_public_contract_preserves_step_up_without_effect_projection() -> None:
    payload = json.loads(FIXTURE.read_text())
    payload["effect"]["riskClass"] = "R4"
    payload["grant"]["maxRiskClass"] = "R4"
    payload["grant"]["stepUpAtOrAbove"] = "R4"
    payload["approval"] = {
        "verified": False,
        "principalId": None,
        "effectId": None,
        "method": None,
    }

    result = _run(payload)

    assert result["agent"]["outcome"] == "STEP_UP"
    assert result["agent"]["reason"] == "principal-step-up-required"
    assert result["effect"] is None
