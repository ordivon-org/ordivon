#!/usr/bin/env python3
"""Read-only browser-domain route planner.

The caller supplies explicit routing requirements. This module does not infer requirements from
natural-language tasks, grant provider authority, execute browser effects, or redefine Harness
Run/Runtime truth. It selects a currently ready browser route before effectful adapter construction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

SOURCE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROUTE_CONFIG = SOURCE_ROOT / "config/browser-capability-routes.json"


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_policy(path: Path = DEFAULT_ROUTE_CONFIG) -> dict[str, Any]:
    value = _read_json(path)
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.browser-domain-route-policy":
        raise ValueError("browser route policy identity mismatch")
    raw_routes = value.get("routes")
    if not isinstance(raw_routes, list) or not raw_routes:
        raise ValueError("browser route policy requires routes")
    seen = set()
    routes = []
    for raw in raw_routes:
        if not isinstance(raw, dict):
            raise ValueError("browser route must be an object")
        route_id = raw.get("routeId")
        provider_flow = raw.get("providerFlow")
        executor = raw.get("executor")
        substrate = raw.get("substrate")
        priority = raw.get("priority")
        provides = raw.get("provides")
        readiness = raw.get("readiness")
        if (
            not isinstance(route_id, str)
            or not route_id
            or route_id in seen
            or not isinstance(provider_flow, str)
            or not provider_flow
            or not isinstance(executor, str)
            or not executor
            or not isinstance(substrate, str)
            or not substrate
            or type(priority) is not int
            or priority < 0
            or not isinstance(provides, list)
            or any(not isinstance(x, str) or not x for x in provides)
            or len(set(provides)) != len(provides)
            or not isinstance(readiness, dict)
            or not isinstance(readiness.get("kind"), str)
        ):
            raise ValueError(f"invalid browser route: {route_id!r}")
        seen.add(route_id)
        routes.append(dict(raw))
    return {
        "schemaVersion": 1,
        "kind": value["kind"],
        "routes": routes,
        "policyDigest": canonical_digest(value),
    }


def validate_request(value: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    if value.get("schemaVersion") != 1:
        raise ValueError("route request requires schemaVersion=1")
    request_id = value.get("requestId")
    provider_flow = value.get("providerFlow")
    if not isinstance(request_id, str) or not request_id or request_id != request_id.strip():
        raise ValueError("requestId must be non-empty trimmed text")
    if not isinstance(provider_flow, str) or not provider_flow or provider_flow != provider_flow.strip():
        raise ValueError("providerFlow must be non-empty trimmed text")
    known_flows = {route["providerFlow"] for route in policy["routes"]}
    if provider_flow not in known_flows:
        raise ValueError(f"unknown providerFlow: {provider_flow}")

    def features(name: str) -> tuple[str, ...]:
        raw = value.get(name, [])
        if not isinstance(raw, list) or any(
            not isinstance(item, str) or not item or item != item.strip() for item in raw
        ):
            raise ValueError(f"{name} must be a list of non-empty trimmed strings")
        if len(set(raw)) != len(raw):
            raise ValueError(f"{name} must not contain duplicates")
        return tuple(raw)

    required = features("requiredFeatures")
    preferred = features("preferredFeatures")
    known_features = {
        feature for route in policy["routes"] for feature in route.get("provides", [])
    }
    unknown = sorted((set(required) | set(preferred)) - known_features)
    if unknown:
        raise ValueError(f"unknown browser routing features: {unknown}")
    explicit = value.get("explicitRouteId")
    if explicit is not None and (
        not isinstance(explicit, str) or not explicit or explicit != explicit.strip()
    ):
        raise ValueError("explicitRouteId must be null or non-empty trimmed text")
    return {
        "schemaVersion": 1,
        "requestId": request_id,
        "providerFlow": provider_flow,
        "requiredFeatures": required,
        "preferredFeatures": preferred,
        "explicitRouteId": explicit,
    }


def _subprocess_json(args: list[str], *, timeout: int = 15) -> tuple[int, dict[str, Any] | None, str]:
    proc = subprocess.run(
        args,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError:
        value = None
    return proc.returncode, value if isinstance(value, dict) else None, (proc.stderr or "").strip()


def _probe_jev(route: Mapping[str, Any], required: set[str]) -> dict[str, Any]:
    cfg = route["readiness"]
    command = str(cfg.get("workstationStatusCommand") or "")
    if not command.startswith("/") or not Path(command).is_file():
        return {
            "ready": False,
            "standing": "WORKSTATION_PROVIDER_UNAVAILABLE",
            "missingEnvironment": [],
        }
    rc, status, stderr = _subprocess_json([command, "status"], timeout=20)
    physical = bool(status and status.get("healthy") is True)
    missing = []
    for name in cfg.get("requiredEnvironment", []):
        if not os.environ.get(name):
            missing.append(name)
    feature_env = cfg.get("featureEnvironment", {})
    if isinstance(feature_env, dict):
        for feature in sorted(required):
            names = feature_env.get(feature, [])
            if isinstance(names, list):
                for name in names:
                    if isinstance(name, str) and name and not os.environ.get(name):
                        missing.append(name)
    missing = sorted(set(missing))
    ready = physical and not missing
    return {
        "ready": ready,
        "standing": (
            "READY"
            if ready
            else "CREDENTIAL_MISSING"
            if physical and missing
            else "WORKSTATION_PROVIDER_UNHEALTHY"
        ),
        "workstationHealthy": physical,
        "chromeVersion": (status or {}).get("chrome", {}).get("version") if status else None,
        "jevVersion": (status or {}).get("packages", {}).get("jevVersion") if status else None,
        "browserHarnessVersion": (
            (status or {}).get("packages", {}).get("browserHarnessVersion") if status else None
        ),
        "missingEnvironment": missing,
        "probeReturnCode": rc,
        "probeError": stderr[:500] or None,
    }


def _probe_browser_use(route: Mapping[str, Any]) -> dict[str, Any]:
    try:
        from browserless_substrate import BrowserlessPool
    except ModuleNotFoundError:
        from scripts.browserless_substrate import BrowserlessPool

    path = Path(str(route["readiness"].get("configPath") or ""))
    if not path.is_file():
        return {"ready": False, "standing": "CONFIG_UNAVAILABLE"}
    try:
        value = _read_json(path)
        executable = Path(str(value.get("browserUseExecutable") or ""))
        pool = BrowserlessPool.from_dict(value.get("browserSubstrate"))
        masked = []
        for endpoint in pool.endpoints:
            service_unit = getattr(endpoint, "service_unit", None)
            if not isinstance(service_unit, str) or not service_unit:
                continue
            proc = subprocess.run(
                ["/usr/bin/systemctl", "is-enabled", service_unit],
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
            )
            if proc.stdout.strip() == "masked":
                masked.append(endpoint.endpoint_id)
        if masked and len(masked) == len(pool.endpoints):
            return {
                "ready": False,
                "standing": "POLICY_DISABLED",
                "executable": str(executable),
                "executableReady": executable.is_file() and os.access(executable, os.X_OK),
                "policyDisabledEndpointIds": masked,
                "browserlessHealthy": False,
                "healthyEndpointIds": [],
            }
        health = pool.health()
    except Exception as error:
        return {
            "ready": False,
            "standing": "READINESS_PROBE_FAILED",
            "detail": f"{type(error).__name__}: {str(error)[:500]}",
        }
    executable_ready = executable.is_file() and os.access(executable, os.X_OK)
    pool_ready = health.get("healthy") is True
    ready = executable_ready and pool_ready
    return {
        "ready": ready,
        "standing": (
            "READY"
            if ready
            else "EXECUTABLE_UNAVAILABLE"
            if not executable_ready
            else "BROWSERLESS_UNAVAILABLE"
        ),
        "executable": str(executable),
        "executableReady": executable_ready,
        "browserlessHealthy": pool_ready,
        "healthyEndpointIds": [
            row.get("id") for row in health.get("endpoints", []) if row.get("healthy") is True
        ],
    }


def _probe_agent_automation(route: Mapping[str, Any]) -> dict[str, Any]:
    try:
        from agent_automation_browserless import BrowserlessAutomationConfig, BrowserlessAutomationService
    except ModuleNotFoundError:
        from scripts.agent_automation_browserless import (
            BrowserlessAutomationConfig,
            BrowserlessAutomationService,
        )

    path = Path(str(route["readiness"].get("configPath") or ""))
    if not path.is_file():
        return {"ready": False, "standing": "CONFIG_UNAVAILABLE"}
    try:
        service = BrowserlessAutomationService(BrowserlessAutomationConfig.from_dict(_read_json(path)))
        doctor = service.doctor()
    except Exception as error:
        return {
            "ready": False,
            "standing": "READINESS_PROBE_FAILED",
            "detail": f"{type(error).__name__}: {str(error)[:500]}",
        }
    ready = doctor.get("healthy") is True
    health = doctor.get("browserSubstrate") if isinstance(doctor.get("browserSubstrate"), dict) else {}
    return {
        "ready": ready,
        "standing": "READY" if ready else "AGENT_AUTOMATION_UNHEALTHY",
        "browserlessHealthy": health.get("healthy") is True,
        "healthyEndpointIds": [
            row.get("id") for row in health.get("endpoints", []) if row.get("healthy") is True
        ],
        "ledgerHealthy": (
            doctor.get("ledger", {}).get("healthy") is True
            if isinstance(doctor.get("ledger"), dict)
            else False
        ),
    }


def probe_route(route: Mapping[str, Any], required_features: set[str]) -> dict[str, Any]:
    kind = route["readiness"]["kind"]
    if kind == "jev_windows":
        return _probe_jev(route, required_features)
    if kind == "browser_use_browserless":
        return _probe_browser_use(route)
    if kind == "agent_automation_browserless":
        return _probe_agent_automation(route)
    if kind == "not_materialized":
        return {"ready": False, "standing": "NOT_MATERIALIZED"}
    return {"ready": False, "standing": "UNKNOWN_READINESS_KIND"}


def plan_route(
    raw_request: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
    readiness_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    policy = policy or load_policy()
    request = validate_request(raw_request, policy)
    required = set(request["requiredFeatures"])
    preferred = set(request["preferredFeatures"])
    overrides = readiness_overrides or {}

    rows = []
    route_by_id = {route["routeId"]: route for route in policy["routes"]}
    explicit = request["explicitRouteId"]
    if explicit is not None and explicit not in route_by_id:
        raise ValueError(f"unknown explicitRouteId: {explicit}")

    if explicit is not None:
        exact = route_by_id[explicit]
        candidate_routes = (
            [exact] if exact["providerFlow"] == request["providerFlow"] else []
        )
    else:
        candidate_routes = [
            route
            for route in policy["routes"]
            if route["providerFlow"] == request["providerFlow"]
        ]

    for route in candidate_routes:
        provides = set(route["provides"])
        missing_features = sorted(required - provides)
        compatible = not missing_features
        if not compatible:
            readiness = {
                "ready": False,
                "standing": "NOT_PROBED_STATIC_INCOMPATIBLE",
            }
        else:
            readiness = (
                dict(overrides[route["routeId"]])
                if route["routeId"] in overrides
                else probe_route(route, required)
            )
        ready = readiness.get("ready") is True
        rows.append(
            {
                "routeId": route["routeId"],
                "executor": route["executor"],
                "substrate": route["substrate"],
                "providerFlow": route["providerFlow"],
                "priority": route["priority"],
                "compatible": compatible,
                "missingFeatures": missing_features,
                "preferredMatches": sorted(preferred & provides),
                "preferredMatchCount": len(preferred & provides),
                "ready": ready,
                "readiness": readiness,
            }
        )

    if explicit is not None:
        row = next(row for row in rows if row["routeId"] == explicit) if any(
            row["routeId"] == explicit for row in rows
        ) else None
        if row is None:
            standing = "HOLD_EXPLICIT_ROUTE_FLOW_MISMATCH"
            selected = None
        elif not row["compatible"]:
            standing = "HOLD_EXPLICIT_ROUTE_INCOMPATIBLE"
            selected = None
        elif not row["ready"]:
            standing = "HOLD_EXPLICIT_ROUTE_NOT_READY"
            selected = None
        else:
            standing = "SELECTED"
            selected = row
    else:
        compatible = [row for row in rows if row["compatible"]]
        ready = [row for row in compatible if row["ready"]]
        if not compatible:
            standing = "HOLD_NO_COMPATIBLE_ROUTE"
            selected = None
        elif not ready:
            standing = "HOLD_NO_READY_ROUTE"
            selected = None
        else:
            ready.sort(
                key=lambda row: (
                    -row["preferredMatchCount"],
                    row["priority"],
                    row["routeId"],
                )
            )
            selected = ready[0]
            standing = "SELECTED"

    selected_route = None
    if selected is not None:
        selected_route = {
            key: selected[key]
            for key in ("routeId", "executor", "substrate", "providerFlow")
        }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-route-plan",
        "requestId": request["requestId"],
        "requestDigest": canonical_digest(
            {
                "schemaVersion": request["schemaVersion"],
                "requestId": request["requestId"],
                "providerFlow": request["providerFlow"],
                "requiredFeatures": list(request["requiredFeatures"]),
                "preferredFeatures": list(request["preferredFeatures"]),
                "explicitRouteId": request["explicitRouteId"],
            }
        ),
        "policyDigest": policy["policyDigest"],
        "standing": standing,
        "selectedRoute": selected_route,
        "candidates": rows,
        "nonClaims": [
            "task_authorization",
            "website_compatibility",
            "provider_semantic_success",
            "runtime_execution_truth",
            "global_capability_registry",
        ],
    }
    result["planDigest"] = canonical_digest(result)
    return result


def doctor(*, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    policy = policy or load_policy()
    rows = []
    for route in policy["routes"]:
        readiness = probe_route(route, set())
        rows.append(
            {
                "routeId": route["routeId"],
                "providerFlow": route["providerFlow"],
                "executor": route["executor"],
                "substrate": route["substrate"],
                "ready": readiness.get("ready") is True,
                "readiness": readiness,
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-capability-router-doctor",
        "policyDigest": policy["policyDigest"],
        "routes": rows,
        "readyRouteIds": [row["routeId"] for row in rows if row["ready"]],
        "healthy": any(row["ready"] for row in rows),
        "nonClaims": ["provider_authorization", "semantic_success", "browser_effect"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", type=Path, default=DEFAULT_ROUTE_CONFIG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    plan = sub.add_parser("plan")
    plan.add_argument("--request-file", type=Path, required=True)
    args = parser.parse_args()
    policy = load_policy(args.policy)
    if args.command == "doctor":
        value = doctor(policy=policy)
    else:
        value = plan_route(_read_json(args.request_file), policy=policy)
    print(json.dumps(value, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
