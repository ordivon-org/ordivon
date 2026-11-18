"""Independent, stdlib-only economic replay of a Capital multistage policy.

Consumes public JSON problem and solver result. Does not import the optimizer,
SciPy, portfolio constraint matrices or the optimizer's numeric objective.
It checks accounting identities and observed-edge collateral before deposits.
This is NOT a proof of global optimality, forecast calibration, or broker truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class EconomicReplayMismatch(ValueError):
    """A reported policy contradicts its supplied economic scenario contract."""


# The native SLSQP consumer admits feasibility errors up to 1e-7 in 1r.
# Ten times that scale covers arithmetic reconstruction and JSON round trips,
# NOT an investor-defined risk budget or a brokerage rounding rule.
_NUMERIC_TOLERANCE_R = 1e-6


def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EconomicReplayMismatch(f"{where}: finite numeric field required")
    result = float(value)
    if not math.isfinite(result):
        raise EconomicReplayMismatch(f"{where}: nonfinite economic field")
    return result


def _near(actual: float, claimed: Any, where: str) -> float:
    expected = _number(claimed, where)
    if not math.isclose(actual, expected, rel_tol=1e-8, abs_tol=_NUMERIC_TOLERANCE_R):
        raise EconomicReplayMismatch(
            f"{where}: independent cashflow replay differs from reported result"
        )
    return abs(actual - expected)


def _vector(values: Any, where: str, n: int) -> tuple[float, ...]:
    if not isinstance(values, (tuple, list)) or len(values) != n:
        raise EconomicReplayMismatch(f"{where}: unexpected asset dimension")
    return tuple(_number(v, where) for v in values)


def _ce(values: list[tuple[float, float]], gamma: float) -> float:
    if gamma == 1.0:
        return math.exp(math.fsum(p * math.log(w) for p, w in values))
    moment = math.fsum(p * math.exp((1 - gamma) * math.log(w)) for p, w in values)
    return math.exp(math.log(moment) / (1 - gamma))


def replay_multistage_json(
    problem: Mapping[str, Any], solution: Mapping[str, Any]
) -> dict[str, Any]:
    """Falsify cashflow, terminal output, and utility using a separate algorithm.

    Every leaf and information node is recomputed from explicit parent holdings.
    The policy is not optimized here. No price, gamma, margin or rate is guessed.
    """
    if not isinstance(problem, Mapping) or not isinstance(solution, Mapping):
        raise EconomicReplayMismatch("problem and solution must be JSON objects")
    gamma = _number(problem.get("gamma"), "gamma")
    if gamma <= 0:
        raise EconomicReplayMismatch("positive CRRA gamma required")
    raw_nodes = problem.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise EconomicReplayMismatch("nonempty information nodes required")
    if not all(isinstance(n, dict) for n in raw_nodes):
        raise EconomicReplayMismatch("information node must be a JSON object")
    ordered = sorted(raw_nodes, key=lambda node: (node["t"], node["id"]))
    by_id = {node["id"]: node for node in ordered}
    if len(by_id) != len(ordered):
        raise EconomicReplayMismatch("duplicate information node")
    roots = [node for node in ordered if node.get("parent") is None]
    if len(roots) != 1 or roots[0].get("t") != 0:
        raise EconomicReplayMismatch("exact time-zero root required")
    n_assets = len(roots[0].get("initial_margin", []))
    if n_assets < 1:
        raise EconomicReplayMismatch("nonempty risky asset universe required")
    decisions = solution.get("node_decisions_r")
    outcomes = solution.get("terminal_distribution")
    if not isinstance(decisions, dict) or not isinstance(outcomes, dict):
        raise EconomicReplayMismatch("public policy and distribution required")
    decision_ids = {node["id"] for node in ordered if not node.get("terminal", False)}
    leaf_ids = set(by_id) - decision_ids
    if set(decisions) != decision_ids or set(outcomes) != leaf_ids:
        raise EconomicReplayMismatch("policy and terminal node identity mismatch")
    outflows = problem.get("node_outflow_after_contribution_r") or {}
    claims = problem.get("terminal_liabilities_r") or {}
    if set(outflows) - decision_ids or set(claims) - leaf_ids:
        raise EconomicReplayMismatch("obligation belongs to wrong information node")
    if (
        problem.get("node_outflow_after_contribution_r") is not None
        and set(outflows) != decision_ids
    ):
        raise EconomicReplayMismatch("intermediate obligation coverage mismatch")
    if problem.get("terminal_liabilities_r") is not None and set(claims) != leaf_ids:
        raise EconomicReplayMismatch("terminal obligation coverage mismatch")

    positions: dict[str, tuple[float, ...]] = {}
    cash: dict[str, float] = {}
    debt: dict[str, float] = {}
    probability: dict[str, float] = {}
    gross_terminal: list[tuple[float, float]] = []
    disposable_terminal: list[tuple[float, float]] = []
    max_identity_residual = 0.0
    min_collateral_surplus = math.inf
    child_sums: dict[str, float] = defaultdict(float)
    depth: set[int] = set()

    for node in ordered:
        ident = node["id"]
        parent = node.get("parent")
        conditional = _number(node.get("conditional_probability"), f"{ident}.prob")
        if conditional <= 0:
            raise EconomicReplayMismatch("nonpositive conditional probability")
        if parent is None:
            if conditional != 1.0:
                raise EconomicReplayMismatch("root conditional probability is not one")
            path_prob = 1.0
            incoming_assets = (0.0,) * n_assets
            incoming_equity = 0.0
            if node.get("risky_gross", []) or node.get("maintenance", []):
                raise EconomicReplayMismatch("root has unexpected incoming market state")
        else:
            if parent not in positions:
                raise EconomicReplayMismatch("child precedes a missing decision")
            if node["t"] != by_id[parent]["t"] + 1:
                raise EconomicReplayMismatch("skipped observation month")
            path_prob = probability[parent] * conditional
            child_sums[parent] += conditional
            observed_gross = _vector(node.get("risky_gross", []), f"{ident}.gross", n_assets)
            maintenance = _vector(node.get("maintenance", []), f"{ident}.maintenance", n_assets)
            incoming_assets = tuple(
                a * g for a, g in zip(positions[parent], observed_gross, strict=True)
            )
            incoming_equity = (
                math.fsum(incoming_assets)
                + cash[parent] * _number(node.get("cash_gross", 1.0), "cash_gross")
                - debt[parent] * _number(node.get("debt_gross", 1.0), "debt_gross")
            )
            collateral = math.fsum(a * m for a, m in zip(incoming_assets, maintenance, strict=True))
            min_collateral_surplus = min(min_collateral_surplus, incoming_equity - collateral)
            if incoming_equity < -_NUMERIC_TOLERANCE_R:
                raise EconomicReplayMismatch(f"{ident}: insolvency before next deposit")
            if incoming_equity + _NUMERIC_TOLERANCE_R < collateral:
                raise EconomicReplayMismatch(f"{ident}: predeposit maintenance breached")
        probability[ident] = path_prob
        if ident in decision_ids:
            row = decisions[ident]
            exposure = _vector(row.get("assetExposuresR"), f"{ident}.exposure", n_assets)
            cash_r = _number(row.get("cashR"), f"{ident}.cash")
            debt_r = _number(row.get("debtR"), f"{ident}.debt")
            if min(*exposure, cash_r, debt_r) < -_NUMERIC_TOLERANCE_R:
                raise EconomicReplayMismatch(f"{ident}: negative long-only balance")
            costs = _vector(node.get("turnover_cost", []), f"{ident}.cost", n_assets)
            margins = _vector(node.get("initial_margin", []), f"{ident}.initial_margin", n_assets)
            trade_cost = math.fsum(
                k * abs(a - old) for k, a, old in zip(costs, exposure, incoming_assets, strict=True)
            )
            due = _number(outflows.get(ident, 0.0), f"{ident}.outflow")
            if due < 0:
                raise EconomicReplayMismatch("negative intermediate obligation")
            funded = incoming_equity + 1.0 - due
            posttrade_equity = math.fsum(exposure) + cash_r - debt_r
            max_identity_residual = max(
                max_identity_residual,
                _near(funded, posttrade_equity + trade_cost, f"{ident}.budget"),
                _near(trade_cost, row.get("tradeCostR"), f"{ident}.tradeCostR"),
                _near(posttrade_equity, row.get("postTradeEquityR"), f"{ident}.postTradeEquityR"),
                _near(path_prob, row.get("historyProbability"), f"{ident}.historyProbability"),
            )
            _near(float(node["t"]), row.get("stage"), f"{ident}.stage")
            margin_required = math.fsum(a * m for a, m in zip(exposure, margins, strict=True))
            min_collateral_surplus = min(min_collateral_surplus, posttrade_equity - margin_required)
            if posttrade_equity + _NUMERIC_TOLERANCE_R < margin_required:
                raise EconomicReplayMismatch(f"{ident}: initial margin breached")
            positions[ident], cash[ident], debt[ident] = exposure, cash_r, debt_r
        else:
            depth.add(node["t"])
            claim = _number(claims.get(ident, 0.0), f"{ident}.terminal_obligation")
            disposable = incoming_equity - claim
            if disposable <= 0:
                raise EconomicReplayMismatch(f"{ident}: nonpositive terminal consumption")
            row = outcomes[ident]
            max_identity_residual = max(
                max_identity_residual,
                _near(path_prob, row.get("probability"), f"{ident}.terminal_probability"),
                _near(incoming_equity, row.get("terminalR"), f"{ident}.terminalR"),
                _near(claim, row.get("obligationR"), f"{ident}.obligationR"),
                _near(disposable, row.get("disposableTerminalR"), f"{ident}.disposableTerminalR"),
            )
            gross_terminal.append((path_prob, incoming_equity))
            disposable_terminal.append((path_prob, disposable))

    if any(
        not math.isclose(child_sums.get(ident, 0), 1.0, abs_tol=1e-10) for ident in decision_ids
    ):
        raise EconomicReplayMismatch("conditional children do not sum to one")
    if len(depth) != 1:
        raise EconomicReplayMismatch("unequal path contribution horizon")
    if not math.isclose(math.fsum(p for p, _ in gross_terminal), 1.0, abs_tol=1e-10):
        raise EconomicReplayMismatch("terminal probability mass is not one")
    horizon = depth.pop()
    _near(float(horizon), solution.get("contributions_r_per_path"), "contributions")
    expected_gross = math.fsum(p * w for p, w in gross_terminal)
    expected_disposable = math.fsum(p * w for p, w in disposable_terminal)
    if gamma == 1:
        utility = math.fsum(p * math.log(w) for p, w in disposable_terminal)
    else:
        utility = math.fsum(
            p * math.expm1((1 - gamma) * math.log(w)) / (1 - gamma) for p, w in disposable_terminal
        )
    max_identity_residual = max(
        max_identity_residual,
        _near(expected_gross, solution.get("expected_terminal_r"), "expected_gross"),
        _near(
            expected_disposable,
            solution.get("expected_disposable_terminal_r"),
            "expected_disposable",
        ),
        _near(utility, solution.get("expected_utility"), "expected_utility"),
        _near(
            _ce(gross_terminal, gamma), solution.get("certainty_equivalent_terminal_r"), "ce_gross"
        ),
        _near(
            _ce(disposable_terminal, gamma),
            solution.get("certainty_equivalent_disposable_r"),
            "ce_disposable",
        ),
    )
    first = decisions[roots[0]["id"]]
    if _vector(solution.get("root_risky_r"), "root_risky", n_assets) != tuple(
        first["assetExposuresR"]
    ):
        raise EconomicReplayMismatch("root exposure projection inconsistent")
    max_identity_residual = max(
        max_identity_residual,
        _near(_number(first["cashR"], "root cash"), solution.get("root_cash_r"), "root_cash"),
        _near(_number(first["debtR"], "root debt"), solution.get("root_debt_r"), "root_debt"),
    )
    gap = _number(solution.get("concavity_global_utility_gap_upper"), "reported_gap")
    if gap < 0:
        raise EconomicReplayMismatch("negative reported gap")
    encoded = json.dumps(
        {"problem": problem, "solution": solution}, sort_keys=True, separators=(",", ":")
    )
    return {
        "standing": "INDEPENDENT_STDLIB_CASHFLOW_REPLAY_NOT_OPTIMALITY_CERTIFICATE",
        "effects": "NONE_NO_BROKER_NO_ACCOUNTING",
        "input_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "decision_node_count": len(decision_ids),
        "terminal_node_count": len(leaf_ids),
        "max_identity_residual_r": max_identity_residual,
        "minimum_collateral_surplus_r": min_collateral_surplus,
        "recomputed_expected_utility": utility,
        "reported_numeric_gap_not_independently_certified": gap,
        "numeric_tolerance_r": _NUMERIC_TOLERANCE_R,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Independent Capital cashflow replay")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = replay_multistage_json(payload["problem"], payload["solution"])
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
