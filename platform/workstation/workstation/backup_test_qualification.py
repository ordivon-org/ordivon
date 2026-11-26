"""Explicit pytest plugin for the native backup recovery qualification lane.

Portable CI may skip these expensive platform tests. This lane must execute
both named obligations, including successful setup, call, and teardown.
"""
from __future__ import annotations

from collections import defaultdict

import pytest

REQUIRED = frozenset({
    "tests/test_pgbackrest_native_recovery_contract.py::NativeBackupRecoveryContract"
    "::test_exact_backup_status_and_required_wal_are_separate_predicates",
    "tests/test_pgbackrest_native_retention_contract.py::NativeBackupRetentionContract"
    "::test_two_full_generations_retain_seven_exact_recovery_points",
})
PHASES = frozenset({"setup", "call", "teardown"})


class BackupQualification:
    def __init__(self) -> None:
        self.collected: list[str] = []
        self.deselected: list[str] = []
        self.reports: dict[str, list[pytest.TestReport]] = defaultdict(list)

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected.extend(item.nodeid for item in items)

    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.collected = [item.nodeid for item in session.items]

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        self.reports[report.nodeid].append(report)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        problems = []
        if len(self.collected) != len(REQUIRED) or set(self.collected) != REQUIRED:
            problems.append("native collection does not equal required backup obligations")
        if self.deselected:
            problems.append("native backup obligations deselected")
        if set(self.reports) != REQUIRED:
            problems.append("native execution does not equal required backup obligations")
        for nodeid in sorted(REQUIRED):
            reports = self.reports.get(nodeid, [])
            if len(reports) != len(PHASES) or {r.when for r in reports} != PHASES:
                problems.append(f"{nodeid}: missing or repeated execution phase")
            elif any(r.outcome != "passed" or hasattr(r, "wasxfail") for r in reports):
                problems.append(f"{nodeid}: non-PASS or expected-failure phase")
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if problems:
            if reporter is not None:
                for problem in problems:
                    reporter.write_line(f"BACKUP_QUALIFICATION_INCOMPLETE: {problem}", red=True)
            # Preserve existing runner failure/interruption/collection error.
            if exitstatus == pytest.ExitCode.OK:
                session.exitstatus = pytest.ExitCode.TESTS_FAILED
        elif exitstatus == pytest.ExitCode.OK and reporter is not None:
            reporter.write_line("BACKUP_QUALIFICATION_COMPLETE: 2/2 native obligations")


def pytest_configure(config: pytest.Config) -> None:
    config.pluginmanager.register(BackupQualification(), "ordivon-backup-qualification")
