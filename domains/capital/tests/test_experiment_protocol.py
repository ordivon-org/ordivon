"""Research plan freezing and holdout admission: pure temporal/effect contracts."""

from __future__ import annotations

import copy

import pytest

from ordivon_capital.research.experiment_protocol import (
    ExperimentContractError,
    assess_holdout_evidence,
    freeze_experiment_plan,
)

SHA = "sha256:" + "a" * 64


def _plan() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.plan",
        "hypothesisId": "momentum-reversal-2026-11",
        "effectBoundary": "RESEARCH_ONLY",
        "frozenAt": "2026-01-01T12:00:00+00:00",
        "codeRevision": "a" * 40,
        "configDigest": SHA,
        "environmentDigest": SHA,
        "trialsPlanned": 2,
        "baselineId": "cash-and-hold",
        "metricDefinition": "net excess return after declared costs",
        "partitions": {
            "train": {"start": "2020-01-01", "end": "2022-12-31"},
            "validation": {"start": "2023-01-01", "end": "2025-12-31"},
            "holdout": {"start": "2026-01-02", "end": "2026-06-30"},
        },
        "historicalSources": [{
            "sourceId": "provider:equities",
            "snapshotDigest": SHA,
            "observedThrough": "2025-12-31T20:00:00+00:00",
            "availableAt": "2026-01-01T06:00:00+00:00",
        }],
    }


def _result(digest: str) -> dict:
    return {
        "planDigest": digest,
        "evaluatedAt": "2026-07-02T12:00:00+00:00",
        "observedThrough": "2026-06-30T21:00:00+00:00",
        "availableAt": "2026-07-01T06:00:00+00:00",
        "holdoutDigest": SHA,
        "trialsEvaluated": 2,
        "multiplicityControl": "DOCUMENTED",
        "costModelDigest": SHA,
        "benchmarkEvidenceDigest": SHA,
        "independentReproduction": True,
    }


def test_canonical_digest_is_order_independent_and_replayable() -> None:
    plan = _plan()
    reordered = dict(reversed(list(plan.items())))
    assert freeze_experiment_plan(plan)["planDigest"] == (
        freeze_experiment_plan(reordered)["planDigest"]
    )


@pytest.mark.parametrize("field,value", [
    ("frozenAt", "2026-01-01T12:00:00"),
    ("effectBoundary", "LIVE"),
    ("trialsPlanned", True),
    ("configDigest", "sha256:xx"),
])
def test_bad_freeze_contract_is_rejected(field: str, value: object) -> None:
    plan = _plan()
    plan[field] = value
    with pytest.raises(ExperimentContractError):
        freeze_experiment_plan(plan)


def test_historical_data_after_freeze_is_not_admitted() -> None:
    plan = _plan()
    plan["historicalSources"][0]["availableAt"] = "2026-01-02T06:00:00+00:00"
    with pytest.raises(ExperimentContractError):
        freeze_experiment_plan(plan)


def test_overlapping_holdout_is_rejected() -> None:
    plan = _plan()
    plan["partitions"]["holdout"]["start"] = "2025-12-31"
    with pytest.raises(ExperimentContractError):
        freeze_experiment_plan(plan)


def test_no_evidence_remains_unknown_with_no_order_authority() -> None:
    result = assess_holdout_evidence(freeze_experiment_plan(_plan()), None)
    assert result["standing"] == "UNKNOWN"
    assert result["externalWriteAllowed"] is False


def test_disclosed_complete_experiment_requires_separate_review() -> None:
    frozen = freeze_experiment_plan(_plan())
    result = assess_holdout_evidence(frozen, _result(frozen["planDigest"]))
    assert result["standing"] == "REVIEW_REQUIRED"
    assert result["capitalAllocationAuthorized"] is False


def test_multiple_testing_not_documented_remains_unknown() -> None:
    frozen = freeze_experiment_plan(_plan())
    result = _result(frozen["planDigest"])
    result["multiplicityControl"] = "UNKNOWN"
    assert assess_holdout_evidence(frozen, result)["standing"] == "UNKNOWN"


def test_temporal_contradiction_is_rejected_not_unknown() -> None:
    frozen = freeze_experiment_plan(_plan())
    result = _result(frozen["planDigest"])
    result["observedThrough"] = "2026-01-02T00:00:00+00:00"
    assert assess_holdout_evidence(frozen, result)["standing"] == "REJECTED"


def test_unreproducible_result_is_rejected() -> None:
    frozen = freeze_experiment_plan(_plan())
    result = _result(frozen["planDigest"])
    result["independentReproduction"] = False
    assert assess_holdout_evidence(frozen, result)["standing"] == "REJECTED"


def test_frozen_identity_tampering_is_rejected() -> None:
    frozen = freeze_experiment_plan(_plan())
    tampered = copy.deepcopy(frozen)
    tampered["plan"]["trialsPlanned"] = 1
    assert assess_holdout_evidence(tampered, None)["standing"] == "REJECTED"


def test_utc_freeze_day_prevents_cross_timezone_holdout_leakage() -> None:
    plan = _plan()
    # Local 2026-01-01 is already UTC Jan 2; the Jan 2 holdout is not future.
    plan["frozenAt"] = "2026-01-01T23:00:00-12:00"
    with pytest.raises(ExperimentContractError, match="after the freeze date"):
        freeze_experiment_plan(plan)


def test_utc_holdout_observation_day_prevents_cross_timezone_admission() -> None:
    frozen = freeze_experiment_plan(_plan())
    evidence = _result(frozen["planDigest"])
    # Local June 30 is UTC June 29; the declared June 30 holdout is unfinished.
    evidence["observedThrough"] = "2026-06-30T00:30:00+14:00"
    assert assess_holdout_evidence(frozen, evidence)["standing"] == "REJECTED"


def test_extra_permission_claim_is_not_forwarded_by_a_frozen_plan() -> None:
    plan = _plan()
    plan["allowExternalWrite"] = True
    with pytest.raises(ExperimentContractError, match="plan keys"):
        freeze_experiment_plan(plan)


def test_forged_frozen_receipt_authority_is_rejected() -> None:
    frozen = freeze_experiment_plan(_plan())
    forged = copy.deepcopy(frozen)
    forged["authority"] = "TRADE"
    assessed = assess_holdout_evidence(forged, _result(frozen["planDigest"]))
    assert assessed["standing"] == "REJECTED"
    assert assessed["externalWriteAllowed"] is False


def test_undeclared_positive_economic_claim_cannot_promote_review() -> None:
    frozen = freeze_experiment_plan(_plan())
    evidence = _result(frozen["planDigest"])
    evidence["independentProfitProof"] = True
    assessed = assess_holdout_evidence(frozen, evidence)
    assert assessed["standing"] == "UNKNOWN"
