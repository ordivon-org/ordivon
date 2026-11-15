"""Read-only paper daily economic performance over native Accounting/Risk receipts.

Portfolio interprets committed Accounting NAV; it never reprices instruments,
mutates the journal, invents benchmarks, or grants any financial effects.
Risk verifies the current NAV against one admitted Markets EOD snapshot.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

from ordivon_capital.markets.etf_eod_snapshot import (
    AdmittedEtfEodSnapshot,
    admit_etf_eod_snapshot,
)
from ordivon_capital.portfolio.strategic_contribution import plan_strategic_contribution
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
    cash_what_if: dict[str, Any] | None = None,
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

    summary = {
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
    if cash_what_if is not None:
        summary["cashDeploymentScenario"] = _paper_cash_whatif(
            summary=summary, current=current, snapshot=snapshot, request=cash_what_if
        )
    return summary


def _paper_cash_whatif(
    *, summary: dict[str, Any], current: dict[str, Any],
    snapshot: AdmittedEtfEodSnapshot, request: dict[str, Any],
) -> dict[str, Any]:
    """Compose verified Paper/Risk facts with the existing contribution planner.

    Only reallocates *existing unencumbered simulated cash* hypothetically.
    This does not fund the account, post an order, or certify issuer data.
    """
    expected = {
        "schemaVersion", "kind", "accountKey", "requestSha256",
        "marketSha256", "currency", "contributionMinor", "targetWeightsBps",
    }
    if type(request) is not dict or set(request) != expected:
        raise PaperPerformanceError("cash what-if request schema mismatch")
    if (
        type(request["schemaVersion"]) is not int
        or request["schemaVersion"] != 1
        or request["kind"] != "ordivon.finance.portfolio.paper-cash-deployment-whatif"
        or request["accountKey"] != summary["accountKey"]
        or request["requestSha256"] != summary["requestSha256"]
        or request["marketSha256"] != summary["marketSha256"]
        or request["currency"] != "USD"
    ):
        raise PaperPerformanceError("cash what-if differs from exact Paper and Markets evidence")

    def cents_from_risk(raw: Any) -> int:
        if type(raw) is not str:
            raise PaperPerformanceError("invalid Risk exposure amount")
        try:
            cents = Decimal(raw) * 100
        except InvalidOperation as exc:
            raise PaperPerformanceError("invalid Risk exposure decimal") from exc
        if (
            not cents.is_finite() or cents < 0 or cents > _MAX_MINOR
            or cents != cents.to_integral_value()
        ):
            raise PaperPerformanceError("Risk exposure cannot map to exact USD cents")
        return int(cents)

    exposure = summary["risk"]["nodes"]["exposureLedger"]
    holdings = {
        pos["instrumentId"]: cents_from_risk(pos["signedNotionalUsd"])
        for pos in exposure["positions"]
    }
    targets = request["targetWeightsBps"]
    if type(targets) is not dict:
        raise PaperPerformanceError("cash what-if requires target weights")
    marks = snapshot.prices_for(summary["session"])
    if set(holdings) - set(targets) or set(targets) - set(marks):
        raise PaperPerformanceError(
            "cash what-if targets must cover held assets and current admitted market marks"
        )
    available = cents_from_risk(exposure["availableEquityUsd"])
    reserve = _minor(current["valuation"]["protected_minor"], "protected cash")
    if available + reserve > _MAX_MINOR:
        raise PaperPerformanceError("cash what-if available envelope exceeds int64")

    # All capital-allocation mathematics remain the original CA09 Portfolio
    # LEGO. Risk already checked Accounting payable/receivable and all marks.
    allocation = plan_strategic_contribution({
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.strategic-contribution-request",
        "currency": "USD",
        "cashMinor": available + reserve,
        "protectedReserveMinor": reserve,
        "contributionMinor": request["contributionMinor"],
        "holdingsMinor": {symbol: holdings.get(symbol, 0) for symbol in targets},
        "targetWeightsBps": targets,
    })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.finance.portfolio.paper-cash-deployment-scenario",
        "standing": "HYPOTHETICAL_UNQUALIFIED_NO_ACTION",
        "decision": "NO_ACTION",
        "fundingConvention": "EXISTING_UNENCUMBERED_PAPER_CASH_NOT_NEW_DEPOSIT",
        "accountingRequestSha256": summary["requestSha256"],
        "marketSha256": summary["marketSha256"],
        "availableUnencumberedMinor": available,
        "riskStanding": summary["riskStanding"],
        "sourceProviderAuthenticityIndependentlyVerified": False,
        "capitalAuthority": "SIMULATION_ONLY",
        "realMoneyOrdersAuthorized": False,
        "allocation": allocation,
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
    scenario = summary.get("cashDeploymentScenario")
    if scenario is not None:
        if (
            type(scenario) is not dict
            or scenario.get("standing") != "HYPOTHETICAL_UNQUALIFIED_NO_ACTION"
            or scenario.get("decision") != "NO_ACTION"
            or scenario.get("accountingRequestSha256") != summary["requestSha256"]
            or scenario.get("marketSha256") != summary["marketSha256"]
            or scenario.get("realMoneyOrdersAuthorized") is not False
            or scenario.get("allocation", {}).get("executionAuthorized") is not False
        ):
            raise PaperPerformanceError("cash what-if must remain source-bound and non-executable")
        allocation = scenario["allocation"]
        lines.extend([
            "## 模拟现金条件性配置",
            "",
            f"当前可用模拟现金：{money(scenario['availableUnencumberedMinor'])}",
            f"假设从现有现金部署：{money(allocation['contributionMinor'])}；不是新入金。",
            *[
                f"- {symbol}：假设新增 {money(amount)}"
                for symbol, amount in sorted(allocation["allocationsMinor"].items())
            ],
            "**行动：NO_ACTION。** 风险预算或行情来源未独立认证；"
            "仅作为既定目标权重下的数学情景，不发出模拟或真实订单。",
            "",
        ])
    return "\n".join(lines)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise PaperPerformanceError("duplicate JSON input key")
        result[name] = value
    return result


def _reject_constant(value: str) -> None:
    raise PaperPerformanceError(f"nonfinite JSON constant: {value}")


def _read_json(path: Path) -> dict[str, Any]:
    obj = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    if type(obj) is not dict:
        raise PaperPerformanceError("JSON input must be an object")
    return obj


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--current-receipt", type=Path)
    source.add_argument("--account")
    parser.add_argument("--previous-receipt", type=Path)
    parser.add_argument("--session")
    parser.add_argument("--previous-session")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--cash-what-if", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args()
    if bool(args.account) != bool(args.session):
        parser.error("--account and --session must be supplied together")
    if args.current_receipt and args.previous_session:
        parser.error("--previous-session requires --account")
    if args.account and args.previous_receipt:
        parser.error("--previous-receipt is only for offline file mode")
    try:
        snapshot = admit_etf_eod_snapshot(
            args.snapshot.read_bytes(), **_read_json(args.binding)
        )
        persistent = bool(args.account)
        if persistent:
            from ordivon_capital.accounting.postgres_paper_close import (
                read_committed_paper_close,
            )

            dsn = os.environ.get("ORDIVON_CAPITAL_PAPER_PG_DSN", "")
            current = read_committed_paper_close(
                dsn, args.account, date.fromisoformat(args.session)
            )
            previous = (
                read_committed_paper_close(
                    dsn, args.account, date.fromisoformat(args.previous_session)
                )
                if args.previous_session else None
            )
        else:
            current = _read_json(args.current_receipt)
            previous = (
                _read_json(args.previous_receipt) if args.previous_receipt else None
            )
        summary = summarize_paper_period(
            current_receipt=current, previous_receipt=previous, snapshot=snapshot,
            cash_what_if=_read_json(args.cash_what_if) if args.cash_what_if else None,
        )
        if persistent:
            summary["accountingPersistenceReverified"] = True
            summary["accountingReadbackMode"] = "POSTGRESQL_CURRENT_COMMITTED_REQUEST"
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(
            json.dumps({
                "standing": "REJECTED", "capitalAuthority": "SIMULATION_ONLY",
                "reason": str(exc) if isinstance(exc, ValueError) else "invalid source input",
            }, sort_keys=True),
            file=sys.stderr,
        )
        return 2
    print(
        render_paper_daily_markdown(summary) if args.format == "markdown"
        else json.dumps(summary, ensure_ascii=False, sort_keys=True, allow_nan=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
