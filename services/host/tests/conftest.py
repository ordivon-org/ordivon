from __future__ import annotations

import os

import psycopg
import pytest

from ordivon_host_v2 import HostV2


@pytest.fixture(scope="session")
def host_test_db_ready() -> None:
    """Qualify the real Host database only for selected DB-test consumers."""
    dsn = os.environ.get("ORDIVON_HOST_V2_TEST_DSN")
    if not dsn:
        pytest.skip("ORDIVON_HOST_V2_TEST_DSN not set")
    try:
        # Bind an explicit timeout so an unavailable DSN does not hang a test session.
        HostV2(psycopg.conninfo.make_conninfo(dsn, connect_timeout=5)).initialize()
    except (RuntimeError, psycopg.Error) as error:
        pytest.exit(f"HOST_TEST_DB_PREFLIGHT_FAILED: {error}", returncode=4)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--host-require-complete-suite",
        action="store_true",
        help="Reject incomplete evidence in the full Host qualification lane.",
    )


class _CompleteSuiteQualification:
    """Observe native pytest events; do not select, retry, or execute tests."""

    def __init__(self) -> None:
        self.deselected = 0
        self.collection_skips = 0
        self.incomplete_reports = 0
        self.passed: dict[str, set[str]] = {}

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected += len(items)

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.skipped:
            self.collection_skips += 1

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.skipped or hasattr(report, "wasxfail"):
            self.incomplete_reports += 1
        elif report.passed:
            self.passed.setdefault(report.nodeid, set()).add(report.when)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        expected = {item.nodeid for item in session.items}
        complete = {
            key for key, phases in self.passed.items() if {"setup", "call", "teardown"} <= phases
        }
        if (
            not expected
            or expected != complete
            or self.deselected
            or self.collection_skips
            or self.incomplete_reports
        ):
            # Preserve native failures, interrupts, collection errors, and no-tests.
            if exitstatus == pytest.ExitCode.OK:
                session.exitstatus = pytest.ExitCode.TESTS_FAILED
            terminal = session.config.pluginmanager.get_plugin("terminalreporter")
            if terminal is not None:
                terminal.write_line(
                    "HOST_COMPLETE_SUITE_INCOMPLETE: "
                    f"selected={len(expected)} complete={len(complete)} "
                    f"deselected={self.deselected} collection_skips={self.collection_skips} "
                    f"incomplete_reports={self.incomplete_reports}"
                )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--host-require-complete-suite"):
        config.pluginmanager.register(_CompleteSuiteQualification(), "host-complete-suite")
