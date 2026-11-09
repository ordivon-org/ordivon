"""A real Finance Research CLI consumer through existing task-local Composition R1.

This test proves a bounded *source-protocol* property and preserves an
unresolved economic claim. An Agent's or caller's claimed independent
reproduction does not attest a financial result or grant broker authority.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from ordivon_composition import (
    canonical_digest,
    compile_verification_obligations,
    evaluate_gate_results,
    resolve_verifier_bindings,
)
from ordivon_composition.cognitive_circuit_r1 import compile_manifest

REPO = Path(__file__).resolve().parents[3]
CLI = REPO / "domains/capital/scripts/finance_lego.py"
CAPITAL = CLI.parent.parent
SOURCE = REPO / "domains/capital/src/ordivon_capital/research/experiment_protocol.py"
SHA = "sha256:" + "a" * 64
PROTOCOL_SCOPE = "real Finance CLI freeze/assess identity, effect-free protocol only"
ECONOMIC_SCOPE = "prospective investment validity requires an externally qualified witness"
FROZEN_FIELDS = frozenset(
    {"schemaVersion", "kind", "planDigest", "plan", "authority", "attestation"}
)
ASSESS_FIELDS = frozenset(
    {
        "schemaVersion",
        "kind",
        "standing",
        "reasons",
        "externalWriteAllowed",
        "capitalAllocationAuthorized",
    }
)


def _plan() -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.capital.research.plan",
        "effectBoundary": "RESEARCH_ONLY",
        "hypothesisId": "test-research-frozen-obligation",
        "baselineId": "cash",
        "metricDefinition": "paired-after-cost-benchmark",
        "frozenAt": "2026-01-01T12:00:00Z",
        "codeRevision": "a" * 40,
        "configDigest": SHA,
        "environmentDigest": SHA,
        "trialsPlanned": 2,
        "partitions": {
            "train": {"start": "2020-01-01", "end": "2022-12-31"},
            "validation": {"start": "2023-01-01", "end": "2025-12-31"},
            "holdout": {"start": "2026-01-02", "end": "2026-06-30"},
        },
        "historicalSources": [
            {
                "sourceId": "synthetic:unattested-training",
                "snapshotDigest": SHA,
                "observedThrough": "2025-12-31T20:00:00Z",
                "availableAt": "2026-01-01T06:00:00Z",
            }
        ],
    }


def _cli(operation: str, payload: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(CLI), operation],
        input=json.dumps(payload, sort_keys=True),
        text=True,
        capture_output=True,
        cwd=CAPITAL,
        env={**os.environ, "PYTHONPATH": str(CAPITAL / "src")},
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _manifest(plan: dict) -> dict:
    source_digest = "sha256:" + hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:capital-research-frozen-consumer",
        "objectiveRef": {
            "id": "objective:finance-prospective-evidence-without-false-authority",
            "digest": canonical_digest(plan),
        },
        "methodBindings": [],
        "capabilityBindings": [
            {
                "id": "capability:capital-research-cli",
                "capability": "capital.research.freeze-assess",
                "ownerId": "capital",
                "sourceKind": "direct-owner",
                "bindingDigest": source_digest,
                "truthBoundary": "Caller-supplied unverified research; no external effect authority.",
            }
        ],
        "stages": [
            {
                "id": "stage:research",
                "ownerId": "capital",
                "responsibility": "Run real Finance freeze/assess research CLI.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": ["capability:capital-research-cli"],
                "inputs": ["research-plan"],
                "outputs": ["frozen-assessment"],
            },
            {
                "id": "stage:composition-consumer",
                "ownerId": "composition",
                "responsibility": "Distinguish source protocol integrity from unknown economic validity.",
                "dependsOn": ["stage:research"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["frozen-assessment"],
                "outputs": ["bounded-test-observation"],
            },
        ],
        "edges": [
            {
                "id": "edge:research-evidence-to-consumer",
                "from": {"stageId": "stage:research", "port": "frozen-assessment"},
                "to": {"stageId": "stage:composition-consumer", "port": "frozen-assessment"},
                "contractRef": "contract:capital-research-source-only",
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:research-freeze-readonly",
                "producerStageId": "stage:research",
                "consumerStageId": "stage:composition-consumer",
                "assumption": "Exact Finance CLI output from caller-declared, source-only plan.",
                "guarantee": "Freeze identity and UNKNOWN/REVIEW_REQUIRED remain effect-free.",
                "verifierOwnerId": "composition",
                "supportScope": PROTOCOL_SCOPE,
                "required": True,
            },
            {
                "id": "gate:prospective-investment-validity",
                "producerStageId": "stage:research",
                "consumerStageId": "stage:composition-consumer",
                "assumption": "Authenticated independently verified prospective data exists.",
                "guarantee": "Economic performance can be independently confirmed.",
                "verifierOwnerId": "composition",
                "supportScope": ECONOMIC_SCOPE,
                "required": True,
            },
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Source-protocol gate SATISFIED does not prove research forecast quality.",
            "Independent external market/holdout evidence is not provided here.",
            "A Composition projection cannot approve an order or domain outcome.",
        ],
    }


def _gate_result(
    manifest: dict, gate: str, scope: str, standing: str, evidence: dict | None
) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compile_manifest(manifest)["manifestDigest"],
        "gateId": gate,
        "verifierOwnerId": "composition",
        "standing": standing,
        "evidenceRefs": (
            [] if evidence is None else ["finance-observed-json:" + canonical_digest(evidence)]
        ),
        "supportScope": scope,
        "nonClaims": ["Local source/test result is not an independent economic or broker verdict."],
    }


def _observed_gates(
    manifest: dict, plan: dict, frozen: dict | None, assessed: dict | None
) -> list[dict]:
    # Source-byte independent output checking; no new Research evaluator.
    if frozen is None or assessed is None:
        protocol_standing = "UNKNOWN"
    else:
        expected_digest = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(
                    plan,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
            ).hexdigest()
        )
        protocol_ok = (
            set(frozen) == FROZEN_FIELDS
            and frozen["schemaVersion"] == 1
            and frozen["kind"] == "ordivon.capital.research.frozen-plan"
            and frozen["planDigest"] == expected_digest
            and frozen["plan"] == plan
            and frozen["authority"] == "NONE"
            and frozen["attestation"] == "CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED"
            and set(assessed) == ASSESS_FIELDS
            and assessed["schemaVersion"] == 1
            and assessed["kind"] == "ordivon.capital.research.evidence-assessment"
            and assessed["externalWriteAllowed"] is False
            and assessed["capitalAllocationAuthorized"] is False
            and assessed["standing"] in {"UNKNOWN", "REVIEW_REQUIRED"}
        )
        protocol_standing = "SATISFIED" if protocol_ok else "UNSATISFIED"

    # No test-local attempt to derive economic truth from caller-declared bytes.
    # A provider-qualified prospective witness must be independently supplied.
    prospective_standing = "UNKNOWN" if protocol_standing != "UNSATISFIED" else "UNSATISFIED"
    return [
        _gate_result(
            manifest,
            "gate:research-freeze-readonly",
            PROTOCOL_SCOPE,
            protocol_standing,
            None if protocol_standing == "UNKNOWN" else {"frozen": frozen, "assessment": assessed},
        ),
        _gate_result(
            manifest,
            "gate:prospective-investment-validity",
            ECONOMIC_SCOPE,
            prospective_standing,
            None if prospective_standing == "UNKNOWN" else {"assessment": assessed},
        ),
    ]


def _holdout(plan_digest: str) -> dict:
    return {
        "planDigest": plan_digest,
        "evaluatedAt": "2026-07-02T12:00:00Z",
        "observedThrough": "2026-06-30T21:00:00Z",
        "availableAt": "2026-07-01T06:00:00Z",
        "holdoutDigest": SHA,
        "trialsEvaluated": 2,
        "multiplicityControl": "DOCUMENTED",
        "costModelDigest": SHA,
        "benchmarkEvidenceDigest": SHA,
        "independentReproduction": True,
    }


def test_real_finance_freeze_closes_protocol_but_not_economic_validity() -> None:
    plan = _plan()
    frozen = _cli("freeze-experiment", plan)
    missing = _cli("assess-holdout", {"frozen": frozen, "result": None})
    assert missing["standing"] == "UNKNOWN"
    assert missing["reasons"] == ["NO_HOLDOUT_EVIDENCE"]

    manifest = _manifest(plan)
    obligations = compile_verification_obligations(manifest)
    assert len(obligations["requiredGateIds"]) == 2
    binding_set = {
        "schemaVersion": 1,
        "kind": "ordivon.task-local-verifier-binding-set",
        "circuitRef": obligations["circuitRef"],
        "obligationSetDigest": obligations["obligationSetDigest"],
        "bindings": [
            {
                "gateId": item["gateId"],
                "obligationDigest": item["obligationDigest"],
                "verifierOwnerId": "composition",
                "verifierRef": {
                    "id": "source-test:finance-research",
                    "digest": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                },
                "verifierClass": "owner-native-consumer-test",
                "nativeSpecificationRef": None,
                "supportScope": item["supportScope"],
                "nonClaims": ["Source test cannot attest independent financial truth."],
            }
            for item in obligations["obligations"]
        ],
        "nonClaims": ["A resolved binding is not a completed economic objective."],
    }
    resolution = resolve_verifier_bindings(obligations, binding_set)
    assert resolution["standing"] == "VERIFIER_BINDINGS_RESOLVED"
    assert resolution["domainAcceptanceEstablished"] is False

    results = _observed_gates(manifest, plan, frozen, missing)
    assert {r["gateId"]: r["standing"] for r in results} == {
        "gate:research-freeze-readonly": "SATISFIED",
        "gate:prospective-investment-validity": "UNKNOWN",
    }
    evaluated = evaluate_gate_results(manifest, results)
    assert evaluated["standing"] == "COMPOSITION_GATES_OPEN"
    assert evaluated["satisfiedGateIds"] == ["gate:research-freeze-readonly"]
    assert evaluated["unknownGateIds"] == ["gate:prospective-investment-validity"]
    assert evaluated["domainAcceptanceEstablished"] is False

    # A syntactically full, self-declared 'independent' result is not a
    # provider-authenticated prospective performance/effect witness.
    claimed = _cli(
        "assess-holdout",
        {
            "frozen": frozen,
            "result": _holdout(frozen["planDigest"]),
        },
    )
    assert claimed["standing"] == "REVIEW_REQUIRED"
    assert claimed["externalWriteAllowed"] is False
    assert claimed["capitalAllocationAuthorized"] is False
    still_open = evaluate_gate_results(manifest, _observed_gates(manifest, plan, frozen, claimed))
    assert still_open["standing"] == "COMPOSITION_GATES_OPEN"
    assert still_open["domainAcceptanceEstablished"] is False


def test_forged_authority_and_tampered_frozen_plan_cannot_become_research_pass() -> None:
    plan = _plan()
    frozen = _cli("freeze-experiment", plan)
    missing = _cli("assess-holdout", {"frozen": frozen, "result": None})
    manifest = _manifest(plan)
    for extra_effect in ("externalWriteAllowed", "capitalAllocationAuthorized"):
        forged = copy.deepcopy(missing)
        forged[extra_effect] = True
        results = _observed_gates(manifest, plan, frozen, forged)
        assert results[0]["standing"] == "UNSATISFIED"
        assert evaluate_gate_results(manifest, results)["standing"] == (
            "COMPOSITION_GATES_UNSATISFIED"
        )

    tampered = copy.deepcopy(frozen)
    tampered["planDigest"] = "sha256:" + "0" * 64
    rejected = _cli("assess-holdout", {"frozen": tampered, "result": None})
    assert rejected["standing"] == "REJECTED"
    results = _observed_gates(manifest, plan, tampered, rejected)
    assert results[0]["standing"] == "UNSATISFIED"
    assert evaluate_gate_results(manifest, results)["standing"] == ("COMPOSITION_GATES_UNSATISFIED")

    no_output = _observed_gates(manifest, plan, None, None)
    assert all(r["standing"] == "UNKNOWN" for r in no_output)
    assert evaluate_gate_results(manifest, no_output)["standing"] == ("COMPOSITION_GATES_OPEN")
