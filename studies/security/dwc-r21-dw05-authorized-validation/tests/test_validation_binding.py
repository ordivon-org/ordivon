from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
R4 = REPO / "studies/security/ai-redteam-foundry-r4"
if str(R4) not in sys.path:
    sys.path.insert(0, str(R4))
from foundry_r4 import (  # noqa: E402
    ExperimentEnvironmentSpec,
    IsolationVector,
    ResourceBudget,
    SandboxProviderBinding,
    admit_environment,
)

MODULE = ROOT / "dwc_dw05" / "validation_binding.py"
SPEC = importlib.util.spec_from_file_location("dw05", MODULE)
assert SPEC and SPEC.loader
dw05 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dw05)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
D4 = "sha256:" + "4" * 64
D5 = "sha256:" + "5" * 64


def dw04():
    return {
        "kind": "ordivon.security.dwc-attack-coverage-projection",
        "caseRef": "case:synthetic",
        "subject": {"subjectRef": "synthetic-subject:test", "snapshotDigest": D1},
        "authorizedValidationCandidateControlRefs": ["control:test"],
    }


def environment(
    *, network="simulated_internet", credentials="synthetic_only", observer="independent"
):
    return ExperimentEnvironmentSpec(
        environment_id="environment:dw05:test",
        threat_class="synthetic_agent",
        base_image_digest=D2,
        synthetic_world_digest=D3,
        tool_surface_digest=D4,
        observer_spec_digest=D5,
        isolation=IsolationVector(
            process="separate_process_tree",
            kernel="shared",
            filesystem="synthetic",
            network=network,
            credentials=credentials,
            devices="none",
            external_effects="synthetic_only",
            lifecycle="resettable",
            observer=observer,
        ),
        budget=ResourceBudget(
            max_wall_seconds=30,
            max_cpu_seconds=20,
            max_memory_mib=256,
            max_disk_mib=64,
            max_processes=16,
            max_network_bytes=1024,
        ),
        provider=SandboxProviderBinding(
            provider_id="provider:synthetic-reference",
            provider_revision="r1",
            provider_kind="in-memory-synthetic",
            provider_evidence_digest=D5,
        ),
    )


def request(spec):
    return {
        "requestRef": "validation:synthetic:test",
        "caseRef": "case:synthetic",
        "subjectRef": "synthetic-subject:test",
        "subjectSnapshotDigest": D1,
        "controlRef": "control:test",
        "targetKind": "synthetic",
        "targetRef": "target:example.test",
        "worldSpecDigest": D3,
        "environmentDigest": spec.digest,
        "authority": {
            "ownerRef": "owner:synthetic-validation",
            "decisionRef": "decision:synthetic-validation:test",
            "standing": "AUTHORIZED",
            "scope": {
                "caseRef": "case:synthetic",
                "subjectRef": "synthetic-subject:test",
                "subjectSnapshotDigest": D1,
                "controlRef": "control:test",
                "targetRef": "target:example.test",
                "targetKind": "synthetic",
                "threatClass": "synthetic_agent",
            },
        },
    }


def observer():
    return {
        "observerId": "observer:synthetic-r7",
        "observerRevision": "r7",
        "independenceClass": "process_local_independent_code_path",
        "applicableThreatClasses": ["synthetic_agent"],
    }


def compile_binding(spec=None, req=None):
    spec = spec or environment()
    req = req or request(spec)
    return dw05.compile_validation_binding(
        dw04_projection=dw04(),
        request=req,
        environment=spec.to_dict(),
        sandbox_admission=admit_environment(spec).to_dict(),
        observer_binding=observer(),
    )


def test_ready_synthetic_binding():
    result = compile_binding()
    assert result["standing"] == "READY_FOR_SYNTHETIC_VALIDATION"
    assert result["validationAdmissionEstablished"] is True
    assert result["executionAuthorityGrantedByDW05"] is False
    assert result["productionSecurityStandingEstablished"] is False


def test_mapping_only_non_candidate_fails_closed():
    projection = dw04()
    projection["authorizedValidationCandidateControlRefs"] = []
    spec = environment()
    result = dw05.compile_validation_binding(
        dw04_projection=projection,
        request=request(spec),
        environment=spec.to_dict(),
        sandbox_admission=admit_environment(spec).to_dict(),
        observer_binding=observer(),
    )
    assert result["standing"] == "REJECTED"
    assert any("not a DW04" in reason for reason in result["rejectionReasons"])


def test_subject_mismatch_fails_closed():
    spec = environment()
    req = request(spec)
    req["subjectSnapshotDigest"] = D2
    result = compile_binding(spec, req)
    assert result["standing"] == "REJECTED"
    assert any("subject binding" in reason for reason in result["rejectionReasons"])


def test_authority_scope_mismatch_fails_closed():
    spec = environment()
    req = request(spec)
    req["authority"]["scope"]["targetRef"] = "target:other.test"
    result = compile_binding(spec, req)
    assert result["standing"] == "REJECTED"
    assert any("authority scope" in reason for reason in result["rejectionReasons"])


def test_non_synthetic_target_fails_closed():
    spec = environment()
    req = request(spec)
    req["targetKind"] = "production"
    req["authority"]["scope"]["targetKind"] = "production"
    result = compile_binding(spec, req)
    assert result["standing"] == "REJECTED"
    assert any("synthetic targets" in reason for reason in result["rejectionReasons"])


def test_full_egress_fails_closed():
    spec = environment(network="full_egress")
    req = request(spec)
    result = compile_binding(spec, req)
    assert result["standing"] == "REJECTED"
    assert any("unrestricted network" in reason for reason in result["rejectionReasons"])


def test_non_synthetic_credentials_fail_closed():
    spec = environment(credentials="provider_scoped")
    req = request(spec)
    result = compile_binding(spec, req)
    assert result["standing"] == "REJECTED"
    assert any("non-synthetic credentials" in reason for reason in result["rejectionReasons"])


def test_observer_declaration_must_be_independent():
    spec = environment(observer="same_trust_domain")
    req = request(spec)
    result = compile_binding(spec, req)
    assert result["standing"] == "REJECTED"
    assert any("independent observer" in reason for reason in result["rejectionReasons"])


def test_validation_evidence_never_promotes_production_security():
    binding = compile_binding()
    effect = {"effectRequestDigest": D2}
    observation = {
        "environmentDigest": binding["environmentDigest"],
        "worldSpecDigest": binding["worldSpecDigest"],
        "effectRequestDigest": D2,
    }
    consistency = {
        "consistent": True,
        "observationDigest": dw05.canonical_digest(observation),
    }
    result = dw05.project_validation_evidence(
        binding=binding,
        effect_receipt=effect,
        observation=observation,
        consistency=consistency,
        predicate={
            "predicateRef": "predicate:benign-canary",
            "verifierOwnerRef": "observer:synthetic-r7",
            "standing": "SATISFIED",
            "evidenceRefs": ["evidence:observation"],
        },
    )
    assert result["studyStanding"] == "SYNTHETIC_VALIDATION_OBSERVED"
    assert result["productionSecurityStandingEstablished"] is False
    assert result["verifiedProtectionEstablished"] is False
    assert result["productionEffectAuthorityGranted"] is False


def test_inconsistent_executor_observer_evidence_fails_closed():
    binding = compile_binding()
    effect = {"effectRequestDigest": D2}
    observation = {
        "environmentDigest": binding["environmentDigest"],
        "worldSpecDigest": binding["worldSpecDigest"],
        "effectRequestDigest": D2,
    }
    with pytest.raises(ValueError, match="inconsistent"):
        dw05.project_validation_evidence(
            binding=binding,
            effect_receipt=effect,
            observation=observation,
            consistency={
                "consistent": False,
                "observationDigest": dw05.canonical_digest(observation),
            },
            predicate={
                "predicateRef": "predicate:benign-canary",
                "verifierOwnerRef": "observer:synthetic-r7",
                "standing": "INCONCLUSIVE",
                "evidenceRefs": [],
            },
        )
