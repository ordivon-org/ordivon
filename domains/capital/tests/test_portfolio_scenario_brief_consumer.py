"""Real Agent CLI consumer: raw positions + thought laws + native what-if abilities.

The acceptance is a read-only portfolio brief, not a new trading framework.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples/portfolio_scenario_brief_r1.json"


def _run(document: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/portfolio_scenario_brief.py")],
        input=document,
        text=True,
        capture_output=True,
        cwd=ROOT,
        env=env,
        check=False,
    )


def test_agent_consumes_raw_thought_capability_into_actual_scenario_brief() -> None:
    result = _run(FIXTURE.read_text(encoding="utf-8"))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["kind"] == "ordivon.capital.portfolio.agent-scenario-brief"
    assert output["scenarioCount"] == 3
    assert output["exposureLedger"]["factorExposure"][0]["signedExposureUsd"] == "60.000000"
    assert output["riskReport"]["nodes"]["riskBudgetRegistration"]["standing"] == "UNSET"
    assert output["riskReport"]["nodes"]["riskLimitEvaluation"]["standing"] == "INCOMPLETE"
    rows = {row["scenarioId"]: row for row in output["counterfactualSet"]["scenarios"]}
    assert rows["reduce-quarter"]["deltas"]["grossNotionalUsd"] == "-30.000000"
    assert rows["reduce-quarter"]["shockProjection"]["afterEquityLossPctFirstOrder"] == "9.000000"
    assert rows["hedge-sector"]["hedgeMechanics"]["standing"] == (
        "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED"
    )
    gates = {row["scenarioId"]: row for row in output["gateSet"]["gates"]}
    assert all(row["standing"] == "INCOMPLETE" for row in gates.values())
    assert all("RISK_BUDGET" in row["incompleteChecks"] for row in gates.values())
    assert output["executionAuthorized"] is False
    assert output["rankingProduced"] is False
    assert output["standing"] == "READ_ONLY_EVIDENCE_INCOMPLETE"
    assert not any(key in output for key in ("order", "orders", "brokerCredentials", "tradeSignal"))


@pytest.mark.parametrize(
    "mutate",
    (
        lambda d: d.update({"executionAuthorized": True}),
        lambda d: d.update({"brokerCredentials": "danger"}),
        lambda d: d.update({"scenarios": []}),
        lambda d: d["scenarios"].append(dict(d["scenarios"][0])),
        lambda d: d["positions"][0].update({"signedNotionalUsd": "NaN"}),
        lambda d: d["scenarios"][1].update({"sizingBasis": "SYSTEM_RECOMMENDED"}),
        lambda d: d.update({"equityUsd": "-1"}),
        lambda d: d.update({"scenarios": [42]}),
    ),
    ids=(
        "execution-flag",
        "credential",
        "empty-scenarios",
        "duplicate-scenario",
        "nonfinite",
        "unqualified-sizing",
        "negative-equity",
        "nonobject-scenario",
    ),
)
def test_bad_agent_inputs_fail_without_any_materialized_output(mutate) -> None:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    mutate(doc)
    result = _run(json.dumps(doc))
    assert result.returncode != 0
    assert result.stdout == ""


@pytest.mark.parametrize(
    "raw",
    (
        '{"schemaVersion":1,"schemaVersion":2}',
        '{"schemaVersion":1,"positions":[{"instrumentId":"x","factorLoadings":{"a":1,"a":2}}]}',
        '{"schemaVersion":1,"equityUsd":NaN}',
        '{"schemaVersion":1,"equityUsd":Infinity}',
        "not-json",
    ),
)
def test_ambiguous_or_nonfinite_json_is_rejected_before_consumer(raw: str) -> None:
    result = _run(raw)
    assert result.returncode != 0
    assert result.stdout == ""


@pytest.mark.parametrize("signed", ("-200", "-100", "100", "200"))
@pytest.mark.parametrize("fraction", ("0.25", "0.5", "0.75", "1"))
def test_bounded_derisk_algebra_is_a_consumed_mechanical_invariant(
    signed: str, fraction: str
) -> None:
    """Enumerate 16 actual source/ability interactions, no inferred alpha."""
    from decimal import Decimal

    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    doc["positions"][0]["signedNotionalUsd"] = signed
    doc["scenarios"] = [
        {
            "scenarioId": "derive",
            "action": "DE_RISK",
            "instrumentId": "SYNTHETIC-A",
            "reductionFraction": fraction,
        }
    ]
    result = _run(json.dumps(doc))
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    case = out["counterfactualSet"]["scenarios"][0]
    expected_reduction = -abs(Decimal(signed)) * Decimal(fraction)
    assert Decimal(case["deltas"]["grossNotionalUsd"]) == expected_reduction
    assert Decimal(case["projected"]["grossNotionalUsd"]) == (
        abs(Decimal(signed)) + expected_reduction
    )
    assert out["gateSet"]["gates"][0]["standing"] == "INCOMPLETE"
    assert out["executionAuthorized"] is False
    assert out["rankingProduced"] is False


@pytest.mark.parametrize(
    ("notional", "loading"),
    (("100", "0.123456789"), ("10000000", "0.0000001")),
    ids=("fractional-drift", "small-factor-erased"),
)
def test_cross_lego_factor_baseline_cannot_succeed_with_contradictory_output(
    notional: str, loading: str
) -> None:
    """The Agent consumer must never materialize conflicting source facts.

    This test admits a future consistent upstream repair instead of freezing
    the current precision bug as a permanent negative expectation.
    """
    from decimal import Decimal

    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    doc["positions"][0]["signedNotionalUsd"] = notional
    doc["positions"][0]["factorLoadings"] = {"sector": loading}
    doc["scenarios"] = [{"scenarioId": "hold", "action": "HOLD"}]
    result = _run(json.dumps(doc))
    if result.returncode:
        assert result.stdout == ""
        assert "factor" in result.stderr.lower()
        return
    output = json.loads(result.stdout)
    ledger = {
        row["factor"]: Decimal(row["signedExposureUsd"])
        for row in output["exposureLedger"]["factorExposure"]
    }
    baseline = {
        row["factor"]: Decimal(row["beforeUsd"])
        for row in output["counterfactualSet"]["scenarios"][0]["deltas"]["factorExposure"]
    }
    assert baseline == ledger, (
        "public Agent brief must not contain two conflicting factor baselines"
    )
