"""Source-bound paper valuation: conservation, temporal admissibility and CLI consumption."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ordivon_capital.portfolio.daily_valuation import (
    DailyValuationError,
    value_paper_portfolio,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "examples" / "paper_daily_valuation_synthetic_r1.json"


def example() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def cli(raw: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "paper_daily_valuation_brief.py")],
        input=raw, text=True, capture_output=True, cwd=ROOT, env=env, check=False,
    )


def test_synthetic_day_conservation_and_cash_reserve() -> None:
    result = value_paper_portfolio(example())
    assert result["kind"] == "ordivon.capital.finance.paper-daily-valuation"
    assert result["closingNav"] == "10022.50"
    assert result["closingCash"] == "4000.00"
    assert result["positionsValue"] == "6022.50"
    assert result["periodEconomicGain"] == "22.50"
    assert result["periodReturn"] == "0.00225"
    assert result["protectedCash"] == "3000.00"
    assert result["executionAuthorized"] is False
    assert result["realCapitalAuthority"] == "NONE"
    assert result["marketSourceVerified"] is False
    assert result["accountingSourceVerified"] is False
    assert result["corporateActionsVerified"] is False
    assert result["standing"] == "SYNTHETIC_RESEARCH_ONLY"


def test_external_deposit_does_not_become_profit() -> None:
    source = example()
    source["externalCashFlowAtStart"] = "1000.00"
    source["cashAtClose"] = "5000.00"
    result = value_paper_portfolio(source)
    assert result["closingNav"] == "11022.50"
    assert result["periodEconomicGain"] == "22.50"
    assert result["periodReturn"].startswith("0.0020454545")


def test_currency_conservation_and_rounding_half_even() -> None:
    source = example()
    source["openingNav"] = "1.00"
    source["cashAtClose"] = "1.00"
    source["protectedCash"] = "1.00"
    source["positions"][0].update({"quantity":"0.5","closePrice":"0.01"})
    result = value_paper_portfolio(source)
    assert result["positionsValue"] == "0.00"
    assert result["closingNav"] == "1.00"
    assert result["periodReturn"] == "0"


def test_unique_position_order_is_canonical() -> None:
    source = example()
    base = source["positions"][0]
    second = {**base,"instrumentId":"SIM_BOND","quantity":"1","closePrice":"20.00"}
    source["positions"].append(second)
    first = value_paper_portfolio(source)
    source["positions"].reverse()
    second_output = value_paper_portfolio(source)
    assert first == second_output
    assert [p["instrumentId"] for p in first["positions"]] == ["SIM_BOND","SIM_INDEX"]


@pytest.mark.parametrize("mutate",[
    lambda s:s.update({"currency":"EUR"}),
    lambda s:s.update({"cashAtClose":"2999.99"}),
    lambda s:s.update({"cashAtClose":True}),
    lambda s:s.update({"cashAtClose":"NaN"}),
    lambda s:s.update({"openingNav":"-1"}),
    lambda s:s.update({"externalCashFlowAtStart":"-10001.00"}),
    lambda s:s.update({"pricesStanding":"PROVIDER_VERIFIED"}),
    lambda s:s.update({"sessionCloseAt":"2026-11-05T16:00:00"}),
    lambda s:s.update({"evaluatedAt":"2026-11-05T15:00:00-05:00"}),
    lambda s:s.update({"unknown":1}),
    lambda s:s["positions"][0].update({"priceAsOf":"2026-11-05T15:59:00-05:00"}),
    lambda s:s["positions"][0].update({"availableAt":"2026-11-05T18:30:00-05:00"}),
    lambda s:s["positions"][0].update({"quantity":"-1"}),
    lambda s:s["positions"][0].update({"quantity":1}),
    lambda s:s["positions"][0].update({"closePrice":"0"}),
    lambda s:s["positions"][0].update({"closePrice":"1.12345"}),
    lambda s:s["positions"][0].update({"instrumentId":"../PATH"}),
    lambda s:s["positions"].append(s["positions"][0].copy()),
    lambda s:s["positions"][0].update({"sourceId":""}),
])
def test_invalid_input_is_rejected(mutate) -> None:
    source=example()
    mutate(source)
    with pytest.raises(DailyValuationError):
        value_paper_portfolio(source)


def test_zero_account_and_zero_denominator() -> None:
    source=example()
    source["openingNav"]="0.00"
    source["cashAtClose"]="0.00"
    source["protectedCash"]="0.00"
    source["positions"]=[]
    result=value_paper_portfolio(source)
    assert result["closingNav"]=="0.00"
    assert result["periodReturn"] is None


def test_real_cli_is_readonly_and_matches_library() -> None:
    raw=FIXTURE.read_text(encoding="utf-8")
    result=cli(raw)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==value_paper_portfolio(example())


@pytest.mark.parametrize("raw",[
    "not json",
    '{"schemaVersion":1,"schemaVersion":2}',
    '{"schemaVersion":1,"cashAtClose":NaN}',
    '{"schemaVersion":1,"cashAtClose":Infinity}',
])
def test_cli_rejects_ambiguous_or_invalid_json_without_success_output(raw) -> None:
    result=cli(raw)
    assert result.returncode!=0
    assert result.stdout==""
