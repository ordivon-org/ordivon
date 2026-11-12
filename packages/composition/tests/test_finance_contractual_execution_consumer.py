"""Finance's real read-only Portfolio consumer composed with existing R1 Gates.

A source-bound and economic-property regression, not a Finance acceptance service:
the test-owned witness is independent of an Agent's Completion Proposal, but it
does not authenticate broker, market-data or provider authority.
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
CLI = REPO / "domains/capital/scripts/strategic_contribution_brief.py"
CAPITAL = CLI.parent.parent
SOURCE = REPO / "domains/capital/src/ordivon_capital/portfolio/strategic_contribution.py"
EXAMPLE = REPO / "domains/capital/examples/strategic_contribution_r1.json"
SUPPORT = "source-observed Finance contribution cash/holdings conservation and no external effect"
# Finance's current published contribution output shape; unknown fields cannot
# silently smuggle a new permission while retaining a satisfied narrow gate.
PLAN_FIELDS = frozenset(
    {
        "schemaVersion",
        "kind",
        "standing",
        "currency",
        "unit",
        "contributionMinor",
        "cashAfterMinor",
        "protectedReserveMinor",
        "currentHoldingsMinor",
        "targetWeightsBps",
        "allocationsMinor",
        "projectedHoldingsMinor",
        "projectedInvestmentMinor",
        "allocationMethod",
        "dataStanding",
        "riskStanding",
        "costsAndTaxesModeled",
        "investmentAdviceProduced",
        "executionAuthorized",
    }
)


def _source_ref() -> str:
    return "sha256:" + hashlib.sha256(SOURCE.read_bytes()).hexdigest()


def _real_finance_output(request: dict) -> dict:
    completed = subprocess.run(
        [sys.executable, str(CLI)],
        input=json.dumps(request, sort_keys=True),
        cwd=CAPITAL,
        env={**os.environ, "PYTHONPATH": str(CAPITAL / "src")},
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _manifest(request: dict) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": "circuit:capital-contribution-source-readback",
        "objectiveRef": {
            "id": "objective:finance-readonly-contribution",
            "digest": canonical_digest(request),
        },
        "methodBindings": [],
        "capabilityBindings": [
            {
                "id": "capability:capital-native-cli",
                "capability": "capital.portfolio.contribution",
                "ownerId": "capital",
                "sourceKind": "direct-owner",
                "bindingDigest": _source_ref(),
                "truthBoundary": "Native source bytes and read-only output, not broker effects.",
            }
        ],
        "stages": [
            {
                "id": "stage:portfolio",
                "ownerId": "capital",
                "responsibility": "Run existing contribution-only Finance native CLI.",
                "dependsOn": [],
                "methodBindings": [],
                "capabilityBindings": ["capability:capital-native-cli"],
                "inputs": ["mandate-input"],
                "outputs": ["contribution-plan"],
            },
            {
                "id": "stage:source-consumer",
                "ownerId": "composition",
                "responsibility": "Check exact output arithmetic and absence of effects.",
                "dependsOn": ["stage:portfolio"],
                "methodBindings": [],
                "capabilityBindings": [],
                "inputs": ["contribution-plan"],
                "outputs": ["bounded-observation"],
            },
        ],
        "edges": [
            {
                "id": "edge:plan-to-consumer",
                "from": {"stageId": "stage:portfolio", "port": "contribution-plan"},
                "to": {"stageId": "stage:source-consumer", "port": "contribution-plan"},
                "contractRef": "contract:capital-contribution-readonly",
            }
        ],
        "gateRequirements": [
            {
                "id": "gate:capital-contribution-consumed",
                "producerStageId": "stage:portfolio",
                "consumerStageId": "stage:source-consumer",
                "assumption": "The real Finance source is executed with this exact input.",
                "guarantee": "Cash/holdings conservation and no external effects in the observed plan.",
                "verifierOwnerId": "composition",
                "supportScope": SUPPORT,
                "required": True,
            }
        ],
        "unresolvedAssumptions": [],
        "nonClaims": [
            "A local test observation is not authenticated market or broker reality.",
            "Composition mechanical closure is never a Finance domain verdict.",
        ],
    }


def _consumer_result(manifest: dict, request: dict, observed: dict | None) -> dict:
    """Check an independently specified budget/no-effects contract, not a new optimizer."""
    if observed is None:
        standing = "UNKNOWN"
    else:
        try:
            allocation = observed["allocationsMinor"]
            holdings = request["holdingsMinor"]
            projected = observed["projectedHoldingsMinor"]
            # Integer cents are a type contract, not Python numeric equality:
            # 40000.0 == 40000 and True == 1 must not certify a receipt.
            valid = (
                all(
                    type(observed[field]) is int
                    for field in (
                        "cashAfterMinor",
                        "protectedReserveMinor",
                        "contributionMinor",
                        "projectedInvestmentMinor",
                    )
                )
                and all(
                    type(value) is int
                    for field in (
                        "currentHoldingsMinor",
                        "projectedHoldingsMinor",
                        "allocationsMinor",
                        "targetWeightsBps",
                    )
                    for value in observed[field].values()
                )
                and set(observed) == PLAN_FIELDS
                and observed["schemaVersion"] == 1
                and observed["currency"] == request["currency"] == "USD"
                and observed["unit"] == "minor"
                and observed["currentHoldingsMinor"] == holdings
                and observed["targetWeightsBps"] == request["targetWeightsBps"]
                and observed["protectedReserveMinor"] == request["protectedReserveMinor"]
                and observed["contributionMinor"] == request["contributionMinor"]
                and observed["allocationMethod"] == "TARGET_DEFICIT_LARGEST_REMAINDER"
                and observed["kind"] == "ordivon.finance.portfolio.strategic-contribution-plan"
                and observed["standing"] == "READ_ONLY_PROJECTION"
                and observed["cashAfterMinor"]
                == request["cashMinor"] - request["contributionMinor"]
                and observed["cashAfterMinor"] >= request["protectedReserveMinor"]
                and sum(allocation.values()) == request["contributionMinor"]
                and all(
                    type(allocation[name]) is int
                    and allocation[name] >= 0
                    and projected[name] == holdings[name] + allocation[name]
                    for name in holdings
                )
                and set(allocation) == set(holdings) == set(projected)
                and observed["projectedInvestmentMinor"] == sum(projected.values())
                and observed["executionAuthorized"] is False
                and observed["investmentAdviceProduced"] is False
                and observed["dataStanding"] == "CALLER_SUPPLIED_UNATTESTED"
                and observed["riskStanding"] == "NOT_EVALUATED"
                and observed["costsAndTaxesModeled"] is False
                and not any(
                    x in observed for x in ("orders", "brokerReceipt", "tradeAuthorization")
                )
            )
        except KeyError, TypeError, ValueError, AttributeError:
            valid = False
        standing = "SATISFIED" if valid else "UNSATISFIED"

    return {
        "schemaVersion": 1,
        "kind": "ordivon.composition-gate-result",
        "circuitId": manifest["circuitId"],
        "manifestDigest": compile_manifest(manifest)["manifestDigest"],
        "gateId": "gate:capital-contribution-consumed",
        "verifierOwnerId": "composition",
        "standing": standing,
        "evidenceRefs": (
            []
            if observed is None
            else [f"finance-source:{_source_ref()}", f"finance-output:{canonical_digest(observed)}"]
        ),
        "supportScope": SUPPORT,
        "nonClaims": [
            "Local regression evidence grants no Finance domain acceptance or broker effect."
        ],
    }


def test_real_finance_output_closes_only_scoped_composition_obligation() -> None:
    request = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    manifest = _manifest(request)
    output = _real_finance_output(request)
    assert output["allocationsMinor"] == {"BOND_CORE": 10000, "INDEX_CORE": 0}
    result = _consumer_result(manifest, request, output)
    assert result["standing"] == "SATISFIED"

    obligations = compile_verification_obligations(manifest)
    obligation = obligations["obligations"][0]
    bindings = {
        "schemaVersion": 1,
        "kind": "ordivon.task-local-verifier-binding-set",
        "circuitRef": obligations["circuitRef"],
        "obligationSetDigest": obligations["obligationSetDigest"],
        "bindings": [
            {
                "gateId": obligation["gateId"],
                "obligationDigest": obligation["obligationDigest"],
                "verifierOwnerId": obligation["verifierOwnerId"],
                "verifierRef": {
                    "id": "source-test:finance-contribution",
                    "digest": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                },
                "verifierClass": "owner-native-consumer-test",
                "nativeSpecificationRef": None,
                "supportScope": SUPPORT,
                "nonClaims": ["Tests are not provider-authenticated financial advice."],
            }
        ],
        "nonClaims": ["Binding is not verification execution or domain completion."],
    }
    resolution = resolve_verifier_bindings(obligations, bindings)
    assert resolution["mechanicalResolution"] is True
    assert resolution["domainAcceptanceEstablished"] is False

    evaluated = evaluate_gate_results(manifest, [result])
    assert evaluated["standing"] == "COMPOSITION_GATES_SATISFIED"
    assert evaluated["mechanicalClosure"] is True
    assert evaluated["domainAcceptanceEstablished"] is False


def test_unknown_and_false_economic_receipts_do_not_close_composition() -> None:
    request = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    manifest = _manifest(request)
    observed = _real_finance_output(request)

    absent = evaluate_gate_results(manifest, [_consumer_result(manifest, request, None)])
    assert absent["standing"] == "COMPOSITION_GATES_OPEN"
    assert absent["domainAcceptanceEstablished"] is False

    for corruption in (
        "broker",
        "cash",
        "holdings",
        "risk",
        "extra-permission",
        "cash-float",
        "holding-float",
        "total-float",
        "allocation-float",
    ):
        tampered = copy.deepcopy(observed)
        if corruption == "broker":
            tampered["executionAuthorized"] = True
        elif corruption == "cash":
            tampered["cashAfterMinor"] += 1
        elif corruption == "holdings":
            tampered["projectedHoldingsMinor"]["BOND_CORE"] += 1
        elif corruption == "risk":
            tampered["riskStanding"] = "APPROVED"
        elif corruption == "extra-permission":
            tampered["externalWriteAllowed"] = True
        elif corruption == "cash-float":
            tampered["cashAfterMinor"] = float(tampered["cashAfterMinor"])
        elif corruption == "holding-float":
            tampered["projectedHoldingsMinor"]["BOND_CORE"] = float(
                tampered["projectedHoldingsMinor"]["BOND_CORE"]
            )
        elif corruption == "total-float":
            tampered["projectedInvestmentMinor"] = float(tampered["projectedInvestmentMinor"])
        else:
            tampered["allocationsMinor"]["BOND_CORE"] = float(
                tampered["allocationsMinor"]["BOND_CORE"]
            )
        result = _consumer_result(manifest, request, tampered)
        assert result["standing"] == "UNSATISFIED", corruption
        rejected = evaluate_gate_results(manifest, [result])
        assert rejected["standing"] == "COMPOSITION_GATES_UNSATISFIED"
        assert rejected["mechanicalClosure"] is False
        assert rejected["domainAcceptanceEstablished"] is False
