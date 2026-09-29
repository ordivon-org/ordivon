#!/usr/bin/env python3
"""Deterministic Research capability route compiler.

The caller supplies an explicit research problem class plus natural-owner observations.
This module does not classify natural language, authorize effects, invoke providers, or decide
scientific completion. It compiles a task-local route binding only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "research-capability-routing-r1.json"


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class RouteRequest:
    problem_class: str
    required_features: tuple[str, ...] = ()
    preferred_features: tuple[str, ...] = ()
    explicit_route_id: str | None = None

    def __post_init__(self) -> None:
        for label, value in (("problem_class", self.problem_class),):
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError(f"{label} must be non-empty trimmed text")
        for label, values in (("required_features", self.required_features), ("preferred_features", self.preferred_features)):
            if any(not isinstance(item, str) or not item or item != item.strip() for item in values):
                raise ValueError(f"{label} must contain non-empty trimmed strings")
            if len(set(values)) != len(values):
                raise ValueError(f"{label} must not contain duplicates")
        if self.explicit_route_id is not None and (
            not isinstance(self.explicit_route_id, str)
            or not self.explicit_route_id
            or self.explicit_route_id != self.explicit_route_id.strip()
        ):
            raise ValueError("explicit_route_id must be null or non-empty trimmed text")


def load_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schemaVersion") != 1 or value.get("kind") != "ordivon.research-capability-routing-profile":
        raise ValueError("research routing profile identity mismatch")
    problem_classes = value.get("problemClasses")
    routes = value.get("routes")
    if not isinstance(problem_classes, list) or not problem_classes or len(set(problem_classes)) != len(problem_classes):
        raise ValueError("profile problemClasses must be a unique non-empty list")
    if not isinstance(routes, list) or not routes:
        raise ValueError("profile routes must be a non-empty list")
    seen: set[str] = set()
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("route must be an object")
        route_id = route.get("routeId")
        if not isinstance(route_id, str) or not route_id or route_id in seen:
            raise ValueError(f"invalid/duplicate routeId: {route_id!r}")
        seen.add(route_id)
        classes = route.get("problemClasses")
        provides = route.get("provides")
        if not isinstance(classes, list) or not classes or any(x not in problem_classes for x in classes):
            raise ValueError(f"route {route_id} has invalid problemClasses")
        if not isinstance(provides, list) or len(set(provides)) != len(provides):
            raise ValueError(f"route {route_id} has invalid provides")
        if not isinstance(route.get("currentnessKey"), str) or not route["currentnessKey"]:
            raise ValueError(f"route {route_id} lacks currentnessKey")
        if not isinstance(route.get("rank"), int) or route["rank"] < 0:
            raise ValueError(f"route {route_id} has invalid rank")
    return value


def _availability(route: Mapping[str, Any], observations: Mapping[str, Mapping[str, Any]], caller_available: set[str], problem_class: str) -> dict[str, Any]:
    key = str(route["currentnessKey"])
    raw = observations.get(key)
    if raw is None:
        return {"state": "unknown", "ready": False, "authorityKey": key, "reason": "currentness observation required from natural owner"}
    state = raw.get("state")
    reason = str(raw.get("reason") or "owner observation supplied")
    if state == "caller_bound":
        ready = key in caller_available
        return {"state": state, "ready": ready, "authorityKey": key, "reason": reason if ready else "caller-bound capability was not admitted by current caller"}
    if state in {"available", "ready"}:
        result: dict[str, Any] = {"state": state, "ready": True, "authorityKey": key, "reason": reason}
        if isinstance(raw.get("bindingRef"), str):
            result["bindingRef"] = raw["bindingRef"]
        binding_problem = route.get("bindingProblemClass")
        if binding_problem is not None:
            bindings = raw.get("bindings")
            binding = bindings.get(problem_class) if isinstance(bindings, dict) else None
            valid_binding = (
                isinstance(binding, str) and bool(binding)
            ) or (
                isinstance(binding, list)
                and bool(binding)
                and all(isinstance(item, str) and item for item in binding)
            )
            if not valid_binding:
                result.update({"state": "binding_missing", "ready": False, "reason": f"owner observation lacks provider binding for {problem_class}"})
            else:
                result["providerBinding"] = binding
        return result
    return {"state": str(state or "unknown"), "ready": False, "authorityKey": key, "reason": reason}


def resolve(request: RouteRequest, *, observations: Mapping[str, Mapping[str, Any]], caller_available: tuple[str, ...] = (), profile: Mapping[str, Any] | None = None) -> dict[str, Any]:
    profile = dict(profile or load_profile())
    known_classes = set(profile["problemClasses"])
    if request.problem_class not in known_classes:
        raise ValueError(f"unknown research problem class: {request.problem_class}")
    caller_bound = set(caller_available)
    route_by_id = {route["routeId"]: route for route in profile["routes"]}
    if request.explicit_route_id is not None and request.explicit_route_id not in route_by_id:
        raise ValueError(f"unknown explicit route: {request.explicit_route_id}")

    candidates: list[dict[str, Any]] = []
    for route in profile["routes"]:
        if request.problem_class not in route["problemClasses"]:
            continue
        if request.explicit_route_id is not None and route["routeId"] != request.explicit_route_id:
            continue
        provides = set(route["provides"])
        missing = sorted(set(request.required_features) - provides)
        availability = _availability(route, observations, caller_bound, request.problem_class)
        compatible = not missing
        ready = compatible and availability["ready"] is True
        candidates.append({
            "routeId": route["routeId"],
            "rank": route["rank"],
            "compatible": compatible,
            "ready": ready,
            "missingFeatures": missing,
            "preferredMatches": sorted(set(request.preferred_features) & provides),
            "preferredMatchCount": len(set(request.preferred_features) & provides),
            "availability": availability,
        })
    if not candidates:
        raise ValueError(f"no route declared for research problem class: {request.problem_class}")

    ready = [row for row in candidates if row["ready"]]
    ready.sort(key=lambda row: (-row["preferredMatchCount"], row["rank"], row["routeId"]))
    selected = ready[0] if ready else None
    if selected is None:
        compatible = [row for row in candidates if row["compatible"]]
        if not compatible:
            standing = "HOLD_NO_COMPATIBLE_ROUTE"
        elif any(row["availability"]["state"] == "unknown" for row in compatible):
            standing = "HOLD_CURRENTNESS_REQUIRED"
        else:
            standing = "HOLD_NO_READY_ROUTE"
        selected_route = None
    else:
        standing = "ROUTED"
        source = route_by_id[selected["routeId"]]
        selected_route = {
            "routeId": source["routeId"],
            "providerClass": source["providerClass"],
            "providerRef": source["providerRef"],
            "bindingAuthority": source["bindingAuthority"],
            "scientificSemanticAuthority": bool(source.get("scientificSemanticAuthority", source["providerClass"] == "skill" and False)),
            "provides": list(source["provides"]),
            "availability": selected["availability"],
            "invocation": dict(source["invocation"]),
            "verification": list(source["verification"]),
        }
        if "bindingRef" in selected["availability"]:
            selected_route["bindingRef"] = selected["availability"]["bindingRef"]
        if "providerBinding" in selected["availability"]:
            selected_route["providerBinding"] = selected["availability"]["providerBinding"]

    request_material = {
        "problemClass": request.problem_class,
        "requiredFeatures": list(request.required_features),
        "preferredFeatures": list(request.preferred_features),
        "explicitRouteId": request.explicit_route_id,
        "callerAvailable": sorted(caller_bound),
    }
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.research-capability-route-decision",
        "truthRole": "task-local-non-authoritative-route-projection",
        "profileId": profile["profileId"],
        "profileDigest": canonical_digest(profile),
        "requestDigest": canonical_digest(request_material),
        "observationDigest": canonical_digest(dict(observations)),
        "standing": standing,
        "problemClass": request.problem_class,
        "selectedRoute": selected_route,
        "candidates": candidates,
        "callerAvailable": sorted(caller_bound),
        "semanticSelector": "agent-or-caller-explicit-problem-class",
        "executionAuthority": "selected-owner-or-provider",
        "completionAuthority": "study-or-owning-domain",
        "authorizationEstablished": False,
        "executed": False,
        "domainCompletionEstablished": False,
        "nonClaims": [
            "Route discovery does not grant authority.",
            "Availability does not imply authorization or effect authority.",
            "Skill instructions are advisory and do not grant execution authority.",
            "Provider/tool/workflow success does not establish scientific or domain completion.",
            "No generic Agent fallback is implied by a HOLD.",
        ],
    }
    result["planDigest"] = canonical_digest(result)
    return result


def _read_observations(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, dict) for k, v in value.items()):
        raise ValueError("observation file must map authority keys to objects")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    plan = sub.add_parser("plan")
    plan.add_argument("--problem-class", required=True)
    plan.add_argument("--required-feature", action="append", default=[])
    plan.add_argument("--preferred-feature", action="append", default=[])
    plan.add_argument("--explicit-route-id")
    plan.add_argument("--observations", type=Path)
    plan.add_argument("--caller-available", action="append", default=[])
    args = parser.parse_args()
    profile = load_profile()
    if args.command == "list":
        print(json.dumps({"schemaVersion": 1, "kind": "ordivon.research-capability-route-list", "profileId": profile["profileId"], "problemClasses": profile["problemClasses"], "routes": profile["routes"]}, sort_keys=True))
        return 0
    decision = resolve(RouteRequest(problem_class=args.problem_class, required_features=tuple(args.required_feature), preferred_features=tuple(args.preferred_feature), explicit_route_id=args.explicit_route_id), observations=_read_observations(args.observations), caller_available=tuple(args.caller_available), profile=profile)
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["standing"] == "ROUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
