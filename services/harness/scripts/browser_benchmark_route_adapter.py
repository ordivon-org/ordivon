#!/usr/bin/env python3
"""Effectful route adapters for Browser Benchmark S3.

This script must run on the execution target selected for the route. It never chooses another
route. The S2 READY receipt is an admission prerequisite. It returns either PRE_EFFECT_ABORTED
(no benchmark effect was admitted) or EXECUTED with an S2-finalized benchmark receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Callable, Mapping
from urllib.parse import quote

import browser_benchmark_contract as benchmark
import browser_capability_router as router

RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
PRE_EFFECT_JEV_STANDINGS = frozenset(
    {"CREDENTIAL_MISSING", "PROVIDER_ENV_INVALID", "FAILED_BEFORE_ACTION"}
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _text_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _inline_html_url(contract: Mapping[str, Any]) -> str:
    html = str(contract["documentHtml"])
    return "data:text/html;charset=utf-8," + quote(html, safe="")


def _metric_cells(observed: Mapping[str, int]) -> dict[str, dict[str, Any]]:
    unknown = set(observed) - set(benchmark.METRIC_CONTRACT)
    if unknown:
        raise ValueError(f"adapter emitted unknown benchmark metrics: {sorted(unknown)}")
    cells = {
        name: {"standing": "NOT_OBSERVED", "value": None}
        for name in benchmark.METRIC_CONTRACT
    }
    for name, value in observed.items():
        if type(value) is not int or value < 0:
            raise ValueError(f"adapter metric {name} must be a non-negative integer")
        cells[name] = {"standing": "OBSERVED", "value": value}
    return cells


def validate_run_request(raw: Mapping[str, Any]) -> dict[str, Any]:
    if raw.get("schemaVersion") != 1 or raw.get("kind") != "ordivon.browser-benchmark-route-run-request":
        raise ValueError("route run request identity mismatch")
    run_id = raw.get("runId")
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ValueError("runId must be a bounded stable identifier")
    case = raw.get("case")
    receipt = raw.get("preflightReceipt")
    if not isinstance(case, dict) or not isinstance(receipt, dict):
        raise ValueError("route run request requires case and preflightReceipt")
    benchmark.validate_receipt(receipt, case=case)
    if receipt["standing"] != "READY":
        raise ValueError("effectful route adapter requires READY preflight receipt")
    if case.get("routeId") != receipt.get("routeId"):
        raise ValueError("route run case/receipt route mismatch")
    contract = case.get("executionContract")
    if (
        not isinstance(contract, dict)
        or case.get("executionContractDigest") != router.canonical_digest(contract)
        or receipt.get("executionContractDigest") != case.get("executionContractDigest")
    ):
        raise ValueError("route run execution contract identity mismatch")
    normalized = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-route-run-request",
        "runId": run_id,
        "case": case,
        "preflightReceipt": receipt,
    }
    expected = router.canonical_digest(normalized)
    if raw.get("requestDigest") != expected:
        raise ValueError("route run request digest mismatch")
    normalized["requestDigest"] = expected
    return normalized


def _normalized_witness(
    case: Mapping[str, Any],
    standing: str,
    *,
    passed: bool | None = None,
    observed_text_digest: str | None = None,
) -> dict[str, Any]:
    if standing == "UNVERIFIED":
        return {"standing": "UNVERIFIED", "checks": []}
    if standing not in {"PASS", "FAIL"} or passed is None:
        raise ValueError("witness standing is invalid")
    check_ids = case["outcomeCheckIds"]
    if len(check_ids) != 1:
        raise ValueError("S3 inline click adapter currently requires one outcome check")
    return {
        "standing": standing,
        "checks": [
            {
                "checkId": check_ids[0],
                "standing": standing,
                "passed": bool(passed),
                "observedTextDigest": observed_text_digest,
            }
        ],
    }


def _jev_route_adapter(
    case: Mapping[str, Any],
    run_id: str,
    *,
    execute_fn: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    if execute_fn is None:
        import jev_fastpath_adapter as jev

        execute_fn = jev.execute_request
    contract = case["executionContract"]
    request_id = "bcrs3-" + hashlib.sha256(
        f"{run_id}:{case['caseDigest']}".encode()
    ).hexdigest()[:32]
    provider_request = {
        "schemaVersion": 1,
        "requestId": request_id,
        "url": _inline_html_url(contract),
        "goal": contract["goal"],
        "requireText": False,
        "witness": {"textContains": contract["successText"]},
    }
    started = monotonic()
    raw_receipt = dict(execute_fn(provider_request))
    elapsed_ms = max(0, int(round((monotonic() - started) * 1000)))
    provider_effect = bool(raw_receipt.get("providerEffectMayHaveOccurred"))
    standing = str(raw_receipt.get("standing") or "")
    observed_metrics: dict[str, int] = {
        "totalElapsedMs": elapsed_ms,
        "taskElapsedMs": elapsed_ms,
        "fallbackCount": 0,
    }
    action_count = raw_receipt.get("actionCount")
    if type(action_count) is int and action_count >= 0:
        observed_metrics["actionCount"] = action_count

    if standing in PRE_EFFECT_JEV_STANDINGS and not provider_effect:
        return {
            "standing": "PRE_EFFECT_ABORTED",
            "providerEffectMayHaveOccurred": False,
            "adapterReceipt": raw_receipt,
            "metrics": observed_metrics,
            "outcomeWitness": {"standing": "UNVERIFIED", "checks": []},
        }

    raw_witness = raw_receipt.get("outcomeWitness")
    raw_witness = raw_witness if isinstance(raw_witness, dict) else {}
    witness_standing = raw_witness.get("standing")
    if witness_standing in {"PASS", "FAIL"}:
        raw_checks = raw_witness.get("checks")
        observed_digest = None
        if isinstance(raw_checks, list):
            for row in raw_checks:
                if isinstance(row, dict) and row.get("kind") == "textContains":
                    candidate = row.get("observedTextDigest")
                    if isinstance(candidate, str):
                        observed_digest = candidate
        witness = _normalized_witness(
            case,
            witness_standing,
            passed=witness_standing == "PASS",
            observed_text_digest=observed_digest,
        )
    else:
        witness = _normalized_witness(case, "UNVERIFIED")
    return {
        "standing": "EXECUTION_OBSERVED",
        "providerEffectMayHaveOccurred": provider_effect,
        "adapterReceipt": raw_receipt,
        "metrics": observed_metrics,
        "outcomeWitness": witness,
    }


def _parse_json_stdout(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise RuntimeError("Browser Use action returned no JSON object")


def _browser_use_route_adapter(
    case: Mapping[str, Any],
    run_id: str,
    *,
    browser_module: Any | None = None,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    if browser_module is None:
        import browser_use_browserless as browser_module

    contract = case["executionContract"]
    value, pool = browser_module.load_config(browser_module.DEFAULT_CONFIG)
    executable = str(value.get("browserUseExecutable") or "")
    session_id = "bcrs3:" + hashlib.sha256(
        f"{run_id}:{case['caseDigest']}".encode()
    ).hexdigest()[:24]
    endpoint = browser_module.select_endpoint(pool, session_id, None)
    provider_effect = False
    action_count = 0
    total_started = monotonic()
    bootstrap_started = total_started
    cleanup = None

    def generated(program: str, *, timeout: int = 90) -> dict[str, Any]:
        proc = browser_module._run_browser_use(
            executable,
            program,
            browser_module._generated_env(endpoint, session_id),
            timeout=timeout,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "Browser Use action failed").strip()[-1000:]
            raise RuntimeError(detail)
        return _parse_json_stdout(proc.stdout or "")

    try:
        browser_module.ensure_daemon(executable, endpoint, session_id)
        bootstrap_ms = max(0, int(round((monotonic() - bootstrap_started) * 1000)))
        task_started = monotonic()

        provider_effect = True
        opened = generated(browser_module.program_open(_inline_html_url(contract)))
        action_count += 1
        before = generated(browser_module.program_observe(include_text=True, max_chars=6000))
        affordances = before.get("affordances")
        matches = [
            row
            for row in (affordances if isinstance(affordances, list) else [])
            if isinstance(row, dict)
            and row.get("role") == contract["buttonRole"]
            and row.get("name") == contract["buttonName"]
        ]
        if len(matches) != 1:
            raise RuntimeError(f"benchmark target affordance count is {len(matches)}, expected 1")
        target = matches[0]
        clicked = generated(
            browser_module.program_click(
                int(target["index"]),
                contract["buttonRole"],
                contract["buttonName"],
            )
        )
        action_count += 1
        after = generated(browser_module.program_observe(include_text=True, max_chars=6000))
        visible = str(after.get("visibleText") or "")
        passed = contract["successText"] in visible
        task_ms = max(0, int(round((monotonic() - task_started) * 1000)))
        total_ms = max(0, int(round((monotonic() - total_started) * 1000)))
        witness = _normalized_witness(
            case,
            "PASS" if passed else "FAIL",
            passed=passed,
            observed_text_digest=_text_digest(visible),
        )
        adapter_receipt = {
            "schemaVersion": 1,
            "kind": "ordivon.browser-use-benchmark-adapter-receipt",
            "endpointId": endpoint.endpoint_id,
            "sessionNameDigest": _text_digest(browser_module.session_name(session_id)),
            "steps": {
                "openStanding": opened.get("standing"),
                "initialObserveStanding": before.get("standing"),
                "clickStanding": clicked.get("standing"),
                "finalObserveStanding": after.get("standing"),
            },
            "target": {
                "role": contract["buttonRole"],
                "name": contract["buttonName"],
            },
            "finalVisibleTextDigest": _text_digest(visible),
            "outcomeWitness": witness,
        }
        return {
            "standing": "EXECUTION_OBSERVED",
            "providerEffectMayHaveOccurred": True,
            "adapterReceipt": adapter_receipt,
            "metrics": {
                "totalElapsedMs": total_ms,
                "bootstrapElapsedMs": bootstrap_ms,
                "taskElapsedMs": task_ms,
                "actionCount": action_count,
                "modelRequestCount": 0,
                "retryCount": 0,
                "staleActionRetryCount": 0,
                "fallbackCount": 0,
            },
            "outcomeWitness": witness,
        }
    except Exception as error:
        elapsed_ms = max(0, int(round((monotonic() - total_started) * 1000)))
        adapter_receipt = {
            "schemaVersion": 1,
            "kind": "ordivon.browser-use-benchmark-adapter-receipt",
            "endpointId": getattr(endpoint, "endpoint_id", None),
            "error": {"type": type(error).__name__, "message": str(error)[:1000]},
            "actionCount": action_count,
        }
        return {
            "standing": "EXECUTION_OBSERVED" if provider_effect else "PRE_EFFECT_ABORTED",
            "providerEffectMayHaveOccurred": provider_effect,
            "adapterReceipt": adapter_receipt,
            "metrics": {
                "totalElapsedMs": elapsed_ms,
                "actionCount": action_count,
                "modelRequestCount": 0,
                "fallbackCount": 0,
            },
            "outcomeWitness": _normalized_witness(case, "UNVERIFIED"),
        }
    finally:
        try:
            cleanup = browser_module.close_session(executable, endpoint, session_id)
        except Exception:
            cleanup = None
        _ = cleanup


REAL_ROUTE_ADAPTERS: dict[str, Callable[..., dict[str, Any]]] = {
    "jev-fast-windows-v1": _jev_route_adapter,
    "browser-use-browserless-v1": _browser_use_route_adapter,
}


def build_run_request(
    case: Mapping[str, Any],
    preflight_receipt: Mapping[str, Any],
    run_id: str,
) -> dict[str, Any]:
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ValueError("runId must be a bounded stable identifier")
    benchmark.validate_receipt(preflight_receipt, case=case)
    if preflight_receipt["standing"] != "READY":
        raise ValueError("route run request requires READY preflight receipt")
    request = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-route-run-request",
        "runId": run_id,
        "case": dict(case),
        "preflightReceipt": dict(preflight_receipt),
    }
    request["requestDigest"] = router.canonical_digest(request)
    return request


def _finalize_run_result(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["resultDigest"] = router.canonical_digest(result)
    return result


def validate_run_result(
    raw: Mapping[str, Any],
    *,
    expected_run_id: str | None = None,
    expected_request_digest: str | None = None,
    expected_case_digest: str | None = None,
    expected_route_id: str | None = None,
) -> dict[str, Any]:
    if (
        raw.get("schemaVersion") != 1
        or raw.get("kind") != "ordivon.browser-benchmark-route-run-result"
    ):
        raise ValueError("route run result identity mismatch")
    run_id = raw.get("runId")
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise ValueError("route run result has invalid runId")
    for key in ("requestDigest", "caseDigest", "routePlanDigest", "routeId", "adapterReceiptDigest"):
        value = raw.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"route run result has invalid {key}")
    if expected_run_id is not None and run_id != expected_run_id:
        raise ValueError("route run result runId differs")
    if expected_request_digest is not None and raw["requestDigest"] != expected_request_digest:
        raise ValueError("route run result requestDigest differs")
    if expected_case_digest is not None and raw["caseDigest"] != expected_case_digest:
        raise ValueError("route run result caseDigest differs")
    if expected_route_id is not None and raw["routeId"] != expected_route_id:
        raise ValueError("route run result routeId differs")
    standing = raw.get("standing")
    if standing not in {"PRE_EFFECT_ABORTED", "EXECUTED"}:
        raise ValueError("route run result standing is invalid")
    provider_effect = raw.get("providerEffectMayHaveOccurred")
    if type(provider_effect) is not bool:
        raise ValueError("route run result providerEffectMayHaveOccurred is invalid")
    adapter_receipt = raw.get("adapterReceipt")
    if not isinstance(adapter_receipt, dict):
        raise ValueError("route run result adapterReceipt is invalid")
    if router.canonical_digest(adapter_receipt) != raw["adapterReceiptDigest"]:
        raise ValueError("route run result adapterReceiptDigest differs")
    benchmark_receipt = raw.get("benchmarkReceipt")
    if standing == "PRE_EFFECT_ABORTED":
        if provider_effect or benchmark_receipt is not None:
            raise ValueError("PRE_EFFECT_ABORTED route result has effect/benchmark receipt")
    else:
        if not isinstance(benchmark_receipt, dict):
            raise ValueError("EXECUTED route result requires benchmarkReceipt")
        benchmark.validate_receipt(benchmark_receipt)
        if benchmark_receipt.get("standing") != "EXECUTED":
            raise ValueError("route run benchmarkReceipt is not EXECUTED")
        for key in ("caseDigest", "routePlanDigest", "routeId"):
            if benchmark_receipt.get(key) != raw.get(key):
                raise ValueError(f"route run benchmarkReceipt differs: {key}")
    expected = dict(raw)
    claimed = expected.pop("resultDigest", None)
    if claimed != router.canonical_digest(expected):
        raise ValueError("route run result digest mismatch")
    return dict(raw)


def run_request(
    raw: Mapping[str, Any],
    *,
    adapters: Mapping[str, Callable[[Mapping[str, Any], str], Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    request = validate_run_request(raw)
    case = request["case"]
    preflight = request["preflightReceipt"]
    route_id = case["routeId"]
    selected = (adapters or REAL_ROUTE_ADAPTERS).get(route_id)
    if selected is None:
        raise ValueError(f"no S3 route adapter for {route_id}")
    adapter_result = dict(selected(case, request["runId"]))
    adapter_receipt = adapter_result.get("adapterReceipt")
    if not isinstance(adapter_receipt, dict):
        raise ValueError("route adapter must return bounded adapterReceipt object")
    adapter_digest = router.canonical_digest(adapter_receipt)
    provider_effect = adapter_result.get("providerEffectMayHaveOccurred")
    if type(provider_effect) is not bool:
        raise ValueError("route adapter must report providerEffectMayHaveOccurred")
    standing = adapter_result.get("standing")
    if standing == "PRE_EFFECT_ABORTED":
        if provider_effect:
            raise ValueError("PRE_EFFECT_ABORTED cannot claim provider effect")
        return _finalize_run_result(
            {
                "schemaVersion": 1,
                "kind": "ordivon.browser-benchmark-route-run-result",
                "runId": request["runId"],
                "requestDigest": request["requestDigest"],
                "standing": "PRE_EFFECT_ABORTED",
                "caseDigest": case["caseDigest"],
                "routePlanDigest": preflight["routePlanDigest"],
                "routeId": route_id,
                "providerEffectMayHaveOccurred": False,
                "adapterReceiptDigest": adapter_digest,
                "adapterReceipt": adapter_receipt,
                "benchmarkReceipt": None,
            }
        )
    if standing != "EXECUTION_OBSERVED":
        raise ValueError("route adapter standing is invalid")
    metrics = _metric_cells(adapter_result.get("metrics") or {})
    witness = adapter_result.get("outcomeWitness")
    if not isinstance(witness, dict):
        raise ValueError("route adapter requires outcomeWitness")
    observation = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-benchmark-execution-observation",
        "caseDigest": case["caseDigest"],
        "routePlanDigest": preflight["routePlanDigest"],
        "routeId": route_id,
        "adapterReceiptDigest": adapter_digest,
        "providerEffectMayHaveOccurred": provider_effect,
        "metrics": metrics,
        "expectedOutcomeCheckIds": list(preflight["outcomeCheckIds"]),
        "outcomeWitness": witness,
    }
    final = benchmark.finalize_execution(preflight, observation)
    return _finalize_run_result(
        {
            "schemaVersion": 1,
            "kind": "ordivon.browser-benchmark-route-run-result",
            "runId": request["runId"],
            "requestDigest": request["requestDigest"],
            "standing": "EXECUTED",
            "caseDigest": case["caseDigest"],
            "routePlanDigest": preflight["routePlanDigest"],
            "routeId": route_id,
            "providerEffectMayHaveOccurred": provider_effect,
            "adapterReceiptDigest": adapter_digest,
            "adapterReceipt": adapter_receipt,
            "benchmarkReceipt": final,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--request-file", type=Path, required=True)
    args = parser.parse_args()
    result = run_request(_read_json(args.request_file))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
