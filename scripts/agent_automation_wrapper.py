#!/usr/bin/env python3
"""Stable Workstation-native entrypoint for Agent Automation.

The installed /root/tools/bin copy is intentionally thin and Workstation-owned. Production
operations delegate to the exact immutable Agent Automation release. The operator surface always delegates to the exact immutable production release; development uses
source-native entrypoints instead. Admission fencing remains Workstation-stable across release cuts.
"""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

DEFAULT_SOURCE_ROOT = Path("/opt/ordivon/agent-automation/current")
CONTROL_PYTHON = Path(
    "/root/.local/share/ordivon-workstation/agent-automation-mcp-v1/.venv/bin/python"
)
ADMISSION_ROOT = Path("/root/.local/state/ordivon-workstation/agent-automation/state")
ADMISSION_LOCK = ADMISSION_ROOT / "release-admission.lock"
ADMISSION_CLOSED = ADMISSION_ROOT / "release-admission.closed.json"
MUTATING_ACTIONS = frozenset({"launch", "birth", "reconcile", "human-resume", "continue"})


def _action(argv: list[str]) -> str | None:
    return next((value for value in argv if value in MUTATING_ACTIONS), None)


@contextmanager
def _admission_read_lease(action: str | None):
    if action is None:
        yield
        return
    ADMISSION_ROOT.mkdir(parents=True, exist_ok=True)
    with ADMISSION_LOCK.open("a+") as handle:
        os.chmod(ADMISSION_LOCK, 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            if ADMISSION_CLOSED.exists():
                raise SystemExit(
                    "agent automation admission is HOLD_CLOSED for immutable release convergence; "
                    "observe/reconcile the release before admitting another provider-effect workflow"
                )
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def main() -> int:
    action = _action(sys.argv[1:])
    with _admission_read_lease(action):
        source_root = DEFAULT_SOURCE_ROOT.resolve()
        scripts = source_root / "scripts"
        facade = scripts / "agent_automation_browserless.py"
        if not facade.is_file():
            raise SystemExit(f"agent automation source facade unavailable: {facade}")
        if not CONTROL_PYTHON.is_file():
            raise SystemExit(f"agent automation control runtime unavailable: {CONTROL_PYTHON}")
        args = list(sys.argv[1:])
        if "--config" not in args:
            args[0:0] = ["--config", "/etc/ordivon/agent-automation-browserless.json"]
        # Keep this Workstation-stable parent alive for the full child process so its shared
        # admission flock cannot disappear across exec. The dependency-bearing facade runs in
        # the MCP control venv rather than inheriting whichever system Python invoked this tool.
        completed = subprocess.run([str(CONTROL_PYTHON), str(facade), *args], check=False)
        return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
