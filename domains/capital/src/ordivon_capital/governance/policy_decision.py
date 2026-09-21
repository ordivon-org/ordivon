from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

DECISION_IMPLEMENTATION = "LOCAL_DETERMINISTIC_PYTHON"


class PolicyDecisionError(RuntimeError):
    """Fail-closed bounded policy-decision error."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise PolicyDecisionError(f"expected JSON object: {path}")
    return value


def _resolve(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise PolicyDecisionError(f"policy input path escapes repository: {relative}") from exc
    if not path.is_file():
        raise PolicyDecisionError(f"policy input unavailable: {relative}")
    return path


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise PolicyDecisionError(f"invalid decimal policy fact: {value!r}") from exc


def _require_local_implementation(cfg: dict[str, Any]) -> None:
    if cfg.get("decisionImplementation") != DECISION_IMPLEMENTATION:
        raise PolicyDecisionError(
            f"unexpected policy decision implementation: {cfg.get('decisionImplementation')!r}"
        )


def _execution_decision(*, current_lane: Any, write_policy: dict[str, Any]) -> dict[str, bool]:
    allow_non_live = (
        current_lane == "NON_LIVE"
        and write_policy.get("state") == "NOT_ADMITTED"
        and write_policy.get("externalFinancialWriteAllowed") is False
        and write_policy.get("providerWriteCapabilityBound") is False
        and write_policy.get("effectVerifier") != "IMPLEMENTED_BOUND_CURRENT"
    )
    allow_external_write = (
        current_lane == "EXTERNAL_WRITE"
        and write_policy.get("state") == "ADMITTED"
        and write_policy.get("externalFinancialWriteAllowed") is True
        and write_policy.get("providerWriteCapabilityBound") is True
        and write_policy.get("effectVerifier") == "IMPLEMENTED_BOUND_CURRENT"
    )
    if allow_non_live and allow_external_write:
        raise PolicyDecisionError("mutually incompatible lane decisions")
    return {
        "allowNonLive": allow_non_live,
        "allowExternalWrite": allow_external_write,
    }


def evaluate_execution_policy(repo: Path, config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise PolicyDecisionError("unexpected execution-policy kind")
    _require_local_implementation(cfg)

    write_doc = _load_json(_resolve(repo, cfg["externalWritePolicyInputContract"]))
    if write_doc.get("kind") != "ordivon.capital.market.external-write-policy-input":
        raise PolicyDecisionError("external-write policy input missing")

    decision = _execution_decision(
        current_lane=cfg.get("currentLane"),
        write_policy=write_doc,
    )
    return {
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "currentLane": cfg.get("currentLane"),
        **decision,
        "externalWritePolicyStanding": write_doc.get("state"),
        "externalWriteVerifier": write_doc.get("effectVerifier", "NOT_IMPLEMENTED"),
        "providerWriteCapabilityBound": bool(
            write_doc.get("providerWriteCapabilityBound", False)
        ),
        "externalFinancialWriteAllowedByContract": bool(
            write_doc.get("externalFinancialWriteAllowed", False)
        ),
    }


def _live_test_account_decision(facts: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if facts.get("venue") not in {"OKX", "BINANCE"}:
        reasons.append("unsupported-venue")
    if facts.get("permissionStanding") != "READ_ONLY_VERIFIED":
        reasons.append("readonly-reality-not-verified")
    if facts.get("externalFinancialWriteAttempted") is not False:
        reasons.append("reality-not-readonly")
    if facts.get("clockPassed") is not True:
        reasons.append("clock-gate-not-passed")
    if facts.get("reconciliationHealthy") is not True:
        reasons.append("reconciliation-not-healthy")
    if facts.get("tradePermission") is not True:
        reasons.append("trade-permission-missing")
    if facts.get("withdrawPermission") is not False:
        reasons.append("withdraw-permission-not-proven-absent")
    if facts.get("transferPermission") not in {False, None}:
        reasons.append("transfer-permission-not-proven-absent")
    if facts.get("hasNonzeroPosition") is True:
        reasons.append("nonzero-position-present")
    if facts.get("hasOpenOrders") is True:
        reasons.append("open-order-present")
    nonquote = facts.get("nonquoteNonzeroAssets") or []
    if nonquote:
        reasons.append("nonquote-balance-present:" + ",".join(nonquote))
    if facts.get("quoteBalanceExceedsThreshold") is True:
        reasons.append("quote-balance-exceeds-test-threshold")
    blocking = sorted(set(reasons))
    return {"admitted": not blocking, "blockingReasons": blocking}


def evaluate_live_test_account(
    *,
    repo: Path,
    config_path: Path,
    reality: dict[str, Any],
    quote_asset: str,
    permission: dict[str, Any],
    clock_passed: bool,
    reconciliation_healthy: bool,
    max_quote_balance: str = "1",
) -> dict[str, Any]:
    del repo
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise PolicyDecisionError("unexpected execution-policy kind")
    _require_local_implementation(cfg)

    venue = str(reality.get("venue") or "").upper()
    positions = [
        row
        for row in (reality.get("positions") or [])
        if _decimal(row.get("quantity", "0")) != 0
    ]
    max_quote = _decimal(max_quote_balance)
    quote_total = Decimal("0")
    nonquote_nonzero: list[str] = []
    for balance in reality.get("balances") or []:
        asset = str(balance.get("asset") or "")
        total = _decimal(balance.get("total", "0"))
        if total == 0:
            continue
        if asset == quote_asset:
            quote_total += total
        else:
            nonquote_nonzero.append(asset)
    nonquote_nonzero.sort()

    decision = _live_test_account_decision(
        {
            "venue": venue,
            "permissionStanding": reality.get("permissionStanding"),
            "externalFinancialWriteAttempted": reality.get(
                "externalFinancialWriteAttempted"
            ),
            "clockPassed": clock_passed,
            "reconciliationHealthy": reconciliation_healthy,
            "tradePermission": permission.get("trade"),
            "withdrawPermission": permission.get("withdraw"),
            "transferPermission": permission.get("transfer"),
            "hasNonzeroPosition": bool(positions),
            "hasOpenOrders": bool(reality.get("openOrders")),
            "nonquoteNonzeroAssets": nonquote_nonzero,
            "quoteBalanceExceedsThreshold": quote_total > max_quote,
        }
    )
    admitted = decision["admitted"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.live-test-account-admission",
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "venue": venue,
        "standing": "ADMITTED_EMPTY_LIVE_TEST_ACCOUNT" if admitted else "BLOCKED",
        "orderSubmissionAllowed": admitted,
        "productionTradingAuthorized": False,
        "withdrawalAuthorized": False,
        "transferAuthorized": False,
        "quoteAsset": quote_asset,
        "observedQuoteBalance": format(quote_total, "f"),
        "maxQuoteBalance": format(max_quote, "f"),
        "nonquoteNonzeroAssets": nonquote_nonzero,
        "blockingReasons": decision["blockingReasons"],
    }


def _risk_budget_decision(facts: dict[str, Any]) -> dict[str, Any]:
    if facts["complete"] is False:
        return {
            "standing": "INCOMPLETE",
            "missingBudgetInputs": facts["missingBudgetInputs"],
            "statuses": {},
        }
    statuses = {
        "MAX_GROSS_TO_EQUITY": (
            "PASS"
            if facts["grossToEquity"] <= facts["maxGrossToEquity"]
            else "FAIL"
        ),
        "MAX_LARGEST_POSITION_GROSS_SHARE": (
            "PASS"
            if facts["largestPositionGrossShare"]
            <= facts["maxLargestPositionGrossShare"]
            else "FAIL"
        ),
        "MIN_AVAILABLE_EQUITY_RATIO": (
            "PASS"
            if facts["availableEquityRatio"] >= facts["minAvailableEquityRatio"]
            else "FAIL"
        ),
        "MAX_EQUITY_LOSS_AT_NAMED_SHOCK": (
            "PASS"
            if facts["shockLossPct"] <= facts["maxEquityLossPctAtShock"]
            else "FAIL"
        ),
    }
    return {
        "standing": (
            "SATISFIED" if all(value == "PASS" for value in statuses.values()) else "BREACHED"
        ),
        "missingBudgetInputs": [],
        "statuses": statuses,
    }


def evaluate_risk_budget_policy(
    *,
    repo: Path,
    config_path: Path,
    exposure_ledger: dict[str, Any],
    budget: dict[str, Any],
) -> dict[str, Any]:
    del repo
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise PolicyDecisionError("unexpected execution-policy kind")
    _require_local_implementation(cfg)

    required = (
        "maxGrossToEquity",
        "maxLargestPositionGrossShare",
        "minAvailableEquityRatio",
        "shockMagnitudePct",
        "maxEquityLossPctAtShock",
    )
    missing = [key for key in required if budget.get(key) is None]
    if missing:
        decision = _risk_budget_decision(
            {"complete": False, "missingBudgetInputs": missing}
        )
        return {
            "schemaVersion": 1,
            "kind": "ordivon.capital.market.risk-limit-evaluation",
            "componentId": "risk-limit-evaluator",
            "decisionImplementation": DECISION_IMPLEMENTATION,
            "standing": decision["standing"],
            "missingBudgetInputs": decision["missingBudgetInputs"],
        }

    max_gross = _decimal(budget["maxGrossToEquity"])
    max_concentration = _decimal(budget["maxLargestPositionGrossShare"])
    min_available = _decimal(budget["minAvailableEquityRatio"])
    shock_pct = _decimal(budget["shockMagnitudePct"])
    max_loss_pct = _decimal(budget["maxEquityLossPctAtShock"])
    if max_gross <= 0:
        raise PolicyDecisionError("budget.maxGrossToEquity must be positive")
    if max_concentration <= 0 or max_concentration > 1:
        raise PolicyDecisionError(
            "budget.maxLargestPositionGrossShare must be in (0, 1]"
        )
    if min_available < 0 or min_available > 1:
        raise PolicyDecisionError("budget.minAvailableEquityRatio must be in [0, 1]")
    if shock_pct <= 0 or shock_pct > 100:
        raise PolicyDecisionError("budget.shockMagnitudePct must be in (0, 100]")
    if max_loss_pct <= 0 or max_loss_pct > 100:
        raise PolicyDecisionError("budget.maxEquityLossPctAtShock must be in (0, 100]")

    gross_to_equity = _decimal(exposure_ledger.get("grossToEquity"))
    concentration = _decimal(exposure_ledger.get("largestPositionGrossShare"))
    available_ratio = _decimal(exposure_ledger.get("availableEquityRatio"))
    positions = exposure_ledger.get("positions")
    if not isinstance(positions, list):
        raise PolicyDecisionError("ledger.positions must be a list")
    largest_equity_multiple = max(
        (_decimal(row.get("equityMultiple")) for row in positions),
        default=Decimal("0"),
    )
    shock_loss_pct = largest_equity_multiple * shock_pct
    decision = _risk_budget_decision(
        {
            "complete": True,
            "missingBudgetInputs": [],
            "grossToEquity": gross_to_equity,
            "maxGrossToEquity": max_gross,
            "largestPositionGrossShare": concentration,
            "maxLargestPositionGrossShare": max_concentration,
            "availableEquityRatio": available_ratio,
            "minAvailableEquityRatio": min_available,
            "shockLossPct": shock_loss_pct,
            "maxEquityLossPctAtShock": max_loss_pct,
        }
    )

    rows = [
        ("MAX_GROSS_TO_EQUITY", gross_to_equity, max_gross, None),
        ("MAX_LARGEST_POSITION_GROSS_SHARE", concentration, max_concentration, None),
        ("MIN_AVAILABLE_EQUITY_RATIO", available_ratio, min_available, None),
        ("MAX_EQUITY_LOSS_AT_NAMED_SHOCK", shock_loss_pct, max_loss_pct, shock_pct),
    ]
    checks = []
    for check_id, observed, limit, shock in rows:
        status = decision["statuses"][check_id]
        row = {
            "id": check_id,
            "observed": format(observed.quantize(Decimal("0.000001")), "f"),
            "limit": format(limit.quantize(Decimal("0.000001")), "f"),
            "passed": status == "PASS",
        }
        if shock is not None:
            row["shockMagnitudePct"] = format(
                shock.quantize(Decimal("0.000001")), "f"
            )
        checks.append(row)
    breached = [row["id"] for row in checks if not row["passed"]]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.risk-limit-evaluation",
        "componentId": "risk-limit-evaluator",
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "standing": decision["standing"],
        "checks": checks,
        "breachedChecks": breached,
    }


def _counterfactual_gate_statuses(facts: dict[str, Any]) -> dict[str, str]:
    standing = facts.get("riskBudgetStanding")
    if standing == "SATISFIED":
        risk = "PASS"
    elif standing == "BREACHED":
        risk = "FAIL"
    else:
        risk = "INCOMPLETE"

    action = facts["action"]
    if action == "DE_RISK":
        gross = (
            "PASS"
            if facts["projectedGrossToEquity"] < facts["baselineGrossToEquity"]
            else "FAIL"
        )
    elif action in {"HOLD", "RECONCILE"}:
        gross = (
            "PASS"
            if facts["projectedGrossToEquity"] == facts["baselineGrossToEquity"]
            else "FAIL"
        )
    else:
        gross = "PASS"

    needs_new = facts["needsNewPositionEvidence"]
    margin = (
        "PASS"
        if needs_new and facts["marginMeasured"]
        else "INCOMPLETE"
        if needs_new
        else "NOT_REQUIRED"
    )
    carry = (
        "PASS"
        if needs_new and facts["carryMeasured"]
        else "INCOMPLETE"
        if needs_new
        else "NOT_REQUIRED"
    )
    changes = facts["changesPosition"]
    liquidity = (
        "PASS"
        if changes and facts["liquidityMeasured"]
        else "INCOMPLETE"
        if changes
        else "NOT_REQUIRED"
    )

    if action == "HEDGE":
        factor = facts.get("targetFactorStanding")
        target = (
            "PASS"
            if factor == "TARGET_FACTOR_ABSOLUTE_EXPOSURE_REDUCED"
            else "FAIL"
            if factor
            in {
                "TARGET_FACTOR_ABSOLUTE_EXPOSURE_INCREASED",
                "TARGET_FACTOR_ABSOLUTE_EXPOSURE_UNCHANGED",
            }
            else "INCOMPLETE"
        )
        if (
            facts.get("dependenceComponentId") == "portfolio-dependence-analysis"
            and facts.get("dependenceSampleCountPresent") is True
        ):
            dependence = "PASS"
        elif (
            facts.get("dependencePresent") is True
            and facts.get("dependenceComponentId") != "portfolio-dependence-analysis"
        ):
            dependence = "FAIL"
        else:
            dependence = "INCOMPLETE"
    else:
        target = "NOT_REQUIRED"
        dependence = "NOT_REQUIRED"

    if action == "DIVERSIFY":
        if facts.get("diversificationComponentId") == "portfolio-dependence-analysis":
            diversification = "PASS"
        elif (
            facts.get("diversificationPresent") is True
            and facts.get("diversificationComponentId")
            != "portfolio-dependence-analysis"
        ):
            diversification = "FAIL"
        else:
            diversification = "INCOMPLETE"
    else:
        diversification = "NOT_REQUIRED"

    reconciliation = (
        "PASS"
        if action == "RECONCILE"
        and facts.get("reconciliationSignpostDefined") is True
        else "INCOMPLETE"
        if action == "RECONCILE"
        else "NOT_REQUIRED"
    )
    return {
        "RISK_BUDGET": risk,
        "GROSS_DIRECTION": gross,
        "MARGIN_DELTA": margin,
        "FUNDING_BASIS_CARRY": carry,
        "LIQUIDITY_COST": liquidity,
        "TARGET_FACTOR_MECHANICS": target,
        "DEPENDENCE_EVIDENCE": dependence,
        "DIVERSIFICATION_EVIDENCE": diversification,
        "RECONCILIATION_SIGNPOST": reconciliation,
    }


def evaluate_counterfactual_gate_policy(
    *,
    repo: Path,
    config_path: Path,
    counterfactual: dict[str, Any],
    risk_budget_evaluation: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del repo
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise PolicyDecisionError("unexpected execution-policy kind")
    _require_local_implementation(cfg)

    evidence = evidence or {}
    action = str(counterfactual.get("action") or "").upper()
    allowed_actions = {"DE_RISK", "HEDGE", "DIVERSIFY", "HOLD", "RECONCILE"}
    if action not in allowed_actions:
        raise PolicyDecisionError("counterfactual action is invalid")
    baseline = counterfactual.get("baseline") or {}
    projected = counterfactual.get("projected") or {}
    mechanics = counterfactual.get("hedgeMechanics") or {}
    dependence = evidence.get("dependence")
    diversification = evidence.get("diversification")
    facts = {
        "action": action,
        "riskBudgetStanding": (risk_budget_evaluation or {}).get("standing"),
        "baselineGrossToEquity": _decimal(baseline.get("grossToEquity")),
        "projectedGrossToEquity": _decimal(projected.get("grossToEquity")),
        "changesPosition": action in {"DE_RISK", "HEDGE", "DIVERSIFY"},
        "needsNewPositionEvidence": action in {"HEDGE", "DIVERSIFY"},
        "marginMeasured": isinstance(evidence.get("margin"), dict)
        and evidence["margin"].get("measured") is True,
        "carryMeasured": isinstance(evidence.get("carry"), dict)
        and evidence["carry"].get("measured") is True,
        "liquidityMeasured": isinstance(evidence.get("liquidity"), dict)
        and evidence["liquidity"].get("measured") is True,
        "targetFactorStanding": mechanics.get("standing"),
        "dependencePresent": isinstance(dependence, dict),
        "dependenceComponentId": (
            dependence.get("componentId") if isinstance(dependence, dict) else None
        ),
        "dependenceSampleCountPresent": isinstance(dependence, dict)
        and dependence.get("overlapReturnCount") is not None,
        "diversificationPresent": isinstance(diversification, dict),
        "diversificationComponentId": (
            diversification.get("componentId")
            if isinstance(diversification, dict)
            else None
        ),
        "reconciliationSignpostDefined": isinstance(
            evidence.get("reconciliationSignpost"), dict
        )
        and evidence["reconciliationSignpost"].get("defined") is True,
    }
    statuses = _counterfactual_gate_statuses(facts)
    order = [
        "RISK_BUDGET",
        "GROSS_DIRECTION",
        "MARGIN_DELTA",
        "FUNDING_BASIS_CARRY",
        "LIQUIDITY_COST",
        "TARGET_FACTOR_MECHANICS",
        "DEPENDENCE_EVIDENCE",
        "DIVERSIFICATION_EVIDENCE",
        "RECONCILIATION_SIGNPOST",
    ]
    detail = {
        "RISK_BUDGET": "explicit risk-limit evaluation",
        "GROSS_DIRECTION": "action exposure-direction constraint",
        "MARGIN_DELTA": "incremental margin evidence",
        "FUNDING_BASIS_CARRY": "funding/basis carry evidence",
        "LIQUIDITY_COST": "spread/impact evidence",
        "TARGET_FACTOR_MECHANICS": "named target-factor mechanics",
        "DEPENDENCE_EVIDENCE": "registered dependence evidence",
        "DIVERSIFICATION_EVIDENCE": "registered diversification evidence",
        "RECONCILIATION_SIGNPOST": "explicit next reconciliation evidence boundary",
    }
    checks = [
        {"id": check_id, "status": statuses[check_id], "detail": detail[check_id]}
        for check_id in order
    ]
    failures = [row["id"] for row in checks if row["status"] == "FAIL"]
    incomplete = [row["id"] for row in checks if row["status"] == "INCOMPLETE"]
    standing = "FAIL" if failures else "INCOMPLETE" if incomplete else "PASS"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.pre-trade-evidence-control",
        "componentId": "pre-trade-evidence-control",
        "decisionImplementation": DECISION_IMPLEMENTATION,
        "scenarioId": counterfactual.get("scenarioId"),
        "action": action,
        "standing": standing,
        "checks": checks,
        "failedChecks": failures,
        "incompleteChecks": incomplete,
    }


def enforce_non_live(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowNonLive"]:
        raise PolicyDecisionError("policy denied non-live execution lane")
    return {
        "standing": "NON_LIVE_POLICY_ALLOWED",
        **decision,
        "externalFinancialWritesAllowed": False,
    }


def enforce_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowExternalWrite"]:
        raise PolicyDecisionError("policy denied external financial write")
    raise PolicyDecisionError("external-write execution path is not implemented")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--mode", choices=("non-live", "external-write"), default="non-live")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = (
        enforce_non_live(args.repo, args.config)
        if args.mode == "non-live"
        else enforce_external_write(args.repo, args.config)
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
