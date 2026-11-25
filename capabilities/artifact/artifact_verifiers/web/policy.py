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


def assess_browser_providers(
    reports: dict[str, Any],
    assignment: dict[str, str],
    profile: dict[str, Any],
    subject_sha256: str,
    expected_tooling: dict[str, str],
) -> dict[str, Any]:
    """Project explicitly selected native observations, not provider admission.

    The caller supplies the provider assignment, exact subject and expected
    method versions. Do not infer fallback from successful observations.
    Keep original reports including unselected failures. This is a pure
    diagnostic consumer; no VSA, isolation, or delivery authority is granted.
    """
    issues: list[str] = []
    required = [
        item.get("name")
        for item in [profile.get("targetRenderer", {}), *profile.get("secondaryRenderers", [])]
        if item.get("required") is True
    ]
    names = {"Chromium", "Firefox", "WebKit"}
    if (
        not required
        or any(not isinstance(n, str) or n not in names for n in required)
        or len(set(required)) != len(required)
        or set(assignment) != set(required)
        or any(not isinstance(p, str) or not p for p in assignment.values())
        or set(reports) != set(assignment.values())
    ):
        issues.append("explicit required renderer assignment is incomplete or ambiguous")
    methods = ("playwright", "axePlaywright")
    if any(
        not isinstance(expected_tooling.get(k), str) or not expected_tooling[k] for k in methods
    ):
        issues.append("expected method versions are unqualified")

    qualified: dict[str, dict[str, Any]] = {}
    for provider, report in reports.items():
        decision = assess_browser_report(report, profile, subject_sha256)
        if decision["issues"]:
            issues.extend(f"{provider}: {issue}" for issue in decision["issues"])
            continue
        if any(decision["tooling"].get(k) != expected_tooling.get(k) for k in methods):
            issues.append(f"{provider}: method version mismatch")
            continue
        qualified[provider] = decision

    selected: dict[str, Any] = {}
    if not issues:
        for name in required:
            result = qualified[assignment[name]]["browserResults"].get(name, {})
            if (
                result.get("status") == "PASS"
                and all(
                    isinstance(result.get(k), str) and result[k] for k in ("version", "executable")
                )
                and isinstance(result.get("title"), str)
                and type(result.get("headingCount")) is int
                and result["headingCount"] >= 0
            ):
                selected[name] = result
            else:
                issues.append(f"{assignment[name]}: {name} observation unavailable or malformed")
    target = "PASS" if not issues else "UNKNOWN"
    accessibility = "UNKNOWN"
    if "Chromium" in selected:
        decision = qualified[assignment["Chromium"]]
        axe = selected["Chromium"].get("accessibility")
        if (
            isinstance(axe, dict)
            and isinstance(axe.get("violations"), list)
            and len(axe["violations"]) == axe.get("violationCount")
        ):
            accessibility = decision["accessibility"]
    return {
        "targetObservation": target,
        "accessibilityObservation": accessibility,
        "requiredRenderers": required,
        "providerAssignment": dict(assignment),
        "providerReports": reports,
        "browserResults": selected,
        "issues": issues,
        "tooling": dict(expected_tooling),
        "providerQualification": "NOT_ESTABLISHED",
    }
