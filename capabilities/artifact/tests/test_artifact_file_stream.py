"""Native file identity controls shared by commitments and snapshots."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from artifact_core.contracts import FileCommitment, sha256_file


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="requires native final-link rejection")
def test_committed_path_cannot_be_rebound_to_identical_alias():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "subject"
        path.write_bytes(b"identical")
        commitment = FileCommitment.from_path(path)
        target = Path(directory) / "other"
        target.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(target)
        with pytest.raises((OSError, RuntimeError)):
            commitment.verify()


@pytest.mark.skipif(
    not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"), reason="requires POSIX FIFO"
)
def test_direct_hash_fifo_is_rejected_without_waiting_for_writer():
    with tempfile.TemporaryDirectory() as directory:
        fifo = Path(directory) / "not-regular"
        os.mkfifo(fifo)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from artifact_core.contracts import sha256_file; "
                "import sys; sha256_file(Path(sys.argv[1]))",
                str(fifo),
            ],
            capture_output=True,
            timeout=3,
            check=False,
        )
        assert result.returncode != 0
        assert b"not a regular file" in result.stderr


def test_initial_alias_is_resolved_before_commitment():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "subject"
        path.write_bytes(b"same")
        alias = path.with_name("alias")
        alias.symlink_to(path)
        commitment = FileCommitment.from_path(alias)
        assert commitment.path == path
        assert commitment.sha256 == sha256_file(alias)
        assert commitment.verify() == commitment
