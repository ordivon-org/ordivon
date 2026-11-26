"""Real subprocess evidence: pytest success alone is not a complete lane."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ARTIFACT_TEST_QUALIFICATION "
PASS = "def test_a(): pass\n"
MIXED = (
    PASS
    + "@pytest.mark.integration\ndef test_b(): pass\n"
    + "@pytest.mark.integration\n@pytest.mark.historical\ndef test_c(): pass\n"
)


def run_probe(tmp_path, source, lane="portable", *args, plugin="", hidden=False):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\ntestpaths = tests\nmarkers =\n    integration: external\n"
        "    historical: prior method\n"
    )
    (tests / "test_probe.py").write_text("import pytest\n" + source)
    if hidden:
        (tests / "test_hidden.py").write_text("def test_hidden(): assert False")
    if plugin:
        (tests / "conftest.py").write_text(plugin)
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONPATH=str(ROOT))
    expr = {
        "portable": "not integration",
        "native": "integration and not historical",
        "historical": "historical",
    }[lane]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "scripts.artifact_test_qualification",
            f"--artifact-qualification={lane}",
            "-m",
            expr,
            *args,
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    rows = [
        json.loads(s[len(PREFIX) :]) for s in result.stdout.splitlines() if s.startswith(PREFIX)
    ]
    assert len(rows) == 1, result.stdout + result.stderr
    return result, rows[0]


@pytest.mark.parametrize("lane", ["portable", "native", "historical"])
def test_lane_partition_is_exact(tmp_path, lane):
    result, receipt = run_probe(tmp_path, MIXED, lane)
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt["standing"] == "PASS"
    assert (
        receipt["discovered"],
        receipt["expected"],
        receipt["selected"],
        receipt["complete"],
    ) == (3, 1, 1, 1)
    assert receipt["deselected"] == 2
    assert receipt["selectedNodeIdsSha256"] == receipt["expectedNodeIdsSha256"]


@pytest.mark.parametrize(
    "source,options",
    [
        ("@pytest.mark.skip(reason='unavailable')\ndef test_a(): pass\n", ()),
        ("def test_a(): pytest.skip('runtime missing')\n", ()),
        ("@pytest.mark.xfail(reason='known')\ndef test_a(): pass\n", ()),
        ("@pytest.mark.xfail(reason='known')\ndef test_a(): assert False\n", ()),
        (PASS + "def test_b(): pass\n", ("-k", "test_a")),
        (PASS, ("--collect-only",)),
        (
            "@pytest.fixture\ndef f():\n    yield\n    pytest.skip('teardown')\ndef test_a(f): pass\n",
            (),
        ),
        ("def test_a(subtests):\n    with subtests.test(): assert False\n", ()),
        ("@pytest.mark.historical\ndef test_a(): pass\n", ()),
    ],
)
def test_incomplete_never_qualifies(tmp_path, source, options):
    result, receipt = run_probe(tmp_path, source, "portable", *options)
    assert result.returncode != 0
    assert receipt["standing"] == "INCOMPLETE"


@pytest.mark.parametrize(
    "plugin",
    [
        "def pytest_collection_modifyitems(items):\n    items.pop()\n",
        "def pytest_collection_modifyitems(items):\n    items.append(items[0])\n",
        """import copy
import pytest
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    class Replay:
        active = False
        def pytest_runtest_logreport(self, report):
            if not self.active and report.when == "call" and report.passed:
                self.active = True
                try:
                    config.hook.pytest_runtest_logreport(report=copy.copy(report))
                finally:
                    self.active = False
    config.pluginmanager.register(Replay())
""",
    ],
)
def test_native_inventory_or_phase_corruption_is_rejected(tmp_path, plugin):
    result, receipt = run_probe(tmp_path, PASS + "def test_b(): pass\n", plugin=plugin)
    assert result.returncode != 0
    assert receipt["standing"] == "INCOMPLETE"


def test_subtests_are_additional_not_parent_invocations(tmp_path):
    result, receipt = run_probe(
        tmp_path,
        "def test_a(subtests):\n    for i in range(3):\n"
        "        with subtests.test(i=i): assert i >= 0\n",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt["complete"] == 1 and receipt["passedSubtests"] == 3


def test_hidden_named_file_is_missing_obligation(tmp_path):
    result, receipt = run_probe(
        tmp_path,
        PASS,
        hidden=True,
        plugin="""def pytest_ignore_collect(collection_path, config):
    if collection_path.name == "test_hidden.py":
        return True
""",
    )
    assert result.returncode != 0
    assert receipt["missingFiles"] == ["test_hidden.py"]
    assert receipt["standing"] == "INCOMPLETE"


def test_failed_call_still_observes_teardown_without_inventing_phase_corruption(tmp_path):
    result, receipt = run_probe(tmp_path, "def test_a(): pytest.skip('unavailable')\n")
    assert result.returncode != 0
    assert receipt["complete"] == 0
    assert receipt["invalidReports"] == [["tests/test_probe.py::test_a", "call", "skipped"]]
