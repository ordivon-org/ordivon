"""Exercise the real Mise shell task body without executing downstream effects."""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TASKS = tomllib.loads((ROOT / "mise.toml").read_text())["tasks"]
GENERAL = "ORDIVON_CAPITAL_PG_TEST_DSN"
PAPER = "ORDIVON_CAPITAL_PAPER_PG_TEST_DSN"


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
    task, missing, value, tmp_path
):
    # Only replace downstream tools, never the actual task or admission logic.
    # A guard regression must be observable even if downstream tools succeed.
    log = tmp_path / "calls"
    for command in ("mise", "uv"):
        tool = tmp_path / command
        tool.write_text('#!/bin/bash\nprintf \'%s\\n\' "$0" >> "$TRACE"\nexit 0\n')
        tool.chmod(0o700)
    env = {
        **os.environ,
        "PATH": str(tmp_path) + ":" + os.environ["PATH"],
        "TRACE": str(log),
        GENERAL: "test_disposable_general",
        PAPER: "test_disposable_paper",
    }
    if value is None:
        env.pop(missing)
    else:
        env[missing] = value
    run = subprocess.run(
        ["/bin/bash", "-c", TASKS[task]["run"]],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert run.returncode != 0
    assert missing in run.stderr
    assert not log.exists(), "downstream tool called before admission"


def test_qualified_task_reaches_downstream_tools(tmp_path):
    log = tmp_path / "calls"
    for command in ("mise", "uv"):
        tool = tmp_path / command
        tool.write_text('#!/bin/bash\nprintf \'%s\\n\' "$0" >> "$TRACE"\nexit 0\n')
        tool.chmod(0o700)
    env = {
        **os.environ,
        "PATH": str(tmp_path) + ":" + os.environ["PATH"],
        "TRACE": str(log),
        GENERAL: "test_disposable_general",
        PAPER: "test_disposable_paper",
    }
    run = subprocess.run(
        ["/bin/bash", "-c", TASKS["verify"]["run"]],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert run.returncode == 0, run.stderr
    assert log.exists()
