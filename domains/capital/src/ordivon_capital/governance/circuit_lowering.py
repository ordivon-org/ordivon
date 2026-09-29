from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ordivon_composition import (
    canonical_digest,
    compile_authority_obligations,
    compile_manifest,
)

ROOT = Path(__file__).resolve().parents[3]
SPEC_SCHEMA = ROOT / "schema/capital-financial-circuit-spec-v2.schema.json"


class FinancialCircuitError(ValueError):
    """Fail-closed Capital-specific lowering error."""


def _load(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text())
    if not isinstance(value, dict):
        raise FinancialCircuitError(f"expected JSON object: {relative}")
    return value


def _file_ref(relative: str) -> dict[str, str]:
    path = ROOT / relative
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return {"id": f"capital:{relative}", "digest": digest}


def _validate_spec(spec: dict[str, Any]) -> None:
    required = {
        "schemaVersion", "kind", "circuitId", "goalClass", "requestedUse",
        "terminalClaim", "stages", "authorityBindings",
    }
    if set(spec) != required:
        raise FinancialCircuitError(
            f"financial circuit spec fields mismatch: expected {sorted(required)}, got {sorted(spec)}"
        )
    if spec["schemaVersion"] != 2 or spec["kind"] != "ordivon.capital.financial-circuit-spec":
        raise FinancialCircuitError("financial circuit spec identity mismatch")
    for key in ("circuitId", "goalClass", "requestedUse", "terminalClaim"):
        if not isinstance(spec[key], str) or not spec[key].strip():
            raise FinancialCircuitError(f"financial circuit spec {key} must be non-empty string")
    if not isinstance(spec["stages"], list) or not spec["stages"]:
        raise FinancialCircuitError("financial circuit spec requires stages")
    if not isinstance(spec["authorityBindings"], list):
        raise FinancialCircuitError("financial circuit authorityBindings must be an array")
    ids: list[str] = []
    for stage in spec["stages"]:
        if not isinstance(stage, dict) or set(stage) != {"id", "legoId", "operation", "dependsOn", "inputs", "outputs"}:
            raise FinancialCircuitError("financial circuit stage shape mismatch")
        for key in ("id", "legoId", "operation"):
            if not isinstance(stage[key], str) or not stage[key]:
                raise FinancialCircuitError(f"financial circuit stage {key} must be non-empty string")
        for key in ("dependsOn", "inputs", "outputs"):
            if not isinstance(stage[key], list) or any(not isinstance(v, str) or not v for v in stage[key]):
                raise FinancialCircuitError(f"financial circuit stage {key} must be string array")
        if not stage["outputs"]:
            raise FinancialCircuitError("financial circuit stage requires at least one output")
        ids.append(stage["id"])
    if len(ids) != len(set(ids)):
        raise FinancialCircuitError("duplicate financial circuit stage id")
    known = set(ids)
    for stage in spec["stages"]:
        missing = sorted(set(stage["dependsOn"]) - known)
        if missing:
            raise FinancialCircuitError(f"{stage['id']}: unknown dependencies: {missing}")
        if stage["id"] in stage["dependsOn"]:
            raise FinancialCircuitError(f"{stage['id']}: self dependency")
    seen_authorities: set[str] = set()
    for binding in spec["authorityBindings"]:
        if not isinstance(binding, dict) or set(binding) != {"authorityClass", "authorityOwnerId", "contractPath"}:
            raise FinancialCircuitError("financial circuit authority binding shape mismatch")
        if any(not isinstance(binding[k], str) or not binding[k] for k in binding):
            raise FinancialCircuitError("financial circuit authority binding values must be non-empty strings")
        authority = binding["authorityClass"]
        if authority in seen_authorities:
            raise FinancialCircuitError(f"duplicate authority binding: {authority}")
        seen_authorities.add(authority)


def _normalize_use(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value not in out:
            out.append(value)
    return out


def _graph(stages: list[dict[str, Any]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    deps = {row["id"]: set(row["dependsOn"]) for row in stages}
    children = {row["id"]: set() for row in stages}
    for stage, parents in deps.items():
        for parent in parents:
            children[parent].add(stage)
    return deps, children


def _reach(start: str, graph: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = list(graph[start])
    while stack:
        item = stack.pop()
        if item in seen:
            continue
        seen.add(item)
        stack.extend(graph[item])
    return seen


def lower_financial_circuit(spec: Mapping[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(dict(spec), sort_keys=True))
    _validate_spec(value)
    registry = _load("config/capital_lego_registry.json")
    rows = {row["legoId"]: row for row in registry["entries"]}
    authority_catalog = _load("contracts/capital-authority-requirement-v1.json")
    effect_catalog = _load("contracts/capital-effect-class-v1.json")
    evidence_catalog = _load("contracts/capital-evidence-obligation-v1.json")
    production = _load("contracts/production-authorization.json")
    authority_bindings = {row["authorityClass"]: row for row in value["authorityBindings"]}
    requested_use = _normalize_use(value["requestedUse"])
    lego_ids = [stage["legoId"] for stage in value["stages"]]
    if len(lego_ids) != len(set(lego_ids)):
        raise FinancialCircuitError("R2 financial circuit rejects duplicate LEGO identities")

    enriched: list[tuple[dict[str, Any], dict[str, Any]]] = []
    evidence: list[str] = []
    effects: list[str] = []
    for stage in value["stages"]:
        row = rows.get(stage["legoId"])
        if row is None:
            raise FinancialCircuitError(f"unregistered LEGO: {stage['legoId']}")
        if row["status"] == "RETIRED":
            raise FinancialCircuitError(f"{stage['legoId']}: retired LEGO cannot compose")
        if row["status"] == "CHALLENGER":
            raise FinancialCircuitError(f"{stage['legoId']}: challenger cannot enter canonical R2 circuit")
        if row["status"] == "BLOCKED_BY_AUTHORITY":
            raise FinancialCircuitError(f"{stage['legoId']}: blocked by independent authority/currentness")
        for prohibited in row["prohibitedUses"]:
            if requested_use and _normalize_use(prohibited) == requested_use:
                raise FinancialCircuitError(
                    f"{stage['legoId']}: requested use is explicitly prohibited: {value['requestedUse']}"
                )
        auth = row["authorityRequirement"]
        if auth not in authority_catalog["classes"]:
            raise FinancialCircuitError(f"unknown financial authority class: {auth}")
        if auth != "NONE":
            meta = authority_catalog["classes"][auth]
            if meta["currentAdmission"] is False:
                raise FinancialCircuitError(f"{stage['legoId']}: authority class {auth} is not currently admitted")
            if auth not in authority_bindings:
                raise FinancialCircuitError(f"{stage['legoId']}: missing exact authority binding for {auth}")
        effect = row["effectClass"]
        if effect not in effect_catalog["classes"]:
            raise FinancialCircuitError(f"unknown financial effect class: {effect}")
        if effect not in {"NONE", "LOCAL_STATE"} and effect not in effects:
            effects.append(effect)
        obligations = [*row["evidenceObligations"]]
        for role in row["functionalRoles"]:
            obligations.extend(evidence_catalog["byFunctionalRole"][role])
        obligations.extend(evidence_catalog["byEffectClass"][effect])
        evidence.extend(obligations)
        enriched.append((stage, row))

    deps, children = _graph(value["stages"])
    stage_rows = {stage["id"]: row for stage, row in enriched}
    for stage, row in enriched:
        effect = row["effectClass"]
        if effect in {"NONE", "LOCAL_STATE"}:
            continue
        meta = effect_catalog["classes"][effect]
        if effect == "PRODUCTION_FINANCIAL_WRITE" and (
            production["state"] != "ADMITTED" or production["externalFinancialWriteAllowed"] is not True
        ):
            raise FinancialCircuitError("production financial write is not authorized")
        ancestors = _reach(stage["id"], deps)
        descendants = _reach(stage["id"], children)
        if meta["requiresReservation"] and not any(
            "Reserve" in stage_rows[s]["functionalRoles"] for s in ancestors
        ):
            raise FinancialCircuitError(f"{effect}: Reserve LEGO must be an ancestor of provider effect")
        if meta["requiresReconciliation"] and not any(
            "Reconcile" in stage_rows[s]["functionalRoles"] for s in descendants
        ):
            raise FinancialCircuitError(f"{effect}: downstream Reconcile LEGO is required")
        if meta["requiresAccountingResolution"] and not any(
            "Account" in stage_rows[s]["functionalRoles"] for s in descendants
        ):
            raise FinancialCircuitError(f"{effect}: downstream Account LEGO is required")

    capabilities: list[dict[str, Any]] = []
    generic_stages: list[dict[str, Any]] = []
    for stage, row in enriched:
        binding_id = f"capability:{stage['id']}"
        capabilities.append({
            "id": binding_id,
            "capability": row["legoId"],
            "ownerId": f"capital.{row['ownerDomain']}",
            "sourceKind": "direct-owner",
            "bindingDigest": canonical_digest(row),
            "truthBoundary": (
                f"Capital {row['ownerDomain']} LEGO mechanics only; this binding does not establish "
                "provider reality, financial authority, or domain acceptance."
            ),
        })
        generic_stages.append({
            "id": stage["id"],
            "ownerId": f"capital.{row['ownerDomain']}",
            "responsibility": f"{row['legoId']} financial owner-native stage",
            "dependsOn": list(stage["dependsOn"]),
            "methodBindings": [],
            "capabilityBindings": [binding_id],
            "inputs": list(stage["inputs"]),
            "outputs": list(stage["outputs"]),
        })

    by_stage = {row["id"]: row for row in generic_stages}
    edges: list[dict[str, Any]] = []
    gates: list[dict[str, Any]] = []
    for consumer in generic_stages:
        for producer_id in consumer["dependsOn"]:
            producer = by_stage[producer_id]
            shared = [p for p in producer["outputs"] if p in consumer["inputs"]]
            if not shared:
                raise FinancialCircuitError(
                    f"{producer_id}->{consumer['id']}: no shared typed port between dependency stages"
                )
            port = shared[0]
            edge_id = f"edge:{producer_id}:{consumer['id']}:{port}"
            edges.append({
                "id": edge_id,
                "from": {"stageId": producer_id, "port": port},
                "to": {"stageId": consumer["id"], "port": port},
                "contractRef": None,
            })
            if producer["ownerId"] != consumer["ownerId"]:
                gates.append({
                    "id": f"gate:{producer_id}:{consumer['id']}",
                    "producerStageId": producer_id,
                    "consumerStageId": consumer["id"],
                    "assumption": "consumer accepts the exact producer-bound financial output contract",
                    "guarantee": "producer output remains bound to its Capital LEGO owner and circuit identity",
                    "verifierOwnerId": "capital.governance",
                    "supportScope": "capital-financial-interface-binding",
                    "required": True,
                })

    spec_digest = canonical_digest(value)
    manifest = {
        "schemaVersion": 1,
        "kind": "ordivon.cognitive-circuit-manifest",
        "circuitId": value["circuitId"],
        "objectiveRef": {"id": f"capital.goal:{value['goalClass']}", "digest": spec_digest},
        "methodBindings": [],
        "capabilityBindings": capabilities,
        "stages": generic_stages,
        "edges": edges,
        "gateRequirements": gates,
        "unresolvedAssumptions": [],
        "nonClaims": [
            "Mechanical circuit compilation is not Capital domain acceptance.",
            "Capability binding does not grant provider, credential, execution, or financial authority.",
            "Capital financial truth remains with provider/domain/accounting authorities, not Composition.",
        ],
    }
    compiled = compile_manifest(manifest)

    requirements: list[dict[str, Any]] = []
    for stage, row in enriched:
        auth = row["authorityRequirement"]
        if auth == "NONE":
            continue
        binding = authority_bindings[auth]
        requirements.append({
            "id": f"authority:{stage['id']}:{auth.lower()}",
            "stageId": stage["id"],
            "capabilityBindingId": f"capability:{stage['id']}",
            "authorityOwnerId": binding["authorityOwnerId"],
            "authorityContractRef": _file_ref(binding["contractPath"]),
            "required": True,
            "nonClaims": [
                f"Binding {auth} records a Capital authority prerequisite; it is not an ALLOW decision.",
            ],
        })
    requirement_set = {
        "schemaVersion": 1,
        "kind": "ordivon.authority-requirement-set",
        "circuitRef": {"id": manifest["circuitId"], "digest": compiled["manifestDigest"]},
        "requirements": requirements,
        "nonClaims": [
            "Capital authored these financial authority requirements; shared Composition does not infer effect coverage.",
        ],
    }
    authority_obligations = compile_authority_obligations(manifest, requirement_set)

    projection = {
        "schemaVersion": 2,
        "kind": "ordivon.capital.financial-circuit-lowering",
        "standing": "FINANCIAL_SEMANTICS_ADMITTED_MECHANICAL_COMPOSITION_COMPILED",
        "financialSpecDigest": spec_digest,
        "circuitId": value["circuitId"],
        "goalClass": value["goalClass"],
        "requestedUse": value["requestedUse"],
        "terminalClaim": value["terminalClaim"],
        "legoIds": [stage["legoId"] for stage in value["stages"]],
        "effectClasses": effects,
        "unresolvedEvidenceObligations": _dedupe(evidence),
        "sharedManifest": manifest,
        "sharedCompiled": compiled,
        "authorityRequirementSet": requirement_set,
        "authorityObligations": authority_obligations,
        "authorityGranted": False,
        "executionPerformed": False,
        "semanticCompletionEvaluated": False,
    }
    projection["loweringDigest"] = canonical_digest(projection)
    return projection


def load_and_lower(relative: str) -> dict[str, Any]:
    return lower_financial_circuit(_load(relative))
