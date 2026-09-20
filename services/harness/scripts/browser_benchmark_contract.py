#!/usr/bin/env python3
"""Provider-neutral Browser Capability Router benchmark contract.

S2 is deliberately not a browser executor. It binds benchmark cases to one explicit route,
materializes read-only pre-execution receipts from Browser Capability Router, and validates/finalizes
execution observations produced by a later adapter/runner. Missing metrics are NOT_OBSERVED rather
than zero. Adapter completion is never promoted to semantic PASS without an explicit outcome witness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import browser_capability_router as router

SOURCE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUITE = SOURCE_ROOT / "config/browser-benchmark-suite.json"
METRIC_CONTRACT: dict[str, str] = {
    "totalElapsedMs": "integer",
    "bootstrapElapsedMs": "integer",
    "taskElapsedMs": "integer",
    "actionCount": "integer",
    "browserProtocolCallCount": "integer",
    "providerApiRequestCount": "integer",
    "modelRequestCount": "integer",
    "inputTokenCount": "integer",
    "outputTokenCount": "integer",
    "retryCount": "integer",
    "staleActionRetryCount": "integer",
    "fallbackCount": "integer",
    "providerBilledMicrousd": "integer",
}
PREEXEC_STANDINGS = frozenset({"READY", "PREEXEC_BLOCKED"})
RECEIPT_STANDINGS = frozenset({"READY", "PREEXEC_BLOCKED", "EXECUTED"})
OUTCOME_STANDINGS = frozenset({"NOT_EXECUTED", "UNVERIFIED", "PASS", "FAIL"})


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _trimmed(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty trimmed text")
    return value


def _strings(value: object, field: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise ValueError(f"{field} must be a list")
    rows = tuple(_trimmed(item, field) for item in value)
    if len(rows) != len(set(rows)):
        raise ValueError(f"{field} must not contain duplicates")
    return rows


def _execution_contract(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("executionContract must be an object")
    if set(value) != {
        "kind",
        "documentHtml",
        "goal",
        "buttonRole",
        "buttonName",
        "successText",
        "witness",
    }:
        raise ValueError("executionContract has unexpected fields")
    if value.get("kind") != "inline-html-click-v1":
        raise ValueError("executionContract kind mismatch")
    document_html = _trimmed(value.get("documentHtml"), "executionContract.documentHtml")
    if len(document_html.encode("utf-8")) > 32768:
        raise ValueError("executionContract.documentHtml exceeds 32768 UTF-8 bytes")
    goal = _trimmed(value.get("goal"), "executionContract.goal")
    button_role = _trimmed(value.get("buttonRole"), "executionContract.buttonRole")
    button_name = _trimmed(value.get("buttonName"), "executionContract.buttonName")
    success_text = _trimmed(value.get("successText"), "executionContract.successText")
    witness = value.get("witness")
    if (
        not isinstance(witness, dict)
        or set(witness) != {"kind", "value"}
        or witness.get("kind") != "textContains"
        or _trimmed(witness.get("value"), "executionContract.witness.value") != success_text
    ):
        raise ValueError("executionContract witness must bind the declared successText")
    return {
        "kind": "inline-html-click-v1",
        "documentHtml": document_html,
        "goal": goal,
        "buttonRole": button_role,
        "buttonName": button_name,
        "successText": success_text,
        "witness": {"kind": "textContains", "value": success_text},
    }


def load_suite(
    path: Path = DEFAULT_SUITE, *, policy: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    policy = policy or router.load_policy()
    value = _read_json(path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.browser-benchmark-suite":
        raise ValueError("browser benchmark suite identity mismatch")
    benchmark_id = _trimmed(value.get("benchmarkId"), "benchmarkId")
    tasks = value.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("browser benchmark suite requires tasks")
    route_by_id = {row["routeId"]: row for row in policy["routes"]}
    seen_tasks: set[str] = set()
    seen_cases: set[str] = set()
    normalized_tasks: list[dict[str, Any]] = []
    for raw in tasks:
        if not isinstance(raw, dict):
            raise ValueError("benchmark task must be an object")
        task_id = _trimmed(raw.get("taskId"), "taskId")
        if task_id in seen_tasks:
            raise ValueError(f"duplicate taskId: {task_id}")
        seen_tasks.add(task_id)
        provider_flow = _trimmed(raw.get("providerFlow"), "providerFlow")
        required = _strings(raw.get("requiredFeatures", []), "requiredFeatures")
        preferred = _strings(raw.get("preferredFeatures", []), "preferredFeatures")
        outcome_checks = _strings(raw.get("outcomeCheckIds"), "outcomeCheckIds", allow_empty=False)
        execution_contract = _execution_contract(raw.get("executionContract"))
        variants = raw.get("variants")
        if not isinstance(variants, list) or len(variants) < 2:
            raise ValueError(f"benchmark task {task_id} requires at least two route variants")
        normalized_variants = []
        for variant in variants:
            if not isinstance(variant, dict):
                raise ValueError("benchmark variant must be an object")
            case_id = _trimmed(variant.get("caseId"), "caseId")
            route_id = _trimmed(variant.get("routeId"), "routeId")
            if case_id in seen_cases:
                raise ValueError(f"duplicate caseId: {case_id}")
            seen_cases.add(case_id)
            route = route_by_id.get(route_id)
            if route is None:
                raise ValueError(f"unknown benchmark routeId: {route_id}")
            if route["providerFlow"] != provider_flow:
                raise ValueError(f"benchmark route providerFlow mismatch: {route_id}")
            missing = sorted(set(required) - set(route["provides"]))
            if missing:
                raise ValueError(f"benchmark route {route_id} lacks required features: {missing}")
            normalized_variants.append({"caseId": case_id, "routeId": route_id})
        task_contract = {
            "taskId": task_id,
            "providerFlow": provider_flow,
            "requiredFeatures": list(required),
            "preferredFeatures": list(preferred),
            "outcomeCheckIds": list(outcome_checks),
            "executionContract": execution_contract,
        }
        normalized_tasks.append(
            {
                **task_contract,
                "taskDigest": router.canonical_digest(task_contract),
                "variants": normalized_variants,
            }
        )
    suite = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-suite",
        "benchmarkId": benchmark_id,
        "tasks": normalized_tasks,
        "metricContract": dict(METRIC_CONTRACT),
    }
    suite["suiteDigest"] = router.canonical_digest(suite)
    return suite


def compile_cases(suite: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in suite["tasks"]:
        for variant in task["variants"]:
            route_request = {
                "schemaVersion": 1,
                "requestId": f"{suite['benchmarkId']}:{variant['caseId']}",
                "providerFlow": task["providerFlow"],
                "requiredFeatures": list(task["requiredFeatures"]),
                "preferredFeatures": list(task["preferredFeatures"]),
                "explicitRouteId": variant["routeId"],
            }
            case = {
                "schemaVersion": 1,
                "kind": "ordivon.browser-benchmark-case",
                "benchmarkId": suite["benchmarkId"],
                "suiteDigest": suite["suiteDigest"],
                "taskId": task["taskId"],
                "taskDigest": task["taskDigest"],
                "caseId": variant["caseId"],
                "routeId": variant["routeId"],
                "routeRequest": route_request,
                "outcomeCheckIds": list(task["outcomeCheckIds"]),
                "executionContract": dict(task["executionContract"]),
                "executionContractDigest": router.canonical_digest(task["executionContract"]),
                "metricNames": list(METRIC_CONTRACT),
            }
            case["caseDigest"] = router.canonical_digest(case)
            rows.append(case)
    return rows


def _not_observed_metrics() -> dict[str, dict[str, Any]]:
    return {
        name: {"standing": "NOT_OBSERVED", "value": None}
        for name in METRIC_CONTRACT
    }


def _blocker_from_plan(case: Mapping[str, Any], plan: Mapping[str, Any]) -> dict[str, Any]:
    candidate = next(
        (row for row in plan.get("candidates", []) if row.get("routeId") == case["routeId"]),
        None,
    )
    readiness = candidate.get("readiness") if isinstance(candidate, dict) else None
    readiness = readiness if isinstance(readiness, dict) else {}
    return {
        "planStanding": plan.get("standing"),
        "routeReadinessStanding": readiness.get("standing"),
        "missingEnvironmentNames": sorted(
            item
            for item in readiness.get("missingEnvironment", [])
            if isinstance(item, str) and item
        ),
        "policyDisabledEndpointIds": sorted(
            item
            for item in readiness.get("policyDisabledEndpointIds", [])
            if isinstance(item, str) and item
        ),
    }


def preflight_case(
    case: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    readiness_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    plan = router.plan_route(
        case["routeRequest"],
        policy=policy,
        readiness_overrides=readiness_overrides,
    )
    selected = plan.get("selectedRoute")
    ready = (
        plan.get("standing") == "SELECTED"
        and isinstance(selected, dict)
        and selected.get("routeId") == case["routeId"]
    )
    receipt = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-receipt",
        "benchmarkId": case["benchmarkId"],
        "suiteDigest": case["suiteDigest"],
        "taskId": case["taskId"],
        "taskDigest": case["taskDigest"],
        "caseId": case["caseId"],
        "caseDigest": case["caseDigest"],
        "routeId": case["routeId"],
        "routePlanDigest": plan["planDigest"],
        "outcomeCheckIds": list(case["outcomeCheckIds"]),
        "executionContractDigest": case["executionContractDigest"],
        "standing": "READY" if ready else "PREEXEC_BLOCKED",
        "blocker": None if ready else _blocker_from_plan(case, plan),
        "adapterReceiptDigest": None,
        "providerEffectMayHaveOccurred": False,
        "metrics": _not_observed_metrics(),
        "fallback": {"attempted": False, "routeIds": []},
        "outcomeWitness": {"standing": "NOT_EXECUTED", "checks": []},
        "nonClaims": [
            "provider_authorization",
            "browser_effect_execution",
            "runtime_execution_truth",
            "semantic_success",
        ],
    }
    receipt["receiptDigest"] = router.canonical_digest(receipt)
    validate_receipt(receipt, case=case, plan=plan)
    return receipt


def preflight_suite(
    suite: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    readiness_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    receipts = [
        preflight_case(case, policy=policy, readiness_overrides=readiness_overrides)
        for case in compile_cases(suite)
    ]
    report = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-preflight-report",
        "benchmarkId": suite["benchmarkId"],
        "suiteDigest": suite["suiteDigest"],
        "receipts": receipts,
        "counts": {
            "READY": sum(row["standing"] == "READY" for row in receipts),
            "PREEXEC_BLOCKED": sum(row["standing"] == "PREEXEC_BLOCKED" for row in receipts),
        },
        "effectsExecuted": False,
    }
    report["reportDigest"] = router.canonical_digest(report)
    return report


def _validate_metric(name: str, value: object) -> None:
    if not isinstance(value, dict) or set(value) != {"standing", "value"}:
        raise ValueError(f"metric {name} must contain exactly standing and value")
    standing = value.get("standing")
    observed = value.get("value")
    if standing == "NOT_OBSERVED":
        if observed is not None:
            raise ValueError(f"metric {name} NOT_OBSERVED must have null value")
        return
    if standing != "OBSERVED":
        raise ValueError(f"metric {name} has invalid standing")
    if METRIC_CONTRACT[name] == "integer" and (
        type(observed) is not int or observed < 0
    ):
        raise ValueError(f"metric {name} OBSERVED requires non-negative integer")


def validate_receipt(
    receipt: Mapping[str, Any],
    *,
    case: Mapping[str, Any] | None = None,
    plan: Mapping[str, Any] | None = None,
) -> None:
    if receipt.get("schemaVersion") != 1 or receipt.get("kind") != "ordivon.browser-benchmark-receipt":
        raise ValueError("benchmark receipt identity mismatch")
    standing = receipt.get("standing")
    if standing not in RECEIPT_STANDINGS:
        raise ValueError("benchmark receipt standing is invalid")
    for key in (
        "benchmarkId", "suiteDigest", "taskId", "taskDigest",
        "caseId", "caseDigest", "routeId", "routePlanDigest", "executionContractDigest",
    ):
        _trimmed(receipt.get(key), key)
    outcome_check_ids = _strings(
        receipt.get("outcomeCheckIds"), "outcomeCheckIds", allow_empty=False
    )
    if case is not None:
        for key in (
            "benchmarkId", "suiteDigest", "taskId", "taskDigest",
            "caseId", "caseDigest", "routeId", "executionContractDigest",
        ):
            if receipt.get(key) != case.get(key):
                raise ValueError(f"benchmark receipt differs from case: {key}")
        if list(outcome_check_ids) != list(case.get("outcomeCheckIds", [])):
            raise ValueError("benchmark receipt differs from case: outcomeCheckIds")
    if plan is not None and receipt.get("routePlanDigest") != plan.get("planDigest"):
        raise ValueError("benchmark receipt routePlanDigest mismatch")

    metrics = receipt.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(METRIC_CONTRACT):
        raise ValueError("benchmark receipt metric set mismatch")
    for name, value in metrics.items():
        _validate_metric(name, value)

    fallback = receipt.get("fallback")
    if (
        not isinstance(fallback, dict)
        or set(fallback) != {"attempted", "routeIds"}
        or type(fallback.get("attempted")) is not bool
        or not isinstance(fallback.get("routeIds"), list)
        or any(not isinstance(item, str) or not item for item in fallback["routeIds"])
    ):
        raise ValueError("benchmark receipt fallback object is invalid")
    if fallback["attempted"] or fallback["routeIds"]:
        raise ValueError("route-locked benchmark receipt forbids fallback")

    witness = receipt.get("outcomeWitness")
    if (
        not isinstance(witness, dict)
        or witness.get("standing") not in OUTCOME_STANDINGS
        or not isinstance(witness.get("checks"), list)
    ):
        raise ValueError("benchmark receipt outcome witness is invalid")

    if standing in PREEXEC_STANDINGS:
        if receipt.get("adapterReceiptDigest") is not None:
            raise ValueError("pre-execution receipt cannot bind adapter receipt")
        if receipt.get("providerEffectMayHaveOccurred") is not False:
            raise ValueError("pre-execution receipt cannot claim provider effect")
        if witness["standing"] != "NOT_EXECUTED" or witness["checks"]:
            raise ValueError("pre-execution receipt outcome witness must be NOT_EXECUTED")
        if any(value["standing"] != "NOT_OBSERVED" for value in metrics.values()):
            raise ValueError("pre-execution receipt cannot claim observed execution metrics")
        if standing == "READY" and receipt.get("blocker") is not None:
            raise ValueError("READY receipt must not carry blocker")
        if standing == "PREEXEC_BLOCKED" and not isinstance(receipt.get("blocker"), dict):
            raise ValueError("PREEXEC_BLOCKED receipt requires blocker")
    else:
        if receipt.get("blocker") is not None:
            raise ValueError("EXECUTED receipt must not carry blocker")
        adapter_digest = _trimmed(receipt.get("adapterReceiptDigest"), "adapterReceiptDigest")
        if not adapter_digest.startswith("sha256:") or len(adapter_digest) != 71:
            raise ValueError("EXECUTED receipt requires adapterReceiptDigest")
        if type(receipt.get("providerEffectMayHaveOccurred")) is not bool:
            raise ValueError("EXECUTED receipt requires boolean providerEffectMayHaveOccurred")
        if witness["standing"] == "NOT_EXECUTED":
            raise ValueError("EXECUTED receipt cannot have NOT_EXECUTED witness")

    expected = dict(receipt)
    claimed_digest = expected.pop("receiptDigest", None)
    if claimed_digest != router.canonical_digest(expected):
        raise ValueError("benchmark receipt digest mismatch")


def finalize_execution(
    ready_receipt: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    validate_receipt(ready_receipt)
    if ready_receipt["standing"] != "READY":
        raise ValueError("only READY preflight receipt can be finalized as EXECUTED")
    if (
        observation.get("schemaVersion") != 1
        or observation.get("kind") != "ordivon.browser-benchmark-execution-observation"
    ):
        raise ValueError("execution observation identity mismatch")
    for key in ("caseDigest", "routePlanDigest", "routeId"):
        if observation.get(key) != ready_receipt.get(key):
            raise ValueError(f"execution observation differs from preflight: {key}")
    adapter_digest = _trimmed(observation.get("adapterReceiptDigest"), "adapterReceiptDigest")
    if not adapter_digest.startswith("sha256:") or len(adapter_digest) != 71:
        raise ValueError("adapterReceiptDigest must be sha256 digest")
    metrics = observation.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(METRIC_CONTRACT):
        raise ValueError("execution observation metric set mismatch")
    for name, value in metrics.items():
        _validate_metric(name, value)
    witness = observation.get("outcomeWitness")
    if (
        not isinstance(witness, dict)
        or witness.get("standing") not in {"UNVERIFIED", "PASS", "FAIL"}
        or not isinstance(witness.get("checks"), list)
    ):
        raise ValueError("execution observation requires UNVERIFIED/PASS/FAIL witness")
    expected_checks = observation.get("expectedOutcomeCheckIds")
    if (
        not isinstance(expected_checks, list)
        or any(not isinstance(item, str) or not item for item in expected_checks)
        or expected_checks != ready_receipt["outcomeCheckIds"]
    ):
        raise ValueError("execution observation outcome contract differs from preflight")
    observed_ids = [
        row.get("checkId")
        for row in witness["checks"]
        if isinstance(row, dict) and isinstance(row.get("checkId"), str)
    ]
    if witness["standing"] in {"PASS", "FAIL"} and sorted(observed_ids) != sorted(expected_checks):
        raise ValueError("semantic witness check set differs from execution contract")
    result = dict(ready_receipt)
    result.update(
        {
            "standing": "EXECUTED",
            "blocker": None,
            "adapterReceiptDigest": adapter_digest,
            "providerEffectMayHaveOccurred": observation.get("providerEffectMayHaveOccurred"),
            "metrics": metrics,
            "outcomeWitness": witness,
            "nonClaims": [
                "provider_authorization",
                "runtime_execution_truth",
                "adapter_completion_is_not_semantic_success",
            ],
        }
    )
    result.pop("receiptDigest", None)
    result["receiptDigest"] = router.canonical_digest(result)
    validate_receipt(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--policy", type=Path, default=router.DEFAULT_ROUTE_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    validate = sub.add_parser("validate-receipt")
    validate.add_argument("--receipt-file", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "validate-receipt":
        receipt = _read_json(args.receipt_file)
        validate_receipt(receipt)
        print(
            json.dumps(
                {"standing": "VALID", "receiptDigest": receipt["receiptDigest"]},
                sort_keys=True,
            )
        )
        return 0

    policy = router.load_policy(args.policy)
    suite = load_suite(args.suite, policy=policy)
    report = preflight_suite(suite, policy=policy)
    print(json.dumps(report, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
