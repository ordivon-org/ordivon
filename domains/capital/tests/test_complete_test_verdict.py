"""Real pytest process falsifiers for the native acceptance verdict."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    "source,args,expected",
    [
        ("def test_pass(): assert 1 == 1", [], 0),
        ("def test_skip(): pytest.skip('missing')", [], 1),
        ("@pytest.mark.xfail\ndef test_xfail(): assert False", [], 1),
        ("@pytest.mark.xfail\ndef test_xpass(): pass", [], 1),
        (
            "@pytest.fixture\ndef resource(): pytest.skip('setup')\ndef test_setup(resource): pass",
            [],
            1,
        ),
        (
            "@pytest.fixture\ndef resource():\n    yield\n    pytest.skip('teardown')\ndef test_teardown(resource): pass",
            [],
            1,
        ),
        ("def test_pass(): pass", ["--collect-only"], 1),
        ("def test_pass(): pass", ["-k", "no_such_test"], 5),
        ("def test_fail(): assert False", [], 1),
    ],
)
def test_complete_native_verdict_uses_actual_phase_reports(tmp_path, source, args, expected):
    # Reuse exact test-only hook and native pytest, not a fake report.
    for name in ("conftest.py", "pg_test_lease.py"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    (tmp_path / "test_case.py").write_text("import pytest\n" + source + "\n")
    env = dict(os.environ)
    for key in (
        "ORDIVON_CAPITAL_PG_TEST_DSN",
        "ORDIVON_CAPITAL_PAPER_PG_TEST_DSN",
        "ORDIVON_CAPITAL_TEST_LEASE",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
    ):
        env.pop(key, None)
    env["ORDIVON_CAPITAL_REQUIRE_COMPLETE_TESTS"] = "1"
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert run.returncode == expected, run.stdout + run.stderr
    if expected == 1 and "test_fail" not in source:
        assert "CAPITAL_REQUIRED_TESTS_INCOMPLETE" in run.stderr
