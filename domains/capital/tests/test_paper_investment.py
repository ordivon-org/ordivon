"""Consumer tests for a GitHub-byte-bound, offline virtual-capital replay."""

import hashlib
import json
from pathlib import Path

import pytest

from ordivon_capital.portfolio.paper_investment import (
    PaperInvestmentError,
    replay_paper_investment,
)

SOURCE = (
    b"Date,SPY,SHY\n"
    b"2025-01-02,100,100\n"
    b"2025-01-03,110,100\n"
    b"2025-01-04,,\n"  # no quotes: do not invent a fill or a daily return
    b"2025-01-06,100,100\n"
)


def make_request(source=SOURCE):
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.paper.replay-request",
        "source": {
            "repository": "fixture/public-data",
            "commit": "1" * 40,
            "commitAt": "2025-01-07T00:00:00Z",
            "path": "daily_adjclose.csv",
            "sha256": hashlib.sha256(source).hexdigest(),
            "gitBlobSha": blob,
            "originStanding": "UNVERIFIED_UPSTREAM_MARKET_PROVENANCE",
        },
        "policy": {
            "startDate": "2025-01-02",
            "endDate": "2025-01-06",
            "startingCapital": "1000",
            "currency": "USD",
            "weightsBps": {"SPY": 5000, "SHY": 5000},
            "benchmarkSymbol": "SPY",
            "strategyAnnualExpenseFraction": "0",
            "benchmarkAnnualExpenseFraction": "0",
            "periodsPerYear": 252,
            "trialsDeclared": 1,
        },
    }


def run(source=SOURCE, request=None):
    return replay_paper_investment(
        request=make_request(source) if request is None else request,
        source_bytes=source,
    )


def test_virtual_wealth_daily_marks_and_passive_reference_agree():
    output = run()
    assert output["standing"] == "RETROSPECTIVE_PAPER_REPLAY_NO_FORWARD_EDGE_CLAIM"
    assert output["capitalAuthority"] == "SIMULATION_ONLY"
    assert output["realMoneyOrders"] == 0
    assert output["providerPriceAuthenticityVerified"] is False
    assert output["gitBlobBytesVerified"] is True
    assert output["sourceSha256Verified"] is True
    assert output["replayedReturnPeriods"] == 2
    assert output["skippedNoQuoteDates"] == ["2025-01-04"]
    assert output["dailySettlements"][0]["strategyNAV"] == "1000"
    assert output["dailySettlements"][1]["strategyNAV"] == "1050.00"
    assert output["dailySettlements"][-1]["benchmarkNAV"] == "1000.000000000000000000000000"
    assert output["finalStrategyNAV"] == output["dailySettlements"][-1]["strategyNAV"]
    assert output["finalBenchmarkNAV"] == output["dailySettlements"][-1]["benchmarkNAV"]
    assert output["finalCashNAV"] == "1000"
    assert run() == output


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["policy"].update({"weightsBps": {"SPY": 9000, "SHY": 2000}}),
        lambda d: d["policy"].update({"weightsBps": {"SPY": True, "SHY": 10000}}),
        lambda d: d["policy"].update({"startingCapital": "NaN"}),
        lambda d: d["policy"].update({"periodsPerYear": 0}),
        lambda d: d["policy"].update({"trialsDeclared": 0}),
        lambda d: d["policy"].update({"endDate": "2025-01-07"}),
        lambda d: d["source"].update({"sha256": "0" * 64}),
        lambda d: d["source"].update({"gitBlobSha": "0" * 40}),
        lambda d: d["source"].update({"originStanding": "PROVIDER_VERIFIED"}),
        lambda d: d.update({"broker": "LIVE"}),
    ],
)
def test_unsupported_claims_or_policies_rejected(mutate):
    request = make_request()
    mutate(request)
    with pytest.raises(PaperInvestmentError):
        run(request=request)


@pytest.mark.parametrize(
    "source",
    [
        b"Date,SPY,SHY\n2025-01-02,100,100\n2025-01-03,110,\n2025-01-06,100,100\n",
        b"Date,SPY,SHY\n2025-01-02,100,100\n2025-01-03,-1,100\n2025-01-06,100,100\n",
        b"Date,SPY,SHY\n2025-01-02,100,100\n2025-01-02,100,100\n2025-01-06,100,100\n",
        b"Date,SPY,SHY\n2025-01-02,100,100\n2025-01-03,110,NaN\n2025-01-06,100,100\n",
        b"Date,SPY,SHY\n2025-01-02,100,100\n2025-01-03,110,100\n2025-01-06,,\n",
    ],
)
def test_unpriced_partial_bad_order_or_empty_terminal_rejected(source):
    with pytest.raises(PaperInvestmentError):
        run(source=source)


def test_byte_identity_binds_price_changes_even_if_csv_schema_valid():
    bad_source = SOURCE.replace(b"110,100", b"180,100")
    with pytest.raises(PaperInvestmentError, match="digest"):
        run(source=bad_source, request=make_request())


def test_source_publication_is_not_mistaken_for_precommitted_historical_test():
    out = run()
    assert out["sourceCommitClaimVerifiedExternally"] is False
    assert out["prospectiveHoldoutVerified"] is False
    assert out["trialsDeclared"] == 1
    assert out["historicalDataPublishedAfterReplayStart"] is True


def test_nonzero_expenses_reduce_nav_without_broker_orders():
    request = make_request()
    request["policy"]["strategyAnnualExpenseFraction"] = "0.252"
    out = run(request=request)
    assert float(out["finalStrategyNAV"]) < float(run()["finalStrategyNAV"])
    assert out["realMoneyOrders"] == 0


def test_cli_writes_paper_receipt_only_to_explicit_file(tmp_path: Path):
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    req = tmp_path / "request.json"
    data = tmp_path / "source.csv"
    receipt = tmp_path / "simulation.json"
    req.write_text(json.dumps(make_request()))
    data.write_bytes(SOURCE)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_capital.portfolio.paper_investment",
            "--request",
            str(req),
            "--source",
            str(data),
            "--output",
            str(receipt),
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    result_json = json.loads(result.stdout)
    assert result_json["receiptWritten"] is True
    assert json.loads(receipt.read_text())["finalStrategyNAV"] == run()["finalStrategyNAV"]


def test_cli_rejects_duplicate_policy_keys(tmp_path: Path):
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    req = tmp_path / "bad.json"
    req.write_text('{"schemaVersion":1,"schemaVersion":2}')
    data = tmp_path / "source.csv"
    data.write_bytes(SOURCE)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ordivon_capital.portfolio.paper_investment",
            "--request",
            str(req),
            "--source",
            str(data),
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["standing"] == "REJECTED"
