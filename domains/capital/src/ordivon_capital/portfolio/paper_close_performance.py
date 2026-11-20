"""Read-only paper daily economic performance over native Accounting/Risk receipts.

Portfolio interprets committed Accounting NAV; it never reprices instruments,
mutates the journal, invents benchmarks, or grants any financial effects.
Risk verifies the current NAV against one admitted Markets EOD snapshot.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any

from ordivon_capital.markets.etf_eod_snapshot import (
    AdmittedEtfEodSnapshot,
)
from ordivon_capital.risk.paper_close_risk import review_paper_close_risk

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_ACCOUNT = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
_MAX_MINOR = 2**63 - 1
_DECIMAL18 = Decimal("0.000000000000000001")


class PaperPerformanceError(ValueError):
    """Paper performance inputs are inconsistent or insufficient."""


def _minor(value: Any, label: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_MINOR:
        raise PaperPerformanceError(f"{label} must be a nonnegative int64 USD-cent amount")
    return value


def _receipt(value: Any, label: str) -> tuple[dict[str, Any], str, date, int, int]:
    if type(value) is not dict or value.get("schema_version") != 1 or value.get("mode") != "PAPER":
        raise PaperPerformanceError(f"{label} is not an Accounting Paper receipt")
    account = value.get("account_key")
    digest = value.get("request_sha256")
    if type(account) is not str or _ACCOUNT.fullmatch(account) is None:
        raise PaperPerformanceError(f"{label} has invalid paper account identity")
    if type(digest) is not str or _SHA.fullmatch(digest) is None:
        raise PaperPerformanceError(f"{label} has invalid request SHA-256")
    valuation = value.get("valuation")
    if type(valuation) is not dict:
        raise PaperPerformanceError(f"{label} valuation missing")
    stamp = valuation.get("session")
    if type(stamp) is not str:
        raise PaperPerformanceError(f"{label} session must be a canonical ISO date")
    try:
        session = date.fromisoformat(stamp)
    except ValueError as exc:
        raise PaperPerformanceError(f"{label} has invalid session date") from exc
    if session.isoformat() != stamp:
        raise PaperPerformanceError(f"{label} session date is noncanonical")
    nav = _minor(valuation.get("nav_minor"), f"{label}.nav_minor")
    contribution = _minor(
        valuation.get("contribution_minor"), f"{label}.contribution_minor"
    )
    return value, account, session, nav, contribution


def summarize_paper_period(
    *,
    current_receipt: dict[str, Any],
    previous_receipt: dict[str, Any] | None,
    snapshot: AdmittedEtfEodSnapshot,
) -> dict[str, Any]:
    """Project funding-neutral gain without calculating a second NAV.

    The optional prior close must be the exact digest predecessor. It is not
    sufficient to compare two arbitrarily selected dates. The return assumes
    all current-period external capital was available at the period start;
    this is neither a GIPS-certified TWR nor an investor IRR.
    """
    current, account, session, closing_nav, funding = _receipt(
        current_receipt, "current"
    )
    predecessor = current.get("previous_request_sha256")
    previous_session: date | None = None
    previous_nav = 0
    previous_digest = None
    if previous_receipt is not None:
        prior, prior_account, previous_session, previous_nav, _ = _receipt(
            previous_receipt, "previous"
        )
        previous_digest = prior["request_sha256"]
        if prior_account != account:
            raise PaperPerformanceError("previous and current paper accounts differ")
        if previous_session >= session:
            raise PaperPerformanceError("previous close must precede the current session")
        if predecessor != previous_digest:
            raise PaperPerformanceError("Accounting receipt predecessor chain is broken")
        # Markets' supersession pointer names a prior *source*, not a
        # revaluation of the old immutable Accounting receipt.  Publishing a
        # cross-period gain would silently compare two incompatible vintages.
        prior_market = prior.get("market_evidence")
        if (
            snapshot.supersedes_sha256 is not None
            and type(prior_market) is dict
            and prior_market.get("sha256") == snapshot.supersedes_sha256
        ):
            raise PaperPerformanceError(
                "superseded previous market valuation requires independent requalification"
            )
    elif predecessor is not None:
        raise PaperPerformanceError("previous Accounting receipt is required")
    # The genesis absence is distinguishable from an omitted predecessor.
    risk = review_paper_close_risk(receipt=current, snapshot=snapshot)
    if risk["netAssetValueMinor"] != closing_nav:
        raise PaperPerformanceError("Risk and Accounting NAV disagree")
    capital_base = previous_nav + funding
    gain = closing_nav - capital_base
    period_return = None
    if previous_session is not None and capital_base:
        with localcontext() as context:
            context.prec = 55
            context.rounding = ROUND_HALF_EVEN
            period_return = format(
                (Decimal(gain) / Decimal(capital_base)).quantize(_DECIMAL18), "f"
            )

    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.paper-close-economic-summary",
        "standing": "READ_ONLY_ACCOUNTING_RECEIPT_CONSUMER",
        "accountKey": account,
        "session": session.isoformat(),
        "previousSession": previous_session.isoformat() if previous_session else None,
        "requestSha256": current["request_sha256"],
        "previousRequestSha256": previous_digest,
        "marketSha256": snapshot.sha256,
        "marketCapturedAt": snapshot.captured_at.isoformat(),
        "marketValuationAsOf": snapshot.decision_at.isoformat(),
        "historicalPointInTimeStanding": "UNKNOWN_NOT_INDEPENDENTLY_VERIFIED",
        "marketStanding": current["market_evidence"]["standing"],
        "accountingPersistenceReverified": False,
        "sourceProviderAuthenticityIndependentlyVerified": False,
        "previousNavMinor": previous_nav if previous_session else None,
        "contributionMinor": funding,
        "startPeriodCapitalBaseMinor": capital_base if previous_session else None,
        "closingNavMinor": closing_nav,
        "fundingNeutralEconomicGainMinor": gain if previous_session else None,
        "simplePeriodReturnDecimal": period_return,
        "returnConvention": "START_PERIOD_CONTRIBUTION_ASSUMED_NOT_GIPS_TWR_OR_IRR",
        "calendarContinuity": "ASCENDING_CHAIN_ONLY_EXCHANGE_CALENDAR_UNATTESTED",
        "riskStanding": risk["standing"],
        "risk": risk["risk"],
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrdersAuthorized": False,
    }


def render_paper_daily_markdown(summary: dict[str, Any]) -> str:
    """Human display of the existing Portfolio/Risk result, never another NAV."""
    if (
        summary.get("schemaVersion") != 1
        or summary.get("kind") != "ordivon.finance.portfolio.paper-close-economic-summary"
        or summary.get("standing") != "READ_ONLY_ACCOUNTING_RECEIPT_CONSUMER"
        or summary.get("capitalAuthority") != "SIMULATION_ONLY"
        or summary.get("realMoneyOrdersAuthorized") is not False
        or summary.get("sourceProviderAuthenticityIndependentlyVerified") is not False
        or summary.get("historicalPointInTimeStanding")
        != "UNKNOWN_NOT_INDEPENDENTLY_VERIFIED"
        or type(summary.get("accountingPersistenceReverified")) is not bool
        or summary.get("returnConvention") != "START_PERIOD_CONTRIBUTION_ASSUMED_NOT_GIPS_TWR_OR_IRR"
    ):
        raise PaperPerformanceError("daily brief requires an unpromoted read-only Paper result")

    def money(value: Any) -> str:
        return f"USD {Decimal(_minor(value, 'daily amount')) / Decimal(100):,.2f}"

    def signed_money(value: Any) -> str:
        if type(value) is not int or not -(2**63 - 1) <= value <= 2**63 - 1:
            raise PaperPerformanceError("invalid signed gain")
        return f"USD {Decimal(value) / Decimal(100):+,.2f}"

    risk = summary.get("riskStanding")
    if type(risk) is not str or not risk:
        raise PaperPerformanceError("missing risk decision")
    lines = [
        "# Finance Paper 日结｜只读模拟",
        "",
        f"账户：{summary['accountKey']}；交易日：{summary['session']}",
        f"期末净值：{money(summary['closingNavMinor'])}",
        f"本期外部入金：{money(summary['contributionMinor'])}",
    ]
    if summary["previousSession"] is None:
        lines.append("首次日结：无上一期净值，不计算当期投资损益或收益率。")
    else:
        lines.extend([
            f"上期净值：{money(summary['previousNavMinor'])}",
            f"扣除外部入金的投资损益：{signed_money(summary['fundingNeutralEconomicGainMinor'])}",
            "本期收益率（假设期初入金；非 GIPS 时间加权收益或 IRR）："
            + f" {Decimal(summary['simplePeriodReturnDecimal']) * Decimal(100):+,.4f}%",
        ])
    lines.extend([
        "",
        "账务来源：" + (
            "专用 PostgreSQL 已提交收据，独立读回核验通过。"
            if summary["accountingPersistenceReverified"] else
            "输入文件模拟收据，未验证实际 PostgreSQL 持久状态。"
        ),
        f"风险状态：{risk}。不等于获得风险合格认定。",
        "行情证据：仅操作方绑定；真实提供者身份、数据使用权、公司行动和历史 PIT 均未经独立认证。",
        f"行情首次捕获：{summary['marketCapturedAt']}",
        "",
        "**决策：观察、非实盘；无真实金融写入权限。**",
        "主动策略与被动基准比较需另有同日期、同资金流、同费用证据。",
        "",
    ])
    return "\n".join(lines)

if __name__ == "__main__":
    raise SystemExit("CLI moved to scripts/applications/paper_performance.py; use scripts/run-capability-python")
