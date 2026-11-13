"""Read-only contribution-first plan derived from a real Paper account head.

Existing Accounting owns committed positions/cash; Markets owns the snapshot;
Risk owns payable/reserve and NAV validation; Portfolio owns allocation math.
This module merely binds those LEGO inputs, without a second ledger or order API.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from ordivon_capital.markets.etf_eod_snapshot import (
    AdmittedEtfEodSnapshot,
    admit_etf_eod_snapshot,
)
from ordivon_capital.portfolio.strategic_contribution import (
    AllocationPolicyError,
    plan_strategic_contribution,
)
from ordivon_capital.risk.paper_close_risk import (
    PaperRiskEvidenceError,
    review_paper_close_risk,
)


class PaperContributionError(ValueError):
    """The requested plan cannot be built from a verified Paper account head."""


def project_paper_account_contribution(
    *,
    committed_receipt: dict[str, Any],
    snapshot: AdmittedEtfEodSnapshot,
    target_weights_bps: dict[str, int],
    invest_minor: int,
) -> dict[str, Any]:
    """Use existing Accounting/Risk/Portfolio semantics without live effects.

    'invest_minor' is cash ALREADY POSTED in the Paper account, not a new
    deposit. Unsettled receivables and purchase payables are excluded.
    The caller's target weights are unverified user intent, not an IPS.
    """
    risk = review_paper_close_risk(
        receipt=committed_receipt,
        snapshot=snapshot,
    )
    valuation = committed_receipt["valuation"]
    protected = valuation["protected_minor"]
    unencumbered = risk["unencumberedCashMinor"]
    if type(protected) is not int or type(unencumbered) is not int:
        raise PaperContributionError("non-integer Paper cash")
    if type(invest_minor) is not int or invest_minor < 0:
        raise PaperContributionError("invest_minor must be nonnegative integer cents")
    if not isinstance(target_weights_bps, dict):
        raise PaperContributionError("target weights must be a JSON object")
    if not set(valuation["positions"]).issubset(target_weights_bps):
        raise PaperContributionError("every existing Paper position needs a target weight")

    marks = snapshot.prices_for(risk["session"])
    holdings = {}
    for asset in target_weights_bps:
        shares = valuation["positions"].get(asset, 0)
        # Existing Risk has already verified positive share counts and marks.
        holdings[asset] = shares * marks[asset] if shares else 0

    # Risk already excludes open buy payables and protected cash. Restore only
    # the protected reserve in strategic_contribution's existing input model,
    # so its native guard can enforce the same post-plan protection.
    available_including_protected = unencumbered + protected
    plan = plan_strategic_contribution({
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": "USD",
        "cashMinor": available_including_protected,
        "protectedReserveMinor": protected,
        "contributionMinor": invest_minor,
        "holdingsMinor": holdings,
        "targetWeightsBps": target_weights_bps,
    })
    if plan["cashAfterMinor"] < protected:
        raise PaperContributionError("native Portfolio cash conservation violated")
    if plan["contributionMinor"] != sum(plan["allocationsMinor"].values()):
        raise PaperContributionError("native Portfolio investment conservation violated")

    missing_purchase_price = sorted(
        symbol for symbol, allocated in plan["allocationsMinor"].items()
        if allocated and symbol not in marks
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.paper-account-contribution-projection",
        "standing": "READ_ONLY_PAPER_ACCOUNT_PLAN",
        "accountKey": risk["accountKey"],
        "accountHeadSession": risk["session"],
        "accountingHeadRequestSha256": risk["accountingRequestSha256"],
        "accountingPersistenceReverified": False,
        "marketSha256": risk["marketSha256"],
        "marketCapturedAt": risk["marketCapturedAt"],
        "marketStanding": "OPERATOR_BOUND_MARKS_NOT_INDEPENDENTLY_VERIFIED",
        "historicalPointInTimeStanding": "UNKNOWN_NOT_INDEPENDENTLY_VERIFIED",
        "marketRightsIndependentlyVerified": False,
        "corporateActionsIndependentlyVerified": False,
        "protectedCashMinor": protected,
        "unsettledPayablesMinor": risk["unsettledPayablesMinor"],
        "unsettledSaleReceivablesMinor": risk["unsettledSaleReceivablesMinor"],
        "unencumberedPaperCashMinor": unencumbered,
        "spendablePaperCashAfterPlanMinor": unencumbered - invest_minor,
        "investmentFundsSource": "ALREADY_COMMITTED_PAPER_UNENCUMBERED_CASH",
        "unpricedAllocationTargets": missing_purchase_price,
        "riskStanding": risk["standing"],
        "plan": plan,
        "investmentAdviceProduced": False,
        "executionAuthorized": False,
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrdersAuthorized": False,
    }


def render_paper_contribution_markdown(report: dict[str, Any]) -> str:
    """User-facing text from native results; never convert amounts to orders."""
    if (
        report.get("kind") != "ordivon.finance.portfolio.paper-account-contribution-projection"
        or report.get("standing") != "READ_ONLY_PAPER_ACCOUNT_PLAN"
        or report.get("capitalAuthority") != "SIMULATION_ONLY"
        or report.get("executionAuthorized") is not False
        or report.get("realMoneyOrdersAuthorized") is not False
        or report.get("marketRightsIndependentlyVerified") is not False
    ):
        raise PaperContributionError("unqualified Paper result cannot be presented as a plan")
    plan = report["plan"]

    def usd(cents: int) -> str:
        if type(cents) is not int or cents < 0:
            raise PaperContributionError("invalid cent amount")
        return f"USD {Decimal(cents) / 100:,.2f}"

    lines = [
        "# Finance 月度新增资金配置｜Paper 账户只读计划",
        "",
        f"模拟账户：{report['accountKey']}；" + (
            "已提交日结：" if report["accountingPersistenceReverified"]
            else "离线输入日结："
        ) + report["accountHeadSession"],
        f"原有可用现金（扣除受保护现金和待结算买入应付款）：{usd(report['unencumberedPaperCashMinor'])}",
        f"受保护储备：{usd(report['protectedCashMinor'])}",
        f"未结算卖出应收款（不能用于这次购买）：{usd(report['unsettledSaleReceivablesMinor'])}",
        f"本次计划使用已入账现金：{usd(plan['contributionMinor'])}",
        f"计划后剩余非受保护现金：{usd(report['spendablePaperCashAfterPlanMinor'])}",
        "",
        "仅买入资产配置（美元额度，并非真实可成交份额）：",
    ]
    for symbol, cents in plan["allocationsMinor"].items():
        lines.append(f"- {symbol}: {usd(cents)}")
    lines.extend([
        "",
        "已提交账务读回：" + ("是" if report["accountingPersistenceReverified"] else "否，仅传入文件"),
        f"风险评价：{report['riskStanding']}；不等于获得风险合格认定或真实交易授权。",
    ])
    if report["unpricedAllocationTargets"]:
        lines.append("待购买资产缺少相同日收盘价：" + ", ".join(report["unpricedAllocationTargets"]))
    lines.extend([
        "本报告仅使用操作方绑定的模拟价格；外部行情权利、真实 PIT 与公司行动未独立认证。",
        "购买费用、税务、分红和实际成交并未建模；没有真实或模拟订单自动提交。",
        "资产目标比例必须由用户事先给定，不是模型自行推荐。",
        "",
    ])
    return "\n".join(lines)


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise PaperContributionError("duplicate source JSON key")
        out[key] = value
    return out


def _read_object(path: Path) -> dict[str, Any]:
    obj = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(
            PaperContributionError("nonfinite source JSON constant")
        ),
    )
    if type(obj) is not dict:
        raise PaperContributionError("expected JSON object")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True)
    parser.add_argument("--market-snapshot", required=True, type=Path)
    parser.add_argument("--market-binding", required=True, type=Path)
    parser.add_argument("--target-weights", required=True, type=Path)
    parser.add_argument("--invest-minor", required=True, type=int)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    try:
        # Exact real Paper PG HEAD, not a caller-invented account state.
        from ordivon_capital.accounting.postgres_paper_close import (
            read_latest_committed_paper_close,
        )

        dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", "")
        receipt = read_latest_committed_paper_close(dsn, args.account)
        if receipt is None:
            raise PaperContributionError("no committed Paper account head; do not create a fake account")
        snapshot = admit_etf_eod_snapshot(
            args.market_snapshot.read_bytes(),
            **_read_object(args.market_binding),
        )
        report = project_paper_account_contribution(
            committed_receipt=receipt,
            snapshot=snapshot,
            target_weights_bps=_read_object(args.target_weights),
            invest_minor=args.invest_minor,
        )
        # Only this CLI has read the current native PostgreSQL account head.
        # The reusable pure projection always starts with persistence=false.
        report["accountingPersistenceReverified"] = True
    except (OSError, ValueError, TypeError, KeyError, PaperRiskEvidenceError,
            AllocationPolicyError) as exc:
        print(json.dumps({
            "standing": "REJECTED",
            "capitalAuthority": "SIMULATION_ONLY",
            "reason": str(exc) if isinstance(exc, ValueError) else "invalid source input",
        }, sort_keys=True), file=sys.stderr)
        return 2
    print(
        render_paper_contribution_markdown(report)
        if args.format == "markdown"
        else json.dumps(report, ensure_ascii=False, sort_keys=True, allow_nan=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
