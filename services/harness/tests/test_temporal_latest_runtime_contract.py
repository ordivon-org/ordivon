"""Keep the live Temporal worker product; gate only its interpreter/SQLite carrier."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VENV = (
    "/root/.local/share/ordivon-workstation/temporal-agent-automation/py315-sqlite354-r19-release"
)
PYTHON = VENV + "/bin/python"


def test_temporal_source_unit_uses_exact_latest_runtime_and_preserves_task_queue():
    unit = (ROOT / "systemd/ordivon-agent-temporal-worker.service").read_text()
    assert "ExecStart=" + PYTHON + " " in unit
    assert (
        "ExecStart=/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python"
        not in unit
    )
    assert "--task-queue ordivon-agent-automation" in unit
    assert "Requires=temporal.service" in unit
    assert "LoadCredential=gateway-local-bearer:" in unit


def test_temporal_owner_deployer_has_explicit_embedded_sqlite_and_python_gate():
    source = (ROOT / "scripts/temporal_agent_automation_deploy.py").read_text()
    tree = ast.parse(source)
    assignments = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "VENV_PY"
    ]
    assert len(assignments) == 1
    expr = assignments[0].value
    assert isinstance(expr, ast.Call) and len(expr.args) == 1
    assert isinstance(expr.args[0], ast.Constant) and expr.args[0].value == PYTHON
    assert '"pythonVersion": "3.15.0"' in source
    assert '"sqliteVersion": "3.54.0"' in source
    assert "sqlite3.sqlite_version" in source
    assert "runtimeVersionsExact" in source


def test_temporal_exact_legacy_workflow_source_is_not_rewritten_by_runtime_upgrade():
    source = ROOT / "scripts/temporal_agent_automation_worker.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == (
        "4fc5ce6c4abf2dd614e7db7b325641e05b8e2bb56c6382414e312b4588d6c754"
    )


def test_real_previous_interpreter_is_not_latest_python_sqlite():
    modspec = importlib.util.spec_from_file_location(
        "temporal_worker_deploy_regression", ROOT / "scripts/temporal_agent_automation_deploy.py"
    )
    assert modspec is not None and modspec.loader is not None
    mod = importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(mod)
    old = Path("/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python")
    if not old.exists():
        return  # GitHub CI does not install the production old interpreter.
    with patch.object(mod, "VENV_PY", old):
        observed = mod.runtime_versions()
    assert observed is not None
    assert observed.get("pythonVersion") != "3.15.0"
    assert observed.get("sqliteVersion") != "3.54.0"
