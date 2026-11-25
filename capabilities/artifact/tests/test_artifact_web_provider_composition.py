"""Exact engine observations, never automatic fallback or provider qualification."""

from copy import deepcopy

import pytest

from artifact_verifiers.web import policy

SHA = "a" * 64
TOOLING = {"playwright": "1.64.1", "axePlaywright": "4.14.0"}
PROFILE = {
    "targetRenderer": {"name": "Chromium", "required": True},
    "secondaryRenderers": [
        {"name": "Firefox", "required": True},
        {"name": "WebKit", "required": True},
    ],
}
ASSIGNMENT = {"Chromium": "oci", "Firefox": "host", "WebKit": "oci"}


def report(*, failed):
    browsers = {
        key: {
            "name": name,
            "status": "PASS",
            "version": "1.2.3",
            "executable": "/browser",
            "title": "fixture",
            "headingCount": 1,
        }
        for key, name in (("chromium", "Chromium"), ("firefox", "Firefox"), ("webkit", "WebKit"))
    }
    browsers["chromium"]["accessibility"] = {
        "status": "PASS",
        "violationCount": 0,
        "violations": [],
    }
    browsers[failed] = {"name": browsers[failed]["name"], "status": "FAIL"}
    status = "FAIL" if failed == "firefox" else "PASS"
    return {
        "status": status,
        "digestBound": True,
        "exitCode": 0,
        "verifierOutput": {
            "schemaVersion": 1,
            "kind": "artifact-web-local-verification-evidence",
            "status": status,
            "subject": {"sha256": SHA},
            "tooling": TOOLING.copy(),
            "browsers": browsers,
        },
    }


def assess(reports, assignment=ASSIGNMENT):
    return policy.assess_browser_providers(reports, assignment, PROFILE, SHA, TOOLING)


def test_explicit_provider_selection_retains_unselected_failures():
    reports = {"host": report(failed="webkit"), "oci": report(failed="firefox")}
    value = assess(reports)
    assert value["targetObservation"] == value["accessibilityObservation"] == "PASS"
    assert value["providerAssignment"] == ASSIGNMENT
    assert value["providerReports"] == reports
    assert value["providerQualification"] == "NOT_ESTABLISHED"
    assert (
        value["providerReports"]["oci"]["verifierOutput"]["browsers"]["firefox"]["status"] == "FAIL"
    )


@pytest.mark.parametrize(
    "case",
    [
        "digest",
        "version",
        "transport",
        "missing_assignment",
        "wrong_engine",
        "malformed_native",
        "missing_tooling",
        "unused_provider",
    ],
)
def test_no_silent_fallback_or_unbound_provider(case):
    reports = {"host": report(failed="webkit"), "oci": report(failed="firefox")}
    assignment = deepcopy(ASSIGNMENT)
    if case == "digest":
        reports["host"]["verifierOutput"]["subject"]["sha256"] = "b" * 64
    elif case == "version":
        reports["host"]["verifierOutput"]["tooling"]["playwright"] = "0.0"
    elif case == "transport":
        reports["host"]["exitCode"] = 126
    elif case == "missing_assignment":
        assignment.pop("Firefox")
    elif case == "wrong_engine":
        assignment["Firefox"] = "oci"
        reports.pop("host")
    elif case == "malformed_native":
        reports["host"]["verifierOutput"]["browsers"]["firefox"].pop("version")
    elif case == "missing_tooling":
        reports["host"]["verifierOutput"].pop("tooling")
    elif case == "unused_provider":
        reports["other"] = report(failed="webkit")
    assert assess(reports, assignment)["targetObservation"] == "UNKNOWN"


def test_decisive_accessibility_is_independent_of_failed_engine():
    reports = {"host": report(failed="webkit"), "oci": report(failed="firefox")}
    reports["oci"]["verifierOutput"]["browsers"]["chromium"]["accessibility"] = {
        "status": "FAIL",
        "violationCount": 1,
        "violations": [{"id": "button-name"}],
    }
    result = assess(reports)
    assert result["targetObservation"] == "PASS" and result["accessibilityObservation"] == "FAIL"


def test_all_explicit_assignments_no_fallback():
    from itertools import product

    reports = {"host": report(failed="webkit"), "oci": report(failed="firefox")}
    engines = tuple(ASSIGNMENT)
    admitted = []
    for values in product(reports, repeat=len(engines)):
        assignment = dict(zip(engines, values, strict=True))
        selected_reports = {name: reports[name] for name in set(values)}
        result = assess(selected_reports, assignment)
        assert result["providerQualification"] == "NOT_ESTABLISHED"
        assert "target" not in result and "accessibility" not in result
        expected = assignment["Firefox"] == "host" and assignment["WebKit"] == "oci"
        assert (result["targetObservation"] == "PASS") is expected
        if expected:
            admitted.append(assignment)
    assert len(admitted) == 2


def test_malformed_axe_count_cannot_be_promoted():
    reports = {"host": report(failed="webkit"), "oci": report(failed="firefox")}
    reports["oci"]["verifierOutput"]["browsers"]["chromium"]["accessibility"]["violations"] = [
        {"id": "button-name"}
    ]
    result = assess(reports)
    assert result["targetObservation"] == "PASS"
    assert result["accessibilityObservation"] == "UNKNOWN"
