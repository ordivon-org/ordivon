from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

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
        self.discovered: Counter[str] = Counter()
        self.discovered_files: set[Path] = set()
        self.passed: dict[str, list[str]] = {}
        # The Host test root uses pytest's default Python file names.
        # This is a source obligation census, not a second test collector.
        root = Path(__file__).resolve().parent
        self.expected_files = {
            path.resolve()
            for pattern in ("test_*.py", "*_test.py")
            for path in root.rglob(pattern)
            if path.is_file()
        }

    def pytest_itemcollected(self, item: pytest.Item) -> None:
        # Native discovery occurs before the ordinary collection modifiers.
        self.discovered[item.nodeid] += 1
        self.discovered_files.add(item.path.resolve())

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected += len(items)

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if report.skipped:
            self.collection_skips += 1

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if not report.passed or hasattr(report, "wasxfail"):
            self.incomplete_reports += 1
            return
        # Native pytest subtests are additional evidence for their parent,
        # not another invocation of the parent's call phase.
        if isinstance(report, pytest.SubtestReport):
            return
        phases = self.passed.setdefault(report.nodeid, [])
        expected = ("setup", "call", "teardown")
        if len(phases) >= len(expected) or report.when != expected[len(phases)]:
            self.incomplete_reports += 1
            return
        phases.append(report.when)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        selected = Counter(item.nodeid for item in session.items)
        expected = set(selected)
        complete = {
            key for key, phases in self.passed.items() if phases == ["setup", "call", "teardown"]
        }
        inventory_mismatch = self.discovered != selected or any(
            count != 1 for count in selected.values()
        )
        missing_files = self.expected_files - self.discovered_files
        if (
            not expected
            or missing_files
            or inventory_mismatch
            or expected != complete
            or set(self.passed) != expected
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
                    f"selected={sum(selected.values())} complete={len(complete)} "
                    f"inventory_mismatch={inventory_mismatch} "
                    f"missing_files={len(missing_files)} "
                    f"deselected={self.deselected} collection_skips={self.collection_skips} "
                    f"incomplete_reports={self.incomplete_reports}"
                )
                root = Path(__file__).resolve().parent
                for path in sorted(missing_files):
                    terminal.write_line(
                        f"HOST_COMPLETE_SUITE_MISSING_FILE: {path.relative_to(root)}"
                    )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--host-require-complete-suite"):
        config.pluginmanager.register(_CompleteSuiteQualification(), "host-complete-suite")
