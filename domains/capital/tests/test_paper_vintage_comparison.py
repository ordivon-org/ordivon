"""Consumer: identical paper policy, two committed historical close vintages."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from ordivon_capital.portfolio.paper_vintage import (
    PaperVintageError,
    compare_paper_vintages,
)

BASE = (
    b"Date,SPY,SHY\n"
    b"2025-01-02,100,100\n"
    b"2025-01-03,110,100\n"
    b"2025-01-06,100,100\n"
)
REVISED = BASE.replace(b"2025-01-03,110,100", b"2025-01-03,120,100")
DIFFERENT_DATES = BASE.replace(
    b"2025-01-03,110,100\n",
    b"2025-01-03,,\n",
)


def _request(raw: bytes, *, commit: str) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.paper.replay-request",
        "source": {
            "repository": "fixture/marketdata",
            "commit": commit,
            "commitAt": "2026-08-20T21:41:22Z",
            "path": "daily_adjclose.csv",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "gitBlobSha": hashlib.sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest(),
            "originStanding": "UNVERIFIED_UPSTREAM_MARKET_PROVENANCE",
        },
        "policy": {
            "startDate": "2025-01-02",
            "endDate": "2025-01-06",
            "startingCapital": "100000",
            "currency": "USD",
            "weightsBps": {"SPY": 6000, "SHY": 4000},
            "benchmarkSymbol": "SHY",
            "strategyAnnualExpenseFraction": "0",
            "benchmarkAnnualExpenseFraction": "0",
            "periodsPerYear": 252,
            "trialsDeclared": 1,
        },
    }


def compare(a: bytes = BASE, b: bytes = REVISED) -> dict:
    return compare_paper_vintages(
        reference_request=_request(a, commit="1" * 40),
        reference_source_bytes=a,
        candidate_request=_request(b, commit="2" * 40),
        candidate_source_bytes=b,
    )


def test_revised_close_shows_material_retroactive_nav_difference() -> None:
    report = compare()
    assert report["standing"] == "COMPARABLE_RETROSPECTIVE_ONLY"
    assert report["sourceBytesChanged"] is True
    assert report["strategyTerminalWealthDelta"] != "0"
    assert report["benchmarkTerminalWealthDelta"] == "0"
    assert report["changedStrategySettlementDates"] == [
        "2025-01-03", "2025-01-06",
    ]
    assert report["capitalAuthority"] == "SIMULATION_ONLY"
    assert report["pointInTimeVintagesAttested"] is False
    assert report["providerPriceAuthenticityVerified"] is False
    assert report["prospectivePerformanceVerified"] is False


def test_identical_bytes_do_not_invent_corrections() -> None:
    report = compare(BASE, BASE)
    assert report["standing"] == "COMPARABLE_RETROSPECTIVE_ONLY"
    assert report["sourceBytesChanged"] is False
    assert report["strategyTerminalWealthDelta"] == "0"
    assert report["changedStrategySettlementDates"] == []


def test_changed_session_coverage_does_not_report_false_return_delta() -> None:
    report = compare(BASE, DIFFERENT_DATES)
    assert report["standing"] == "INCOMPARABLE_SESSION_COVERAGE"
    assert report["onlyReferenceSessions"] == ["2025-01-03"]
    assert report["onlyCandidateSessions"] == []
    assert "strategyTerminalWealthDelta" not in report


@pytest.mark.parametrize("mutation", [
    lambda r: r["policy"]["weightsBps"].update({"SPY": 7000, "SHY": 3000}),
    lambda r: r["source"].update({"repository": "other/mirror"}),
    lambda r: r["source"].update({"path": "other.csv"}),
])
def test_changed_policy_or_source_lineage_rejected(mutation) -> None:
    candidate = _request(REVISED, commit="2" * 40)
    mutation(candidate)
    with pytest.raises(PaperVintageError):
        compare_paper_vintages(
            reference_request=_request(BASE, commit="1" * 40),
            reference_source_bytes=BASE,
            candidate_request=candidate,
            candidate_source_bytes=REVISED,
        )


def test_changed_bytes_must_have_valid_distinct_byte_commitment() -> None:
    candidate = _request(REVISED, commit="2" * 40)
    candidate["source"]["sha256"] = hashlib.sha256(BASE).hexdigest()
    with pytest.raises(PaperVintageError):
        compare_paper_vintages(
            reference_request=_request(BASE, commit="1" * 40),
            reference_source_bytes=BASE,
            candidate_request=candidate,
            candidate_source_bytes=REVISED,
        )


def test_vintage_cli_real_native_consumer(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    paths = {
        "reference-request.json": _request(BASE, commit="1" * 40),
        "candidate-request.json": _request(REVISED, commit="2" * 40),
    }
    for name, data in paths.items():
        (tmp_path / name).write_text(json.dumps(data))
    (tmp_path / "reference.csv").write_bytes(BASE)
    (tmp_path / "candidate.csv").write_bytes(REVISED)
    cmd = [
        str(root / "scripts/run-paper-etf-vintage-compare-r1"),
        "--reference-request", str(tmp_path / "reference-request.json"),
        "--reference-source", str(tmp_path / "reference.csv"),
        "--candidate-request", str(tmp_path / "candidate-request.json"),
        "--candidate-source", str(tmp_path / "candidate.csv"),
    ]
    output = subprocess.run(
        cmd, cwd=root, env=os.environ.copy(),
        capture_output=True, text=True, check=False,
    )
    assert output.returncode == 0, output.stderr
    assert json.loads(output.stdout) == compare()


def test_cli_rejects_duplicate_json_key(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    bad = tmp_path / "bad.json"
    bad.write_text('{"kind":"a","kind":"b"}')
    raw = tmp_path / "source.csv"
    raw.write_bytes(BASE)
    proc = subprocess.run(
        [
            str(root / "scripts/run-paper-etf-vintage-compare-r1"),
            "--reference-request", str(bad),
            "--reference-source", str(raw),
            "--candidate-request", str(bad),
            "--candidate-source", str(raw),
        ], cwd=root, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 2
    assert json.loads(proc.stdout)["standing"] == "REJECTED"
