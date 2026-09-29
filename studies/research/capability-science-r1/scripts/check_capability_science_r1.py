#!/usr/bin/env python3
"""Native R1 acceptance checks without adding a new runtime dependency.

This checker validates Capability Science invariants and bounded fixtures. It does not
reimplement JSON Schema; the JSON Schema files remain machine contracts for external
standards-native validators when available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from semantic_novelty_oracle_r1 import novelty_report


STUDY = Path(__file__).resolve().parents[1]
REPO = STUDY.parents[2]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_schema_surfaces() -> list[str]:
    names = [
        "observation-trace-v1.schema.json",
        "semantic-capability-v1.schema.json",
        "novelty-witness-v1.schema.json",
        "computational-lift-certificate-v1.schema.json",
    ]
    checks: list[str] = []
    for name in names:
        schema = load_json(STUDY / "schemas" / name)
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{name}: draft mismatch")
        require(isinstance(schema.get("$id"), str) and schema["$id"], f"{name}: missing $id")
        require(schema.get("type") == "object", f"{name}: top-level type must be object")
        checks.append(f"schema-parse:{name}")

    semantic = load_json(STUDY / "schemas" / "semantic-capability-v1.schema.json")
    props = semantic["properties"]
    require(props["authorityGranted"].get("const") is False, "semantic schema must force authorityGranted=false")
    require(props["executionAuthorityGranted"].get("const") is False, "semantic schema must force executionAuthorityGranted=false")
    require("effects" in props and "authority" in props and "informationFlow" in props, "effect/authority/flow must remain separate")
    require("repeatabilityEvidenceRefs" in props and "causalEvidenceRefs" in props, "semantic promotion evidence fields must be explicit")
    checks.append("schema-invariant:effect-authority-flow-separated")
    checks.append("schema-invariant:no-authority-laundering")

    lift = load_json(STUDY / "schemas" / "computational-lift-certificate-v1.schema.json")
    require(lift["properties"]["universalDecisionProcedureClaimed"].get("const") is False, "lift schema must reject universal decision procedure claim")
    require("completenessEvidenceRefs" in lift["properties"], "lift schema must separate completeness evidence from ordinary witnesses")
    checks.append("schema-invariant:no-universal-decision-procedure")
    checks.append("schema-invariant:no-lift-requires-completeness-evidence")
    return checks


def check_positive_novelty() -> tuple[list[str], dict[str, Any]]:
    fixture = load_json(STUDY / "fixtures" / "novelty-positive-r1.json")
    report = novelty_report(fixture)
    require(report["verdict"] == fixture["expectedVerdict"], "positive fixture did not establish bounded novelty")
    require(report["comparedBaselineCount"] == len(fixture["library"]), "positive fixture baseline count mismatch")
    require(len(report["witnesses"]) == len(fixture["library"]), "positive fixture requires one witness per baseline")
    for witness in report["witnesses"]:
        require(witness["boundedComparison"] is True, "witness must be bounded")
        require(witness["candidateObservationDigest"] != witness["baselineObservationDigest"], "witness observations must differ")
        require(witness["observationPolicyRef"] == fixture["observationPolicy"]["policyId"], "witness policy drift")
    require(report["authorityGranted"] is False and report["executionAuthorityGranted"] is False, "novelty must not grant authority")
    return [
        "novelty-positive:one-distinguishing-witness-per-baseline",
        "novelty-positive:exact-observation-digests",
        "novelty-positive:no-authority-grant",
    ], report


def check_negative_novelty() -> tuple[list[str], dict[str, Any]]:
    fixture = load_json(STUDY / "fixtures" / "novelty-negative-r1.json")
    report = novelty_report(fixture)
    require(report["verdict"] == fixture["expectedVerdict"], "negative fixture incorrectly admitted novelty")
    require(fixture["expectedNotDistinguishedFromWithinPolicy"] in report["notDistinguishedFromWithinPolicy"], "negative fixture did not bind bounded non-distinguishability baseline")
    return ["novelty-negative:not-distinguished-candidate-not-admitted"], report


def check_semantic_capability_and_observation() -> list[str]:
    cap = load_json(STUDY / "fixtures" / "semantic-capability-durable-memory-r1.json")
    require(cap["authorityGranted"] is False, "fixture authorityGranted must be false")
    require(cap["executionAuthorityGranted"] is False, "fixture executionAuthorityGranted must be false")
    require(set(["effects", "authority", "informationFlow"]).issubset(cap), "fixture must separate effects/authority/informationFlow")
    require(cap["standing"] == "CERTIFIED_NOVEL_CAPABILITY", "semantic fixture standing mismatch")
    require(len(cap["repeatabilityEvidenceRefs"]) >= 1, "inferred/certified capability must name repeatability evidence")
    require(len(cap["causalEvidenceRefs"]) >= 1, "inferred/certified capability must name causal/interventional evidence")
    require(len(cap["noveltyWitnessRefs"]) >= 1, "certified novel fixture must name witness refs")

    obs = load_json(STUDY / "fixtures" / "observation-trace-r1.json")
    runs = obs["repeatability"]["runs"]
    successful = obs["repeatability"]["successfulReproductions"]
    require(0 <= successful <= runs, "observation repeatability counts invalid")
    require(obs["observationId"] in cap["repeatabilityEvidenceRefs"], "semantic fixture must bind exact repeatability observation")

    causal = load_json(STUDY / "fixtures" / "observation-causal-r1.json")
    require(causal["standing"] == "INTERVENTION_SUPPORTED_EFFECT", "causal fixture standing mismatch")
    causal_runs = causal["repeatability"]["runs"]
    causal_successful = causal["repeatability"]["successfulReproductions"]
    require(0 <= causal_successful <= causal_runs, "causal observation repeatability counts invalid")
    require(causal["observationId"] in cap["causalEvidenceRefs"], "semantic fixture must bind exact causal observation")
    return [
        "semantic-capability:no-authority-grant",
        "semantic-capability:effect-authority-flow-separated",
        "semantic-capability:promotion-evidence-gated",
        "observation:repeatability-counts-valid",
        "observation:intervention-supported-effect-present",
    ]


def check_external_provider_pilots() -> tuple[list[str], dict[str, Any]]:
    pilots_doc = load_json(STUDY / "evidence" / "external-provider-pilots-r1.json")
    require(pilots_doc.get("standing") == "BOUNDED_EXTERNAL_PROVIDER_PILOTS_ACCEPTED", "provider pilot standing mismatch")
    require(pilots_doc["dependencyPolicy"]["permanentDependenciesAdded"] is False, "provider pilots must not silently add permanent dependencies")
    pilots = pilots_doc.get("pilots")
    require(isinstance(pilots, list) and len(pilots) == 4, "expected four bounded external provider pilots")
    expected = {
        "R1": ("AALpy", "ACTIVE_BEHAVIOR_IDENTIFICATION"),
        "R2": ("cvc5", "VOCABULARY_PREDICATE_CANDIDATE_GENERATION"),
        "R4": ("pyribs", "GOAL_FREE_CANDIDATE_GENERATION"),
        "R6": ("DoWhy", "CAUSAL_INTERVENTION_VALIDATION"),
    }
    seen: set[str] = set()
    for item in pilots:
        lego = item.get("lego")
        require(lego in expected and lego not in seen, f"unexpected/duplicate provider pilot LEGO: {lego}")
        seen.add(lego)
        provider, role = expected[lego]
        require(item.get("provider") == provider and item.get("role") == role, f"{lego}: provider/role mismatch")
        require(item.get("standing") == "PASS_BOUNDED_PROVIDER_PILOT", f"{lego}: pilot did not pass")
        require(item.get("semanticAuthority") is False, f"{lego}: provider must not become semantic authority")
        require(item.get("permanentDependencyAdmitted") is False, f"{lego}: provider must not become permanent dependency from one pilot")
        refs = item.get("evidenceRefs")
        require(isinstance(refs, list) and any(str(r).startswith("runtime:job:") for r in refs), f"{lego}: Runtime Job evidence missing")
        require(any(str(r).startswith("runtime:artifact:") for r in refs), f"{lego}: Runtime Artifact evidence missing")
    require(seen == set(expected), "provider pilot coverage incomplete")
    return [
        "external-provider:four-bounded-pilots-bound",
        "external-provider:runtime-job-and-artifact-evidence-bound",
        "external-provider:no-semantic-authority-transfer",
        "external-provider:no-permanent-dependency-admission",
    ], pilots_doc


def check_computational_lift() -> list[str]:
    fixture = load_json(STUDY / "fixtures" / "computational-lift-r1.json")
    certificates = fixture.get("certificates")
    require(isinstance(certificates, list) and len(certificates) == 3, "expected three lift fixtures")
    standings = {item["standing"] for item in certificates}
    require(
        standings == {"CERTIFIED_LIFT", "CERTIFIED_NO_LIFT_WITHIN_MODEL_CLASS", "UNKNOWN"},
        "lift fixture must exercise the full three-valued standing",
    )
    model_order = [
        "L0_STATELESS_RELATION",
        "L1_FINITE_STATE_TRANSDUCER",
        "L2_REGISTER_DATA_AUTOMATON",
        "L3_VISIBLY_PUSHDOWN_PROCEDURAL",
        "L4_PETRI_VAS_COUNTERLIKE",
        "L5_FIFO_MULTISTACK_MINSKY_LIKE",
        "L6_GENERAL_INTERACTIVE_COMPUTATION",
    ]
    for item in certificates:
        require(item["universalDecisionProcedureClaimed"] is False, "lift fixture must reject universal decision procedure")
        require(model_order.index(item["higherModelClass"]) > model_order.index(item["lowerModelClass"]), f"{item['certificateId']}: model ladder direction invalid")
        if item["standing"] != "UNKNOWN":
            require(bool(item["witnessRefs"]), f"{item['certificateId']}: certified standing requires witness")
        if item["standing"] == "CERTIFIED_NO_LIFT_WITHIN_MODEL_CLASS":
            require(item["basis"] == "MODEL_CHECK", "bounded no-lift R1 certificate requires complete model checking")
            require(bool(item["completenessEvidenceRefs"]), "bounded no-lift certificate requires completeness evidence")
            require(bool(item["bounds"]), "bounded no-lift certificate requires explicit checked bounds")
        if item["standing"] == "UNKNOWN":
            require(item["basis"] == "NONE", "UNKNOWN fixture must not fabricate proof basis")
            require(not item["witnessRefs"], "UNKNOWN fixture must not carry a positive/negative witness")
            require(not item["completenessEvidenceRefs"], "UNKNOWN fixture must not fabricate completeness evidence")
    return [
        "computational-lift:three-valued-standing",
        "computational-lift:model-ladder-direction-valid",
        "computational-lift:certified-results-have-witness",
        "computational-lift:no-lift-has-completeness-evidence",
        "computational-lift:unknown-remains-first-class",
        "computational-lift:no-universal-decider-claim",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()

    checks: list[str] = []
    checks.extend(check_schema_surfaces())
    positive_checks, positive_report = check_positive_novelty()
    negative_checks, negative_report = check_negative_novelty()
    checks.extend(positive_checks)
    checks.extend(negative_checks)
    checks.extend(check_semantic_capability_and_observation())
    provider_checks, provider_pilots = check_external_provider_pilots()
    checks.extend(provider_checks)
    schema_validation = load_json(STUDY / "evidence" / "external-schema-validation-r1.json")
    require(schema_validation.get("standing") == "PASS_EXTERNAL_SCHEMA_VALIDATION", "external schema validation standing mismatch")
    require(schema_validation.get("permanentDependencyAdmitted") is False, "external validator must not be silently admitted as a permanent dependency")
    require(schema_validation.get("negativeDestroyersPassed") == 2, "external schema destroyer coverage mismatch")
    checks.append("external-schema-validator:draft-2020-12-pass")
    checks.append("external-schema-validator:negative-destroyers-pass")
    checks.extend(check_computational_lift())

    source_revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    tracked = [
        STUDY / "README.md",
        STUDY / "ARCHITECTURE_R1.md",
        STUDY / "scripts" / "semantic_novelty_oracle_r1.py",
        STUDY / "schemas" / "semantic-capability-v1.schema.json",
        STUDY / "fixtures" / "semantic-capability-durable-memory-r1.json",
        STUDY / "fixtures" / "observation-trace-r1.json",
        STUDY / "fixtures" / "observation-causal-r1.json",
        STUDY / "schemas" / "novelty-witness-v1.schema.json",
        STUDY / "schemas" / "computational-lift-certificate-v1.schema.json",
        STUDY / "fixtures" / "computational-lift-r1.json",
        STUDY / "evidence" / "external-provider-pilots-r1.json",
        STUDY / "evidence" / "external-schema-validation-r1.json",
        STUDY / "planning" / "lego-plan-r1.json",
    ]
    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.capability-science-r1-acceptance",
        "studyRef": "study:capability-science-r1",
        "sourceRevision": source_revision,
        "standing": "R1_BOUNDED_ACCEPTED_WITH_PROVIDER_PILOTS",
        "checks": checks,
        "positiveNoveltyVerdict": positive_report["verdict"],
        "positiveWitnessCount": len(positive_report["witnesses"]),
        "negativeNoveltyVerdict": negative_report["verdict"],
        "negativeNotDistinguishedFromWithinPolicy": negative_report["notDistinguishedFromWithinPolicy"],
        "externalProviderPilotsStanding": provider_pilots["standing"],
        "externalProviderPilotLegos": sorted(item["lego"] for item in provider_pilots["pilots"]),
        "externalSchemaValidationStanding": schema_validation["standing"],
        "artifactDigests": {str(path.relative_to(REPO)): file_digest(path) for path in tracked},
        "authorityGranted": False,
        "executionAuthorityGranted": False,
        "domainAcceptanceEstablished": False,
        "nonClaims": [
            "R1 validates bounded local fixtures plus four isolated synthetic external-provider pilots only.",
            "Provider pilots establish task-local compatibility evidence, not production adoption or permanent dependency admission.",
            "R1 does not establish universal contextual equivalence or computational universality.",
        ],
    }

    if args.write_evidence:
        path = STUDY / "evidence" / "capability-science-r1-acceptance.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
