"""Owner-local native pytest qualification, adapted from Host #2862.

No new test runner: the plugin observes discovery, selection and execution
phases, then rejects incomplete evidence. The source census is intentionally
bounded to pytest's ordinary Python file naming in this owner test root.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

LANES = ("portable", "native", "historical")
PHASES = ["setup", "call", "teardown"]


def lane_of(item: pytest.Item) -> str:
    if item.get_closest_marker("historical"):
        return "historical"
    if item.get_closest_marker("integration"):
        return "native"
    return "portable"


def ids_digest(ids: Counter[str]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(ids.items()), separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


class Qualification:
    def __init__(self, lane: str, root: Path) -> None:
        self.lane = lane
        self.root = root
        self.files = {
            p.resolve()
            for pattern in ("test_*.py", "*_test.py")
            for p in root.rglob(pattern)
            if p.is_file()
        }
        self.discovered_files: set[Path] = set()
        self.discovered: Counter[str] = Counter()
        self.expected: Counter[str] = Counter()
        self.deselected: Counter[str] = Counter()
        self.phases: dict[str, list[str]] = {}
        self.failed_nodes: set[str] = set()
        self.invalid: list[tuple[str, str, str]] = []
        self.collection_failures: list[str] = []
        self.subtests = 0

    def pytest_itemcollected(self, item: pytest.Item) -> None:
        self.discovered[item.nodeid] += 1
        self.discovered_files.add(item.path.resolve())
        if item.get_closest_marker("historical") and not item.get_closest_marker("integration"):
            self.invalid.append((item.nodeid, "collection", "historical-without-integration"))
        if lane_of(item) == self.lane:
            self.expected[item.nodeid] += 1

    def pytest_deselected(self, items: list[pytest.Item]) -> None:
        self.deselected.update(item.nodeid for item in items)

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if not report.passed:
            self.collection_failures.append(report.nodeid)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        good = report.passed and not hasattr(report, "wasxfail")
        if not good:
            self.invalid.append((report.nodeid, report.when, str(report.outcome)))
            self.failed_nodes.add(report.nodeid)
        if isinstance(report, pytest.SubtestReport):
            if good:
                self.subtests += 1
            return
        phases = self.phases.setdefault(report.nodeid, [])
        # A failed setup legitimately suppresses call but teardown is still
        # observed. Keep physical phase observation separate from success.
        if phases == ["setup"] and report.nodeid in self.failed_nodes and report.when == "teardown":
            phases.append(report.when)
            return
        if len(phases) >= len(PHASES) or report.when != PHASES[len(phases)]:
            self.invalid.append((report.nodeid, report.when, "unexpected-phase"))
            self.failed_nodes.add(report.nodeid)
            return
        phases.append(report.when)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        selected = Counter(item.nodeid for item in session.items)
        complete = {
            key
            for key, phases in self.phases.items()
            if phases == PHASES and key not in self.failed_nodes
        }
        missing_files = sorted(
            str(p.relative_to(self.root)) for p in self.files - self.discovered_files
        )
        inventory_match = (
            selected == self.expected
            and self.deselected == self.discovered - self.expected
            and all(n == 1 for n in self.discovered.values())
        )
        fully_observed = (
            bool(self.expected)
            and not missing_files
            and inventory_match
            and set(selected) == complete == set(self.phases)
            and not self.collection_failures
            and not self.invalid
            and exitstatus == pytest.ExitCode.OK
        )
        if not fully_observed and exitstatus == pytest.ExitCode.OK:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
        receipt = {
            "schemaVersion": 1,
            "kind": "artifact-test-qualification",
            "lane": self.lane,
            "standing": "PASS" if fully_observed else "INCOMPLETE",
            "nativeExitCode": int(exitstatus),
            "discovered": sum(self.discovered.values()),
            "expected": sum(self.expected.values()),
            "selected": sum(selected.values()),
            "complete": len(complete),
            "deselected": sum(self.deselected.values()),
            "inventoryMatch": inventory_match,
            "selectedNodeIdsSha256": ids_digest(selected),
            "expectedNodeIdsSha256": ids_digest(self.expected),
            "missingFiles": missing_files,
            "missingComplete": sorted(set(self.expected) - complete),
            "unexpectedComplete": sorted(complete - set(self.expected)),
            "invalidReports": self.invalid,
            "collectionFailures": self.collection_failures,
            "passedSubtests": self.subtests,
            "pytestVersion": pytest.__version__,
        }
        terminal = session.config.pluginmanager.get_plugin("terminalreporter")
        line = "ARTIFACT_TEST_QUALIFICATION " + json.dumps(receipt, sort_keys=True)
        if terminal is not None:
            terminal.write_line("")
            terminal.write_line(line)
        else:
            print(line)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--artifact-qualification", choices=LANES, default=None)


def pytest_configure(config: pytest.Config) -> None:
    lane = config.getoption("--artifact-qualification")
    if lane is not None:
        config.pluginmanager.register(
            Qualification(lane, config.rootpath / "tests"), "artifact-test-qualification"
        )
