from __future__ import annotations

import copy
import json
import tomllib
from pathlib import Path

from scripts.cognitive_circuit_r1 import (
    canonical_digest,
    evaluate_gate_results,
    validate_manifest,
)
from scripts.research_artifact_gate_r3 import (
    build_gate_result as research_artifact_gate,
)
from scripts.web_security_gate_r3 import build_gate_result as web_security_gate

ROOT = Path(__file__).resolve().parents[3]
NEXT_ROOT = Path(__file__).resolve().parents[1]


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def research_artifact_manifest() -> dict:
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:research-artifact-publication-r3",
        "objectiveRef": {
            "id": "objective:publication-carrier-seam",
            "digest": _digest("publication-carrier-seam"),
        },
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:research-profile",
                "ownerId": "research",
                "responsibility": "Bind study-owned publication closure profile.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": [],
                "outputs": ["publication-profile"],
            },
            {
                "id": "stage:artifact-carrier",
                "ownerId": "artifact",
                "responsibility": "Evaluate publication carrier mechanics.",
                "dependsOn": ["stage:research-profile"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["publication-profile"],
                "outputs": ["carrier-evaluation"],
            },
            {
                "id": "stage:research-closure",
                "ownerId": "research",
                "responsibility": "Consume bounded carrier evidence without lifting truth.",
                "dependsOn": ["stage:artifact-carrier"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["carrier-evaluation"],
                "outputs": ["carrier-stage-standing"],
            },
        ],
        "edges": [
            {
                "id": "edge:research-to-artifact",
                "from": {
                    "stageId": "stage:research-profile",
                    "port": "publication-profile",
                },
                "to": {
                    "stageId": "stage:artifact-carrier",
                    "port": "publication-profile",
                },
                "contractRef": "contract:research-publication-profile",
            },
            {
                "id": "edge:artifact-to-research",
                "from": {
                    "stageId": "stage:artifact-carrier",
                    "port": "carrier-evaluation",
                },
                "to": {
                    "stageId": "stage:research-closure",
                    "port": "carrier-evaluation",
                },
                "contractRef": "contract:artifact-publication-carrier",
            },
        ],
        "gateRequirements": [
            {
                "id": "gate:research-artifact-carrier",
                "producerStageId": "stage:artifact-carrier",
                "consumerStageId": "stage:research-closure",
                "assumption": (
                    "Artifact carrier evidence is bounded to carrier mechanics and "
                    "preserves external scientific and Human authority."
                ),
                "guarantee": (
                    "Research may consume the carrier-machine result without treating "
                    "it as scientific, perceptual, venue, or submission closure."
                ),
                "verifierOwnerId": "research",
                "supportScope": (
                    "Artifact publication carrier machine mechanics may satisfy the "
                    "Research carrier stage without establishing scientific, Human "
                    "perceptual, venue-policy, or submission authority."
                ),
                "required": True,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Publication carrier closure is not scientific correctness.",
            "Machine carrier closure is not Human perceptual signoff.",
        ],
    }
    validate_manifest(manifest)
    return manifest


def web_security_manifest() -> dict:
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:web-security-agent-authority-r3",
        "objectiveRef": {
            "id": "objective:web-security-agent-authority-seam",
            "digest": _digest("web-security-agent-authority-seam"),
        },
        "methodBindings": [],
        "capabilityBindings": [],
        "stages": [
            {
                "id": "stage:security-contract",
                "ownerId": "security",
                "responsibility": (
                    "Verify delegated-Agent request identity and evaluate bounded "
                    "Agent/Effect admission contracts."
                ),
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": [],
                "outputs": ["security-contract-result"],
            },
            {
                "id": "stage:web-effect",
                "ownerId": "web",
                "responsibility": (
                    "Own local replay, Grant, approval, effect transaction, and "
                    "receipt semantics."
                ),
                "dependsOn": ["stage:security-contract"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["security-contract-result"],
                "outputs": ["web-effect-receipt"],
            },
        ],
        "edges": [
            {
                "id": "edge:security-to-web",
                "from": {
                    "stageId": "stage:security-contract",
                    "port": "security-contract-result",
                },
                "to": {
                    "stageId": "stage:web-effect",
                    "port": "security-contract-result",
                },
                "contractRef": "contract:security-public-agent-authority",
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:web-security-agent-authority",
                "producerStageId": "stage:security-contract",
                "consumerStageId": "stage:web-effect",
                "assumption": (
                    "Web consumes only Security public verifier/admission contracts "
                    "for the delegated-Agent security seam."
                ),
                "guarantee": (
                    "Web retains its local replay, Grant, approval, effect, and "
                    "receipt semantics while Security retains protocol/admission truth."
                ),
                "verifierOwnerId": "web",
                "supportScope": (
                    "Web may consume Security public request-verification and admission "
                    "contracts while Web retains local replay, Grant, approval, effect, "
                    "and receipt state."
                ),
                "required": True,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Security admission is not Web effect completion.",
            "Web effect success is not OAuth/DPoP protocol authority.",
        ],
    }
    validate_manifest(manifest)
    return manifest


def _research_inputs() -> tuple[dict, dict]:
    return (
        _load_json("meta/research/publication-closure-profile-r1.json"),
        _load_json("meta/research/evidence/publication-carrier-paper3-dogfood-r1.json"),
    )


def _web_inputs() -> tuple[dict, dict, str, str, str]:
    with (ROOT / "tools/repo/dependency_contracts.toml").open("rb") as handle:
        dependencies = tomllib.load(handle)
    return (
        dependencies,
        _load_json("apps/web/evidence/AGENT-NATIVE-WEBSITE-E2E-R1.json"),
        (ROOT / "apps/web/src/security-agent-verifier.ts").read_text(encoding="utf-8"),
        (ROOT / "apps/web/src/agent-authority.ts").read_text(encoding="utf-8"),
        (ROOT / "apps/web/src/store.ts").read_text(encoding="utf-8"),
    )


def test_research_artifact_real_paper3_dogfood_satisfies_bounded_gate() -> None:
    profile, dogfood = _research_inputs()
    manifest = research_artifact_manifest()

    result = research_artifact_gate(manifest, profile, dogfood)
    projection = evaluate_gate_results(manifest, [result])

    assert result["standing"] == "SATISFIED"
    assert projection["mechanicalClosure"] is True
    assert projection["domainAcceptanceEstablished"] is False


def test_research_artifact_truth_owner_drift_is_unsatisfied() -> None:
    profile, dogfood = _research_inputs()
    profile = copy.deepcopy(profile)
    profile["ownerBindings"]["scientificTruth"] = "capabilities/artifact"

    result = research_artifact_gate(
        research_artifact_manifest(),
        profile,
        dogfood,
    )

    assert result["standing"] == "UNSATISFIED"


def test_research_artifact_machine_failure_is_unsatisfied() -> None:
    profile, dogfood = _research_inputs()
    dogfood = copy.deepcopy(dogfood)
    dogfood["evaluation"]["machineStanding"] = "FAIL"

    result = research_artifact_gate(
        research_artifact_manifest(),
        profile,
        dogfood,
    )

    assert result["standing"] == "UNSATISFIED"


def test_research_artifact_missing_truth_boundary_nonclaims_is_unsatisfied() -> None:
    profile, dogfood = _research_inputs()
    dogfood = copy.deepcopy(dogfood)
    dogfood["nonClaims"] = ["Carrier observation only."]

    result = research_artifact_gate(
        research_artifact_manifest(),
        profile,
        dogfood,
    )

    assert result["standing"] == "UNSATISFIED"


def test_web_security_real_native_e2e_satisfies_bounded_gate() -> None:
    dependencies, e2e, request_source, admission_source, store_source = _web_inputs()
    manifest = web_security_manifest()

    result = web_security_gate(
        manifest,
        dependencies,
        e2e,
        request_source,
        admission_source,
        store_source,
    )
    projection = evaluate_gate_results(manifest, [result])

    assert result["standing"] == "SATISFIED"
    assert projection["mechanicalClosure"] is True
    assert projection["domainAcceptanceEstablished"] is False


def test_web_security_missing_public_seam_declaration_is_unsatisfied() -> None:
    dependencies, e2e, request_source, admission_source, store_source = _web_inputs()
    dependencies = copy.deepcopy(dependencies)
    dependencies["seams"] = [
        row
        for row in dependencies["seams"]
        if row.get("source_glob") != "apps/web/src/agent-authority.ts"
    ]

    result = web_security_gate(
        web_security_manifest(),
        dependencies,
        e2e,
        request_source,
        admission_source,
        store_source,
    )

    assert result["standing"] == "UNSATISFIED"


def test_web_security_direct_policy_import_is_unsatisfied() -> None:
    dependencies, e2e, request_source, admission_source, store_source = _web_inputs()
    admission_source += "\n// platform/security/policies/agent_admission.rego\n"

    result = web_security_gate(
        web_security_manifest(),
        dependencies,
        e2e,
        request_source,
        admission_source,
        store_source,
    )

    assert result["standing"] == "UNSATISFIED"


def test_web_security_missing_local_replay_owner_is_unsatisfied() -> None:
    dependencies, e2e, request_source, admission_source, store_source = _web_inputs()
    store_source = store_source.replace("consumeDpopProof(", "removedReplayMethod(")

    result = web_security_gate(
        web_security_manifest(),
        dependencies,
        e2e,
        request_source,
        admission_source,
        store_source,
    )

    assert result["standing"] == "UNSATISFIED"


def test_web_security_e2e_failure_matrix_drift_is_unsatisfied() -> None:
    dependencies, e2e, request_source, admission_source, store_source = _web_inputs()
    e2e = copy.deepcopy(e2e)
    e2e["matrix"]["proofReplay"] = 200

    result = web_security_gate(
        web_security_manifest(),
        dependencies,
        e2e,
        request_source,
        admission_source,
        store_source,
    )

    assert result["standing"] == "UNSATISFIED"


def test_web_security_production_claim_cannot_be_smuggled_into_dogfood() -> None:
    dependencies, e2e, request_source, admission_source, store_source = _web_inputs()
    e2e = copy.deepcopy(e2e)
    e2e["productionEligible"] = True

    result = web_security_gate(
        web_security_manifest(),
        dependencies,
        e2e,
        request_source,
        admission_source,
        store_source,
    )

    assert result["standing"] == "UNSATISFIED"
