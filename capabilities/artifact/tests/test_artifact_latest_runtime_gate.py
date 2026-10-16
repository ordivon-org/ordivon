"""Current Artifact Python runtime must not silently admit an older SQLite."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "artifact_python_currentness", ROOT / "scripts/artifact_python_environment.py"
)
assert SPEC is not None and SPEC.loader is not None
ENV = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENV)


def test_artifact_runtime_requires_latest_python_and_sqlite():
    lock = json.loads((ROOT / "artifact-delivery/artifact-python-runtime-v1.lock.json").read_text())
    assert lock["pythonRuntime"] == "3.15.0"
    assert lock["sqliteRuntime"] == "3.54.0"
    project = ROOT / "artifact-delivery/python-uv"
    assert 'requires-python = "==3.15.0"' in (project / "uv.lock").read_text()
    assert "python3.15" in str(ENV.SYSTEM_PYTHON)


def test_artifact_interpreter_probe_validates_embedded_sqlite():
    source = (ROOT / "scripts/artifact_python_environment.py").read_text()
    wrapper = (ROOT / "scripts/artifact_python_wrapper.py").read_text()
    assert "sqlite3.sqlite_version" in source
    assert "sqliteRuntime" in source
    assert "sqlite3.sqlite_version" in wrapper
    assert "sqliteRuntime" in wrapper


def test_artifact_interpreter_rejects_embedded_sqlite_below_target():
    import subprocess
    from unittest.mock import patch

    lock = ENV.load_lock()
    bad = subprocess.CompletedProcess(
        ["python", "-c", "probe"],
        0,
        '{"version":"3.15.0","sqlite":"3.53.1","executable":"python"}',
        "",
    )
    with patch.object(ENV, "run", return_value=bad):
        try:
            ENV.python_status(lock)
        except RuntimeError as error:
            assert "SQLite drifted" in str(error)
        else:
            raise AssertionError("Artifact old embedded SQLite 3.53.1 incorrectly admitted")
