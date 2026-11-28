"""Real native collection/report controls; no mock verdict implementation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).with_name("conftest.py")
COLLECT_DROP = """
def pytest_collection_modifyitems(items):
    items.pop()
"""
COLLECT_DUPLICATE = """
def pytest_collection_modifyitems(items):
    items.append(items[0])
"""
COLLECT_REORDER = """
def pytest_collection_modifyitems(items):
    items.reverse()
"""
REPORT_REPLAY = """
import copy
import pytest
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    class ReplayReport:
        active = False
        def pytest_runtest_logreport(self, report):
            if not self.active and report.when == "call" and report.passed:
                self.active = True
                try:
                    duplicate = copy.copy(report)
                    config.hook.pytest_runtest_logreport(report=duplicate)
                finally:
                    self.active = False
    config.pluginmanager.register(ReplayReport())
"""
REPORT_RETRY = (
    REPORT_REPLAY.replace(
        "config.hook.pytest_runtest_logreport(report=duplicate)",
        'duplicate.outcome = "rerun"\n                    config.hook.pytest_runtest_logreport(report=duplicate)',
    )
    + """
def pytest_report_teststatus(report):
    if report.outcome == "rerun":
        return "rerun", "R", "RERUN"
"""
)


def _run(tmp_path: Path, source: str, plugin: str = ""):
    shutil.copy2(FIXTURE, tmp_path / "conftest.py")
    (tmp_path / "test_probe.py").write_text("import pytest\n" + source, encoding="utf-8")
    (tmp_path / "probe_plugin.py").write_text(plugin, encoding="utf-8")
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "probe_plugin",
            "--host-require-complete-suite",
            str(tmp_path),
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


@pytest.mark.parametrize(
    "plugin",
    [COLLECT_DROP, COLLECT_DUPLICATE, REPORT_REPLAY, REPORT_RETRY],
    ids=["silent-drop", "duplicate-item", "duplicate-phase", "retry-report"],
)
def test_native_inventory_incomplete_never_qualifies(tmp_path, plugin):
    result = _run(tmp_path, "def test_a(): pass\ndef test_b(): pass\n", plugin)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "HOST_COMPLETE_SUITE_INCOMPLETE" in result.stdout + result.stderr


def test_native_reorder_and_subtests_remain_valid(tmp_path):
    result = _run(
        tmp_path,
        """def test_a(subtests):
    for i in range(3):
        with subtests.test(i=i):
            assert i >= 0
def test_b(): pass
""",
        COLLECT_REORDER,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3 subtests passed" in result.stdout


@pytest.mark.parametrize(
    "plugin",
    [
        "def pytest_collection(session):\n    session.config.option.ignore = ['test_hidden.py']",
        "def pytest_ignore_collect(collection_path, config):\n    if collection_path.name == 'test_hidden.py': return True",
    ],
    ids=["configured-ignore", "native-ignore-hook"],
)
def test_missing_named_test_module_never_qualifies(tmp_path, plugin):
    (tmp_path / "test_hidden.py").write_text("def test_hidden(): assert False\n", encoding="utf-8")
    result = _run(tmp_path, "def test_a(): pass\n", plugin)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "HOST_COMPLETE_SUITE_INCOMPLETE" in result.stdout + result.stderr
    assert "test_hidden.py" in result.stdout


def test_named_empty_module_is_not_an_executed_obligation(tmp_path):
    (tmp_path / "test_hidden.py").write_text("def helper(): pass\n", encoding="utf-8")
    result = _run(tmp_path, "def test_a(): pass\n")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "test_hidden.py" in result.stdout
