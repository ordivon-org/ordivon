"""A falsification consumer for source-to-return recomputation (not source truth)."""

import hashlib
import json
from copy import deepcopy

import pytest

from ordivon_capital.research.investment_candidate import (
    CandidateEvidenceError,
    evaluate_investment_candidate,
)

MARKET_ROWS = [
    {
        "periodEndAt": "2026-11-02T00:00:00+00:00",
        "availableAt": "2026-11-02T00:00:01+00:00",
        "assetGrossReturn": "0.04",
        "cashGrossReturn": "0.00",
        "benchmarkGrossReturn": "0.02",
    },
    {
        "periodEndAt": "2026-11-03T00:00:00+00:00",
        "availableAt": "2026-11-03T00:00:01+00:00",
        "assetGrossReturn": "-0.02",
        "cashGrossReturn": "0.00",
        "benchmarkGrossReturn": "-0.01",
    },
]

HOLDOUT = [
    {
        "periodEndAt": "2026-11-02T00:00:00+00:00",
        "availableAt": "2026-11-02T00:00:01+00:00",
        "strategyGrossReturn": "0.01",
        "benchmarkNetReturn": "0.019",
        "fees": "0.001",
        "slippage": "0",
        "financing": "0",
        "taxes": "0",
    },
    {
        "periodEndAt": "2026-11-03T00:00:00+00:00",
        "availableAt": "2026-11-03T00:00:01+00:00",
        "strategyGrossReturn": "-0.005",
        "benchmarkNetReturn": "-0.011",
        "fees": "0.001",
        "slippage": "0",
        "financing": "0",
        "taxes": "0",
    },
]


def candidate(markets=None, returns=None, extra=None):
    src = json.dumps(MARKET_ROWS if markets is None else markets, sort_keys=True).encode()
    out = json.dumps(HOLDOUT if returns is None else returns, sort_keys=True).encode()
    manifest = {
        "schemaVersion": 2,
        "kind": "ordivon.capital.finance.replayable-research-candidate",
        "candidateId": "synthetic-replay",
        "hypothesis": "Fixed 25% exposure to a synthetic asset",
        "frozenAt": "2026-11-01T00:00:00+00:00",
        "featureDataLatestAvailableAt": "2026-10-31T00:00:00+00:00",
        "sourceSha256": hashlib.sha256(src).hexdigest(),
        "holdoutSha256": hashlib.sha256(out).hexdigest(),
        "trialCount": 3,
        "currency": "USD",
        "costCoverage": ["fees", "slippage", "financing", "taxes"],
        "strategyAssetWeight": "0.25",
        "benchmarkExpenseFraction": "0.001",
    }
    if extra:
        manifest.update(extra)
    return manifest, src, out


def replay(markets=None, returns=None, extra=None):
    manifest, src, out = candidate(markets, returns, extra)
    return evaluate_investment_candidate(
        manifest=manifest, source_bytes=src, holdout_bytes=out
    )


def test_source_to_holdout_recomputed_with_frozen_weight():
    answer = replay()
    assert answer["schemaVersion"] == 2
    assert answer["standing"] == "SOURCE_REPLAYED_PROVIDER_NOT_ATTESTED"
    assert answer["sourceToReturnRecomputationVerified"] is True
    assert answer["sourceObservationProvenanceVerified"] is False
    assert answer["freezeAttestationVerified"] is False
    assert answer["capitalAuthority"] == "NONE"
    assert answer["holdoutPeriods"] == 2
    assert answer["economicSummary"]["strategyNetGrowth"] == "1.002946"


@pytest.mark.parametrize(
    "mutator",
    [
        lambda rows: rows[0].update({"strategyGrossReturn": "0.05"}),
        lambda rows: rows[1].update({"benchmarkNetReturn": "0.01"}),
        lambda rows: rows[1].update({"strategyGrossReturn": "-0.004"}),
    ],
)
def test_committed_but_false_return_claims_are_rejected(mutator):
    rows = deepcopy(HOLDOUT)
    mutator(rows)
    with pytest.raises(CandidateEvidenceError, match="source"):
        replay(returns=rows)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda rows: rows[1].update({"periodEndAt": rows[0]["periodEndAt"]}),
        lambda rows: rows[1].update({"availableAt": "2026-11-04T00:00:00+00:00"}),
        lambda rows: rows[0].update({"benchmarkGrossReturn": "NaN"}),
        lambda rows: rows[0].update({"assetGrossReturn": "-1.1"}),
        lambda rows: rows[0].update({"unexpected": "orders"}),
    ],
)
def test_source_time_and_type_mismatches_are_rejected(mutator):
    rows = deepcopy(MARKET_ROWS)
    mutator(rows)
    with pytest.raises(CandidateEvidenceError):
        replay(markets=rows)


@pytest.mark.parametrize("weight", ["1.1", "-0.1", "NaN", 0.25])
def test_weight_out_of_range_or_not_decimal_rejected(weight):
    with pytest.raises(CandidateEvidenceError):
        replay(extra={"strategyAssetWeight": weight})


def test_source_and_holdout_different_cardinality_rejected():
    with pytest.raises(CandidateEvidenceError, match="same length"):
        replay(markets=MARKET_ROWS[:1])


def test_earlier_source_publish_than_close_rejected_even_if_hash_matches():
    src = deepcopy(MARKET_ROWS)
    src[0]["availableAt"] = "2026-11-01T00:00:00+00:00"
    with pytest.raises(CandidateEvidenceError):
        replay(markets=src)


def test_v1_still_only_checks_envelope_not_false_verification():
    # V1 remains an intentionally weaker compatibility contract.
    old_src = b'{"arbitrary":true}'
    old_holdout = json.dumps(HOLDOUT, sort_keys=True).encode()
    manifest, _, _ = candidate()
    manifest.pop("strategyAssetWeight")
    manifest.pop("benchmarkExpenseFraction")
    manifest.update({
        "schemaVersion": 1,
        "kind": "ordivon.capital.finance.frozen-research-candidate",
        "sourceSha256": hashlib.sha256(old_src).hexdigest(),
        "holdoutSha256": hashlib.sha256(old_holdout).hexdigest(),
    })
    out = evaluate_investment_candidate(
        manifest=manifest, source_bytes=old_src, holdout_bytes=old_holdout
    )
    assert out["sourceToReturnRecomputationVerified"] is False
    assert out["capitalAuthority"] == "NONE"
