"""Shared native Godot process qualification; no game-rule or receipt authority."""
import re

SCRIPT_FAILURES = ("SCRIPT ERROR:", "Parse Error:", "Parser Error:", "ERROR: Failed to load")
STRICT_FAILURES = re.compile(
    r"ObjectDB instances were leaked|resources still in use at exit|(?:^|\s)ERROR:",
    re.MULTILINE,
)


def verify_process(exit_code: int, stdout: str, stderr: str, *, allowed_exit_codes=(0,)):
    combined = stdout + "\n" + stderr
    if (exit_code not in allowed_exit_codes or any(term in combined for term in SCRIPT_FAILURES)
            or STRICT_FAILURES.search(combined)):
        raise AssertionError(
            f"native Godot process rejected: exit={exit_code} "
            f"stdout={stdout[-3000:]} stderr={stderr[-3000:]}")
