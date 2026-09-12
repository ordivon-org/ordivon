from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

_ALLOWED_STATES = {
    "resolved",
    "resolved_with_pedigree",
    "exploitable",
    "in_triage",
    "false_positive",
    "not_affected",
}
_ALLOWED_JUSTIFICATIONS = {
    "code_not_present",
    "code_not_reachable",
    "requires_configuration",
    "requires_dependency",
    "requires_environment",
    "protected_by_compiler",
    "protected_at_runtime",
    "protected_at_perimeter",
    "protected_by_mitigating_control",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _uuid_from_serial(serial: str) -> str:
    prefix = "urn:uuid:"
    if not isinstance(serial, str) or not serial.startswith(prefix) or len(serial) <= len(prefix):
        raise ValueError("SBOM serialNumber must be urn:uuid:<uuid>")
    return serial[len(prefix):]


def bom_link(*, sbom_serial: str, sbom_version: int, bom_ref: str) -> str:
    if not isinstance(sbom_version, int) or isinstance(sbom_version, bool) or sbom_version < 1:
        raise ValueError("SBOM version must be a positive integer")
    if not isinstance(bom_ref, str) or not bom_ref:
        raise ValueError("bom-ref is required")
    # CycloneDX BOM-Link uses the BOM serial UUID/version plus URI fragment. Keep the
    # provider bom-ref exact while escaping characters that are not safe in a fragment.
    return f"urn:cdx:{_uuid_from_serial(sbom_serial)}/{sbom_version}#{quote(bom_ref, safe=':@/?=&+,$;') }"


def sbom_component_links(sbom: dict[str, Any]) -> set[str]:
    serial = sbom.get("serialNumber")
    version = sbom.get("version")
    components = sbom.get("components")
    if sbom.get("bomFormat") != "CycloneDX" or sbom.get("specVersion") != "1.7":
        raise ValueError("expected a CycloneDX 1.7 SBOM")
    if not isinstance(components, list):
        raise ValueError("SBOM components must be an array")
    links: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("SBOM component must be an object")
        ref = component.get("bom-ref")
        if not isinstance(ref, str) or not ref:
            raise ValueError("every SBOM component must have bom-ref")
        link = bom_link(sbom_serial=serial, sbom_version=version, bom_ref=ref)
        if link in links:
            raise ValueError("duplicate SBOM component BOM-Link")
        links.add(link)
    return links


def validate_vex_against_sbom(vex: dict[str, Any], sbom: dict[str, Any]) -> dict[str, Any]:
    if vex.get("bomFormat") != "CycloneDX" or vex.get("specVersion") != "1.7":
        raise ValueError("expected a CycloneDX 1.7 VEX document")
    vulnerabilities = vex.get("vulnerabilities")
    if not isinstance(vulnerabilities, list) or not vulnerabilities:
        raise ValueError("VEX must contain at least one vulnerability")
    valid_links = sbom_component_links(sbom)
    seen_ids: set[str] = set()
    summaries: list[dict[str, Any]] = []
    for vulnerability in vulnerabilities:
        if not isinstance(vulnerability, dict):
            raise ValueError("VEX vulnerability must be an object")
        vuln_id = vulnerability.get("id")
        if not isinstance(vuln_id, str) or not vuln_id:
            raise ValueError("VEX vulnerability id is required")
        if vuln_id in seen_ids:
            raise ValueError(f"duplicate VEX vulnerability id: {vuln_id}")
        seen_ids.add(vuln_id)
        analysis = vulnerability.get("analysis")
        if not isinstance(analysis, dict):
            raise ValueError(f"VEX analysis is required: {vuln_id}")
        state = analysis.get("state")
        if state not in _ALLOWED_STATES:
            raise ValueError(f"unsupported VEX analysis state for {vuln_id}: {state}")
        justification = analysis.get("justification")
        detail = analysis.get("detail")
        if justification is not None and justification not in _ALLOWED_JUSTIFICATIONS:
            raise ValueError(f"unsupported VEX justification for {vuln_id}: {justification}")
        if state == "not_affected":
            if justification not in _ALLOWED_JUSTIFICATIONS:
                raise ValueError(f"not_affected requires a recognized justification: {vuln_id}")
            if not isinstance(detail, str) or not detail.strip():
                raise ValueError(f"not_affected requires specific analysis detail: {vuln_id}")
        affects = vulnerability.get("affects")
        if not isinstance(affects, list) or not affects:
            raise ValueError(f"VEX affects is required: {vuln_id}")
        refs: list[str] = []
        for affected in affects:
            if not isinstance(affected, dict) or not isinstance(affected.get("ref"), str):
                raise ValueError(f"VEX affects.ref is required: {vuln_id}")
            ref = affected["ref"]
            if ref not in valid_links:
                raise ValueError(f"VEX affects.ref does not bind an exact SBOM component: {ref}")
            refs.append(ref)
        summaries.append({
            "id": vuln_id,
            "state": state,
            "justification": justification,
            "response": analysis.get("response", []),
            "affects": sorted(refs),
        })
    return {
        "standing": "VEX_BOUND_TO_EXACT_SBOM_COMPONENTS",
        "vulnerabilityCount": len(summaries),
        "vulnerabilities": sorted(summaries, key=lambda item: item["id"]),
    }


def load_and_validate_vex(vex_path: Path, sbom_path: Path) -> dict[str, Any]:
    vex = json.loads(vex_path.read_text())
    sbom = json.loads(sbom_path.read_text())
    result = validate_vex_against_sbom(vex, sbom)
    result["vexSha256"] = _sha256(vex_path)
    result["sbomSha256"] = _sha256(sbom_path)
    return result
