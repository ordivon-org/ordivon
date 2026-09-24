#!/usr/bin/env python3
"""Evidence-derived convergence pressure gates.

This module diagnoses observations. It has no provider client and no mutation
surface. A PROVEN gate permits an experiment to be considered; it does not
grant provider authority or execute a control action.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STATUSES = {"INSUFFICIENT_EVIDENCE", "NOT_PROVEN", "PROVEN", "REGRESSED"}


def gate(name: str, status: str, reason: str, evidence: dict[str, Any]) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(status)
    return {
        "gate": name,
        "status": status,
        "reason": reason,
        "evidence": evidence,
        "allowedExperiments": [],
    }


def assess(
    queue_projection: dict[str, Any],
    ci_projection: dict[str, Any] | None = None,
    owner_cost_episodes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    qmetrics = queue_projection.get("metrics", {})
    qcoverage = queue_projection.get("coverage", {})
    queue_count = int(qcoverage.get("queueAttributedPullRequests") or 0)
    requeues = int(qmetrics.get("requeues") or 0)
    unsuccessful = int(qmetrics.get("unsuccessfulMergeGroupRuns") or 0)
    peak = qmetrics.get("observedPeakQueueDepthLowerBound")

    if queue_count == 0:
        contention = gate(
            "QUEUE_CONTENTION",
            "INSUFFICIENT_EVIDENCE",
            "no queue-attributed episodes",
            {"episodes": 0},
        )
    elif requeues == 0 and unsuccessful == 0:
        contention = gate(
            "QUEUE_CONTENTION",
            "NOT_PROVEN",
            "observed episodes contain no requeue or unsuccessful merge-group signal",
            {"episodes": queue_count, "requeues": requeues, "unsuccessfulMergeGroupRuns": unsuccessful},
        )
    else:
        contention = gate(
            "QUEUE_CONTENTION",
            "INSUFFICIENT_EVIDENCE",
            "queue disruption exists but its cause is not established as contention",
            {"episodes": queue_count, "requeues": requeues, "unsuccessfulMergeGroupRuns": unsuccessful},
        )

    if peak is None:
        high_depth = gate(
            "HIGH_QUEUE_DEPTH",
            "INSUFFICIENT_EVIDENCE",
            "no reconstructed queue depth",
            {"observedPeakQueueDepthLowerBound": None},
        )
    elif float(peak) <= 2:
        high_depth = gate(
            "HIGH_QUEUE_DEPTH",
            "NOT_PROVEN",
            "observed lower-bound peak depth does not establish sustained high depth",
            {"observedPeakQueueDepthLowerBound": peak, "episodes": queue_count},
        )
    else:
        high_depth = gate(
            "HIGH_QUEUE_DEPTH",
            "INSUFFICIENT_EVIDENCE",
            "depth above the current baseline was observed but no validated admission threshold exists",
            {"observedPeakQueueDepthLowerBound": peak, "episodes": queue_count},
        )

    if ci_projection is None:
        ci_waste = gate(
            "CI_WASTE",
            "INSUFFICIENT_EVIDENCE",
            "CI economic observations are absent",
            {},
        )
    else:
        cmetrics = ci_projection.get("metrics", {})
        explicit_waste = int(cmetrics.get("explicitAvoidableWasteRuns") or 0)
        unclassified = int(cmetrics.get("unclassifiedTerminalRuns") or 0)
        runs = int(cmetrics.get("runs") or 0)
        if explicit_waste > 0:
            ci_waste = gate(
                "CI_WASTE",
                "PROVEN",
                "at least one run has explicit evidence-backed avoidable-waste classification",
                {
                    "runs": runs,
                    "explicitAvoidableWasteRuns": explicit_waste,
                    "explicitAvoidableWasteExecutionSeconds": cmetrics.get(
                        "explicitAvoidableWasteExecutionSeconds"
                    ),
                    "unclassifiedTerminalRuns": unclassified,
                },
            )
            ci_waste["allowedExperiments"] = ["ci-deduplication", "cancellation-optimization"]
        elif unclassified > 0:
            ci_waste = gate(
                "CI_WASTE",
                "INSUFFICIENT_EVIDENCE",
                "terminal CI exists but economic outcomes remain deliberately unclassified",
                {"runs": runs, "unclassifiedTerminalRuns": unclassified},
            )
        elif runs > 0:
            ci_waste = gate(
                "CI_WASTE",
                "NOT_PROVEN",
                "observed CI contains no explicitly classified avoidable waste",
                {"runs": runs},
            )
        else:
            ci_waste = gate(
                "CI_WASTE",
                "INSUFFICIENT_EVIDENCE",
                "no CI runs were observed",
                {"runs": 0},
            )

    owner_costs = owner_cost_episodes or []
    long_tail = gate(
        "LONG_TAIL_OWNER",
        "INSUFFICIENT_EVIDENCE",
        "owner long-tail optimization requires repeated comparable episodes before admission",
        {"ownerCostEpisodes": len(owner_costs)},
    )
    predictor = gate(
        "PREDICTOR_DATA",
        "INSUFFICIENT_EVIDENCE",
        "no validated history-size or calibration threshold has been admitted",
        {"queueEpisodes": queue_count, "ownerCostEpisodes": len(owner_costs)},
    )

    gates = [contention, high_depth, ci_waste, long_tail, predictor]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.convergence-pressure-assessment",
        "truthRole": "diagnosis-only-no-provider-or-control-authority",
        "gates": gates,
        "controlsAdmitted": sorted(
            {
                experiment
                for row in gates
                for experiment in row.get("allowedExperiments", [])
            }
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--ci", type=Path)
    parser.add_argument("--owner-cost", action="append", default=[], type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text())
    ci = json.loads(args.ci.read_text()) if args.ci else None
    owner_cost = [json.loads(path.read_text()) for path in args.owner_cost]
    result = assess(queue, ci, owner_cost)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
