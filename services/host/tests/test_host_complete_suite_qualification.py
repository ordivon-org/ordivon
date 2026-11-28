"""Real pytest subprocess controls for complete versus focused qualification."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).with_name("conftest.py")


def _run(tmp_path: Path, source: str, *options: str):
    shutil.copy2(FIXTURE, tmp_path / "conftest.py")
    (tmp_path / "test_probe.py").write_text("import pytest\n" + source, encoding="utf-8")
    env = dict(os.environ)
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *options, str(tmp_path)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


@pytest.mark.parametrize(
    ("source", "options"),
    [
        ("@pytest.mark.skip(reason='unavailable')\ndef test_a(): pass\n", ()),
        ("def test_a(): pytest.skip('runtime')\n", ()),
        ("pytest.skip('missing module',allow_module_level=True)\ndef test_a(): pass\n", ()),
        ("@pytest.mark.xfail(reason='known')\ndef test_a(): assert False\n", ()),
        ("@pytest.mark.xfail(reason='known')\ndef test_a(): pass\n", ()),
        ("def test_a(): pass\ndef test_b(): pass\n", ("-k", "test_a")),
        ("def test_a(): pass\n", ("--collect-only",)),
        (
            "@pytest.fixture\ndef dep():\n    yield\n    pytest.skip('teardown')\ndef test_a(dep): pass\n",
            (),
        ),
    ],
)
def test_partial_evidence_never_qualifies(tmp_path, source, options):
    # A normal pytest exit may be zero for these incomplete executions.
    result = _run(tmp_path, source, "--host-require-complete-suite", *options)
    assert result.returncode != 0, result.stdout + result.stderr
    # No tests collected already fails natively; otherwise require our verdict.
    assert (
        "HOST_COMPLETE_SUITE_INCOMPLETE" in result.stdout + result.stderr or result.returncode == 5
    )


def test_complete_suite_passes(tmp_path):
    result = _run(
        tmp_path, "def test_a(): pass\ndef test_b(): pass\n", "--host-require-complete-suite"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "HOST_COMPLETE_SUITE_INCOMPLETE" not in result.stdout + result.stderr


def test_focused_skip_preserves_native_semantics(tmp_path):
    result = _run(tmp_path, "def test_a(): pytest.skip('optional native dependency')\n")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 skipped" in result.stdout


def test_existing_failure_not_rewritten(tmp_path):
    result = _run(tmp_path, "def test_a(): assert False\n", "--host-require-complete-suite")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "1 failed" in result.stdout
