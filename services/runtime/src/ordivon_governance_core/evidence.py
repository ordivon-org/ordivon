"""Evidence utilities — hashing and evidence record creation."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_hex(data: str) -> str:
    """SHA256 hash, truncated to 16 hex chars."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def hash_file(path: Path) -> str:
    """SHA256 hash of a file's contents."""
    return sha256_hex(path.read_text())


def make_evidence_record(
    evidence_id: str,
    command: str,
    exit_code: int,
    stdout_path: str = "",
    stderr_path: str = "",
    sha256_stdout: str = "",
    sha256_stderr: str = "",
    started_at: str = "",
    duration_ms: int = 0,
    expected_failure: bool = False,
) -> dict:
    """Create a structured evidence record."""
    return {
        "evidence_id": evidence_id,
        "command": command,
        "exit_code": exit_code,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "sha256_stdout": sha256_stdout,
        "sha256_stderr": sha256_stderr,
        "started_at": started_at,
        "duration_ms": duration_ms,
        "expected_failure": expected_failure,
        "status": (
            "completed_expected_failure"
            if expected_failure and exit_code != 0
            else "completed"
            if exit_code == 0
            else "failed"
        ),
    }
