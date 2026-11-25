"""Test actual Mise task admission and downstream argv, not shell spelling.

Downstream tools are replaced only in this control-plane test. Native
database, solver and formal execution are qualified by their real tasks.
"""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASKS = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
GENERAL = "ORDIVON_CAPITAL_PG_TEST_DSN"
PAPER = "ORDIVON_CAPITAL_PAPER_PG_TEST_DSN"


@pytest.fixture
def task_runner(tmp_path):
    trace = tmp_path / "calls.jsonl"
    for command in ("mise", "uv"):
        tool = tmp_path / command
        tool.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "with open(os.environ['TRACE'], 'a', encoding='utf-8') as out:\n"
            "    print(json.dumps({'tool': os.path.basename(sys.argv[0]),"
            "'argv': sys.argv[1:], 'physical': os.environ.get('ORDIVON_FINANCE_REQUIRE_PHYSICAL_PG')}),file=out)\n"
        )
        tool.chmod(0o700)

    def run(task, overrides=None):
        trace.unlink(missing_ok=True)
        env = {
            **os.environ,
            "PATH": str(tmp_path) + ":" + os.environ["PATH"],
            "TRACE": str(trace),
            GENERAL: "test_disposable_general",
            PAPER: "test_disposable_paper",
        }
        env.pop("ORDIVON_FINANCE_REQUIRE_PHYSICAL_PG", None)
        for key, value in (overrides or {}).items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        result = subprocess.run(
            ["/bin/bash", "-c", TASKS[task]["run"]],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        calls = (
            [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        )
        return result, calls

    return run


@pytest.mark.parametrize(
    "task,missing",
    [
        ("verify", GENERAL),
        ("verify", PAPER),
        ("verify:nonlive:nautilus", PAPER),
    ],
)
@pytest.mark.parametrize("value", [None, "", "  \t"])
def test_required_task_rejects_missing_db_before_any_downstream_effect(
    task, missing, value, task_runner
):
    result, calls = task_runner(task, {missing: value})
    assert result.returncode != 0
    assert missing in result.stderr
    assert not calls


@pytest.mark.parametrize(
    "task,selection",
    [
        ("verify", "not provider_qualification"),
        ("verify:provider", "provider_qualification"),
        ("verify:nonlive:nautilus", "native_nonlive"),
    ],
)
def test_actual_pytest_selection_and_qualification(task, selection, task_runner):
    result, calls = task_runner(task)
    assert result.returncode == 0, result.stderr
    pytest_calls = []
    for call in calls:
        args = call["argv"]
        for i in range(len(args) - 2):
            if args[i : i + 3] == ["python", "-m", "pytest"]:
                pytest_calls.append((call, args[i + 3 :]))
    assert len(pytest_calls) == 1
    call, args = pytest_calls[0]
    assert args.count("-m") == 1 and args[args.index("-m") + 1] == selection
    assert "--locked" in call["argv"]
    if task == "verify":
        assert "--hypothesis-show-statistics" in args and "-rs" in args
    if task == "verify:nonlive:nautilus":
        assert call["physical"] == "1"
        assert {"tests/test_nautilus_candidate.py", "tests/test_native_dbn.py"} <= set(args)


def test_declared_marker_and_strictness_contract():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["pytest"]["ini_options"]
    markers = {marker.split(":", 1)[0] for marker in config["markers"]}
    assert {"provider_qualification", "native_nonlive"} <= markers
    assert config["strict_markers"] is True
    assert config["strict_xfail"] is True
