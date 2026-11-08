"""Real Finance CLI and Security Owner contract composition for research roles.

These are *consumer* tests, not an authentication service. The Security input
fixture represents an already verified identity/grant projection in a synthetic
test; public callers must never self-assert that projection.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FINANCE = Path(__file__).resolve().parents[1]
REPO = FINANCE.parents[1]
RESEARCH_CLI = FINANCE / "scripts" / "finance_lego.py"
SECURITY_EVALUATOR = (
    REPO / "platform" / "security" / "contracts" / "agent-admission-v1" / "evaluate.py"
)
ADMISSION_FIXTURE = (
    REPO / "platform" / "security" / "fixtures" / "agent-admission" / "v0-allow.json"
)
SHA = "sha256:" + "a" * 64


def _finance(operation: str, body: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RESEARCH_CLI), operation],
        input=json.dumps(body, sort_keys=True),
        text=True,
        capture_output=True,
        check=False,
        cwd=FINANCE,
        env={**os.environ, "PYTHONPATH": str(FINANCE / "src")},
    )


def _research_plan() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.plan",
        "effectBoundary": "RESEARCH_ONLY",
        "hypothesisId": "agent-research-prospective-001",
        "baselineId": "cash",
        "metricDefinition": "paired-after-cost-benchmark",
        "frozenAt": "2026-01-01T12:00:00Z",
        "codeRevision": "a" * 40,
        "configDigest": SHA,
        "environmentDigest": SHA,
        "trialsPlanned": 2,
        "partitions": {
            "train": {"start": "2020-01-01", "end": "2022-12-31"},
            "validation": {"start": "2023-01-01", "end": "2025-12-31"},
            "holdout": {"start": "2026-01-02", "end": "2026-06-30"},
        },
        "historicalSources": [{
            "sourceId": "synthetic:admitted-historical-data",
            "snapshotDigest": SHA,
            "observedThrough": "2025-12-31T20:00:00Z",
            "availableAt": "2026-01-01T06:00:00Z",
        }],
    }


def _holdout(plan_digest: str) -> dict:
    return {
        "planDigest": plan_digest,
        "evaluatedAt": "2026-07-02T12:00:00Z",
        "observedThrough": "2026-06-30T21:00:00Z",
        "availableAt": "2026-07-01T06:00:00Z",
        "holdoutDigest": SHA,
        "trialsEvaluated": 2,
        "multiplicityControl": "DOCUMENTED",
        "costModelDigest": SHA,
        "benchmarkEvidenceDigest": SHA,
        "independentReproduction": True,
    }


def test_director_researcher_reviewer_use_existing_finance_cli_without_trade_authority() -> None:
    """One production CLI, different task roles; role names confer no effects."""
    frozen_result = _finance("freeze-experiment", _research_plan())
    assert frozen_result.returncode == 0, frozen_result.stderr
    frozen = json.loads(frozen_result.stdout)
    assert frozen["authority"] == "NONE"
    assert frozen["attestation"] == "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED"

    # The independent review phase cannot falsely promote missing evidence.
    missing_result = _finance("assess-holdout", {"frozen": frozen, "result": None})
    assert missing_result.returncode == 0, missing_result.stderr
    assert json.loads(missing_result.stdout)["standing"] == "UNKNOWN"

    assessed_result = _finance("assess-holdout", {
        "frozen": frozen, "result": _holdout(frozen["planDigest"]),
    })
    assert assessed_result.returncode == 0, assessed_result.stderr
    assessment = json.loads(assessed_result.stdout)
    # Even an Agent-provided 'independentReproduction=true' is NOT authority.
    assert assessment["standing"] == "REVIEW_REQUIRED"
    assert assessment["capitalAllocationAuthorized"] is False
    assert assessment["externalWriteAllowed"] is False

    tampered = copy.deepcopy(frozen)
    tampered["plan"]["trialsPlanned"] = 1
    rejected_result = _finance("assess-holdout", {"frozen": tampered, "result": None})
    assert rejected_result.returncode == 0, rejected_result.stderr
    assert json.loads(rejected_result.stdout)["standing"] == "REJECTED"


def test_research_role_cannot_smuggle_effect_authority_into_plan() -> None:
    plan = _research_plan()
    plan["externalWriteAllowed"] = True
    rejection = _finance("freeze-experiment", plan)
    assert rejection.returncode == 2
    assert rejection.stdout == ""
    assert "INVALID_FINANCE_LEGO_INPUT" in rejection.stderr


def test_research_heldout_result_cannot_smuggle_trade_permission() -> None:
    frozen = json.loads(_finance("freeze-experiment", _research_plan()).stdout)
    result = _holdout(frozen["planDigest"])
    result["orderSubmissionAllowed"] = True
    assessed = _finance("assess-holdout", {"frozen": frozen, "result": result})
    assert assessed.returncode == 0, assessed.stderr
    actual = json.loads(assessed.stdout)
    assert actual["standing"] == "UNKNOWN"
    assert actual["capitalAllocationAuthorized"] is False
    assert actual["externalWriteAllowed"] is False


def _synthetic_verified_agent_request(
    *, action: str, resource: str = "/finance/research/experiment-42",
) -> dict:
    """Tests ONLY: stand-in for a trusted verifier's normalized projection."""
    body = json.loads(ADMISSION_FIXTURE.read_text(encoding="utf-8"))
    body["grant"]["allowedActions"] = [
        "finance.research.freeze", "finance.research.assess",
    ]
    body["grant"]["resourcePrefixes"] = ["/finance/research/"]
    body["effect"]["action"] = action
    body["effect"]["resource"] = resource
    body["effect"]["effectType"] = "finance.research.operation"
    body["effect"]["riskClass"] = "R2"
    body["grant"]["maxRiskClass"] = "R4"
    body["grant"]["stepUpAtOrAbove"] = "R4"
    return body


def _security(body: dict) -> dict:
    output = subprocess.run(
        [sys.executable, str(SECURITY_EVALUATOR)],
        input=json.dumps(body),
        text=True,
        capture_output=True,
        check=False,
        cwd=FINANCE,
    )
    assert output.returncode == 0, output.stderr
    return json.loads(output.stdout)


@pytest.mark.provider_qualification
@pytest.mark.parametrize("action", ["finance.research.freeze", "finance.research.assess"])
def test_verified_research_task_uses_actual_security_admission(action: str) -> None:
    assert shutil.which("opa"), "Security policy qualification requires native OPA"
    body = _synthetic_verified_agent_request(action=action)
    decision = _security(body)
    assert decision["agent"]["outcome"] == "ALLOW"
    assert decision["effect"]["admitted"] is True
    assert decision["effect"]["inputContractVersion"] == 2
    assert decision["effect"]["authorityDigestBound"] is True
    assert decision["effect"]["authorityDigest"] == body["grant"]["grantDigest"]
    assert decision["effect"]["capability"] == action


@pytest.mark.provider_qualification
@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda x: x["effect"].update(action="finance.trading.order.submit"), "action-not-granted"),
        (lambda x: x["effect"].update(resource="/finance/portfolio/live"), "resource-not-granted"),
        (lambda x: x["agent"].update(agentId="agent:impersonator"), "agent-grant-mismatch"),
        (lambda x: x["grant"].update(remainingEffects=0), "effect-budget-exhausted"),
        (lambda x: x["grant"].update(active=False), "grant-inactive"),
        (lambda x: x.update(nowEpochSeconds=x["grant"]["expiresAtEpochSeconds"]), "grant-expired"),
    ],
)
def test_research_delegation_denies_ungranted_or_stale_effect(mutation, reason: str) -> None:
    assert shutil.which("opa"), "Security policy qualification requires native OPA"
    body = _synthetic_verified_agent_request(action="finance.research.freeze")
    mutation(body)
    decision = _security(body)
    assert decision["agent"]["outcome"] == "DENY"
    assert decision["agent"]["reason"] == reason
    assert decision["effect"] is None


@pytest.mark.provider_qualification
def test_research_role_has_no_automatic_high_consequence_step_up() -> None:
    assert shutil.which("opa"), "Security policy qualification requires native OPA"
    body = _synthetic_verified_agent_request(action="finance.research.freeze")
    body["effect"]["riskClass"] = "R4"
    decision = _security(body)
    assert decision["agent"]["outcome"] == "STEP_UP"
    assert decision["agent"]["reason"] == "principal-step-up-required"
    assert decision["effect"] is None
