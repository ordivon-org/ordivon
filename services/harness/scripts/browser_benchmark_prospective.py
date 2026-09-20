#!/usr/bin/env python3
"""BCR-S5 prospective paired browser-route benchmark gate.

The manifest is frozen before live readiness observation. The live gate observes each exact route
under normal policy, refuses to prepare any trial unless all paired routes are simultaneously READY,
and never admits a Runtime Job itself.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Callable, Mapping

import browser_benchmark_contract as benchmark
import browser_benchmark_runner as runner
import browser_benchmark_runtime_handoff as handoff
import browser_capability_router as router

CAMPAIGN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,47}$")
PAIRED_ROUTES = ("jev-fast-windows-v1", "browser-use-browserless-v1")
DEFAULT_TASK_ID = "generic-navigate-click-r1"


def _task_and_cases(
    suite: Mapping[str, Any], task_id: str
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    tasks = [row for row in suite["tasks"] if row["taskId"] == task_id]
    if len(tasks) != 1:
        raise ValueError(f"taskId must resolve exactly once: {task_id}")
    task = tasks[0]
    cases = {
        row["routeId"]: row
        for row in benchmark.compile_cases(suite)
        if row["taskId"] == task_id
    }
    missing = sorted(set(PAIRED_ROUTES) - set(cases))
    if missing:
        raise ValueError(f"paired benchmark routes missing cases: {missing}")
    return task, cases


def build_manifest(
    *,
    campaign_id: str,
    pair_count: int,
    suite: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
    task_id: str = DEFAULT_TASK_ID,
) -> dict[str, Any]:
    if not CAMPAIGN_ID.fullmatch(campaign_id):
        raise ValueError("campaignId must be a bounded stable identifier")
    if type(pair_count) is not int or not 1 <= pair_count <= 50:
        raise ValueError("pairCount must be an integer in 1..50")
    policy = policy or router.load_policy()
    suite = suite or benchmark.load_suite(policy=policy)
    task, cases = _task_and_cases(suite, task_id)
    pairs = []
    for pair_index in range(1, pair_count + 1):
        order = list(PAIRED_ROUTES)
        if pair_index % 2 == 0:
            order.reverse()
        trials = []
        for order_index, route_id in enumerate(order, start=1):
            case = cases[route_id]
            run_id = f"bcrs5:{campaign_id}:p{pair_index:02d}:o{order_index}:{route_id}"
            if len(run_id) > 128:
                raise ValueError("derived runId exceeds route-run contract")
            trials.append(
                {
                    "orderIndex": order_index,
                    "routeId": route_id,
                    "caseId": case["caseId"],
                    "caseDigest": case["caseDigest"],
                    "runId": run_id,
                }
            )
        pairs.append({"pairIndex": pair_index, "trials": trials})
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-prospective-paired-manifest",
        "campaignId": campaign_id,
        "benchmarkId": suite["benchmarkId"],
        "suiteDigest": suite["suiteDigest"],
        "taskId": task_id,
        "taskDigest": task["taskDigest"],
        "pairCount": pair_count,
        "routeIds": list(PAIRED_ROUTES),
        "pairing": {
            "kind": "alternating-order-paired-v1",
            "oddPairOrder": list(PAIRED_ROUTES),
            "evenPairOrder": list(reversed(PAIRED_ROUTES)),
        },
        "readinessContract": {
            "kind": "independent-exact-route-normal-policy-v1",
            "callerReadinessOverridesAccepted": False,
            "allRoutesMustBeReadyBeforeAnyTrialPreparation": True,
            "fallbackAllowed": False,
        },
        "pairs": pairs,
        "effectsExecuted": False,
        "nonClaims": [
            "route_readiness",
            "runtime_admission",
            "provider_authorization",
            "semantic_success",
            "model_intelligence_ranking",
        ],
    }
    value["manifestDigest"] = router.canonical_digest(value)
    return value


def validate_manifest(
    raw: Mapping[str, Any],
    *,
    suite: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if (
        raw.get("schemaVersion") != 1
        or raw.get("kind")
        != "ordivon.browser-benchmark-prospective-paired-manifest"
    ):
        raise ValueError("prospective manifest identity mismatch")
    campaign_id = raw.get("campaignId")
    pair_count = raw.get("pairCount")
    if not isinstance(campaign_id, str) or not CAMPAIGN_ID.fullmatch(campaign_id):
        raise ValueError("prospective manifest campaignId is invalid")
    if type(pair_count) is not int or not 1 <= pair_count <= 50:
        raise ValueError("prospective manifest pairCount is invalid")
    policy = policy or router.load_policy()
    suite = suite or benchmark.load_suite(policy=policy)
    expected = build_manifest(
        campaign_id=campaign_id,
        pair_count=pair_count,
        suite=suite,
        policy=policy,
        task_id=str(raw.get("taskId") or ""),
    )
    if dict(raw) != expected:
        raise ValueError("prospective manifest differs from deterministic contract")
    return dict(raw)


def _default_plan(
    request: Mapping[str, Any], *, policy: Mapping[str, Any]
) -> dict[str, Any]:
    return router.plan_route(request, policy=policy)


def gate_manifest(
    manifest: Mapping[str, Any],
    *,
    workspace_id: str,
    state_root: Path,
    suite: Mapping[str, Any] | None = None,
    policy: Mapping[str, Any] | None = None,
    plan_fn: Callable[..., Mapping[str, Any]] = _default_plan,
    jev_status_fn: Callable[[], Mapping[str, Any]] = runner._default_jev_status,
    windows_path_fn: Callable[[Path], str] = runner._default_windows_path,
) -> dict[str, Any]:
    policy = policy or router.load_policy()
    suite = suite or benchmark.load_suite(policy=policy)
    frozen = validate_manifest(manifest, suite=suite, policy=policy)
    _, cases = _task_and_cases(suite, frozen["taskId"])

    readiness_rows = []
    readiness_by_route: dict[str, dict[str, Any]] = {}
    all_ready = True
    for route_id in frozen["routeIds"]:
        case = cases[route_id]
        plan = dict(plan_fn(case["routeRequest"], policy=policy))
        candidate = next(
            (
                row
                for row in plan.get("candidates", [])
                if isinstance(row, dict) and row.get("routeId") == route_id
            ),
            None,
        )
        readiness = (
            dict(candidate.get("readiness") or {})
            if isinstance(candidate, dict)
            else {}
        )
        selected = plan.get("selectedRoute")
        ready = bool(
            plan.get("standing") == "SELECTED"
            and isinstance(selected, dict)
            and selected.get("routeId") == route_id
            and readiness.get("ready") is True
        )
        all_ready = all_ready and ready
        readiness_by_route[route_id] = readiness
        readiness_rows.append(
            {
                "routeId": route_id,
                "ready": ready,
                "planStanding": plan.get("standing"),
                "planDigest": plan.get("planDigest"),
                "readinessStanding": readiness.get("standing"),
                "readinessDigest": router.canonical_digest(readiness),
            }
        )

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-prospective-gate",
        "campaignId": frozen["campaignId"],
        "manifestDigest": frozen["manifestDigest"],
        "standing": (
            "READY_FOR_PAIRED_RUNTIME_BINDING"
            if all_ready
            else "BLOCKED_BY_ROUTE_READINESS"
        ),
        "readiness": readiness_rows,
        "trialBundles": [],
        "effectsExecuted": False,
        "runtimeJobsCreated": False,
        "nonClaims": [
            "runtime_admission",
            "provider_secret_binding",
            "semantic_success",
            "model_intelligence_ranking",
        ],
    }
    if not all_ready:
        result["gateDigest"] = router.canonical_digest(result)
        return result

    jev_status = dict(jev_status_fn())

    for pair in frozen["pairs"]:
        for trial in pair["trials"]:
            route_id = trial["routeId"]
            prep = runner.prepare_case(
                trial["caseId"],
                trial["runId"],
                state_root=state_root,
                policy=policy,
                suite=suite,
                readiness_overrides={route_id: readiness_by_route[route_id]},
                jev_status_fn=lambda: jev_status,
                windows_path_fn=windows_path_fn,
            )
            if prep["standing"] != "READY_FOR_RUNTIME":
                raise RuntimeError("captured READY route did not reproduce READY preparation")
            observed_plan = next(
                row["planDigest"]
                for row in readiness_rows
                if row["routeId"] == route_id
            )
            if prep["preflightReceipt"]["routePlanDigest"] != observed_plan:
                raise RuntimeError("captured readiness plan identity drifted during preparation")
            template = handoff.build_admission_template(
                prep,
                workspace_id=workspace_id,
            )
            if template["standing"] != "ADMISSION_TEMPLATE_READY":
                raise RuntimeError("READY preparation did not produce admission template")
            result["trialBundles"].append(
                {
                    "pairIndex": pair["pairIndex"],
                    "orderIndex": trial["orderIndex"],
                    "routeId": route_id,
                    "runId": trial["runId"],
                    "caseDigest": trial["caseDigest"],
                    "preparationDigest": prep["preparationDigest"],
                    "templateDigest": template["templateDigest"],
                    "requiredSecretEnvironment": list(
                        template["requiredSecretEnvironment"]
                    ),
                    "preparation": prep,
                    "admissionTemplate": template,
                }
            )

    result["gateDigest"] = router.canonical_digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=benchmark.DEFAULT_SUITE)
    parser.add_argument("--policy", type=Path, default=router.DEFAULT_ROUTE_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    manifest = sub.add_parser("manifest")
    manifest.add_argument("--campaign-id", required=True)
    manifest.add_argument("--pair-count", type=int, default=8)
    gate = sub.add_parser("gate")
    gate.add_argument("--manifest-file", type=Path, required=True)
    gate.add_argument("--workspace-id", required=True)
    gate.add_argument("--state-root", type=Path, required=True)
    args = parser.parse_args()
    policy = router.load_policy(args.policy)
    suite = benchmark.load_suite(args.suite, policy=policy)
    if args.command == "manifest":
        value = build_manifest(
            campaign_id=args.campaign_id,
            pair_count=args.pair_count,
            suite=suite,
            policy=policy,
        )
    else:
        raw = json.loads(args.manifest_file.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise ValueError("manifest file must contain one JSON object")
        value = gate_manifest(
            raw,
            workspace_id=args.workspace_id,
            state_root=args.state_root,
            suite=suite,
            policy=policy,
        )
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
