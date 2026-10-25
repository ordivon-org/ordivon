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


def gate(
    name: str, status: str, reason: str, evidence: dict[str, Any]
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(status)
    return {
        "gate": name,
        "status": status,
        "reason": reason,
        "evidence": evidence,
        "allowedExperiments": [],
    }


def owner_cost_rows(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value in payloads:
        kind = value.get("kind")
        if kind == "ordivon.convergence-owner-cost-episode-corpus":
            episodes = value.get("episodes")
            if not isinstance(episodes, list):
                raise ValueError("owner-cost corpus episodes must be a list")
            for row in episodes:
                if not isinstance(row, dict):
                    raise ValueError("owner-cost corpus episode must be an object")
                rows.append(row)
        elif kind in {
            "ordivon.convergence-owner-cost-episode",
            "ordivon.convergence-owner-cost-observation",
        }:
            rows.append(value)
        else:
            raise ValueError(f"unsupported owner-cost evidence kind: {kind!r}")
    return rows


def _ci_waste_has_run_witness(
    projection: dict[str, Any], *, runs: int, explicit_waste: int,
    unclassified: int,
) -> bool:
    """A summary cannot establish control eligibility without its source runs.

    This is an evidence-integrity check, not independent GitHub attestation.
    The CI provider remains authoritative; this read-only projection never is.
    """
    observed = projection.get("runs")
    if not isinstance(observed, list) or len(observed) != runs:
        return False
    identities: set[tuple[int | str, int | None]] = set()
    waste = unknown = 0
    for row in observed:
        if not isinstance(row, dict):
            return False
        run_id, attempt = row.get("runId"), row.get("runAttempt")
        if not isinstance(run_id, (str, int)) or isinstance(run_id, bool):
            return False
        if attempt is not None and (type(attempt) is not int or attempt < 1):
            return False
        identity = (run_id, attempt)
        if identity in identities:
            return False
        identities.add(identity)
        outcome = row.get("economicOutcome")
        status = row.get("status")
        if status == "completed" and outcome == "UNCLASSIFIED":
            unknown += 1
        if outcome in {"AVOIDABLE_WASTE", "DUPLICATED"}:
            if (
                status != "completed"
                or not isinstance(row.get("economicReason"), str)
                or not row["economicReason"].strip()
            ):
                return False
            waste += 1
    return waste == explicit_waste and unknown == unclassified


def pr_source_duplication_gate(snapshot: dict[str, Any] | None) -> dict[str, Any]:
    """Partition one time-scoped GitHub PR snapshot by exact (base, head).

    Same base+head proves a duplicate candidate SourceCut, not duplicate
    consumer outcomes, merge effects, or permission to delete a branch.
    No network requests or controller mutations occur in this projection.
    """
    if snapshot is None:
        return gate(
            "PR_SOURCE_DUPLICATION", "INSUFFICIENT_EVIDENCE",
            "no source-bound GitHub PR snapshot", {},
        )
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("kind") != "ordivon.gh-pr-sourcecut-snapshot"
        or not isinstance(snapshot.get("observedAt"), str)
        or not isinstance(snapshot.get("pullRequests"), list)
        or not isinstance(snapshot.get("coverage"), dict)
        or type(snapshot["coverage"].get("complete")) is not bool
        or snapshot["coverage"].get("stateFilter") not in {"all", "open"}
    ):
        return gate(
            "PR_SOURCE_DUPLICATION", "INSUFFICIENT_EVIDENCE",
            "snapshot identity or time is absent/invalid", {},
        )
    import re
    from datetime import datetime
    try:
        observed = datetime.fromisoformat(snapshot["observedAt"].replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise ValueError("missing offset")
    except ValueError:
        return gate(
            "PR_SOURCE_DUPLICATION", "INSUFFICIENT_EVIDENCE",
            "invalid or timezone-naive PR observation time", {"deleteAuthority": "NONE"},
        )

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen: set[int] = set()
    for row in snapshot["pullRequests"]:
        if not isinstance(row, dict):
            break
        number, base, head, state = (
            row.get("number"), row.get("baseRefOid"),
            row.get("headRefOid"), row.get("state"),
        )
        if (
            type(number) is not int or number <= 0 or number in seen
            or not isinstance(base, str)
            or not isinstance(head, str)
            or not re.fullmatch(r"[0-9a-fA-F]{40}", base)
            or not re.fullmatch(r"[0-9a-fA-F]{40}", head)
            or state not in {"OPEN", "CLOSED", "MERGED"}
        ):
            break
        seen.add(number)
        groups.setdefault((base.lower(), head.lower()), []).append(
            {"number": number, "state": state}
        )
    else:
        repeated = [
            {
                "baseRefOid": base,
                "headRefOid": head,
                "pullRequests": sorted(rows, key=lambda row: row["number"]),
            }
            for (base, head), rows in sorted(groups.items())
            if len(rows) > 1
        ]
        complete = snapshot["coverage"]["complete"]
        standing = (
            "PROVEN" if repeated
            else "NOT_PROVEN" if complete
            else "INSUFFICIENT_EVIDENCE"
        )
        return gate(
            "PR_SOURCE_DUPLICATION", standing,
            (
                "multiple records name an identical base/head Git candidate; "
                "consumer equivalence and closure authority are not established"
                if repeated
                else "no duplicate source cut within a complete observed PR universe"
                if complete
                else "a partial PR snapshot cannot establish global absence"
            ),
            {
                "observedAt": snapshot["observedAt"],
                "coverage": snapshot["coverage"],
                "prRecords": len(seen),
                "duplicateGroups": repeated,
                "sourceCutIdentity": "exact(baseRefOid,headRefOid)",
                "deleteAuthority": "NONE",
            },
        )
    return gate(
        "PR_SOURCE_DUPLICATION", "INSUFFICIENT_EVIDENCE",
        "invalid, partial, or duplicate-identity PR record in supplied snapshot",
        {"validPrefixRecords": len(seen), "deleteAuthority": "NONE"},
    )


def assess(
    queue_projection: dict[str, Any],
    ci_projection: dict[str, Any] | None = None,
    owner_cost_episodes: list[dict[str, Any]] | None = None,
    pr_source_snapshot: dict[str, Any] | None = None,
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
            {
                "episodes": queue_count,
                "requeues": requeues,
                "unsuccessfulMergeGroupRuns": unsuccessful,
            },
        )
    else:
        contention = gate(
            "QUEUE_CONTENTION",
            "INSUFFICIENT_EVIDENCE",
            "queue disruption exists but its cause is not established as contention",
            {
                "episodes": queue_count,
                "requeues": requeues,
                "unsuccessfulMergeGroupRuns": unsuccessful,
            },
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
        if explicit_waste > 0 and not _ci_waste_has_run_witness(
            ci_projection,
            runs=runs,
            explicit_waste=explicit_waste,
            unclassified=unclassified,
        ):
            ci_waste = gate(
                "CI_WASTE",
                "INSUFFICIENT_EVIDENCE",
                "claimed waste lacks matching terminal, unique source-run evidence",
                {
                    "runs": runs,
                    "explicitAvoidableWasteRuns": explicit_waste,
                    "unclassifiedTerminalRuns": unclassified,
                },
            )
        elif explicit_waste > 0:
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
            ci_waste["allowedExperiments"] = [
                "ci-deduplication",
                "cancellation-optimization",
            ]
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
    owner_candidates = sorted(
        {
            str(candidate)
            for row in owner_costs
            for candidate in (row.get("candidateSha") or row.get("measuredCandidate"),)
            if candidate
        }
    )
    successful_owner_costs = [
        row
        for row in owner_costs
        if row.get("result") == "PASS"
        and isinstance(row.get("totalSeconds"), (int, float))
    ]
    owner_evidence = {
        "ownerCostEpisodes": len(owner_costs),
        "ownerCostCandidates": len(owner_candidates),
        "successfulMeasuredOwnerCostEpisodes": len(successful_owner_costs),
    }
    long_tail_reason = (
        "multiple owner-cost candidates are observed, but no validated comparable cross-candidate admission threshold exists"
        if len(owner_candidates) >= 2
        else "owner long-tail optimization requires repeated comparable candidates before admission"
    )
    long_tail = gate(
        "LONG_TAIL_OWNER",
        "INSUFFICIENT_EVIDENCE",
        long_tail_reason,
        owner_evidence,
    )
    predictor = gate(
        "PREDICTOR_DATA",
        "INSUFFICIENT_EVIDENCE",
        "no validated history-size or calibration threshold has been admitted",
        {
            "queueEpisodes": queue_count,
            "ownerCostEpisodes": len(owner_costs),
            "ownerCostCandidates": len(owner_candidates),
        },
    )

    gates = [
        contention, high_depth, ci_waste, long_tail, predictor,
        pr_source_duplication_gate(pr_source_snapshot),
    ]
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
    parser.add_argument("--pr-source", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    queue = json.loads(args.queue.read_text())
    ci = json.loads(args.ci.read_text()) if args.ci else None
    owner_cost_payloads = [json.loads(path.read_text()) for path in args.owner_cost]
    owner_cost = owner_cost_rows(owner_cost_payloads)
    pr_source = json.loads(args.pr_source.read_text()) if args.pr_source else None
    result = assess(queue, ci, owner_cost, pr_source_snapshot=pr_source)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
