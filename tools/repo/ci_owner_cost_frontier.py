#!/usr/bin/env python3
"""Read-only cost scenarios over the native LPT sharder.

No scheduling effects, task selection, evidence promotion, or automatic
historical-weight replacement. Costs are explicit integer milliseconds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ci_owner_shards import MAX_SHARDS, shard_queue


def dominates(left: dict, right: dict) -> bool:
    a, b = left["modeledLatencyMs"], left["modeledTotalMs"]
    c, d = right["modeledLatencyMs"], right["modeledTotalMs"]
    return a <= c and b <= d and (a < c or b < d)


def cost_frontier(
    tasks: list[str], task_milliseconds: dict[str, int], fixed_milliseconds: int,
) -> dict:
    """Enumerate nondominated *LPT candidates*, not all optimal partitions.

    Assumes identical runners, constant per-active-lane overhead, zero
    queue wait, additive task costs, and no inter-task cache interaction.
    An empty Owner selection has no active lane; its matrix sentinel is
    preserved for representation compatibility, not counted as execution.
    """
    if not isinstance(tasks, list) or not all(isinstance(task, str) for task in tasks):
        raise ValueError("tasks must be a list of strings")
    if type(fixed_milliseconds) is not int or fixed_milliseconds < 0:
        raise ValueError("fixed overhead must be a nonnegative integer")
    if not isinstance(task_milliseconds, dict):
        raise ValueError("explicit task costs required")
    # Validate task identities, duplicates and complete weights via the
    # same admission and partition operator as the real matrix projection.
    baseline = shard_queue(tasks, 1, task_weights=task_milliseconds)
    n = sum(len(row["tasks"]) for row in baseline["include"])
    rows = []
    for cap in range(1, max(1, min(n, MAX_SHARDS)) + 1):
        matrix = baseline if cap == 1 else shard_queue(tasks, cap, task_weights=task_milliseconds)
        work = [sum(task_milliseconds[t] for t in row["tasks"])
                for row in matrix["include"] if row["tasks"]]
        rows.append({
            "cap": cap,
            "activeLanes": len(work),
            "laneWorkMs": work,
            "modeledLatencyMs": max(work) + fixed_milliseconds if work else 0,
            "modeledTotalMs": sum(work) + len(work) * fixed_milliseconds,
            "matrix": matrix,
        })
    return {
        "scope": "ADVISORY_LPT_SCENARIO_NOT_DISPATCH",
        "assumptions": [
            "homogeneous-runners", "constant-fixed-overhead", "zero-queue-wait",
            "additive-task-cost", "no-inter-task-cache-interaction",
            "formal-excluded",
        ],
        "taskMilliseconds": dict(sorted(task_milliseconds.items())),
        "fixedMilliseconds": fixed_milliseconds,
        "candidates": rows,
        "frontierCaps": [row["cap"] for row in rows
                         if not any(dominates(other, row) for other in rows)],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()
    with args.scenario.open(encoding="utf-8") as stream:
        scenario = json.load(stream)
    if not isinstance(scenario, dict) or set(scenario) != {
        "tasks", "taskMilliseconds", "fixedMilliseconds"
    }:
        raise ValueError("scenario must explicitly declare tasks, costs and overhead")
    print(json.dumps(cost_frontier(
        scenario["tasks"], scenario["taskMilliseconds"], scenario["fixedMilliseconds"]
    ), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
