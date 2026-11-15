#!/usr/bin/env python3
"""GitHub Actions runner-shard projection over already admitted Owner queue tasks.

This does NOT select, add, downgrade, or delete an Owner verification.
It partitions the existing canonical directed-consumer closure for isolated
GitHub runners, each of which executes actual native mise tasks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import affected_owners

MAX_SHARDS = 4

# Measured GitHub Actions 42452651529, 2026-11-08. These are placement
# hints only, not admission, status, proof, or consumer correctness data.
# Unknown and newly registered Owner tasks use the same conservative weight.
HISTORICAL_SECONDS = {
    "runtime:verify": 285,
    "game:verify": 238,
    "capital:verify": 89,
    "harness:queue": 79,
    "host:queue": 54,
    "composition:verify": 29,
    "network:ci": 21,
}
DEFAULT_SECONDS = 12


def shard_queue(tasks: list[str], count: int = MAX_SHARDS) -> dict[str, object]:
    if not 1 <= count <= MAX_SHARDS:
        raise ValueError("invalid CI shard count")
    canonical = {owner.queue_task for owner in affected_owners.OWNERS}
    if len(tasks) != len(set(tasks)):
        raise ValueError("duplicate selected Owner verification task")
    if set(tasks) - canonical - {"formal:verify"}:
        raise ValueError("unknown selected verification task")
    # Formal is already executed by the source-qualified dedicated step in
    # the root preflight job: it must never silently run a second time.
    owners = [task for task in tasks if task != "formal:verify"]
    # Classic Longest Processing Time (LPT) greedy bin packing: the few
    # measured slow owners start independently, while light owners fill
    # lower-load runners. This changes placement ONLY, not task selection.
    lanes: list[list[str]] = [[] for _ in range(count)]
    loads = [0] * count
    for task in sorted(
        owners,
        key=lambda candidate: (
            -HISTORICAL_SECONDS.get(candidate, DEFAULT_SECONDS),
            candidate,
        ),
    ):
        index = min(range(count), key=lambda lane: (loads[lane], lane))
        lanes[index].append(task)
        loads[index] += HISTORICAL_SECONDS.get(task, DEFAULT_SECONDS)
    included = [
        {"shard": index, "tasks": lane} for index, lane in enumerate(lanes) if lane
    ]
    # Always run an empty, successful sentinel when no owner is selected,
    # so the stable root-verification aggregate never disappears.
    if not included:
        included = [{"shard": 0, "tasks": []}]
    output = [task for row in included for task in row["tasks"]]
    if len(output) != len(owners) or set(output) != set(owners):
        raise ValueError("CI matrix does not preserve the selected task set")
    return {"include": included}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tasks_file", type=Path)
    args = parser.parse_args()
    items = args.tasks_file.read_text(encoding="utf-8").splitlines()
    if items == [""]:
        items = []
    print(json.dumps(shard_queue(items), separators=(",", ":"), sort_keys=True))


if __name__ == "__main__":
    main()
