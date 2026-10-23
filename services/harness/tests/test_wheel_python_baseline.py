"""The isolated wheel test must not silently fall back to an old Python."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_wheel.py"
SPEC = importlib.util.spec_from_file_location("check_wheel_python_baseline", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_exact_project_python_passes_to_isolated_wheel_env():
    assert MODULE.wheel_python_interpreter(
        "==3.15.1", "3.15.1", "/opt/uv-py3.15/bin/python"
    ) == "/opt/uv-py3.15/bin/python"


@pytest.mark.parametrize(
    "requirement, observed, executable",
    [
        ("==3.15.1", "3.14.7", "/opt/old/bin/python"),
        ("==3.15.1", "3.16.0", "/opt/newer/bin/python"),
        (">=3.14", "3.15.1", "/opt/python"),
        ("==3.15.1", "3.15.1", "python"),
    ],
)
def test_wrong_or_unbound_interpreter_fails_closed(requirement, observed, executable):
    with pytest.raises(SystemExit):
        MODULE.wheel_python_interpreter(requirement, observed, executable)
