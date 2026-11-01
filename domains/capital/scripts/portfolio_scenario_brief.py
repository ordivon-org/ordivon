#!/usr/bin/env python3
"""The Agent-consumable Capital product: raw positions + thought rules + abilities.

This is only composition glue, not a new factor/portfolio math owner.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from typing import Any

from ordivon_capital.portfolio.portfolio_counterfactuals import (
    build_counterfactual_gate_set,
    build_counterfactual_set,
)
from ordivon_capital.risk.portfolio_risk import (
    build_exposure_ledger,
    build_portfolio_risk_report,
)

# Actual read-only Agent consumer: positions -> exposure/risk -> counterfactual
# -> deterministic evidence gates. No second LEGO registry or trading authority.
_INPUT_FIELDS = frozenset(
    {
        "schemaVersion",
        "equityUsd",
        "availableEquityUsd",
        "initialMarginUsd",
        "maintenanceMarginUsd",
        "positions",
        "scenarios",
    }
)


def _single_value(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"ambiguous duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def build_agent_scenario_brief(input_data: Mapping[str, Any]) -> dict[str, Any]:
    """Materialize a read-only high-order LEGO from existing native consumers.

    A missing risk budget and missing liquidity/dependence evidence stay
    INCOMPLETE. Even a complete gate is NOT permission for execution.
    """
    if not isinstance(input_data, dict):
        raise ValueError("input must be a JSON object")
    unknown = set(input_data) - _INPUT_FIELDS
    if unknown:
        raise ValueError(f"unrecognized input fields: {', '.join(sorted(unknown))}")
    if type(input_data.get("schemaVersion")) is not int or input_data["schemaVersion"] != 1:
        raise ValueError("schemaVersion must be exactly 1")
    positions = input_data.get("positions")
    scenarios = input_data.get("scenarios")
    if not isinstance(positions, list) or not all(isinstance(row, dict) for row in positions):
        raise ValueError("positions must be an array of objects")
    if (
        not isinstance(scenarios, list)
        or not scenarios
        or not all(isinstance(row, dict) for row in scenarios)
    ):
        raise ValueError("scenarios must be a nonempty array of objects")

    ledger = build_exposure_ledger(
        equity_usd=input_data.get("equityUsd"),
        available_equity_usd=input_data.get("availableEquityUsd"),
        initial_margin_usd=input_data.get("initialMarginUsd"),
        maintenance_margin_usd=input_data.get("maintenanceMarginUsd"),
        positions=positions,
    )
    risk = build_portfolio_risk_report(exposure_ledger=ledger)
    scenario_set = build_counterfactual_set(exposure_ledger=ledger, scenarios=scenarios)
    budget = risk["nodes"]["riskLimitEvaluation"]
    gates = build_counterfactual_gate_set(
        counterfactual_set=scenario_set,
        risk_budget_by_scenario={row["scenarioId"]: budget for row in scenario_set["scenarios"]},
    )

    standings = {row["standing"] for row in gates["gates"]}
    if "FAIL" in standings or budget["standing"] == "FAIL":
        standing = "READ_ONLY_CONSTRAINT_FAILURE"
    elif "INCOMPLETE" in standings or budget["standing"] != "SATISFIED":
        standing = "READ_ONLY_EVIDENCE_INCOMPLETE"
    else:
        standing = "READ_ONLY_EVIDENCE_COMPLETE_NOT_AUTHORIZED"

    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.portfolio.agent-scenario-brief",
        "standing": standing,
        "scenarioCount": scenario_set["scenarioCount"],
        "exposureLedger": ledger,
        "riskReport": risk,
        "counterfactualSet": scenario_set,
        "gateSet": gates,
        "rankingProduced": False,
        "executionAuthorized": False,
        "limits": [
            "Counterfactual mechanics do not predict returns or rank actions.",
            "Overlapping factor exposures are not additive risk contributions.",
            "Evidence-gate PASS is not an order, trade recommendation, or execution authority.",
            "No private account read, network request or financial write is performed.",
        ],
    }


def main() -> int:
    try:
        source = json.loads(
            sys.stdin.read(),
            object_pairs_hook=_single_value,
            parse_constant=_reject_nonfinite,
        )
        brief = build_agent_scenario_brief(source)
        rendered = json.dumps(brief, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"portfolio scenario rejected: {exc}", file=sys.stderr)
        return 2
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
