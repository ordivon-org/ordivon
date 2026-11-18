from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from statistics import median
from typing import Any

import psycopg
from psycopg.rows import dict_row


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def _summary(values: list[float]) -> dict[str, float | int]:
    return {
        "n": len(values),
        "mean": sum(values) / len(values),
        "median": median(values),
        "p95": _percentile(values, 0.95),
        "min": min(values),
        "max": max(values),
    }


def generalization_gate(data_classes: Counter[str]) -> dict[str, Any]:
    development = data_classes.get("DEVELOPMENT", 0)
    judge = data_classes.get("JUDGE", 0)
    if development < 1 or judge < 1:
        return {
            "standing": "NOT_IDENTIFIED",
            "reason": "INSUFFICIENT_EXPLICIT_DEVELOPMENT_JUDGE_SPLIT",
            "developmentEpisodes": development,
            "judgeEpisodes": judge,
        }
    return {
        "standing": "ELIGIBLE_FOR_SEPARATE_GENERALIZATION_STUDY",
        "reason": "EXPLICIT_DEVELOPMENT_JUDGE_SPLIT_PRESENT",
        "developmentEpisodes": development,
        "judgeEpisodes": judge,
    }


def intervention_gate(
    *, intervention_contract_ref: str | None, assigned_episode_count: int
) -> dict[str, Any]:
    if intervention_contract_ref is None:
        return {
            "standing": "NOT_IDENTIFIED",
            "reason": "NO_FROZEN_INTERVENTION_CONTRACT",
            "assignedEpisodes": assigned_episode_count,
        }
    if assigned_episode_count < 2:
        return {
            "standing": "NOT_IDENTIFIED",
            "reason": "INSUFFICIENT_EXPLICIT_ASSIGNMENT",
            "assignedEpisodes": assigned_episode_count,
            "interventionContractRef": intervention_contract_ref,
        }
    return {
        "standing": "ELIGIBLE_FOR_SEPARATE_CAUSAL_STUDY",
        "reason": "FROZEN_CONTRACT_AND_EXPLICIT_ASSIGNMENT_PRESENT",
        "assignedEpisodes": assigned_episode_count,
        "interventionContractRef": intervention_contract_ref,
    }


def _fetch_dimensions(
    conn: psycopg.Connection[dict[str, Any]], profile_id: str
) -> dict[str, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT d.episode_id, d.name, d.value
        FROM episode_dimensions d
        JOIN episode_projections p
          USING (episode_id, projection_digest)
        WHERE p.profile_id = %s
        ORDER BY d.episode_id, d.name
        """,
        (profile_id,),
    ).fetchall()
    values: dict[str, dict[str, Any]] = defaultdict(dict)
    for row in rows:
        values[row["episode_id"]][row["name"]] = row["value"]
    return dict(values)


def _fetch_measures(
    conn: psycopg.Connection[dict[str, Any]], profile_id: str
) -> dict[str, dict[str, float]]:
    rows = conn.execute(
        """
        SELECT m.episode_id, m.name, m.value
        FROM episode_measures m
        JOIN episode_projections p
          USING (episode_id, projection_digest)
        WHERE p.profile_id = %s
        ORDER BY m.episode_id, m.name
        """,
        (profile_id,),
    ).fetchall()
    values: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        values[row["episode_id"]][row["name"]] = float(row["value"])
    return dict(values)


def analyze_store(
    dsn: str,
    *,
    intervention_contract_ref: str | None = None,
) -> dict[str, Any]:
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        profile_rows = conn.execute(
            """
            SELECT profile_id, data_class, count(*) AS n
            FROM episode_projections
            GROUP BY profile_id, data_class
            ORDER BY profile_id, data_class
            """
        ).fetchall()
        data_classes: Counter[str] = Counter()
        profiles: Counter[str] = Counter()
        for row in profile_rows:
            profiles[row["profile_id"]] += row["n"]
            data_classes[row["data_class"]] += row["n"]

        runtime_dims = _fetch_dimensions(conn, "runtime-r5c-v1")
        runtime_measures = _fetch_measures(conn, "runtime-r5c-v1")
        harness_dims = _fetch_dimensions(conn, "harness-rsi-acceptance-v1")
        harness_measures = _fetch_measures(conn, "harness-rsi-acceptance-v1")

        states: Counter[str] = Counter()
        resource_by_state: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for episode_id, dims in runtime_dims.items():
            state = str(dims.get("runtime.execution_state"))
            states[state] += 1
            for name, value in runtime_measures.get(episode_id, {}).items():
                resource_by_state[state][name].append(value)

        terminal_unsuccessful = (
            states.get("failed", 0)
            + states.get("timed_out", 0)
            + states.get("cancelled", 0)
        )
        terminal_total = sum(states.values()) - states.get("running", 0)
        resource_profiles = {
            state: {
                name: _summary(values)
                for name, values in sorted(measures.items())
                if values
            }
            for state, measures in sorted(resource_by_state.items())
        }

        provider_signal_names = (
            "harness.acceptedTrajectoryProviderCost.completedProviderCalls",
            "harness.acceptedTrajectoryProviderCost.promptTokens",
            "harness.acceptedTrajectoryProviderCost.completionTokens",
            "harness.acceptedTrajectoryProviderCost.totalTokens",
            "harness.r12Discovery.providerCalls",
            "harness.r12Discovery.totalTokens",
        )
        provider_signals: dict[str, list[dict[str, Any]]] = defaultdict(list)
        cost_episode_ids: set[str] = set()
        for episode_id, measures in harness_measures.items():
            for name in provider_signal_names:
                if name in measures:
                    provider_signals[name].append(
                        {"episodeId": episode_id, "value": measures[name]}
                    )
                    cost_episode_ids.add(episode_id)

        owner_rows = conn.execute(
            """
            SELECT p.profile_id, r.owner_id, r.object_kind, r.relation, count(*) AS n
            FROM episode_owner_refs r
            JOIN episode_projections p
              USING (episode_id, projection_digest)
            GROUP BY p.profile_id, r.owner_id, r.object_kind, r.relation
            ORDER BY p.profile_id, r.owner_id, r.object_kind, r.relation
            """
        ).fetchall()
        owner_observations = [
            {
                "profileId": row["profile_id"],
                "ownerId": row["owner_id"],
                "objectKind": row["object_kind"],
                "relation": row["relation"],
                "count": row["n"],
            }
            for row in owner_rows
        ]

        assigned = conn.execute(
            """
            SELECT count(DISTINCT episode_id) AS n
            FROM episode_dimensions
            WHERE name IN ('experimental.assignment', 'experimental.treatment')
            """
        ).fetchone()["n"]

    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.experimental-system-analysis-r1",
        "truthRole": "derived-analysis-not-owner-truth",
        "population": {
            "episodes": sum(profiles.values()),
            "profiles": dict(sorted(profiles.items())),
            "dataClasses": dict(sorted(data_classes.items())),
        },
        "failure": {
            "standing": "DESCRIPTIVE_ONLY",
            "runtimeExecutionStateDistribution": dict(sorted(states.items())),
            "terminalUnsuccessfulEpisodes": terminal_unsuccessful,
            "terminalEpisodes": terminal_total,
            "terminalUnsuccessfulRate": (
                terminal_unsuccessful / terminal_total if terminal_total else None
            ),
            "resourceProfilesByExecutionState": resource_profiles,
            "nonClaims": [
                "Resource associations do not establish failure causation.",
                "Runtime resolution is not domain success.",
            ],
        },
        "cost": {
            "standing": "PARTIAL_COVERAGE",
            "runtimeMechanicalProxyCoverageEpisodes": len(runtime_measures),
            "runtimeMechanicalProxyKinds": sorted(
                {name for values in runtime_measures.values() for name in values}
            ),
            "harnessProviderCostCoverageEpisodes": len(cost_episode_ids),
            "harnessEpisodes": len(harness_dims),
            "observedProviderSignals": dict(sorted(provider_signals.items())),
            "nonClaims": [
                "Runtime event/artifact rows are mechanical load proxies, not monetary cost.",
                "Provider token/call signals are sparse and are not summed across differently named evidence because they may overlap semantically.",
            ],
        },
        "capability": {
            "standing": "DESCRIPTIVE_ONLY",
            "ownerReferenceObservations": owner_observations,
            "nonClaims": [
                "Observed owner references are evidence coverage, not a capability registry.",
                "Reference frequency is not capability quality or importance.",
            ],
        },
        "generalization": generalization_gate(data_classes),
        "intervention": intervention_gate(
            intervention_contract_ref=intervention_contract_ref,
            assigned_episode_count=assigned,
        ),
        "analysisBoundary": [
            "No universal fitness score is computed.",
            "No ranking or promotion decision is emitted.",
            "NOT_IDENTIFIED is a valid outcome when design evidence is absent.",
        ],
    }
    digest_material = dict(result)
    result["analysisDigest"] = _canonical_digest(digest_material)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", default=os.environ.get("ORDIVON_EXPERIMENTAL_DSN"))
    parser.add_argument("--intervention-contract-ref")
    parser.add_argument("--output")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if not args.dsn:
        raise SystemExit("set --dsn or ORDIVON_EXPERIMENTAL_DSN")
    result = analyze_store(
        args.dsn,
        intervention_contract_ref=args.intervention_contract_ref,
    )
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
