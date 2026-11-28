"""Shared native Godot process qualification; no game-rule or receipt authority."""
import os
from pathlib import Path
import re
import subprocess
import sys

SCRIPT_FAILURES = ("SCRIPT ERROR:", "Parse Error:", "Parser Error:", "ERROR: Failed to load")
STRICT_FAILURES = re.compile(
    r"ObjectDB instances were leaked|resources still in use at exit|(?:^|\s)ERROR:",
    re.MULTILINE,
)


def private_player_environment(root: Path) -> dict[str, str]:
    """Create fresh XDG player directories without changing the parent environment."""
    env = os.environ.copy()
    for name in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        path = root / name
        path.mkdir()
        env[name] = str(path)
    return env


def verify_process(exit_code: int, stdout: str, stderr: str, *, allowed_exit_codes=(0,)):
    combined = stdout + "\n" + stderr
    if (exit_code not in allowed_exit_codes or any(term in combined for term in SCRIPT_FAILURES)
            or STRICT_FAILURES.search(combined)):
        raise AssertionError(
            f"native Godot process rejected: exit={exit_code} "
            f"stdout={stdout[-3000:]} stderr={stderr[-3000:]}")


def main() -> None:
    """Run one real native process, preserve its diagnostics, fail closed."""
    args = sys.argv[1:]
    if not args or args[0] != "--" or len(args) < 2:
        raise SystemExit("usage: native_process.py -- executable [args ...]")
    proc = subprocess.run(args[1:], capture_output=True, text=True, errors="replace",
                          timeout=180, check=False)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    verify_process(proc.returncode, proc.stdout, proc.stderr)


if __name__ == "__main__":
    main()
