from __future__ import annotations

import argparse
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation
import subprocess
from typing import Any


class ExecutionPolicyError(RuntimeError):
    """Fail-closed execution-policy evaluation error."""


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ExecutionPolicyError(f"expected JSON object: {path}")
    return value


def _resolve(repo: Path, relative: str) -> Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError as exc:
        raise ExecutionPolicyError(f"policy path escapes repository: {relative}") from exc
    if not path.is_file():
        raise ExecutionPolicyError(f"policy input unavailable: {relative}")
    return path


def _evaluate_opa_value(*, binary: Path, policy: Path, query: str, input_doc: dict[str, Any]) -> Any:
    if not binary.is_file():
        raise ExecutionPolicyError(f"OPA binary unavailable: {binary}")
    proc = subprocess.run(
        [str(binary), "eval", "--format=json", "--data", str(policy), "--stdin-input", query],
        input=json.dumps(input_doc),
        text=True,
        capture_output=True,
        timeout=10,
    )
    if proc.returncode != 0:
        raise ExecutionPolicyError(f"OPA policy evaluation failed: {proc.stderr.strip()}")
    try:
        envelope = json.loads(proc.stdout)
        return envelope["result"][0]["expressions"][0]["value"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise ExecutionPolicyError("unexpected OPA policy result envelope") from exc


def _evaluate_opa(*, binary: Path, policy: Path, query: str, input_doc: dict[str, Any]) -> bool:
    value = _evaluate_opa_value(binary=binary, policy=policy, query=query, input_doc=input_doc)
    if not isinstance(value, bool):
        raise ExecutionPolicyError(f"unexpected OPA boolean policy result: {value!r}")
    return value


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ExecutionPolicyError(f"invalid decimal policy fact: {value!r}") from exc


def evaluate_execution_policy(repo: Path, config_path: Path) -> dict[str, Any]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise ExecutionPolicyError("unexpected execution-policy kind")

    write_doc = _load_json(_resolve(repo, cfg["externalWritePolicyInputContract"]))
    if write_doc.get("kind") != "ordivon.capital.market.external-write-policy-input":
        raise ExecutionPolicyError("external-write policy input missing")

    engine = cfg.get("policyEngine")
    if not isinstance(engine, dict) or engine.get("name") != "OPA":
        raise ExecutionPolicyError("OPA policy engine is required")
    policy = _resolve(repo, str(engine.get("policy") or ""))
    binary = Path(str(engine.get("binary") or ""))

    policy_input = {
        "currentLane": cfg.get("currentLane"),
        "writePolicy": write_doc,
    }
    allow_non_live = _evaluate_opa(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryNonLive") or ""),
        input_doc=policy_input,
    )
    allow_external_write = _evaluate_opa(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryExternalWrite") or ""),
        input_doc=policy_input,
    )
    if allow_non_live and allow_external_write:
        raise ExecutionPolicyError("OPA returned mutually incompatible lane decisions")

    return {
        "policyEngine": "OPA",
        "currentLane": cfg.get("currentLane"),
        "allowNonLive": allow_non_live,
        "allowExternalWrite": allow_external_write,
        "externalWritePolicyStanding": write_doc.get("state"),
        "externalWriteVerifier": write_doc.get("effectVerifier", "NOT_IMPLEMENTED"),
        "providerWriteCapabilityBound": bool(write_doc.get("providerWriteCapabilityBound", False)),
        "externalFinancialWriteAllowedByContract": bool(write_doc.get("externalFinancialWriteAllowed", False)),
    }


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
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise ExecutionPolicyError("unexpected execution-policy kind")
    engine = cfg.get("policyEngine")
    if not isinstance(engine, dict) or engine.get("name") != "OPA":
        raise ExecutionPolicyError("OPA policy engine is required")
    policy = _resolve(repo, str(engine.get("policy") or ""))
    binary = Path(str(engine.get("binary") or ""))

    venue = str(reality.get("venue") or "").upper()
    positions = [
        row for row in (reality.get("positions") or [])
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

    policy_input = {
        "liveTest": {
            "venue": venue,
            "permissionStanding": reality.get("permissionStanding"),
            "externalFinancialWriteAttempted": reality.get("externalFinancialWriteAttempted"),
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
    }
    decision = _evaluate_opa_value(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryLiveTestAccount") or ""),
        input_doc=policy_input,
    )
    if not isinstance(decision, dict) or not isinstance(decision.get("admitted"), bool) or not isinstance(decision.get("blockingReasons"), list):
        raise ExecutionPolicyError("unexpected OPA live-test decision")
    admitted = decision["admitted"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.live-test-account-admission",
        "policyEngine": "OPA",
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


def _opa_engine(repo: Path, config_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path, Path]:
    cfg = _load_json(config_path)
    if cfg.get("kind") != "ordivon.capital.market.execution-policy":
        raise ExecutionPolicyError("unexpected execution-policy kind")
    engine = cfg.get("policyEngine")
    if not isinstance(engine, dict) or engine.get("name") != "OPA":
        raise ExecutionPolicyError("OPA policy engine is required")
    policy = _resolve(repo, str(engine.get("policy") or ""))
    binary = Path(str(engine.get("binary") or ""))
    return cfg, engine, policy, binary


def evaluate_risk_budget_policy(
    *,
    repo: Path,
    config_path: Path,
    exposure_ledger: dict[str, Any],
    budget: dict[str, Any],
) -> dict[str, Any]:
    _, engine, policy, binary = _opa_engine(repo, config_path)
    required = (
        "maxGrossToEquity",
        "maxLargestPositionGrossShare",
        "minAvailableEquityRatio",
        "shockMagnitudePct",
        "maxEquityLossPctAtShock",
    )
    missing = [key for key in required if budget.get(key) is None]
    if missing:
        decision = _evaluate_opa_value(
            binary=binary,
            policy=policy,
            query=str(engine.get("queryRiskBudget") or ""),
            input_doc={"riskBudget": {"complete": False, "missingBudgetInputs": missing}},
        )
        return {
            "schemaVersion": 1,
            "kind": "ordivon.capital.market.risk-limit-evaluation",
            "componentId": "risk-limit-evaluator",
            "policyEngine": "OPA",
            "standing": decision["standing"],
            "missingBudgetInputs": decision["missingBudgetInputs"],
        }

    max_gross = _decimal(budget["maxGrossToEquity"])
    max_concentration = _decimal(budget["maxLargestPositionGrossShare"])
    min_available = _decimal(budget["minAvailableEquityRatio"])
    shock_pct = _decimal(budget["shockMagnitudePct"])
    max_loss_pct = _decimal(budget["maxEquityLossPctAtShock"])
    if max_gross <= 0:
        raise ExecutionPolicyError("budget.maxGrossToEquity must be positive")
    if max_concentration <= 0 or max_concentration > 1:
        raise ExecutionPolicyError("budget.maxLargestPositionGrossShare must be in (0, 1]")
    if min_available < 0 or min_available > 1:
        raise ExecutionPolicyError("budget.minAvailableEquityRatio must be in [0, 1]")
    if shock_pct <= 0 or shock_pct > 100:
        raise ExecutionPolicyError("budget.shockMagnitudePct must be in (0, 100]")
    if max_loss_pct <= 0 or max_loss_pct > 100:
        raise ExecutionPolicyError("budget.maxEquityLossPctAtShock must be in (0, 100]")

    gross_to_equity = _decimal(exposure_ledger.get("grossToEquity"))
    concentration = _decimal(exposure_ledger.get("largestPositionGrossShare"))
    available_ratio = _decimal(exposure_ledger.get("availableEquityRatio"))
    positions = exposure_ledger.get("positions")
    if not isinstance(positions, list):
        raise ExecutionPolicyError("ledger.positions must be a list")
    largest_equity_multiple = max(
        (_decimal(row.get("equityMultiple")) for row in positions),
        default=Decimal("0"),
    )
    shock_loss_pct = largest_equity_multiple * shock_pct
    facts = {
        "complete": True,
        "missingBudgetInputs": [],
        "grossToEquity": float(gross_to_equity),
        "maxGrossToEquity": float(max_gross),
        "largestPositionGrossShare": float(concentration),
        "maxLargestPositionGrossShare": float(max_concentration),
        "availableEquityRatio": float(available_ratio),
        "minAvailableEquityRatio": float(min_available),
        "shockLossPct": float(shock_loss_pct),
        "maxEquityLossPctAtShock": float(max_loss_pct),
    }
    decision = _evaluate_opa_value(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryRiskBudget") or ""),
        input_doc={"riskBudget": facts},
    )
    statuses = decision.get("statuses")
    if not isinstance(statuses, dict):
        raise ExecutionPolicyError("unexpected OPA risk-budget decision")
    rows = [
        ("MAX_GROSS_TO_EQUITY", gross_to_equity, max_gross, None),
        ("MAX_LARGEST_POSITION_GROSS_SHARE", concentration, max_concentration, None),
        ("MIN_AVAILABLE_EQUITY_RATIO", available_ratio, min_available, None),
        ("MAX_EQUITY_LOSS_AT_NAMED_SHOCK", shock_loss_pct, max_loss_pct, shock_pct),
    ]
    checks = []
    for check_id, observed, limit, shock in rows:
        status = statuses.get(check_id)
        if status not in {"PASS", "FAIL"}:
            raise ExecutionPolicyError(f"unexpected OPA risk-budget status for {check_id}: {status!r}")
        row = {
            "id": check_id,
            "observed": format(observed.quantize(Decimal("0.000001")), "f"),
            "limit": format(limit.quantize(Decimal("0.000001")), "f"),
            "passed": status == "PASS",
        }
        if shock is not None:
            row["shockMagnitudePct"] = format(shock.quantize(Decimal("0.000001")), "f")
        checks.append(row)
    breached = [row["id"] for row in checks if not row["passed"]]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.risk-limit-evaluation",
        "componentId": "risk-limit-evaluator",
        "policyEngine": "OPA",
        "standing": decision.get("standing"),
        "checks": checks,
        "breachedChecks": breached,
    }


def evaluate_counterfactual_gate_policy(
    *,
    repo: Path,
    config_path: Path,
    counterfactual: dict[str, Any],
    risk_budget_evaluation: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _, engine, policy, binary = _opa_engine(repo, config_path)
    evidence = evidence or {}
    action = str(counterfactual.get("action") or "").upper()
    allowed_actions = {"DE_RISK", "HEDGE", "DIVERSIFY", "HOLD", "RECONCILE"}
    if action not in allowed_actions:
        raise ExecutionPolicyError("counterfactual action is invalid")
    baseline = counterfactual.get("baseline") or {}
    projected = counterfactual.get("projected") or {}
    mechanics = counterfactual.get("hedgeMechanics") or {}
    dependence = evidence.get("dependence")
    diversification = evidence.get("diversification")
    facts = {
        "action": action,
        "riskBudgetStanding": (risk_budget_evaluation or {}).get("standing"),
        "baselineGrossToEquity": float(_decimal(baseline.get("grossToEquity"))),
        "projectedGrossToEquity": float(_decimal(projected.get("grossToEquity"))),
        "changesPosition": action in {"DE_RISK", "HEDGE", "DIVERSIFY"},
        "needsNewPositionEvidence": action in {"HEDGE", "DIVERSIFY"},
        "marginMeasured": isinstance(evidence.get("margin"), dict) and evidence["margin"].get("measured") is True,
        "carryMeasured": isinstance(evidence.get("carry"), dict) and evidence["carry"].get("measured") is True,
        "liquidityMeasured": isinstance(evidence.get("liquidity"), dict) and evidence["liquidity"].get("measured") is True,
        "targetFactorStanding": mechanics.get("standing"),
        "dependencePresent": isinstance(dependence, dict),
        "dependenceComponentId": dependence.get("componentId") if isinstance(dependence, dict) else None,
        "dependenceSampleCountPresent": isinstance(dependence, dict) and dependence.get("overlapReturnCount") is not None,
        "diversificationPresent": isinstance(diversification, dict),
        "diversificationComponentId": diversification.get("componentId") if isinstance(diversification, dict) else None,
        "reconciliationSignpostDefined": isinstance(evidence.get("reconciliationSignpost"), dict) and evidence["reconciliationSignpost"].get("defined") is True,
    }
    statuses = _evaluate_opa_value(
        binary=binary,
        policy=policy,
        query=str(engine.get("queryCounterfactualGate") or ""),
        input_doc={"counterfactual": facts},
    )
    if not isinstance(statuses, dict):
        raise ExecutionPolicyError("unexpected OPA counterfactual-gate decision")
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
    checks = []
    for check_id in order:
        status = statuses.get(check_id)
        if status not in {"PASS", "FAIL", "INCOMPLETE", "NOT_REQUIRED"}:
            raise ExecutionPolicyError(f"unexpected OPA counterfactual status for {check_id}: {status!r}")
        checks.append({"id": check_id, "status": status, "detail": detail[check_id]})
    failures = [row["id"] for row in checks if row["status"] == "FAIL"]
    incomplete = [row["id"] for row in checks if row["status"] == "INCOMPLETE"]
    standing = "FAIL" if failures else "INCOMPLETE" if incomplete else "PASS"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.market.pre-trade-evidence-control",
        "componentId": "pre-trade-evidence-control",
        "policyEngine": "OPA",
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
        raise ExecutionPolicyError("OPA denied non-live execution lane")
    return {
        "standing": "NON_LIVE_POLICY_ALLOWED",
        **decision,
        "externalFinancialWritesAllowed": False,
    }


def enforce_external_write(repo: Path, config_path: Path) -> dict[str, Any]:
    decision = evaluate_execution_policy(repo, config_path)
    if not decision["allowExternalWrite"]:
        raise ExecutionPolicyError("OPA denied external financial write")
    raise ExecutionPolicyError("external-write execution path is not implemented")


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
