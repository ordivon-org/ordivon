#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

SECURITY_ROOT = Path(__file__).resolve().parents[2]
AGENT_ADMISSION = SECURITY_ROOT / "contracts" / "agent-admission-v1" / "evaluate.py"
QUALIFIED_CAPABILITY = "artifact.runtime"


class GatewayCapabilityAuthzError(ValueError):
    pass


def _load_agent_admission() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "ordivon_security_agent_admission_v1", AGENT_ADMISSION
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Agent Admission contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_AGENT_ADMISSION = _load_agent_admission()


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GatewayCapabilityAuthzError(f"{label} must be a non-empty string")
    return value.strip()


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    if set(payload) != {
        "schemaVersion",
        "kind",
        "verifiedIngress",
        "requestedCapability",
        "agentAdmission",
    }:
        raise GatewayCapabilityAuthzError("Gateway capability AuthZ input has unexpected fields")
    if payload["schemaVersion"] != 1 or payload["kind"] != (
        "ordivon.security.gateway-capability-authz-request"
    ):
        raise GatewayCapabilityAuthzError("Gateway capability AuthZ version or kind is invalid")

    ingress = payload["verifiedIngress"]
    admission = payload["agentAdmission"]
    if not isinstance(ingress, dict) or set(ingress) != {"principalId", "issuer"}:
        raise GatewayCapabilityAuthzError("verifiedIngress must contain principalId and issuer only")
    if not isinstance(admission, dict):
        raise GatewayCapabilityAuthzError("agentAdmission must be an object")

    principal_id = _text(ingress["principalId"], "verified ingress principalId")
    issuer = _text(ingress["issuer"], "verified ingress issuer")
    requested_capability = _text(payload["requestedCapability"], "requestedCapability")

    principal = admission.get("principal")
    effect = admission.get("effect")
    if not isinstance(principal, dict) or not isinstance(effect, dict):
        raise GatewayCapabilityAuthzError(
            "agentAdmission must contain normalized principal and effect objects"
        )
    if principal.get("principalId") != principal_id:
        raise GatewayCapabilityAuthzError(
            "verified ingress Principal does not match Agent Admission Principal"
        )
    if effect.get("action") != requested_capability:
        raise GatewayCapabilityAuthzError(
            "requested capability does not match Agent Admission effect action"
        )

    chain = _AGENT_ADMISSION.evaluate(admission)
    agent = chain.get("agent")
    if not isinstance(agent, dict):
        raise RuntimeError("Agent Admission contract omitted agent decision")

    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.gateway-capability-authz",
        "principalId": principal_id,
        "issuer": issuer,
        "requestedCapability": requested_capability,
        "qualificationTarget": requested_capability == QUALIFIED_CAPABILITY,
        "outcome": agent.get("outcome"),
        "reason": agent.get("reason"),
        "authorityProjection": agent.get("authorityProjection"),
        "effectAdmission": chain.get("effect"),
        "claimBoundary": (
            "Security authorization only. This decision does not prove Gateway routing, "
            "Runtime execution, provider acceptance, external effect occurrence, or domain success."
        ),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise GatewayCapabilityAuthzError("input must be a JSON object")
        json.dump(evaluate(payload), sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")
        return 0
    except Exception as exc:
        json.dump(
            {
                "schemaVersion": 1,
                "kind": "ordivon.security.gateway-capability-authz-error",
                "error": type(exc).__name__,
                "detail": str(exc),
            },
            sys.stderr,
            separators=(",", ":"),
        )
        sys.stderr.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
