"""Deterministic non-authoritative Browser/Network plan binding.

This module composes exact already-selected Browser and Network route references. It does not
select routes, inspect owner-native plans, grant authority, mutate browser/network state, dispatch
execution, or establish provider/domain success.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .cognitive_circuit_r1 import CircuitContractError, canonical_digest

ROOT = Path(__file__).resolve().parent
BINDING_SCHEMA = ROOT / "schemas" / "browser-network-binding-v1.schema.json"


class BrowserNetworkBindingError(CircuitContractError):
    """Machine-classified composition error without moving owner semantics."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _schema() -> dict[str, Any]:
    value = json.loads(BINDING_SCHEMA.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BrowserNetworkBindingError(
            "INVALID_BINDING_SCHEMA", "browser/network binding schema root must be an object"
        )
    return value


def _validate_schema(value: dict[str, Any]) -> None:
    validator = Draft202012Validator(_schema())
    errors = sorted(validator.iter_errors(value), key=lambda item: list(item.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise BrowserNetworkBindingError(
            "INVALID_BINDING",
            f"browser/network binding schema violation at {location}: {first.message}",
        )


def _copy_ref(value: dict[str, str], label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"id", "digest"}:
        raise BrowserNetworkBindingError(
            "INVALID_PLAN_REF", f"{label} must contain exactly id and digest"
        )
    identifier = value.get("id")
    digest = value.get("digest")
    if not isinstance(identifier, str) or not identifier or identifier != identifier.strip():
        raise BrowserNetworkBindingError("INVALID_PLAN_REF", f"{label}.id must be trimmed text")
    if not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:"):
        raise BrowserNetworkBindingError("INVALID_PLAN_REF", f"{label}.digest must be sha256")
    return {"id": identifier, "digest": digest}


def _copy_browser_route(value: dict[str, Any]) -> dict[str, str]:
    required = {"routeId", "executor", "substrate", "providerFlow"}
    if not isinstance(value, dict) or set(value) != required:
        raise BrowserNetworkBindingError(
            "INVALID_BROWSER_ROUTE", "browser route summary must contain exact stable route fields"
        )
    result: dict[str, str] = {}
    for name in sorted(required):
        item = value.get(name)
        if not isinstance(item, str) or not item or item != item.strip():
            raise BrowserNetworkBindingError(
                "INVALID_BROWSER_ROUTE", f"browserRoute.{name} must be trimmed text"
            )
        result[name] = item
    return {name: result[name] for name in ("routeId", "executor", "substrate", "providerFlow")}


def _copy_network_route(value: dict[str, Any]) -> dict[str, Any]:
    required = {"routeId", "providerProfileId", "provides", "readinessStanding"}
    if not isinstance(value, dict) or set(value) != required:
        raise BrowserNetworkBindingError(
            "INVALID_NETWORK_ROUTE", "network route summary must contain exact stable route fields"
        )
    route_id = value.get("routeId")
    provider = value.get("providerProfileId")
    provides = value.get("provides")
    standing = value.get("readinessStanding")
    if not isinstance(route_id, str) or not route_id or route_id != route_id.strip():
        raise BrowserNetworkBindingError(
            "INVALID_NETWORK_ROUTE", "networkRoute.routeId must be trimmed text"
        )
    if provider is not None and (
        not isinstance(provider, str) or not provider or provider != provider.strip()
    ):
        raise BrowserNetworkBindingError(
            "INVALID_NETWORK_ROUTE", "networkRoute.providerProfileId must be null or trimmed text"
        )
    if (
        not isinstance(provides, (list, tuple))
        or not provides
        or any(not isinstance(item, str) or not item or item != item.strip() for item in provides)
        or len(set(provides)) != len(provides)
    ):
        raise BrowserNetworkBindingError(
            "INVALID_NETWORK_ROUTE", "networkRoute.provides must be unique trimmed strings"
        )
    if standing != "READY":
        raise BrowserNetworkBindingError(
            "NETWORK_ROUTE_NOT_READY", "only a current READY network route may be bound"
        )
    return {
        "routeId": route_id,
        "providerProfileId": provider,
        "provides": sorted(provides),
        "readinessStanding": standing,
    }


def compile_browser_network_binding(
    *,
    browser_plan_ref: dict[str, str],
    network_plan_ref: dict[str, str],
    browser_route: dict[str, Any],
    network_route: dict[str, Any],
    required_network_features: tuple[str, ...] = (),
    unresolved_inputs: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Bind exact caller-selected routes while preserving explicit network requirements."""

    browser = _copy_browser_route(browser_route)
    network = _copy_network_route(network_route)

    required = sorted(set(required_network_features))
    if any(not isinstance(item, str) or not item or item != item.strip() for item in required):
        raise BrowserNetworkBindingError(
            "INVALID_NETWORK_REQUIREMENT", "required network features must be trimmed strings"
        )

    unresolved = sorted(set(unresolved_inputs))
    if any(not isinstance(item, str) or not item or item != item.strip() for item in unresolved):
        raise BrowserNetworkBindingError(
            "INVALID_UNRESOLVED_INPUT", "unresolved inputs must be trimmed strings"
        )

    missing = sorted(set(required) - set(network["provides"]))
    projection: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-network-binding",
        "truthRole": "task-local-non-authoritative-browser-network-binding-projection",
        "browserPlanRef": _copy_ref(browser_plan_ref, "browser_plan_ref"),
        "networkPlanRef": _copy_ref(network_plan_ref, "network_plan_ref"),
        "browserRoute": browser,
        "networkRoute": network,
        "requiredNetworkFeatures": required,
        "missingNetworkFeatures": missing,
        "unresolvedInputs": unresolved,
        "readyForExecution": not missing and not unresolved,
        "authorityGranted": False,
        "browserEffectAuthorized": False,
        "providerEffectAuthorized": False,
        "executionDispatched": False,
        "claimBoundary": (
            "This projection binds exact already-selected Browser and Network routes and checks "
            "only that explicit required network features are preserved by the selected Network "
            "route. It does not inspect owner-native plan semantics, select or rerank routes, "
            "grant Browser/Network/provider authority, mutate state, dispatch execution, or "
            "establish website/provider/domain success."
        ),
    }
    projection["bindingDigest"] = canonical_digest(projection)
    validate_browser_network_binding(projection)
    return projection


def validate_browser_network_binding(value: dict[str, Any]) -> None:
    """Validate schema, digest, requirement preservation and readiness invariants."""

    _validate_schema(value)

    expected_missing = sorted(
        set(value["requiredNetworkFeatures"]) - set(value["networkRoute"]["provides"])
    )
    if value["missingNetworkFeatures"] != expected_missing:
        raise BrowserNetworkBindingError(
            "MISSING_FEATURE_MISMATCH",
            "missingNetworkFeatures must exactly equal required minus provided features",
        )

    expected_ready = not expected_missing and not value["unresolvedInputs"]
    if value["readyForExecution"] is not expected_ready:
        raise BrowserNetworkBindingError(
            "READINESS_MISMATCH",
            "readyForExecution must equal feature preservation plus resolved inputs",
        )

    embedded = value["bindingDigest"]
    base = dict(value)
    del base["bindingDigest"]
    if canonical_digest(base) != embedded:
        raise BrowserNetworkBindingError(
            "BINDING_DIGEST_MISMATCH", "browser/network binding digest mismatch"
        )


def require_ready_browser_network_binding(value: dict[str, Any]) -> None:
    """Fail closed before any owner-specific lowering or execution."""

    validate_browser_network_binding(value)
    if not value["readyForExecution"]:
        reasons = list(value["unresolvedInputs"]) + [
            f"missing-network-feature:{item}" for item in value["missingNetworkFeatures"]
        ]
        raise BrowserNetworkBindingError(
            "BINDING_NOT_READY", "browser/network binding is not ready: " + ", ".join(reasons)
        )


__all__ = [
    "BrowserNetworkBindingError",
    "compile_browser_network_binding",
    "require_ready_browser_network_binding",
    "validate_browser_network_binding",
]
