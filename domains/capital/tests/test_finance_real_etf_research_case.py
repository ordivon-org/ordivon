"""Source-bound economic finding and honest prospective research freeze.

Offline tests verify the published contract. The optional provider-qualified
test consumes original upstream source bytes from a local, read-only input,
not a canned synthetic market path or a downloaded-on-import fixture.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import os
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from ordivon_capital.portfolio.paper_investment import replay_paper_investment
from ordivon_capital.research.experiment_protocol import (
    ExperimentContractError,
    assess_holdout_evidence,
    freeze_experiment_plan,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "finance-research" / "spy-shy-forward-20261108"
REQUEST = ROOT / "examples" / "paper_fixed_mix_etf_20261106.json"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_native_research_freeze_recreates_exact_published_digest() -> None:
    plan = _json(EVIDENCE / "research-plan.json")
    frozen = _json(EVIDENCE / "frozen-plan.json")
    assert freeze_experiment_plan(plan) == frozen
    assert frozen["authority"] == "NONE"
    assert frozen["attestation"] == "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED"


def test_future_holdout_remains_unknown_without_future_market_evidence() -> None:
    frozen = _json(EVIDENCE / "frozen-plan.json")
    assessment = assess_holdout_evidence(frozen, None)
    assert assessment == _json(EVIDENCE / "current-assessment.json")
    assert assessment["standing"] == "UNKNOWN"
    assert assessment["reasons"] == ["NO_HOLDOUT_EVIDENCE"]
    assert assessment["capitalAllocationAuthorized"] is False
    assert assessment["externalWriteAllowed"] is False


def test_prospective_split_and_source_identity_are_fixed_before_holdout() -> None:
    frozen = _json(EVIDENCE / "frozen-plan.json")
    p = frozen["plan"]
    request = _json(REQUEST)
    source = request["source"]
    assert p["trialsPlanned"] == request["policy"]["trialsDeclared"] == 1
    assert p["effectBoundary"] == "RESEARCH_ONLY"
    assert p["partitions"]["validation"]["end"] == request["policy"]["endDate"]
    assert p["partitions"]["holdout"] == {
        "start": "2026-11-09", "end": "2027-03-31",
    }
    assert p["frozenAt"].startswith("2026-11-08T")
    assert p["historicalSources"][0]["snapshotDigest"] == "sha256:" + source["sha256"]
    assert p["historicalSources"][0]["availableAt"] == source["commitAt"]
    assert p["configDigest"] == "sha256:" + hashlib.sha256(REQUEST.read_bytes()).hexdigest()


def test_actual_case_is_an_economic_tradeoff_not_fictional_alpha() -> None:
    finding = _json(EVIDENCE / "retrospective-result.json")
    cmp = finding["comparison"]
    assert finding["researchStanding"] == "RETROSPECTIVE_ONLY_NO_VERIFIED_ALPHA"
    assert finding["capitalAuthority"] == "NONE"
    assert finding["decision"] == "NO_VERIFIED_ACTIVE_EDGE_NO_ORDER"
    assert finding["sourceIdentity"]["originalMarketProviderAttested"] is False
    assert finding["sourceIdentity"]["historicalAsOfAttested"] is False
    assert finding["sourceIdentity"]["sha256"] == _json(REQUEST)["source"]["sha256"]
    assert cmp["portfolioWeightsBps"] == {"SPY": 6000, "SHY": 4000}
    assert cmp["returnPeriods"] == 400
    assert Decimal(cmp["strategyTerminalWealth"]) < Decimal(cmp["benchmarkTerminalWealth"])
    assert Decimal(cmp["strategyMaxDrawdown"]) < Decimal(cmp["benchmarkMaxDrawdown"])
    assert (
        Decimal(cmp["strategyTerminalWealth"]) - Decimal(cmp["benchmarkTerminalWealth"])
    ) == Decimal(cmp["terminalWealthDifference"])


def test_researcher_cannot_retroactively_add_new_market_info() -> None:
    plan = _json(EVIDENCE / "research-plan.json")
    forged = copy.deepcopy(plan)
    forged["historicalSources"][0]["availableAt"] = "2026-11-09T12:00:00Z"
    with pytest.raises(ExperimentContractError, match="unavailable at frozen research cut"):
        freeze_experiment_plan(forged)


def test_forged_already_complete_holdout_is_rejected_not_promoted() -> None:
    frozen = _json(EVIDENCE / "frozen-plan.json")
    fake = {
        "planDigest": frozen["planDigest"],
        "evaluatedAt": "2026-11-08T15:20:00Z",
        "observedThrough": "2026-08-10T20:00:00Z",
        "availableAt": "2026-08-20T21:41:22Z",
        "holdoutDigest": "sha256:" + "a" * 64,
        "trialsEvaluated": 1,
        "multiplicityControl": "DOCUMENTED",
        "costModelDigest": "sha256:" + "b" * 64,
        "benchmarkEvidenceDigest": "sha256:" + "c" * 64,
        "independentReproduction": True,
    }
    assessment = assess_holdout_evidence(frozen, fake)
    assert assessment["standing"] == "REJECTED"
    assert assessment["externalWriteAllowed"] is False
    assert assessment["capitalAllocationAuthorized"] is False


@pytest.mark.provider_qualification
def test_actual_github_source_independently_reproduces_economics() -> None:
    """Needs externally retrieved bytes; GitHub-host identity != price truth."""
    path = os.environ.get("ORDIVON_FINANCE_RESEARCH_SOURCE_CSV")
    if not path:
        pytest.skip("supply actual pinned GitHub CSV for provider qualification")
    raw = Path(path).read_bytes()
    request = _json(REQUEST)
    evidence = _json(EVIDENCE / "retrospective-result.json")
    source = evidence["sourceIdentity"]
    assert hashlib.sha256(raw).hexdigest() == source["sha256"]
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == source["gitBlobSha"]

    actual = replay_paper_investment(request=request, source_bytes=raw)
    cmp = evidence["comparison"]
    assert actual["replayedReturnPeriods"] == cmp["returnPeriods"]
    assert actual["replayId"] == evidence["sourceReplayId"]
    for old, new in [
        ("strategyTerminalWealth", "finalStrategyNAV"),
        ("benchmarkTerminalWealth", "finalBenchmarkNAV"),
        ("strategyMaxDrawdown", "strategyMaxDrawdown"),
        ("benchmarkMaxDrawdown", "benchmarkMaxDrawdown"),
    ]:
        assert Decimal(cmp[old]) == Decimal(actual[new])

    # Separate standard-library implementation, not Portfolio replay of itself.
    with localcontext() as ctx:
        ctx.prec = 42
        weights = {k: Decimal(v) / 10000 for k, v in cmp["portfolioWeightsBps"].items()}
        s_cost = Decimal(cmp["strategyAnnualExpenseFraction"]) / cmp["periodsPerYear"]
        b_cost = Decimal(cmp["benchmarkAnnualExpenseFraction"]) / cmp["periodsPerYear"]
        strategy = benchmark = Decimal(cmp["initialCapital"])
        strategy_peak = strategy
        benchmark_peak = benchmark
        strategy_dd = benchmark_dd = Decimal(0)
        previous = None
        periods = 0
        for row in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
            if not cmp["firstSession"] <= row["Date"] <= cmp["lastSession"]:
                continue
            if not row["SPY"] or not row["SHY"]:
                continue
            current = {key: Decimal(row[key]) for key in ("SPY", "SHY")}
            if previous is not None:
                gross = sum(
                    weights[k] * (current[k] / previous[k] - 1)
                    for k in sorted(weights)
                )
                benchmark_gross = current["SPY"] / previous["SPY"] - 1
                strategy = (strategy - strategy * s_cost) * (1 + gross)
                benchmark = (benchmark - benchmark * b_cost) * (1 + benchmark_gross)
                strategy_peak = max(strategy_peak, strategy)
                benchmark_peak = max(benchmark_peak, benchmark)
                strategy_dd = max(strategy_dd, 1 - strategy / strategy_peak)
                benchmark_dd = max(benchmark_dd, 1 - benchmark / benchmark_peak)
                periods += 1
            previous = current
        tolerance = Decimal("0.000001")
        assert periods == cmp["returnPeriods"]
        assert abs(strategy - Decimal(cmp["strategyTerminalWealth"])) < tolerance
        assert abs(benchmark - Decimal(cmp["benchmarkTerminalWealth"])) < tolerance
        assert abs(strategy_dd - Decimal(cmp["strategyMaxDrawdown"])) < tolerance
        assert abs(benchmark_dd - Decimal(cmp["benchmarkMaxDrawdown"])) < tolerance
