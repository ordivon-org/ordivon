from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "gateway-capability-authz-v1" / "evaluate.py"
FIXTURE = ROOT / "fixtures" / "agent-admission" / "v0-allow.json"

SPEC = importlib.util.spec_from_file_location("gateway_capability_authz_v1", CONTRACT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _payload() -> dict[str, object]:
    admission = json.loads(FIXTURE.read_text(encoding="utf-8"))
    principal_id = admission["principal"]["principalId"]
    admission["grant"]["audience"] = "ordivon.gateway"
    admission["grant"]["allowedActions"] = ["artifact.runtime"]
    admission["grant"]["resourcePrefixes"] = ["runtime-artifact:"]
    admission["effect"]["action"] = "artifact.runtime"
    admission["effect"]["resource"] = "runtime-artifact:artifact-test"
    admission["effect"]["audience"] = "ordivon.gateway"
    admission["effect"]["riskClass"] = "R1"
    admission["grant"]["maxRiskClass"] = "R2"
    admission["grant"]["stepUpAtOrAbove"] = "R4"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.security.gateway-capability-authz-request",
        "verifiedIngress": {
            "principalId": principal_id,
            "issuer": "https://example.cloudflareaccess.com",
        },
        "requestedCapability": "artifact.runtime",
        "agentAdmission": admission,
    }


class GatewayCapabilityAuthzContractTests(unittest.TestCase):
    def test_qualified_artifact_capability_reuses_security_admission(self) -> None:
        result = MODULE.evaluate(_payload())
        self.assertEqual(result["kind"], "ordivon.security.gateway-capability-authz")
        self.assertEqual(result["requestedCapability"], "artifact.runtime")
        self.assertIs(result["qualificationTarget"], True)
        self.assertEqual(result["outcome"], "ALLOW")
        self.assertEqual(result["reason"], "admitted")
        self.assertEqual(result["authorityProjection"]["capability"], "artifact.runtime")
        self.assertIs(result["effectAdmission"]["admitted"], True)
        self.assertIn("does not prove Gateway routing", result["claimBoundary"])

    def test_verified_ingress_principal_cannot_be_replaced_by_payload(self) -> None:
        payload = _payload()
        payload["verifiedIngress"]["principalId"] = "principal:forged"
        with self.assertRaisesRegex(
            MODULE.GatewayCapabilityAuthzError,
            "does not match Agent Admission Principal",
        ):
            MODULE.evaluate(payload)

    def test_requested_capability_must_equal_policy_effect_action(self) -> None:
        payload = _payload()
        payload["requestedCapability"] = "execution.linux"
        with self.assertRaisesRegex(
            MODULE.GatewayCapabilityAuthzError,
            "does not match Agent Admission effect action",
        ):
            MODULE.evaluate(payload)

    def test_security_deny_is_preserved_and_not_upgraded(self) -> None:
        payload = _payload()
        payload["agentAdmission"]["grant"]["allowedActions"] = ["execution.linux"]
        result = MODULE.evaluate(payload)
        self.assertEqual(result["outcome"], "DENY")
        self.assertEqual(result["reason"], "action-not-granted")
        self.assertIsNone(result["authorityProjection"])
        self.assertIsNone(result["effectAdmission"])

    def test_unqualified_capability_is_explicit_not_silently_generalized(self) -> None:
        payload = _payload()
        payload["requestedCapability"] = "execution.linux"
        payload["agentAdmission"]["effect"]["action"] = "execution.linux"
        payload["agentAdmission"]["grant"]["allowedActions"] = ["execution.linux"]
        result = MODULE.evaluate(payload)
        self.assertEqual(result["outcome"], "ALLOW")
        self.assertIs(result["qualificationTarget"], False)


if __name__ == "__main__":
    unittest.main()
