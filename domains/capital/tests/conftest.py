"""Admission before any Finance test module collection or native test effect."""

import os
import sys

import pytest
from pg_test_lease import LeaseError, verify_leases


def pytest_sessionstart(session):
    if sys.flags.optimize:
        pytest.exit("Capital verification requires enabled Python assertions", returncode=2)
    try:
        verify_leases(os.environ)
    except LeaseError as exc:
        pytest.exit(str(exc), returncode=2)


# Native acceptance requires every selected test's three real phase reports.
# The report hook is independent of pytest's textual summaries and subtests.
_PHASES = pytest.StashKey[dict[str, bool]]()
_COMPLETE = "ORDIVON_CAPITAL_REQUIRE_COMPLETE_TESTS"


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    if os.environ.get(_COMPLETE) == "1":
        phases = item.stash.setdefault(_PHASES, {})
        phases[report.when] = report.passed and not hasattr(report, "wasxfail")
    return report


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get(_COMPLETE) != "1" or exitstatus != 0:
        return
    expected = {"setup": True, "call": True, "teardown": True}
    incomplete = [item.nodeid for item in session.items if item.stash.get(_PHASES, {}) != expected]
    if not session.items or incomplete:
        print(
            f"CAPITAL_REQUIRED_TESTS_INCOMPLETE selected={len(session.items)} "
            f"incomplete={len(incomplete)} examples={incomplete[:5]}",
            file=sys.stderr,
        )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
