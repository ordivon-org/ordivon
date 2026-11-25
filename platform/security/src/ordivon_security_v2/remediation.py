from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, TypedDict

from .evidence import read_json_evidence


class ReportDelta(TypedDict):
    standing: Literal["BASELINE_VULNERABILITY_IDS_ABSENT_IN_SUPPLIED_REPORTS"]
    scanInputBinding: Literal["UNKNOWN"]
    authenticated: Literal[False]
    package: str
    clearedVulnerabilityIds: list[str]
    clearedCount: int
    newOrRemainingAfterCount: int
    beforeObservedVersions: list[str]
    afterVulnerableVersions: list[str]
    beforeSbomSha256: str
    afterSbomSha256: str
    beforeReportSha256: str
    afterReportSha256: str


def _digest(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


def _package_vulnerabilities(report: dict[str, Any], package: str) -> dict[str, dict[str, Any]]:
    findings: dict[str, dict[str, Any]] = {}
    results = report.get("Results")
    if not isinstance(results, list):
        raise ValueError("Trivy Results must be an explicit array for this evidence profile")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Trivy result must be an object")
        vulnerabilities = result.get("Vulnerabilities")
        if vulnerabilities is None:
            continue
        if not isinstance(vulnerabilities, list):
            raise ValueError("Trivy Vulnerabilities must be an array")
        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                raise ValueError("Trivy vulnerability must be an object")
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
) -> ReportDelta:
    """Compare supplied reports; changed SBOM bytes do not prove scan-input binding.

    A native producer receipt and independently qualified scanner coverage are
    required before this observation can become a remediation acceptance.
    """
    if not package:
        raise ValueError("package is required")
    before_sbom_digest = _digest(before_sbom_path)
    after_sbom_digest = _digest(after_sbom_path)
    if before_sbom_digest == after_sbom_digest:
        raise ValueError("remediation requires fresh changed SBOM evidence")

    before, before_report_digest = read_json_evidence(before_report_path)
    after, after_report_digest = read_json_evidence(after_report_path)
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
        "standing": "BASELINE_VULNERABILITY_IDS_ABSENT_IN_SUPPLIED_REPORTS",
        "scanInputBinding": "UNKNOWN",
        "authenticated": False,
        "package": package,
        "clearedVulnerabilityIds": sorted(before_findings),
        "clearedCount": len(before_findings),
        "newOrRemainingAfterCount": len(after_findings),
        "beforeObservedVersions": before_versions,
        "afterVulnerableVersions": after_versions,
        "beforeSbomSha256": before_sbom_digest,
        "afterSbomSha256": after_sbom_digest,
        "beforeReportSha256": before_report_digest,
        "afterReportSha256": after_report_digest,
    }
