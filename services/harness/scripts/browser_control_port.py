#!/usr/bin/env python3
"""BrowserControlPort adapter contract and qualification projection.

Browser Router remains the route selector. This module only validates the stable BrowserControlPort
operation vocabulary and route-to-adapter bindings, then projects whether one explicit operation is
inside that adapter's independently qualified envelope. It never performs browser actions or grants
BrowserControl/ProviderEffect authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

SOURCE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = SOURCE_ROOT / "config/browser-control-port.json"
DEFAULT_ROUTES = SOURCE_ROOT / "config/browser-capability-routes.json"

ALLOWED_EFFECT_CLASSES = {"observation", "navigation", "interaction", "commit"}
ALLOWED_QUALIFICATION = {
    "QUALIFIED_READ_ONLY_BASELINE",
    "EXISTING_ROUTE_CONTRACT_NOT_F6_QUALIFIED",
    "NOT_MATERIALIZED",
}


def canonical_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    value = _read_json(path)
    if (
        value.get("schemaVersion") != 1
        or value.get("kind") != "ordivon.browser-control-port-contract"
    ):
        raise ValueError("browser control port contract identity mismatch")

    operations = value.get("operations")
    adapters = value.get("adapters")
    feature_map = value.get("routeFeatureOperationMap")
    if not isinstance(operations, list) or not operations:
        raise ValueError("browser control port requires operations")
    if not isinstance(adapters, list) or not adapters:
        raise ValueError("browser control port requires adapters")
    if not isinstance(feature_map, dict):
        raise ValueError("routeFeatureOperationMap must be an object")

    operation_ids: set[str] = set()
    normalized_ops = []
    for raw in operations:
        if not isinstance(raw, dict) or set(raw) != {"operationId", "effectClass"}:
            raise ValueError("invalid BrowserControlPort operation")
        operation = raw.get("operationId")
        effect_class = raw.get("effectClass")
        if (
            not isinstance(operation, str)
            or not operation
            or operation in operation_ids
            or effect_class not in ALLOWED_EFFECT_CLASSES
            or operation.lower().startswith("cdp.")
        ):
            raise ValueError(f"invalid BrowserControlPort operation: {operation!r}")
        operation_ids.add(operation)
        normalized_ops.append(dict(raw))

    for feature, operation in feature_map.items():
        if not isinstance(feature, str) or not feature or operation not in operation_ids:
            raise ValueError(f"invalid route feature operation mapping: {feature!r}")

    adapter_ids: set[str] = set()
    route_ids: set[str] = set()
    normalized_adapters = []
    for raw in adapters:
        if not isinstance(raw, dict):
            raise ValueError("adapter must be an object")
        required = {
            "adapterId",
            "transportFamily",
            "routeIds",
            "implementationSupports",
            "qualifiedOperations",
            "qualificationStanding",
            "currentnessOwner",
            "rawProtocolEscapesDomainApi",
            "evidence",
        }
        if set(raw) != required:
            raise ValueError(f"invalid adapter fields: {raw.get('adapterId')!r}")
        adapter_id = raw.get("adapterId")
        transport = raw.get("transportFamily")
        routes = raw.get("routeIds")
        supports = raw.get("implementationSupports")
        qualified = raw.get("qualifiedOperations")
        standing = raw.get("qualificationStanding")
        currentness = raw.get("currentnessOwner")
        evidence = raw.get("evidence")
        if (
            not isinstance(adapter_id, str)
            or not adapter_id
            or adapter_id in adapter_ids
            or not isinstance(transport, str)
            or not transport
            or not isinstance(routes, list)
            or any(not isinstance(x, str) or not x for x in routes)
            or len(set(routes)) != len(routes)
            or any(x in route_ids for x in routes)
            or not isinstance(supports, list)
            or any(x not in operation_ids for x in supports)
            or len(set(supports)) != len(supports)
            or not isinstance(qualified, list)
            or any(x not in supports for x in qualified)
            or len(set(qualified)) != len(qualified)
            or standing not in ALLOWED_QUALIFICATION
            or not isinstance(currentness, str)
            or not currentness
            or raw.get("rawProtocolEscapesDomainApi") is not False
            or not isinstance(evidence, list)
            or any(not isinstance(x, str) or not x for x in evidence)
        ):
            raise ValueError(f"invalid BrowserControlPort adapter: {adapter_id!r}")
        if standing == "QUALIFIED_READ_ONLY_BASELINE":
            effect_by_id = {item["operationId"]: item["effectClass"] for item in normalized_ops}
            if any(effect_by_id[x] != "observation" for x in qualified):
                raise ValueError("read-only baseline may qualify only observation operations")
        adapter_ids.add(adapter_id)
        route_ids.update(routes)
        normalized_adapters.append(dict(raw))

    return {
        "schemaVersion": 1,
        "kind": value["kind"],
        "operations": normalized_ops,
        "routeFeatureOperationMap": dict(feature_map),
        "adapters": normalized_adapters,
        "nonClaims": value.get("nonClaims", []),
        "contractDigest": canonical_digest(value),
    }


def load_browser_routes(path: Path = DEFAULT_ROUTES) -> dict[str, dict[str, Any]]:
    value = _read_json(path)
    routes = value.get("routes")
    if not isinstance(routes, list):
        raise ValueError("browser route policy requires routes")
    result = {}
    for raw in routes:
        if not isinstance(raw, dict):
            raise ValueError("browser route must be object")
        route_id = raw.get("routeId")
        if not isinstance(route_id, str) or not route_id or route_id in result:
            raise ValueError("invalid browser route id")
        result[route_id] = raw
    return result


def check_route_binding(
    route_id: str,
    *,
    operation: str,
    contract: Mapping[str, Any] | None = None,
    routes: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    contract = dict(contract or load_contract())
    routes = dict(routes or load_browser_routes())
    known_ops = {item["operationId"] for item in contract["operations"]}
    if operation not in known_ops:
        raise ValueError(f"unknown BrowserControlPort operation: {operation}")
    route = routes.get(route_id)
    if route is None:
        raise ValueError(f"unknown browser route: {route_id}")
    adapter_id = route.get("controlPortAdapter")
    if not isinstance(adapter_id, str) or not adapter_id:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.browser-control-port-binding",
            "standing": "HOLD_ROUTE_UNBOUND",
            "routeId": route_id,
            "operation": operation,
            "adapterId": None,
            "authorityGranted": False,
            "browserEffectAuthorized": False,
            "providerEffectAuthorized": False,
            "executionDispatched": False,
            "contractDigest": contract["contractDigest"],
        }
    adapter = next(
        (item for item in contract["adapters"] if item["adapterId"] == adapter_id),
        None,
    )
    if adapter is None or route_id not in adapter["routeIds"]:
        standing = "HOLD_ADAPTER_BINDING_INVALID"
        qualified = False
        supported = False
    else:
        supported = operation in adapter["implementationSupports"]
        qualified = operation in adapter["qualifiedOperations"]
        if not supported:
            standing = "HOLD_OPERATION_UNSUPPORTED"
        elif not qualified:
            standing = "HOLD_OPERATION_UNQUALIFIED"
        else:
            standing = "QUALIFIED_OPERATION"

    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-control-port-binding",
        "standing": standing,
        "routeId": route_id,
        "operation": operation,
        "adapterId": adapter_id,
        "transportFamily": adapter.get("transportFamily") if adapter else None,
        "implementationSupported": supported,
        "operationQualified": qualified,
        "qualificationStanding": adapter.get("qualificationStanding") if adapter else None,
        "authorityGranted": False,
        "browserEffectAuthorized": False,
        "providerEffectAuthorized": False,
        "executionDispatched": False,
        "contractDigest": contract["contractDigest"],
        "nonClaims": [
            "qualified-operation-does-not-grant-browser-control-authority",
            "qualified-operation-does-not-grant-provider-effect-authority",
            "adapter-transport-does-not-establish-cross-adapter-substitutability",
        ],
    }


def validate_route_feature_bindings(
    *,
    contract: Mapping[str, Any] | None = None,
    routes: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    contract = dict(contract or load_contract())
    routes = dict(routes or load_browser_routes())
    feature_map = contract["routeFeatureOperationMap"]
    adapters_by_id = {item["adapterId"]: item for item in contract["adapters"]}
    rows = []
    healthy = True
    for route_id, route in sorted(routes.items()):
        adapter_id = route.get("controlPortAdapter")
        if adapter_id is None:
            continue
        adapter = adapters_by_id.get(adapter_id)
        missing = []
        invalid_binding = adapter is None or route_id not in adapter.get("routeIds", [])
        if not invalid_binding:
            supported = set(adapter["implementationSupports"])
            for feature in route.get("provides", []):
                operation = feature_map.get(feature)
                if operation is not None and operation not in supported:
                    missing.append({"feature": feature, "operation": operation})
        row = {
            "routeId": route_id,
            "adapterId": adapter_id,
            "bindingValid": not invalid_binding,
            "missingImplementationOperations": missing,
        }
        if invalid_binding or missing:
            healthy = False
        rows.append(row)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-control-port-route-conformance",
        "healthy": healthy,
        "rows": rows,
        "contractDigest": contract["contractDigest"],
        "authorityGranted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--routes", type=Path, default=DEFAULT_ROUTES)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("catalog")
    sub.add_parser("validate-routes")
    check = sub.add_parser("check-route")
    check.add_argument("--route-id", required=True)
    check.add_argument("--operation", required=True)
    args = parser.parse_args()
    contract = load_contract(args.contract)
    if args.command == "catalog":
        value = contract
        rc = 0
    elif args.command == "validate-routes":
        value = validate_route_feature_bindings(
            contract=contract, routes=load_browser_routes(args.routes)
        )
        rc = 0 if value["healthy"] else 2
    else:
        value = check_route_binding(
            args.route_id,
            operation=args.operation,
            contract=contract,
            routes=load_browser_routes(args.routes),
        )
        rc = 0 if value["standing"] == "QUALIFIED_OPERATION" else 3
    print(json.dumps(value, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
