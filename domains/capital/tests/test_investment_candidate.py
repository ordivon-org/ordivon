"""Exact consumer checks: only evidence envelopes, never capital grants."""

import hashlib
import json
from copy import deepcopy

import pytest

from ordivon_capital.research.investment_candidate import (
    CandidateEvidenceError,
    evaluate_investment_candidate,
)

SOURCE = b'{"synthetic": true, "not-a-market-claim": true}\n'
ROWS = [
    {
        "periodEndAt": "2026-11-02T00:00:00+00:00",
        "availableAt": "2026-11-02T00:00:01+00:00",
        "strategyGrossReturn": "0.03",
        "benchmarkNetReturn": "0.01",
        "fees": "0.001",
        "slippage": "0.002",
        "financing": "0",
        "taxes": "0",
    },
    {
        "periodEndAt": "2026-11-03T00:00:00+00:00",
        "availableAt": "2026-11-03T00:00:01+00:00",
        "strategyGrossReturn": "-0.01",
        "benchmarkNetReturn": "0.00",
        "fees": "0.001",
        "slippage": "0.001",
        "financing": "0",
        "taxes": "0",
    },
]


def evidence(rows=None):
    raw = json.dumps(ROWS if rows is None else rows, sort_keys=True).encode()
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.capital.finance.frozen-research-candidate",
        "candidateId": "synthetic-research-001",
        "hypothesis": "Synthetic development fixture, not an investment claim",
        "frozenAt": "2026-11-01T00:00:00+00:00",
        "featureDataLatestAvailableAt": "2026-10-31T23:00:00+00:00",
        "sourceSha256": hashlib.sha256(SOURCE).hexdigest(),
        "holdoutSha256": hashlib.sha256(raw).hexdigest(),
        "trialCount": 12,
        "currency": "USD",
        "costCoverage": ["fees", "slippage", "financing", "taxes"],
    }
    return manifest, raw


def run(manifest=None, source=SOURCE, holdout=None):
    original, encoded = evidence()
    return evaluate_investment_candidate(
        manifest=original if manifest is None else manifest,
        source_bytes=source,
        holdout_bytes=encoded if holdout is None else holdout,
    )


def test_deterministic_compounded_benchmark_and_no_capital_authority():
    first = run()
    assert first == run()
    assert first["standing"] == "STRUCTURALLY_REVIEWABLE_NOT_INDEPENDENTLY_VERIFIED"
    assert first["capitalAuthority"] == "NONE"
    assert first["economicSummary"]["strategyNetGrowth"] == "1.014676"
    assert first["economicSummary"]["benchmarkNetGrowth"] == "1.0100"
    assert first["declaredTrials"] == 12
    assert first["statisticalGeneralizationVerified"] is False


@pytest.mark.parametrize(
    "change",
    [
        {"featureDataLatestAvailableAt": "2026-11-02T00:00:00+00:00"},
        {"frozenAt": "2026-11-01T00:00:00"},
        {"trialCount": True},
        {"trialCount": 0},
        {"costCoverage": ["fees", "slippage", "taxes"]},
        {"costCoverage": [{"unhashable": "bad"}]},
        {"currency": "usd"},
        {"sourceSha256": "bad"},
        {"holdoutSha256": "0" * 64},
        {"kind": "ordivon.capital.finance.order-intent"},
    ],
)
def test_invalid_candidate_manifest_is_rejected(change):
    manifest, raw = evidence()
    manifest.update(change)
    with pytest.raises(CandidateEvidenceError):
        run(manifest=manifest, holdout=raw)


def test_uncommitted_source_bytes_are_rejected():
    with pytest.raises(CandidateEvidenceError, match="source bytes differ"):
        run(source=SOURCE + b"x")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows[0].update({"periodEndAt": "2026-10-31T00:00:00+00:00"}),
        lambda rows: rows[1].update({"periodEndAt": rows[0]["periodEndAt"]}),
        lambda rows: rows[0].update({"availableAt": "2026-11-01T00:00:00+00:00"}),
        lambda rows: rows[0].update({"fees": "-0.001"}),
        lambda rows: rows[0].update({"strategyGrossReturn": "NaN"}),
        lambda rows: rows[0].update({"benchmarkNetReturn": "-1.1"}),
        lambda rows: rows[0].update({"slippage": 0.0}),
        lambda rows: rows[0].update({"unknownTradePermission": True}),
    ],
)
def test_committed_but_invalid_holdout_is_rejected(mutate):
    rows = deepcopy(ROWS)
    mutate(rows)
    manifest, raw = evidence(rows)
    with pytest.raises(CandidateEvidenceError):
        run(manifest=manifest, holdout=raw)


def test_missing_or_malformed_holdout_rejected():
    for rows in ([], {}, [{"periodEndAt": "x"}]):
        manifest, raw = evidence(rows)
        with pytest.raises(CandidateEvidenceError):
            run(manifest=manifest, holdout=raw)


def test_raw_replay_fails_sha256_identity():
    manifest, _ = evidence()
    with pytest.raises(CandidateEvidenceError, match="source bytes differ"):
        run(manifest=manifest, holdout=b"[]")


def test_all_loss_benchmark_ratio_is_unknown_not_fake_positive():
    rows = deepcopy(ROWS)
    rows[0]["benchmarkNetReturn"] = "-1"
    manifest, raw = evidence(rows)
    out = run(manifest=manifest, holdout=raw)
    assert out["economicSummary"]["relativeGrowth"] is None
    assert out["capitalAuthority"] == "NONE"
