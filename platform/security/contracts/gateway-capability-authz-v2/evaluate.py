#!/usr/bin/env python3
from __future__ import annotations

import base64
import importlib.util
import json
import sys
import unicodedata
from pathlib import Path
from types import ModuleType
from typing import Any

SECURITY_ROOT = Path(__file__).resolve().parents[2]
AGENT_ADMISSION = SECURITY_ROOT / "contracts" / "agent-admission-v1" / "evaluate.py"
QUALIFIED_CAPABILITY = "artifact.runtime"
RESOURCE_TYPE = "ordivon.runtime.artifact"
RESOURCE_CONTRACT = "ordivon.runtime-artifact-resource-key.v1"
_RUNTIME_OWNERS = frozenset({"runtime.linux", "runtime.windows"})


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


def _base64url_text(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _artifact_resource_id(operation_ref: str, artifact_id: str) -> str:
    return (
        "runtime-artifact:v1:" + _base64url_text(operation_ref) + "." + _base64url_text(artifact_id)
    )


def _parse_runtime_operation_ref(value: str) -> tuple[str, str]:
    prefix = "ordivon-exec:v1:"
    if not value.startswith(prefix):
        raise GatewayCapabilityAuthzError("requestedResource operationRef is invalid")
    try:
        owner_id, job_id = value[len(prefix) :].rsplit(":", 1)
    except ValueError as exc:
        raise GatewayCapabilityAuthzError("requestedResource operationRef is invalid") from exc
    if owner_id not in _RUNTIME_OWNERS or not job_id:
        raise GatewayCapabilityAuthzError("requestedResource owner is not a qualified Runtime")
    return owner_id, job_id


def _validate_artifact_id(value: Any) -> str:
    artifact_id = _text(value, "requestedResource artifactId")
    if (
        len(artifact_id.encode("utf-8")) > 256
        or "\x00" in artifact_id
        or any(unicodedata.category(ch) == "Cc" for ch in artifact_id)
    ):
        raise GatewayCapabilityAuthzError("requestedResource artifactId is invalid")
    return artifact_id


def _validated_resource(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"type", "id", "properties"}:
        raise GatewayCapabilityAuthzError(
            "requestedResource must contain type, id, and properties only"
        )
    if value.get("type") != RESOURCE_TYPE:
        raise GatewayCapabilityAuthzError("requestedResource type is not qualified")
    properties = value.get("properties")
    if not isinstance(properties, dict) or set(properties) != {
        "identityContract",
        "operationRef",
        "ownerId",
        "jobId",
        "artifactId",
    }:
        raise GatewayCapabilityAuthzError("requestedResource properties are invalid")
    if properties.get("identityContract") != RESOURCE_CONTRACT:
        raise GatewayCapabilityAuthzError("requestedResource identity contract is invalid")
    operation_ref = _text(properties.get("operationRef"), "requestedResource operationRef")
    owner_id, job_id = _parse_runtime_operation_ref(operation_ref)
    if properties.get("ownerId") != owner_id or properties.get("jobId") != job_id:
        raise GatewayCapabilityAuthzError(
            "requestedResource owner/job properties do not match operationRef"
        )
    artifact_id = _validate_artifact_id(properties.get("artifactId"))
    expected_id = _artifact_resource_id(operation_ref, artifact_id)
    if value.get("id") != expected_id:
        raise GatewayCapabilityAuthzError("requestedResource id does not match its coordinates")
    return {
        "type": RESOURCE_TYPE,
        "id": expected_id,
        "properties": dict(properties),
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    if set(payload) != {
        "schemaVersion",
        "kind",
        "verifiedIngress",
        "requestedCapability",
        "requestedResource",
        "agentAdmission",
    }:
        raise GatewayCapabilityAuthzError("Gateway capability AuthZ input has unexpected fields")
    if payload["schemaVersion"] != 2 or payload["kind"] != (
        "ordivon.security.gateway-capability-authz-request"
    ):
        raise GatewayCapabilityAuthzError("Gateway capability AuthZ version or kind is invalid")

    ingress = payload["verifiedIngress"]
    admission = payload["agentAdmission"]
    if not isinstance(ingress, dict) or set(ingress) != {"principalId", "issuer"}:
        raise GatewayCapabilityAuthzError(
            "verifiedIngress must contain principalId and issuer only"
        )
    if not isinstance(admission, dict):
        raise GatewayCapabilityAuthzError("agentAdmission must be an object")

    principal_id = _text(ingress["principalId"], "verified ingress principalId")
    issuer = _text(ingress["issuer"], "verified ingress issuer")
    requested_capability = _text(payload["requestedCapability"], "requestedCapability")
    requested_resource = _validated_resource(payload["requestedResource"])

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
    if effect.get("resource") != requested_resource["id"]:
        raise GatewayCapabilityAuthzError(
            "requested resource does not match Agent Admission effect resource"
        )

    chain = _AGENT_ADMISSION.evaluate(admission)
    agent = chain.get("agent")
    if not isinstance(agent, dict):
        raise RuntimeError("Agent Admission contract omitted agent decision")

    return {
        "schemaVersion": 2,
        "kind": "ordivon.security.gateway-capability-authz",
        "principalId": principal_id,
        "issuer": issuer,
        "requestedCapability": requested_capability,
        "requestedResource": requested_resource,
        "qualificationTarget": (
            requested_capability == QUALIFIED_CAPABILITY
            and requested_resource["type"] == RESOURCE_TYPE
        ),
        "outcome": agent.get("outcome"),
        "reason": agent.get("reason"),
        "authorityProjection": agent.get("authorityProjection"),
        "effectAdmission": chain.get("effect"),
        "claimBoundary": (
            "Security authorization only. This decision does not prove Gateway routing, "
            "Runtime execution, Artifact bytes, external effect occurrence, or domain success."
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
                "schemaVersion": 2,
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
