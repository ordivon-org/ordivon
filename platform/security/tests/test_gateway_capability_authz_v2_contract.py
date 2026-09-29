from __future__ import annotations

import base64
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "gateway-capability-authz-v2" / "evaluate.py"
FIXTURE = ROOT / "fixtures" / "agent-admission" / "v0-allow.json"

SPEC = importlib.util.spec_from_file_location("gateway_capability_authz_v2", CONTRACT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _b64(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def _resource(
    operation_ref: str = "ordivon-exec:v1:runtime.linux:job-1",
    artifact_id: str = "attempt-1.stdout",
) -> dict[str, object]:
    owner_id, job_id = operation_ref.removeprefix("ordivon-exec:v1:").rsplit(":", 1)
    return {
        "type": "ordivon.runtime.artifact",
        "id": f"runtime-artifact:v1:{_b64(operation_ref)}.{_b64(artifact_id)}",
        "properties": {
            "identityContract": "ordivon.runtime-artifact-resource-key.v1",
            "operationRef": operation_ref,
            "ownerId": owner_id,
            "jobId": job_id,
            "artifactId": artifact_id,
        },
    }


def _payload() -> dict[str, object]:
    admission = json.loads(FIXTURE.read_text(encoding="utf-8"))
    principal_id = admission["principal"]["principalId"]
    resource = _resource()
    admission["grant"]["audience"] = "ordivon.gateway"
    admission["grant"]["allowedActions"] = ["artifact.runtime"]
    admission["grant"]["resourcePrefixes"] = ["runtime-artifact:v1:"]
    admission["effect"]["action"] = "artifact.runtime"
    admission["effect"]["resource"] = resource["id"]
    admission["effect"]["audience"] = "ordivon.gateway"
    admission["effect"]["riskClass"] = "R1"
    admission["grant"]["maxRiskClass"] = "R2"
    admission["grant"]["stepUpAtOrAbove"] = "R4"
    return {
        "schemaVersion": 2,
        "kind": "ordivon.security.gateway-capability-authz-request",
        "verifiedIngress": {
            "principalId": principal_id,
            "issuer": "https://example.cloudflareaccess.com",
        },
        "requestedCapability": "artifact.runtime",
        "requestedResource": resource,
        "agentAdmission": admission,
    }


class GatewayCapabilityAuthzV2ContractTests(unittest.TestCase):
    def test_exact_artifact_resource_is_bound_through_security_decision(self) -> None:
        payload = _payload()
        result = MODULE.evaluate(payload)
        self.assertEqual(result["schemaVersion"], 2)
        self.assertEqual(result["requestedResource"], payload["requestedResource"])
        self.assertEqual(result["outcome"], "ALLOW")
        self.assertIs(result["effectAdmission"]["admitted"], True)

    def test_effect_for_different_artifact_is_rejected_before_policy(self) -> None:
        payload = _payload()
        payload["agentAdmission"]["effect"]["resource"] = _resource(artifact_id="other")["id"]
        with self.assertRaisesRegex(
            MODULE.GatewayCapabilityAuthzError, "requested resource does not match"
        ):
            MODULE.evaluate(payload)

    def test_resource_id_is_reconstructed_not_trusted(self) -> None:
        payload = _payload()
        payload["requestedResource"]["id"] = "runtime-artifact:v1:forged"
        with self.assertRaisesRegex(MODULE.GatewayCapabilityAuthzError, "id does not match"):
            MODULE.evaluate(payload)

    def test_operation_ref_must_bind_owner_and_job_properties(self) -> None:
        payload = _payload()
        payload["requestedResource"]["properties"]["jobId"] = "job-other"
        with self.assertRaisesRegex(
            MODULE.GatewayCapabilityAuthzError, "owner/job properties do not match"
        ):
            MODULE.evaluate(payload)

    def test_external_pull_artifact_is_not_qualified_as_runtime_artifact(self) -> None:
        payload = _payload()
        payload["requestedResource"] = _resource(
            operation_ref="ordivon-exec:v1:external.pull:operation-1"
        )
        payload["agentAdmission"]["effect"]["resource"] = payload["requestedResource"]["id"]
        with self.assertRaisesRegex(MODULE.GatewayCapabilityAuthzError, "not a qualified Runtime"):
            MODULE.evaluate(payload)

    def test_principal_and_capability_binding_remain_fail_closed(self) -> None:
        payload = _payload()
        payload["verifiedIngress"]["principalId"] = "principal:forged"
        with self.assertRaisesRegex(MODULE.GatewayCapabilityAuthzError, "Principal does not match"):
            MODULE.evaluate(payload)

        payload = _payload()
        payload["requestedCapability"] = "execution.linux"
        with self.assertRaisesRegex(MODULE.GatewayCapabilityAuthzError, "effect action"):
            MODULE.evaluate(payload)

    def test_security_deny_is_preserved(self) -> None:
        payload = _payload()
        payload["agentAdmission"]["grant"]["allowedActions"] = ["execution.linux"]
        result = MODULE.evaluate(payload)
        self.assertEqual(result["outcome"], "DENY")
        self.assertIsNone(result["authorityProjection"])
        self.assertIsNone(result["effectAdmission"])


if __name__ == "__main__":
    unittest.main()
