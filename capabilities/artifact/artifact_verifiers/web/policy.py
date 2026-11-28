"""Pure projection of subject-bound browser evidence onto required gates."""

from __future__ import annotations

from typing import Any


def assess_browser_report(
    report: Any, profile: dict[str, Any], subject_sha256: str
) -> dict[str, Any]:
    issues: list[str] = []
    report = report if isinstance(report, dict) else {}
    output = report.get("verifierOutput")
    output = output if isinstance(output, dict) else {}
    subject = output.get("subject")
    if (
        report.get("digestBound") is not True
        or type(report.get("exitCode")) is not int
        or report["exitCode"] != 0
        or output.get("schemaVersion") != 1
        or output.get("kind") != "artifact-web-local-verification-evidence"
        or not isinstance(subject, dict)
        or subject.get("sha256") != subject_sha256
        or report.get("status") not in ("PASS", "FAIL")
        or output.get("status") != report.get("status")
    ):
        issues.append("browser report transport or subject identity is unqualified")
    browsers = output.get("browsers")
    if not isinstance(browsers, dict):
        issues.append("browser results are absent or malformed")
        browsers = {}
    by_name: dict[str, dict[str, Any]] = {}
    for key, item in browsers.items():
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            issues.append("malformed browser result")
            continue
        name = item["name"]
        if name in by_name or key != name.lower():
            issues.append(f"ambiguous browser identity: {name}")
        by_name[name] = item
    required = []
    for item in [profile.get("targetRenderer", {}), *profile.get("secondaryRenderers", [])]:
        if item.get("required") is True:
            required.append(item.get("name"))
    if not required or any(not isinstance(n, str) or not n for n in required):
        issues.append("required renderer policy is absent or malformed")
    chromium = by_name.get("Chromium", {})
    accessibility = chromium.get("accessibility")
    if (
        not isinstance(accessibility, dict)
        or accessibility.get("status") not in ("PASS", "FAIL")
        or type(accessibility.get("violationCount")) is not int
        or accessibility["violationCount"] < 0
        or (accessibility["status"] == "PASS") != (accessibility["violationCount"] == 0)
    ):
        accessibility = {}
    # Engine launch/load errors are operational observations, not independent
    # falsification of the HTML. Only a qualified axe violation is negative
    # accessibility evidence. All required engines must actually report PASS.
    target = "UNKNOWN"
    access = "UNKNOWN"
    if not issues:
        if all(by_name.get(n, {}).get("status") == "PASS" for n in required):
            target = "PASS"
        if chromium.get("status") == "PASS":
            access = accessibility.get("status", "UNKNOWN")
    tooling = output.get("tooling")
    tooling = tooling if isinstance(tooling, dict) else {}
    return {
        "target": target,
        "accessibility": access,
        "requiredRenderers": required,
        "browserResults": by_name,
        "issues": issues,
        "tooling": tooling,
    }
