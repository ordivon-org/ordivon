"""Actual Paper Accounting -> Markets/Risk -> existing Portfolio contribution operator.

No second cash ledger, mark producer, broker execution or portfolio optimizer.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from test_paper_close_risk import _evidence, _receipt, _sell_case

from ordivon_capital.portfolio.paper_contribution_plan import (
    PaperContributionError,
    project_paper_account_contribution,
    render_paper_contribution_markdown,
)
from ordivon_capital.portfolio.strategic_contribution import AllocationPolicyError
from ordivon_capital.risk.paper_close_risk import PaperRiskEvidenceError

ROOT = Path(__file__).resolve().parents[1]
TARGET = {"ETF": 6000, "BOND_CORE": 4000}


def offline_case():
    _, _, snapshot, genesis, buy_day = _evidence()
    return snapshot, _receipt(snapshot, genesis, buy_day)


def test_actual_account_risk_cash_binds_native_contribution_without_selling():
    snapshot, receipt = offline_case()
    source = copy.deepcopy(receipt)
    result = project_paper_account_contribution(
        committed_receipt=receipt,
        snapshot=snapshot,
        target_weights_bps=TARGET,
        invest_minor=20_000,
    )
    assert receipt == source
    assert result["kind"] == "ordivon.finance.portfolio.paper-account-contribution-projection"
    assert result["accountingPersistenceReverified"] is False
    assert result["capitalAuthority"] == "SIMULATION_ONLY"
    assert result["realMoneyOrdersAuthorized"] is False
    assert result["riskStanding"] == "RISK_BUDGET_INCOMPLETE"
    assert result["unencumberedPaperCashMinor"] == 599_900
    assert result["unsettledPayablesMinor"] == 100_100
    assert result["protectedCashMinor"] == 300_000
    assert result["plan"]["currentHoldingsMinor"] == {"BOND_CORE": 0, "ETF": 102_000}
    assert result["plan"]["allocationsMinor"] == {"BOND_CORE": 20_000, "ETF": 0}
    assert result["spendablePaperCashAfterPlanMinor"] == 579_900
    assert result["unpricedAllocationTargets"] == ["BOND_CORE"]
    assert result["plan"]["riskStanding"] == "NOT_EVALUATED"
    assert result["plan"]["investmentAdviceProduced"] is False
    shown = render_paper_contribution_markdown(result)
    assert "本次计划使用已入账现金：USD 200.00" in shown
    assert "未结算卖出应收款" in shown
    assert "待购买资产缺少相同日收盘价：BOND_CORE" in shown
    assert "不等于获得风险合格认定" in shown
    assert "无真实" in shown or "没有真实" in shown


def test_never_double_spends_pending_payables_or_protected_reserve():
    snapshot, receipt = offline_case()
    with pytest.raises(AllocationPolicyError, match="protected cash reserve"):
        project_paper_account_contribution(
            committed_receipt=receipt, snapshot=snapshot,
            target_weights_bps=TARGET, invest_minor=599_901,
        )
    valid = project_paper_account_contribution(
        committed_receipt=receipt, snapshot=snapshot,
        target_weights_bps=TARGET, invest_minor=599_900,
    )
    assert valid["spendablePaperCashAfterPlanMinor"] == 0
    assert valid["plan"]["cashAfterMinor"] == 300_000


def test_unsettled_sale_receivable_is_not_investable_cash():
    _, _, snapshot, _, receipt = _sell_case()
    target = {"ETF": 6000, "BOND_CORE": 4000}
    result = project_paper_account_contribution(
        committed_receipt=receipt, snapshot=snapshot,
        target_weights_bps=target, invest_minor=5_000,
    )
    assert result["unsettledSaleReceivablesMinor"] == 102_900
    assert result["unencumberedPaperCashMinor"] == 599_900
    with pytest.raises(AllocationPolicyError, match="protected cash reserve"):
        project_paper_account_contribution(
            committed_receipt=receipt, snapshot=snapshot,
            target_weights_bps=target, invest_minor=599_901,
        )


def test_unknown_or_omitted_existing_position_cannot_be_discarded():
    snapshot, receipt = offline_case()
    with pytest.raises(PaperContributionError, match="every existing Paper position"):
        project_paper_account_contribution(
            committed_receipt=receipt, snapshot=snapshot,
            target_weights_bps={"BOND_CORE": 10000}, invest_minor=1,
        )
    with pytest.raises(PaperRiskEvidenceError, match="market evidence"):
        forged = copy.deepcopy(receipt)
        forged["market_evidence"]["sha256"] = "sha256:" + "a" * 64
        project_paper_account_contribution(
            committed_receipt=forged, snapshot=snapshot,
            target_weights_bps=TARGET, invest_minor=1,
        )
    with pytest.raises(PaperContributionError, match="nonnegative integer cents"):
        project_paper_account_contribution(
            committed_receipt=receipt, snapshot=snapshot,
            target_weights_bps=TARGET, invest_minor=True,
        )


def test_human_report_never_promotes_independent_rights_or_order_authority():
    snapshot, receipt = offline_case()
    result = project_paper_account_contribution(
        committed_receipt=receipt, snapshot=snapshot,
        target_weights_bps=TARGET, invest_minor=20_000,
    )
    for field, false_value in (
        ("capitalAuthority", "LIVE"),
        ("executionAuthorized", True),
        ("realMoneyOrdersAuthorized", True),
        ("marketRightsIndependentlyVerified", True),
    ):
        forged = dict(result) | {field: false_value}
        with pytest.raises(PaperContributionError, match="unqualified Paper result"):
            render_paper_contribution_markdown(forged)


def test_real_pg_latest_readonly_head_to_monthly_plan_and_markdown(tmp_path):
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable dedicated paper PostgreSQL is required")
    from ordivon_capital.accounting.postgres_paper_close import (
        PostgresPaperClose,
        read_latest_committed_paper_close,
    )

    raw, binding, snapshot, genesis, buy_day = _evidence()
    account = "monthly-" + uuid4().hex
    store = PostgresPaperClose(dsn)
    store.close_session(account, genesis)
    committed = store.close_session(account, buy_day, mark_snapshot=snapshot)
    latest = read_latest_committed_paper_close(dsn, account)
    assert latest == committed

    paths = {
        "source": tmp_path / "market.json",
        "binding": tmp_path / "binding.json",
        "target": tmp_path / "target.json",
    }
    paths["source"].write_bytes(raw)
    paths["binding"].write_text(json.dumps(binding))
    paths["target"].write_text(json.dumps(TARGET))
    command = [
        sys.executable, "-m", "ordivon_capital.portfolio.paper_contribution_plan",
        "--account", account, "--market-snapshot", str(paths["source"]),
        "--market-binding", str(paths["binding"]),
        "--target-weights", str(paths["target"]),
        "--invest-minor", "20000",
    ]
    env = os.environ | {
        "PYTHONPATH": str(ROOT / "src"),
        "ORDIVON_CAPITAL_PAPER_PG_DSN": dsn,
    }
    json_output = subprocess.run(
        command, env=env, cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert json_output.returncode == 0, json_output.stderr
    plan = json.loads(json_output.stdout)
    assert plan["accountingPersistenceReverified"] is True
    assert plan["accountingHeadRequestSha256"] == latest["request_sha256"]
    assert plan["unencumberedPaperCashMinor"] == 599_900
    assert plan["plan"]["allocationsMinor"] == {"BOND_CORE": 20_000, "ETF": 0}
    assert read_latest_committed_paper_close(dsn, account) == committed
    markdown = subprocess.run(
        command + ["--format", "markdown"],
        env=env, cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert markdown.returncode == 0, markdown.stderr
    assert "已提交账务读回：是" in markdown.stdout
    assert "USD 200.00" in markdown.stdout
    assert "不等于获得风险合格认定" in markdown.stdout
    assert read_latest_committed_paper_close(dsn, account) == committed


def test_unknown_account_does_not_create_a_new_investment_portfolio(tmp_path):
    dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_TEST_DSN")
    if not dsn:
        pytest.skip("disposable dedicated paper PostgreSQL is required")
    raw, binding, _, _, _ = _evidence()
    (tmp_path / "snapshot").write_bytes(raw)
    (tmp_path / "binding").write_text(json.dumps(binding))
    (tmp_path / "targets").write_text(json.dumps(TARGET))
    result = subprocess.run(
        [
            sys.executable, "-m", "ordivon_capital.portfolio.paper_contribution_plan",
            "--account", "missing-" + uuid4().hex,
            "--market-snapshot", str(tmp_path / "snapshot"),
            "--market-binding", str(tmp_path / "binding"),
            "--target-weights", str(tmp_path / "targets"), "--invest-minor", "10",
        ],
        env=os.environ | {
            "PYTHONPATH": str(ROOT / "src"),
            "ORDIVON_CAPITAL_PAPER_PG_DSN": dsn,
        }, cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stderr)["standing"] == "REJECTED"
    assert result.stdout == ""
