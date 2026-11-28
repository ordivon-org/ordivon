"""Actual Finance Research consumer: precommit -> source replay -> bounded review."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from ordivon_capital.research.experiment_protocol import (
    candidate_policy_digest,
    freeze_experiment_plan,
    review_replayed_candidate,
)

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/finance_lego.py"


def _bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _fixture() -> tuple[dict, dict, list, list]:
    identity = "sha256:" + "b" * 64
    source = [
        {
            "periodEndAt": "2026-01-31T20:00:00Z",
            "availableAt": "2026-02-01T06:00:00Z",
            "assetGrossReturn": "0.10",
            "cashGrossReturn": "0",
            "benchmarkGrossReturn": "0.03",
        },
        {
            "periodEndAt": "2026-02-28T20:00:00Z",
            "availableAt": "2026-03-01T05:00:00Z",
            "assetGrossReturn": "-0.10",
            "cashGrossReturn": "0",
            "benchmarkGrossReturn": "0.01",
        },
    ]
    holdout = [
        {
            "periodEndAt": "2026-01-31T20:00:00Z",
            "availableAt": "2026-02-01T10:00:00Z",
            "strategyGrossReturn": "0.050",
            "benchmarkNetReturn": "0.029",
            "fees": "0.001",
            "slippage": "0.001",
            "financing": "0",
            "taxes": "0",
        },
        {
            "periodEndAt": "2026-02-28T20:00:00Z",
            "availableAt": "2026-03-01T10:00:00Z",
            "strategyGrossReturn": "-0.050",
            "benchmarkNetReturn": "0.009",
            "fees": "0.001",
            "slippage": "0.001",
            "financing": "0",
            "taxes": "0",
        },
    ]
    manifest = {
        "schemaVersion": 2,
        "kind": "ordivon.capital.finance.replayable-research-candidate",
        "candidateId": "test-precommitted-momentum",
        "hypothesis": "constant half allocation versus cash",
        "frozenAt": "2026-01-01T12:00:00+00:00",
        "trialCount": 2,
        "currency": "USD",
        "costCoverage": ["fees", "slippage", "financing", "taxes"],
        "strategyAssetWeight": "0.5",
        "benchmarkExpenseFraction": "0.001",
        "featureDataLatestAvailableAt": "2025-12-31T18:00:00Z",
        "sourceSha256": hashlib.sha256(_bytes(source)).hexdigest(),
        "holdoutSha256": hashlib.sha256(_bytes(holdout)).hexdigest(),
    }
    plan = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.plan",
        "hypothesisId": manifest["candidateId"],
        "effectBoundary": "RESEARCH_ONLY",
        "frozenAt": manifest["frozenAt"],
        "codeRevision": "a" * 40,
        "configDigest": candidate_policy_digest(manifest),
        "environmentDigest": identity,
        "trialsPlanned": 2,
        "baselineId": "index-net-of-expense",
        "metricDefinition": "strategy vs index, after per-period stated costs",
        "partitions": {
            "train": {"start": "2020-01-01", "end": "2022-12-31"},
            "validation": {"start": "2023-01-01", "end": "2025-12-31"},
            "holdout": {"start": "2026-01-02", "end": "2026-02-28"},
        },
        "historicalSources": [{
            "sourceId": "synthetic-pre-freeze-training-source",
            "snapshotDigest": identity,
            "observedThrough": "2025-12-31T18:00:00Z",
            "availableAt": "2025-12-31T19:00:00Z",
        }],
    }
    return plan, manifest, source, holdout


def _run(plan: dict, manifest: dict, source: list, holdout: list) -> dict:
    return review_replayed_candidate(
        frozen=freeze_experiment_plan(plan),
        manifest=manifest,
        source_bytes=_bytes(source),
        holdout_bytes=_bytes(holdout),
        evaluated_at="2026-03-02T12:00:00Z",
    )


def test_real_source_replay_composes_without_grant_or_independent_attestation() -> None:
    plan, manifest, source, holdout = _fixture()
    result = _run(plan, manifest, source, holdout)
    assert result["standing"] == "UNKNOWN"
    assert result["sourceToReturnRecomputationVerified"] is True
    assert result["capitalAuthority"] == "NONE"
    assert result["externalWriteAllowed"] is False
    assert "INDEPENDENT_REPRODUCTION_UNKNOWN" in result["reasons"]
    assert result["economicSummary"]["strategyNetGrowth"] != "1"


def test_policy_reweighting_after_holdout_is_rejected_even_when_recommitted() -> None:
    plan, manifest, source, holdout = _fixture()
    manifest["strategyAssetWeight"] = "1"
    holdout[0]["strategyGrossReturn"] = "0.10"
    holdout[1]["strategyGrossReturn"] = "-0.10"
    manifest["holdoutSha256"] = hashlib.sha256(_bytes(holdout)).hexdigest()
    result = _run(plan, manifest, source, holdout)
    assert result["standing"] == "REJECTED"
    assert "PRECOMMITTED_POLICY_MISMATCH" in result["reasons"]


def test_recomputed_false_alphas_rejected_even_with_new_holdout_digest() -> None:
    plan, manifest, source, holdout = _fixture()
    holdout[0]["strategyGrossReturn"] = "0.9"
    manifest["holdoutSha256"] = hashlib.sha256(_bytes(holdout)).hexdigest()
    result = _run(plan, manifest, source, holdout)
    assert result["standing"] == "REJECTED"
    assert "SOURCE_REPLAY_OR_POLICY_INVALID" in result["reasons"]


def test_trial_family_change_not_accepted() -> None:
    plan, manifest, source, holdout = _fixture()
    manifest["trialCount"] = 4
    result = _run(plan, manifest, source, holdout)
    assert result["standing"] == "REJECTED"
    assert "TRIAL_FAMILY_CHANGED_AFTER_FREEZE" in result["reasons"]


def test_insufficient_future_holdout_remains_unknown() -> None:
    plan, manifest, source, holdout = _fixture()
    source, holdout = source[:1], holdout[:1]
    manifest["sourceSha256"] = hashlib.sha256(_bytes(source)).hexdigest()
    manifest["holdoutSha256"] = hashlib.sha256(_bytes(holdout)).hexdigest()
    result = _run(plan, manifest, source, holdout)
    assert result["standing"] == "UNKNOWN"
    assert result["reasons"] == ["PROSPECTIVE_HOLDOUT_INCOMPLETE"]


def test_freeze_and_candidate_time_must_be_same_instant() -> None:
    plan, manifest, source, holdout = _fixture()
    manifest["frozenAt"] = "2026-01-01T11:00:00Z"
    result = _run(plan, manifest, source, holdout)
    assert result["standing"] == "REJECTED"
    assert result["reasons"] == ["FREEZE_TIME_IDENTITY_MISMATCH"]


def test_forged_frozen_evidence_is_rejected_without_economics() -> None:
    plan, manifest, source, holdout = _fixture()
    frozen = freeze_experiment_plan(plan)
    forged = copy.deepcopy(frozen)
    forged["authority"] = "TRADE"
    result = review_replayed_candidate(
        frozen=forged, manifest=manifest, source_bytes=_bytes(source),
        holdout_bytes=_bytes(holdout), evaluated_at="2026-03-02T12:00:00Z",
    )
    assert result["standing"] == "REJECTED"
    assert "economicSummary" not in result


def test_policy_digest_is_stable_across_semantically_equal_timezones() -> None:
    plan, manifest, source, holdout = _fixture()
    altered = dict(manifest, frozenAt="2026-01-01T20:00:00+08:00",
                   strategyAssetWeight="0.50")
    assert candidate_policy_digest(altered) == plan["configDigest"]


def test_precommitment_digest_is_exact_for_high_precision_weights() -> None:
    from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext

    plan, manifest, source, holdout = _fixture()
    first = dict(manifest, strategyAssetWeight="0.1234567890123456789012345678901234567890")
    changed = dict(manifest, strategyAssetWeight="0.1234567890123456789012345678901234567891")
    assert Decimal(first["strategyAssetWeight"]) != Decimal(changed["strategyAssetWeight"])
    first_digest = candidate_policy_digest(first)
    assert first_digest != candidate_policy_digest(changed)

    # Adding insignificant zeros changes the byte spelling, not the policy.
    equivalent = dict(first, strategyAssetWeight=first["strategyAssetWeight"] + "0000")
    assert candidate_policy_digest(equivalent) == first_digest
    assert candidate_policy_digest(dict(manifest, strategyAssetWeight="0.5000")) == (
        candidate_policy_digest(manifest)
    )
    # Neither caller precision nor caller rounding mode can change the digest.
    for precision, rounding in ((2, ROUND_DOWN), (2, ROUND_UP), (70, ROUND_DOWN)):
        with localcontext() as context:
            context.prec = precision
            context.rounding = rounding
            assert candidate_policy_digest(first) == first_digest
            assert candidate_policy_digest(changed) != first_digest

    # Actual frozen source-replay consumer must reject modifying an admitted
    # high-precision weight, even if market arithmetic later rounds to 28 digits.
    plan["configDigest"] = first_digest
    result = _run(plan, changed, source, holdout)
    assert result["standing"] == "REJECTED"
    assert result["reasons"] == ["PRECOMMITTED_POLICY_MISMATCH"]


def test_precommitment_digest_is_exact_for_high_precision_benchmark_cost() -> None:
    _, manifest, _, _ = _fixture()
    left = dict(manifest, benchmarkExpenseFraction="0.000000000000000000000000000000001")
    right = dict(manifest, benchmarkExpenseFraction="0.000000000000000000000000000000002")
    assert candidate_policy_digest(left) != candidate_policy_digest(right)
    assert candidate_policy_digest(dict(left, benchmarkExpenseFraction="1e-33")) == (
        candidate_policy_digest(left)
    )


def test_cli_fingerprint_freeze_review_full_composition(tmp_path: Path) -> None:
    plan, manifest, source, holdout = _fixture()
    for filename, payload in (
        ("manifest.json", manifest),
        ("source.json", source),
        ("holdout.json", holdout),
    ):
        (tmp_path / filename).write_bytes(_bytes(payload))
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))

    def invoke(op: str, obj: dict, *args: str) -> dict:
        proc = subprocess.run(
            [sys.executable, str(CLI), op, *args],
            input=json.dumps(obj), cwd=ROOT, env=env,
            capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 0, proc.stderr
        return json.loads(proc.stdout)

    fingerprint = invoke("fingerprint-policy", manifest)
    assert fingerprint["configDigest"] == plan["configDigest"]
    frozen = invoke("freeze-experiment", plan)
    assessed = invoke(
        "review-candidate",
        {"frozen": frozen, "evaluatedAt": "2026-03-02T12:00:00Z"},
        "--manifest", str(tmp_path / "manifest.json"),
        "--source", str(tmp_path / "source.json"),
        "--holdout", str(tmp_path / "holdout.json"),
    )
    assert assessed["standing"] == "UNKNOWN"
    assert assessed["sourceToReturnRecomputationVerified"] is True
    assert assessed["capitalAuthority"] == "NONE"
