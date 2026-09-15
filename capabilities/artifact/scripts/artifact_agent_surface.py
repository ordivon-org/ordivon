#!/usr/bin/env python3
"""Thin Agent-facing semantic surface over existing Artifact R1 CLIs.

The surface compiles bounded Artifact intent into exact Runtime-ready process plans.
It does not execute effects, invent a universal document model, or duplicate family
verifier semantics. Runtime remains physical execution authority.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifact-delivery"
TAXONOMY = ART / "taxonomy-v1.json"
PROFILE_MAPPING = ART / "shadow-v2/profile-v2-mapping-manifest-r1.json"
DONOR = ART / "donor-r1/manifest.json"
VERIFY = ROOT / "scripts/artifact_verify.py"
DELIVERY = ROOT / "scripts/artifact_delivery.py"
DOCTOR = ROOT / "scripts/artifact_delivery_toolchain_doctor.py"
ARTIFACT_PYTHON = Path(os.environ.get("ARTIFACT_PYTHON", "/root/.local/share/ordivon-workstation/artifact-delivery-python-v1/current/bin/python"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _service_profiles() -> list[str]:
    tree = ast.parse(VERIFY.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "ROUTES":
            value = ast.literal_eval(node.value)
            return sorted(str(x) for x in value)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ROUTES" for t in node.targets):
            value = ast.literal_eval(node.value)
            return sorted(str(x) for x in value)
    raise RuntimeError("Artifact verification ROUTES literal is unavailable")


def _plan(script: Path, args: list[str], *, postcondition: str) -> dict[str, Any]:
    ready = ARTIFACT_PYTHON.is_file() and script.is_file()
    return {
        "ready": ready,
        "blockers": [] if ready else (["ARTIFACT_PYTHON_ABSENT"] if not ARTIFACT_PYTHON.is_file() else ["ARTIFACT_SCRIPT_ABSENT"]),
        "plan": {
            "executable": str(ARTIFACT_PYTHON),
            "args": [str(script.relative_to(ROOT)), *args],
            "cwdRelative": ".",
            "executionTarget": "local_linux",
            "postcondition": postcondition,
        } if ready else None,
    }


def family_status(family_id: str | None = None) -> dict[str, Any]:
    taxonomy = _load_json(TAXONOMY)
    families = list(taxonomy.get("families", []))
    if family_id is not None:
        families = [x for x in families if x.get("id") == family_id]
        if not families:
            raise ValueError(f"unknown Artifact family: {family_id}")
    routed = set(_service_profiles())
    rows = []
    for family in families:
        profiles = list(family.get("currentProfiles", []))
        rows.append({
            "id": family.get("id"),
            "currentCoverage": family.get("currentCoverage"),
            "localToolStanding": family.get("localToolStanding"),
            "currentProfiles": profiles,
            "serviceRoutedProfiles": [p for p in profiles if p in routed],
            "exampleFormats": family.get("exampleFormats", []),
            "standards": family.get("standards", []),
        })
    return {
        "schemaVersion": 1,
        "kind": "ordivon.artifact-family-status",
        "truthRole": "artifact-taxonomy-and-verification-route-projection",
        "families": rows,
        "serviceProfileCount": len(routed),
        "boundary": "Taxonomy/profile presence and service routing are mechanical Artifact facts. They do not imply target acceptance, domain suitability, or support for every example format named by a family."
    }


COVERAGE_GATE_IDS = (
    "parse",
    "build",
    "structuralValidate",
    "semanticValidate",
    "nativeConsumerOpen",
    "nativeRender",
    "roundTripEdit",
    "deliveryReadback",
)


def _gate(status: str, *basis: str) -> dict[str, Any]:
    return {"status": status, "basis": [x for x in basis if x]}


def profile_coverage(profile_id: str | None = None, family_id: str | None = None) -> dict[str, Any]:
    """Project explicit profile contracts into a conservative eight-gate coverage matrix."""
    mapping = _load_json(PROFILE_MAPPING)
    donor = _load_json(DONOR)
    donor_by_id = {x["profileId"]: x for x in donor.get("profiles", [])}
    rows: list[dict[str, Any]] = []
    for item in mapping.get("mappings", []):
        if profile_id is not None and item.get("profileId") != profile_id:
            continue
        if family_id is not None and item.get("family") != family_id:
            continue
        value = _load_json(ROOT / str(item["mapped"]))
        evidence = value.get("requiredEvidence", {})
        authorities = list(value.get("targetAuthorities", []))
        outputs = list(value.get("outputs", []))
        purposes = set(value.get("classification", {}).get("purposes", []))
        native = [x for x in authorities if x.get("authorityClass") == "native-consumer" and x.get("required")]
        editable_declared = any(x.get("editable") is True for x in outputs) or any("editable" in str(x).lower() or "authoring" in str(x).lower() for x in purposes)
        structural_keys = [x for x in ("structural", "nativeDrc", "nativeSimulation", "profileSchema") if evidence.get(x, {}).get("required")]
        semantic_keys = [x for x in ("semantic", "boardContract", "measurements") if evidence.get(x, {}).get("required")]
        visual_required = bool(evidence.get("visual", {}).get("required"))
        target_required = bool(evidence.get("target", {}).get("required")) or bool(native)
        donor_row = donor_by_id.get(item["profileId"], {})
        binding = donor_row.get("capabilityBinding") or {}
        gates = {
            "parse": _gate("IMPLIED_BY_VALIDATION_CONTRACT", *structural_keys) if structural_keys else _gate("NOT_EXPLICITLY_MODELED"),
            "build": _gate("BUILD_ROUTE_DECLARED", item.get("sourceKind", "")) if item.get("sourceKind") == "production-v1" else _gate("VERIFY_OR_SOURCE_AUTHORITY_ONLY", item.get("sourceKind", "")),
            "structuralValidate": _gate("EXPLICIT_REQUIRED", *structural_keys) if structural_keys else _gate("NOT_EXPLICITLY_MODELED"),
            "semanticValidate": _gate("EXPLICIT_REQUIRED", *semantic_keys) if semantic_keys else _gate("NOT_EXPLICITLY_MODELED"),
            "nativeConsumerOpen": _gate("EXPLICIT_REQUIRED", *(str(x.get("name")) for x in native)) if target_required else _gate("NOT_EXPLICITLY_MODELED"),
            "nativeRender": _gate("EXPLICIT_REQUIRED", "visual", *(str(x.get("name")) for x in native)) if visual_required and target_required else (_gate("VISUAL_GATE_WITHOUT_NATIVE_RENDER_CONTRACT", "visual") if visual_required else _gate("NOT_EXPLICITLY_MODELED")),
            "roundTripEdit": _gate("EDITABLE_OUTPUT_DECLARED_BUT_ROUNDTRIP_GATE_UNMODELED", "editable output/purpose") if editable_declared else _gate("NOT_APPLICABLE_OR_UNDECLARED"),
            "deliveryReadback": _gate("EXPLICIT_REQUIRED", "deliveryReadback") if evidence.get("deliveryReadback", {}).get("required") else _gate("NOT_EXPLICITLY_MODELED"),
        }
        rows.append({
            "profileId": item["profileId"],
            "family": item["family"],
            "sourceKind": item.get("sourceKind"),
            "mappingValidation": item.get("validation"),
            "capabilityStanding": binding.get("standing", "NO_LIVE_BINDING_IN_DONOR"),
            "gates": gates,
        })
    if profile_id is not None and not rows:
        raise ValueError(f"unknown Artifact profile: {profile_id}")
    if family_id is not None and not rows:
        raise ValueError(f"unknown or empty Artifact family: {family_id}")
    summary = {gate_id: {} for gate_id in COVERAGE_GATE_IDS}
    for row in rows:
        for gate_id, gate_value in row["gates"].items():
            status = gate_value["status"]
            summary[gate_id][status] = summary[gate_id].get(status, 0) + 1
    return {
        "schemaVersion": 1,
        "kind": "ordivon.artifact-profile-coverage-matrix",
        "truthRole": "profile-contract-projection-not-occurrence-verdict",
        "profileCount": len(rows),
        "gateIds": list(COVERAGE_GATE_IDS),
        "summary": summary,
        "profiles": rows,
        "boundary": "This matrix projects what each current profile explicitly requires or declares. Contract presence, mapping validation, and LOCAL_LIVE_PROVEN capability never imply PASS for a particular artifact occurrence. Round-trip editing remains unproven unless a future profile defines and satisfies an explicit mutation/read-back gate.",
    }


def verify_proposal(request: str) -> dict[str, Any]:
    path = Path(request)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    blockers: list[str] = []
    profile_id = None
    if not path.is_file():
        blockers.append("REQUEST_ABSENT")
    else:
        try:
            value = _load_json(path)
            profile_id = value.get("profile", {}).get("id") if isinstance(value, dict) else None
        except Exception:
            blockers.append("REQUEST_JSON_UNREADABLE")
    routed = set(_service_profiles())
    if profile_id is not None and profile_id not in routed:
        blockers.append("PROFILE_NOT_SERVICE_ROUTED")
    base = _plan(VERIFY, [str(path)], postcondition="require artifact-verification-result status PASS and consume exact evidenceDirectory/service-result.json")
    blockers.extend(base["blockers"])
    ready = not blockers
    return {
        "schemaVersion": 1,
        "kind": "ordivon.artifact-operation-proposal",
        "operation": "verify",
        "profileId": profile_id,
        "ready": ready,
        "blockers": blockers,
        "plan": base["plan"] if ready else None,
        "boundary": "This compiles an existing verification request into the supported Artifact service entrypoint. Runtime executes it; the family verifier, not this surface, owns PASS semantics."
    }


def build_proposal(request: str, output_directory: str) -> dict[str, Any]:
    request_path = Path(request)
    if not request_path.is_absolute():
        request_path = (ROOT / request_path).resolve()
    out = Path(output_directory)
    if not out.is_absolute():
        out = (ROOT / out).resolve()
    blockers = [] if request_path.is_file() else ["REQUEST_ABSENT"]
    base = _plan(DELIVERY, ["build-request", str(request_path), "--output-directory", str(out)], postcondition="require Artifact build result PASS and independently continue profile-required target/visual/delivery gates")
    blockers.extend(base["blockers"])
    ready = not blockers
    return {
        "schemaVersion": 1,
        "kind": "ordivon.artifact-operation-proposal",
        "operation": "build",
        "ready": ready,
        "blockers": blockers,
        "plan": base["plan"] if ready else None,
        "boundary": "Build PASS does not imply target rendering, visual acceptance, accessibility, publication or delivery/read-back PASS unless the selected profile closes those gates separately."
    }


def doctor_proposal(output: str | None = None) -> dict[str, Any]:
    args: list[str] = []
    if output:
        args.extend(["--output", output])
    base = _plan(DOCTOR, args, postcondition="require toolchain doctor mechanical checks PASS; do not promote mechanical readiness to artifact acceptance")
    return {"schemaVersion": 1, "kind": "ordivon.artifact-operation-proposal", "operation": "toolchain-doctor", **base}


def cad_boundary_status() -> dict[str, Any]:
    taxonomy = _load_json(TAXONOMY)
    family = next(x for x in taxonomy["families"] if x.get("id") == "design-3d")
    profiles = list(family.get("currentProfiles", []))
    cad_profiles = [x for x in profiles if any(token in x.lower() for token in ("step", "ifc", "3mf", "cad", "bim"))]
    tools = {
        "blender": Path("/usr/bin/blender").is_file(),
        "freecad": Path("/usr/bin/freecad").is_file() or Path("/usr/bin/FreeCAD").is_file(),
        "openscadWindows": Path("/mnt/c/Program Files/OpenSCAD/openscad.exe").is_file(),
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.artifact-cad-admission-status",
        "graduated": bool(cad_profiles),
        "currentDesign3dProfiles": profiles,
        "currentCadProfiles": cad_profiles,
        "observedToolPresence": tools,
        "requiredNextEvidence": [
            "native parametric/BREP source authority from a mature CAD tool",
            "STEP or another selected CAD/manufacturing interchange profile with exact units/topology contract",
            "independent target-grade consumer/readback",
            "destructive negative proving invalid or contract-divergent geometry fails closed",
        ],
        "boundary": "Current GLB scene/mesh profiles are not CAD/BIM/manufacturing graduation. Tool presence is navigation only and does not create a profile or domain standing."
    }


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {"name": "artifact_family_status", "description": "Read Artifact families, current profiles and which profiles are actually routed through the verification service.", "inputSchema": {"type": "object", "properties": {"familyId": {"type": "string"}}, "additionalProperties": False}},
        {"name": "artifact_profile_coverage", "description": "Project current Artifact profiles into a conservative eight-gate contract matrix without claiming occurrence-level PASS.", "inputSchema": {"type": "object", "properties": {"profileId": {"type": "string"}, "familyId": {"type": "string"}}, "additionalProperties": False}},
        {"name": "artifact_verify_propose", "description": "Compile one exact Artifact verification request into the supported Runtime-ready verifier plan without executing it.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string", "minLength": 1}}, "required": ["request"], "additionalProperties": False}},
        {"name": "artifact_build_propose", "description": "Compile one exact Artifact build request into the supported Runtime-ready build plan without executing it.", "inputSchema": {"type": "object", "properties": {"request": {"type": "string", "minLength": 1}, "outputDirectory": {"type": "string", "minLength": 1}}, "required": ["request", "outputDirectory"], "additionalProperties": False}},
        {"name": "artifact_toolchain_doctor_propose", "description": "Compile the cross-format Artifact toolchain doctor into a Runtime-ready read/verification plan.", "inputSchema": {"type": "object", "properties": {"output": {"type": "string"}}, "additionalProperties": False}},
        {"name": "artifact_cad_admission_status", "description": "Read the explicit boundary between current GLB design-3D support and ungraduated CAD/BIM/manufacturing support.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    ]


def execute_surface_action(name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
    if name == "artifact_family_status":
        family_id = arguments.get("familyId")
        return family_status(str(family_id) if family_id is not None else None)
    if name == "artifact_profile_coverage":
        profile_id = arguments.get("profileId")
        family_id = arguments.get("familyId")
        return profile_coverage(
            str(profile_id) if profile_id is not None else None,
            str(family_id) if family_id is not None else None,
        )
    if name == "artifact_verify_propose":
        return verify_proposal(str(arguments["request"]))
    if name == "artifact_build_propose":
        return build_proposal(str(arguments["request"]), str(arguments["outputDirectory"]))
    if name == "artifact_toolchain_doctor_propose":
        value = arguments.get("output")
        return doctor_proposal(str(value) if value is not None else None)
    if name == "artifact_cad_admission_status":
        return cad_boundary_status()
    raise ValueError(f"unsupported Artifact Agent surface action: {name}")


def surface_projection() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.artifact-agent-tool-surface",
        "truthRole": "artifact-domain-semantic-actions",
        "domainId": "domain:ordivon-artifact",
        "revision": "artifact-agent-surface-r1",
        "tools": tool_definitions(),
        "runtimeOwnsPhysicalExecution": True,
        "harnessMayAdmitSubsetOnly": True,
        "mcpRequired": False,
        "boundary": "Artifact owns format/profile verification and build/delivery semantics. The surface compiles intent into existing CLI entrypoints; Runtime remains process authority and mature format/target tools remain format truth authorities."
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", nargs="?")
    ap.add_argument("--arguments", default="{}")
    args = ap.parse_args()
    if args.action is None:
        value = surface_projection()
    else:
        raw = json.loads(args.arguments)
        if not isinstance(raw, dict):
            raise ValueError("--arguments must decode to a JSON object")
        value = execute_surface_action(args.action, raw)
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
