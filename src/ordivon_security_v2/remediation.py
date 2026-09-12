from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _package_vulnerabilities(report: dict[str, Any], package: str) -> dict[str, dict[str, Any]]:
    findings: dict[str, dict[str, Any]] = {}
    for result in report.get("Results") or []:
        for vulnerability in result.get("Vulnerabilities") or []:
            if vulnerability.get("PkgName") != package:
                continue
            vuln_id = vulnerability.get("VulnerabilityID")
            if not isinstance(vuln_id, str) or not vuln_id:
                raise ValueError("Trivy vulnerability has no VulnerabilityID")
            if vuln_id in findings:
                raise ValueError(f"duplicate vulnerability identity: {vuln_id}")
            findings[vuln_id] = vulnerability
    return findings


def verify_remediation_delta(
    *,
    package: str,
    before_sbom_path: Path,
    before_report_path: Path,
    after_sbom_path: Path,
    after_report_path: Path,
) -> dict[str, Any]:
    if not package:
        raise ValueError("package is required")
    before_sbom_digest = _digest(before_sbom_path)
    after_sbom_digest = _digest(after_sbom_path)
    if before_sbom_digest == after_sbom_digest:
        raise ValueError("remediation requires fresh changed SBOM evidence")

    before = json.loads(before_report_path.read_text())
    after = json.loads(after_report_path.read_text())
    if before.get("ArtifactType") != "cyclonedx" or after.get("ArtifactType") != "cyclonedx":
        raise ValueError("remediation verification requires Trivy CycloneDX-SBOM reports")

    before_findings = _package_vulnerabilities(before, package)
    after_findings = _package_vulnerabilities(after, package)
    if not before_findings:
        raise ValueError("no baseline vulnerabilities exist for requested package")

    uncleared = sorted(set(before_findings) & set(after_findings))
    if uncleared:
        raise ValueError("baseline vulnerabilities remain after remediation: " + ", ".join(uncleared))

    before_versions = sorted({str(item.get("InstalledVersion")) for item in before_findings.values()})
    after_versions = sorted({str(item.get("InstalledVersion")) for item in after_findings.values()})
    return {
        "standing": "BASELINE_VULNERABILITIES_CLEARED_ON_FRESH_EVIDENCE",
        "package": package,
        "clearedVulnerabilityIds": sorted(before_findings),
        "clearedCount": len(before_findings),
        "newOrRemainingAfterCount": len(after_findings),
        "beforeObservedVersions": before_versions,
        "afterVulnerableVersions": after_versions,
        "beforeSbomSha256": before_sbom_digest,
        "afterSbomSha256": after_sbom_digest,
        "beforeReportSha256": _digest(before_report_path),
        "afterReportSha256": _digest(after_report_path),
    }
