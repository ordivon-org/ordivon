"""Compose pure Research PIT evidence with the existing Portfolio solver.

This is a read-only use-case boundary: no market data fetch, PG, orders or OMS.
Forecast evidence remains owned by Research; optimizer mechanics by Portfolio.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..portfolio.multistage_policy import InformationNode, MultistageProblem, solve_multistage
from ..research.pit_joint_forecast import PointInTimeError, from_json_payload, load_pit_payload


def solve_pit_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Research-to-Portfolio native consumer, no second optimization engine.

    The only market probabilities are the caller's past-visible empirical or
    lagged-neighbor hypotheses. The caller must also supply actual economic
    preferences and provider financing/margin terms. This function neither
    authenticates those inputs nor creates any order/Paper event.
    """
    result = from_json_payload(payload)
    contract = result["optimizer_input"]
    vectors = {"risky_gross", "maintenance", "initial_margin", "turnover_cost"}
    nodes = tuple(
        InformationNode(
            **{key: tuple(value) if key in vectors else value for key, value in raw.items()}
        )
        for raw in contract["nodes"]
    )
    solution = solve_multistage(MultistageProblem(gamma=contract["gamma"], nodes=nodes))
    return {
        **result,
        "conditional_allocation": dataclasses.asdict(solution),
        "allocation_standing": "CONDITIONAL_UNCALIBRATED_ONE_STEP_RESEARCH",
    }

def main() -> int:
    parser = argparse.ArgumentParser(description="Research PIT evidence -> existing Portfolio optimizer")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        outcome = solve_pit_payload(load_pit_payload(args.input))
    except (PointInTimeError, ValueError, TypeError, KeyError) as exc:
        parser.error(f"incomplete PIT/Portfolio economic contract: {exc}")
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
