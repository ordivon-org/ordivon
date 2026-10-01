#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ordivon_security_v2.admission import canonical_digest
from ordivon_security_v2.consequence_binding import (
    compile_consequence_input,
    composition_gate_result,
    evaluate_bound_consequence,
)

OPA_IMAGE = (
    "docker.io/openpolicyagent/opa@"
    "sha256:9c5770a0023d56a11224b0514fec2e4e0247357db4392b955c1270fd49cb1f0f"
)


def opa_decision(policy_dir: Path, payload: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        input_path = root / "input.json"
        input_path.write_text(json.dumps(payload), encoding="utf-8")
        proc = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--user",
                "0",
                "-v",
                f"{policy_dir.resolve()}:/policies:ro",
                "-v",
                f"{root.resolve()}:/input:ro",
                OPA_IMAGE,
                "eval",
                "--format=json",
                "--data",
                "/policies/consequence_verification.rego",
                "--input",
                "/input/input.json",
                "data.ordivon.security.v2.consequence.decision",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    value = json.loads(proc.stdout)
    return value["result"][0]["expressions"][0]["value"]


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    policy_dir = repo / "platform/security/policies"
    out_dir = repo / "platform/security/evidence/acceptance"
    dw07_path = out_dir / "dw07-reversible-effect-r1-20261001.json"
    dw07_evidence = json.loads(dw07_path.read_text(encoding="utf-8"))
    dw07_result = dw07_evidence["normalCommit"]
    receipt = dw07_result["receipt"]
    if receipt is None:
        raise RuntimeError("DW07 normal acceptance receipt is absent")

    synthetic_manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:dw08:reversible-acceptance",
        "purpose": (
            "Qualification-only circuit for the same in-memory fixture subject used by the "
            "DW07 reversible acceptance. It does not discharge the historical DW06 circuit."
        ),
        "gateIds": ["gate:dw07-dw08-effect-receipt"],
    }
    manifest_digest = canonical_digest(synthetic_manifest)
    binding = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-consequence-verifier-binding-r1",
        "bindingRef": "verifier-binding:dw08:reversible-acceptance:configuration",
        "caseRef": "case:dw07:reversible-acceptance",
        "subjectRef": "fixture:in-memory-flag",
        "subjectSnapshotDigest": "sha256:" + "1" * 64,
        "protectionClaimRef": "protection:fixture-flag:on",
        "supportScope": "DW07->DW08 exact receipt/consequence-input seam only",
        "verifierClass": "configuration",
        "predicate": {
            "class": "configuration",
            "expectedConfigurationDigest": receipt["stateDigestAfterWrite"],
        },
        "compositionGate": {
            "circuitId": synthetic_manifest["circuitId"],
            "manifestDigest": manifest_digest,
            "gateId": "gate:dw07-dw08-effect-receipt",
            "verifierOwnerId": "security.dw08",
            "supportScope": "DW07->DW08 exact receipt/consequence-input seam only",
        },
    }

    observation = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-authoritative-observation-r1",
        "plane": "world-truth",
        "caseRef": binding["caseRef"],
        "subjectRef": binding["subjectRef"],
        "subjectSnapshotDigest": binding["subjectSnapshotDigest"],
        "requestId": dw07_result["requestId"],
        "requestDigest": dw07_result["requestDigest"],
        "stateDigest": receipt["stateDigestAfterWrite"],
        "ownerRef": "observer:dw08-independent-memory-fixture",
        "sourceRef": "evidence:dw08:independent-memory-observation",
        "sourceDigest": canonical_digest(
            {
                "fixture": "in-memory-flag",
                "value": "on",
                "requestId": dw07_result["requestId"],
                "requestDigest": dw07_result["requestDigest"],
            }
        ),
        "observedAt": "2026-10-01T15:25:00+08:00",
        "currentnessStanding": "POINT_IN_TIME_OBSERVED",
        "facts": {
            "configurationDigest": receipt["stateDigestAfterWrite"],
            "fixtureValue": "on",
        },
    }

    policy_input = compile_consequence_input(
        binding=binding,
        dw07_result=dw07_result,
        observation=observation,
    )
    decision = opa_decision(policy_dir, policy_input)
    result = evaluate_bound_consequence(
        binding=binding,
        dw07_result=dw07_result,
        observation=observation,
        consequence_decision=decision,
    )
    gate = composition_gate_result(binding=binding, verification_result=result)

    receipt_only_input = compile_consequence_input(
        binding=binding,
        dw07_result=dw07_result,
        observation=None,
    )
    receipt_only_decision = opa_decision(policy_dir, receipt_only_input)
    receipt_only_result = evaluate_bound_consequence(
        binding=binding,
        dw07_result=dw07_result,
        observation=None,
        consequence_decision=receipt_only_decision,
    )

    stale_observation = dict(observation)
    stale_observation["currentnessStanding"] = "HISTORICAL_NOT_CURRENT"
    stale_input = compile_consequence_input(
        binding=binding,
        dw07_result=dw07_result,
        observation=stale_observation,
    )
    stale_decision = opa_decision(policy_dir, stale_input)
    stale_result = evaluate_bound_consequence(
        binding=binding,
        dw07_result=dw07_result,
        observation=stale_observation,
        consequence_decision=stale_decision,
    )

    assert decision["standing"] == "VERIFIED_CONSEQUENCE"
    assert result["standing"] == "SATISFIED"
    assert result["verifiedProtectionEstablished"] is True
    assert result["compromiseAbsenceEstablished"] is False
    assert result["eradicationEstablished"] is False
    assert result["recoveryEstablished"] is False
    assert result["domainAcceptanceEstablished"] is False
    assert gate["standing"] == "SATISFIED"
    assert receipt_only_decision["standing"] == "EXECUTED_UNVERIFIED"
    assert receipt_only_result["standing"] == "UNKNOWN"
    assert receipt_only_result["verifiedProtectionEstablished"] is False
    assert stale_decision["standing"] == "VERIFIED_CONSEQUENCE"
    assert stale_result["standing"] == "UNKNOWN"
    assert stale_result["verifiedProtectionEstablished"] is False

    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dw08-consequence-verification-r1-acceptance",
        "observedAt": "2026-10-01T15:25:00+08:00",
        "workRef": "work:security:dwc-r21:dw08-consequence-verification:20261001",
        "standing": "DW08_CONSEQUENCE_BINDING_AND_HARMLESS_ACCEPTANCE_QUALIFIED",
        "baseRevision": "6549bca0a90676784bb9fe43e29c76b395782ba7",
        "opaImage": OPA_IMAGE,
        "implementation": {
            "module": "platform/security/src/ordivon_security_v2/consequence_binding.py",
            "tests": "platform/security/tests/test_consequence_binding.py",
            "acceptanceScript": "platform/security/scripts/run_dw08_consequence_acceptance.py",
            "policy": "platform/security/policies/consequence_verification.rego",
            "design": "platform/security/docs/DW08-CONSEQUENCE-VERIFICATION-R1.md",
        },
        "sourceEvidence": {
            "dw07AcceptancePath": str(dw07_path.relative_to(repo)),
            "dw07AcceptanceDigest": dw07_evidence["evidenceDigest"],
            "dw07RequestId": dw07_result["requestId"],
            "dw07RequestDigest": dw07_result["requestDigest"],
            "providerReceiptWorldEffectVerified": receipt["worldEffectVerified"],
        },
        "binding": binding,
        "authoritativeObservation": observation,
        "consequencePolicyDecision": decision,
        "verificationResult": result,
        "compositionGateResult": gate,
        "negativeControls": {
            "receiptOnly": {
                "policyStanding": receipt_only_decision["standing"],
                "verificationStanding": receipt_only_result["standing"],
                "verifiedProtectionEstablished": receipt_only_result[
                    "verifiedProtectionEstablished"
                ],
            },
            "staleObservation": {
                "policyStanding": stale_decision["standing"],
                "verificationStanding": stale_result["standing"],
                "verifiedProtectionEstablished": stale_result[
                    "verifiedProtectionEstablished"
                ],
            },
        },
        "supportedVerifierClasses": [
            "version",
            "configuration",
            "exposure",
            "attack-negative",
        ],
        "invalidationKeys": result["invalidationKeys"],
        "nonClaims": [
            "The authoritative observation is an independent read of the harmless in-memory fixture, not a production system observation.",
            "The synthetic qualification circuit exists only to keep the DW07 acceptance case and DW08 gate case identical; it does not discharge the historical DW06 ProxyLogon circuit.",
            "A SATISFIED DW08 result establishes only the explicit bounded protection predicate in supportScope.",
            "Verified protection does not establish compromise absence, eradication, recovery, or domain acceptance.",
            "No OS, network, Runtime service, Security configuration or external system is mutated by this acceptance.",
        ],
    }
    evidence["evidenceDigest"] = canonical_digest(evidence)
    output = out_dir / "dw08-consequence-verification-r1-20261001.json"
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "standing": evidence["standing"],
                "evidenceDigest": evidence["evidenceDigest"],
                "policyStanding": decision["standing"],
                "verificationStanding": result["standing"],
                "gateStanding": gate["standing"],
                "receiptOnlyStanding": receipt_only_result["standing"],
                "staleStanding": stale_result["standing"],
                "verifiedProtectionEstablished": result[
                    "verifiedProtectionEstablished"
                ],
                "compromiseAbsenceEstablished": result[
                    "compromiseAbsenceEstablished"
                ],
                "recoveryEstablished": result["recoveryEstablished"],
                "output": str(output.relative_to(repo)),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
