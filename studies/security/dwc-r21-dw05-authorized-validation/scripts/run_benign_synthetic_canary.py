#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SECURITY_SRC = ROOT / "platform/security/src"
R4 = ROOT / "studies/security/ai-redteam-foundry-r4"
R5 = ROOT / "studies/security/ai-redteam-foundry-r5"
R6 = ROOT / "studies/security/ai-redteam-foundry-r6"
R7 = ROOT / "studies/security/ai-redteam-foundry-r7"
DW05_ROOT = Path(__file__).resolve().parents[1]
for path in (SECURITY_SRC, R4, R5, R6, R7, DW05_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ordivon_security_v2.attack_coverage import project_attack_coverage  # noqa: E402
from ordivon_security_v2.subject_exposure import build_subject_exposure_snapshot  # noqa: E402
from ordivon_security_v2.threat_applicability import fuse_threat_applicability  # noqa: E402
from foundry_r4 import (  # noqa: E402
    ExperimentEnvironmentSpec,
    IsolationVector,
    ResourceBudget,
    SandboxProviderBinding,
    admit_environment,
)
from foundry_r5 import (  # noqa: E402
    InMemorySyntheticWorld,
    SyntheticIdentity,
    SyntheticService,
    SyntheticWorldSpec,
)
from foundry_r6 import EffectAttempt, ReferenceEffectProxy  # noqa: E402
from foundry_r7 import SyntheticWorldObserver, reconcile_receipt  # noqa: E402
from dwc_dw05.validation_binding import (  # noqa: E402
    compile_validation_binding,
    project_validation_evidence,
)


D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64


def main() -> int:
    subject = build_subject_exposure_snapshot(
        case_ref="case:dw05:benign-synthetic-canary",
        epoch_ref="epoch:dw05:benign-synthetic-canary",
        subject_ref="synthetic-subject:example.test",
        identity_observations=[
            {
                "id": "product",
                "ownerId": "synthetic-fixture-owner",
                "sourceRef": "fixture:dw05:canary",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T14:00:00+08:00",
                "evidenceRefs": ["fixture:dw05:subject"],
                "dimension": "product",
                "identityRef": {"scheme": "synthetic-service", "value": "example.test"},
            }
        ],
        exposure_observations=[
            {
                "id": "http",
                "ownerId": "synthetic-fixture-owner",
                "sourceRef": "fixture:dw05:canary",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T14:00:00+08:00",
                "evidenceRefs": ["fixture:dw05:exposure"],
                "surfaceId": "synthetic-http",
                "endpointRef": "https://target.example.test",
                "originScope": "synthetic-world",
                "transport": "https",
                "reachability": "REACHABLE",
            }
        ],
        required_identity_dimensions=["product"],
        expected_exposure_surfaces=["synthetic-http"],
        non_claims=["closed-world synthetic target only"],
    )
    binding = {
        "subjectRef": subject["subjectRef"],
        "snapshotDigest": subject["snapshotDigest"],
        "evidenceRef": subject["evidenceRef"],
    }
    applicability = fuse_threat_applicability(
        subject=subject,
        vulnerability_ref="SYNTH-DW05-CANARY",
        evidence=[
            {
                "evidenceRef": "fixture:dw05:affected",
                "sourceKind": "local-observation",
                "providerNativeRef": "fixture://dw05/affected",
                "artifactDigest": D1,
                "vulnerabilityRef": "SYNTH-DW05-CANARY",
                "admission": "ADMITTED",
                "currentness": "CURRENT",
                "subjectBinding": binding,
                "projectedApplicability": "AFFECTED",
            }
        ],
    )
    flow = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dwc-attack-flow-reference",
        "flowRef": "attack-flow:dw05:benign-canary",
        "sourceRef": "fixture:dw05:canary",
        "sourceDigest": D2,
        "attackFlowVersion": "4.0",
        "subjectBinding": {
            "caseRef": subject["caseRef"],
            "epochRef": subject["epochRef"],
            "subjectRef": subject["subjectRef"],
            "snapshotDigest": subject["snapshotDigest"],
            "evidenceRef": subject["evidenceRef"],
        },
        "actions": [
            {
                "actionRef": "canary-action",
                "techniqueRef": "synthetic:benign-canary",
                "name": "Benign closed-world validation canary",
                "sourceRefs": ["fixture:dw05:canary"],
                "evidenceRefs": ["fixture:dw05:flow"],
            }
        ],
        "edges": [],
        "entryActionRefs": ["canary-action"],
        "objectiveActionRefs": ["canary-action"],
    }
    coverage = project_attack_coverage(
        subject=subject,
        applicability=applicability,
        flow=flow,
        controls=[
            {
                "controlRef": "control:dw05:canary",
                "ownerRef": "owner:synthetic-control",
                "mappedActionRefs": ["canary-action"],
                "attackMitigationRefs": ["synthetic:control-reference"],
                "d3fendRefs": [],
                "detectionStrategyRefs": [],
                "mappingEvidenceRefs": ["fixture:dw05:mapping"],
                "implementationStanding": "IMPLEMENTED",
                "implementationEvidenceRefs": ["fixture:dw05:implementation"],
                "observationStanding": "OBSERVED",
                "observationEvidenceRefs": ["fixture:dw05:implementation-observed"],
                "effectivenessStanding": "UNKNOWN",
                "effectivenessEvidenceRefs": [],
            }
        ],
    )
    assert coverage["authorizedValidationCandidateControlRefs"] == ["control:dw05:canary"]

    world_spec = SyntheticWorldSpec(
        world_id="world:dw05:benign-canary",
        identities=(SyntheticIdentity("agent:dw05:canary"),),
        services=(SyntheticService("service:http:canary", "http"),),
        resources=(),
        secrets=(),
    )
    world = InMemorySyntheticWorld(world_spec)
    observer = SyntheticWorldObserver()

    environment = ExperimentEnvironmentSpec(
        environment_id="environment:dw05:benign-canary",
        threat_class="synthetic_agent",
        base_image_digest=D2,
        synthetic_world_digest=world_spec.digest,
        tool_surface_digest=D3,
        observer_spec_digest=D4,
        isolation=IsolationVector(
            process="separate_process_tree",
            kernel="shared",
            filesystem="synthetic",
            network="simulated_internet",
            credentials="synthetic_only",
            devices="none",
            external_effects="synthetic_only",
            lifecycle="resettable",
            observer="independent",
        ),
        budget=ResourceBudget(
            max_wall_seconds=30,
            max_cpu_seconds=20,
            max_memory_mib=256,
            max_disk_mib=64,
            max_processes=16,
            max_network_bytes=4096,
        ),
        provider=SandboxProviderBinding(
            provider_id="provider:dw05:synthetic-reference",
            provider_revision="r1",
            provider_kind="in-memory-synthetic",
            provider_evidence_digest=D4,
        ),
    )
    admission = admit_environment(environment)
    assert admission.admitted

    request = {
        "requestRef": "validation:dw05:benign-canary",
        "caseRef": coverage["caseRef"],
        "subjectRef": coverage["subject"]["subjectRef"],
        "subjectSnapshotDigest": coverage["subject"]["snapshotDigest"],
        "controlRef": "control:dw05:canary",
        "targetKind": "synthetic",
        "targetRef": "target:target.example.test",
        "worldSpecDigest": world_spec.digest,
        "environmentDigest": environment.digest,
        "authority": {
            "ownerRef": "owner:dw05:synthetic-validation",
            "decisionRef": "decision:dw05:benign-canary",
            "standing": "AUTHORIZED",
            "scope": {
                "caseRef": coverage["caseRef"],
                "subjectRef": coverage["subject"]["subjectRef"],
                "subjectSnapshotDigest": coverage["subject"]["snapshotDigest"],
                "controlRef": "control:dw05:canary",
                "targetRef": "target:target.example.test",
                "targetKind": "synthetic",
                "threatClass": "synthetic_agent",
            },
        },
    }
    validation_binding = compile_validation_binding(
        dw04_projection=coverage,
        request=request,
        environment=environment.to_dict(),
        sandbox_admission=admission.to_dict(),
        observer_binding=observer.binding.to_dict(),
    )
    assert validation_binding["standing"] == "READY_FOR_SYNTHETIC_VALIDATION"

    proxy = ReferenceEffectProxy(world)
    attempt = EffectAttempt(
        effect_id="effect:dw05:benign-canary",
        actor_id="agent:dw05:canary",
        environment_digest=environment.digest,
        world_spec_digest=world_spec.digest,
        scope="synthetic_world",
        service_id="service:http:canary",
        operation="request",
        target="https://target.example.test/probe",
        content="ORDIVON_DW05_BENIGN_CANARY",
    )
    anchor = observer.start(world, environment_digest=environment.digest)
    receipt = proxy.handle(attempt)
    observation = observer.finish(
        anchor,
        world,
        effect_id=attempt.effect_id,
        effect_request_digest=attempt.digest,
    )
    consistency = reconcile_receipt(receipt, observation)
    assert consistency.consistent
    canary_satisfied = (
        observation.after_outbound_count == observation.before_outbound_count + 1
        and not observation.synthetic_secret_crossing_ids
    )
    assert canary_satisfied

    evidence = project_validation_evidence(
        binding=validation_binding,
        effect_receipt=receipt.to_dict(),
        observation=observation.to_dict(),
        consistency=consistency.to_dict(),
        predicate={
            "predicateRef": "predicate:dw05:benign-pipeline-canary",
            "verifierOwnerRef": observer.binding.observer_id,
            "standing": "SATISFIED",
            "evidenceRefs": [observation.digest, consistency.digest],
        },
    )

    result = {
        "schemaVersion": 1,
        "kind": "ordivon.security.dw05-benign-synthetic-canary-result",
        "dw04": {
            "validationStanding": coverage["validationStanding"],
            "candidateControlRefs": coverage["authorizedValidationCandidateControlRefs"],
            "verifiedProtectionEstablished": coverage["verifiedProtectionEstablished"],
        },
        "binding": validation_binding,
        "foundry": {
            "sandboxAdmission": admission.to_dict(),
            "effectReceipt": receipt.to_dict(),
            "observation": observation.to_dict(),
            "consistency": consistency.to_dict(),
        },
        "validationEvidence": evidence,
        "claimBoundary": (
            "Closed-world .test canary only. This proves regime/admission/effect-proxy/"
            "independent-observer plumbing and exact evidence return. It does not prove "
            "production control effectiveness, verified protection, exploitability, "
            "compromise absence, eradication, or recovery."
        ),
    }
    output = DW05_ROOT / "evidence/acceptance/dw05-benign-synthetic-canary-r1.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "standing": evidence["studyStanding"],
        "bindingStanding": validation_binding["standing"],
        "consistency": consistency.consistent,
        "productionSecurityStandingEstablished": evidence["productionSecurityStandingEstablished"],
        "verifiedProtectionEstablished": evidence["verifiedProtectionEstablished"],
        "output": str(output),
        "evidenceDigest": evidence["evidenceDigest"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
