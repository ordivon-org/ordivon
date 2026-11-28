"""Owner-local native backup fixture; never dispatch against operator PGDATA."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def run_private(*args, check=True, timeout=70):
    # Clear environment AFTER changing user: PGBACKREST_* options take
    # precedence over config, and a spawned postmaster inherits its environment.
    return subprocess.run(
        ["sudo", "-u", "postgres", "/usr/bin/env", "-i",
         "PATH=/usr/bin:/bin", "LANG=C", "LC_ALL=C", *map(str, args)],
        capture_output=True, text=True, check=check, timeout=timeout,
    )


class PrivatePostmasters:
    """Track only direct children of a freshly allocated private fixture root."""

    def __init__(self, root: Path, run=run_private):
        self.root = root
        self.run = run
        self.attempts: dict[Path, bool] = {}

    def _private_directory(self, path: Path) -> None:
        if (path.parent != self.root or self.root.is_symlink()
                or path.is_symlink() or not path.is_dir()):
            raise ValueError("postmaster path must be an owned fixture child directory")

    def start(self, path: Path, sock: Path, port: int):
        self._private_directory(path)
        self._private_directory(sock)
        if path == sock or path in self.attempts:
            raise ValueError("duplicate or overlapping fixture start")
        # Record the obligation before dispatch: a timed-out pg_ctl may
        # have launched a server even if it never returned success.
        self.attempts[path] = False
        self.run("/usr/bin/pg_ctl", "-D", path, "-l", self.root / (path.name + ".log"),
                 "-o", f"-c listen_addresses='' -c unix_socket_directories={sock} -p {port}",
                 "-w", "-t", "30", "start", timeout=45)
        self.attempts[path] = True

    def status(self, path: Path):
        return self.run("/usr/bin/pg_ctl", "-D", path, "status", check=False, timeout=10)

    def stop(self, path: Path):
        if path not in self.attempts:
            raise ValueError("postmaster was not acquired by this fixture")
        self._private_directory(path)
        observed = self.status(path)
        if observed.returncode == 0:
            self.run("/usr/bin/pg_ctl", "-D", path, "-m", "fast", "-w", "stop",
                     timeout=35)
            observed = self.status(path)
        elif not self.attempts[path]:
            # A failed start with no observed server is not evidence that
            # a delayed child cannot still start. Preserve this fixture.
            raise RuntimeError(f"unqualified start; retaining {path}")
        pid = path / "postmaster.pid"
        if observed.returncode != 3 or pid.exists() or pid.is_symlink():
            raise RuntimeError(f"private postmaster stop unqualified; retaining {path}")
        del self.attempts[path]

    def cleanup(self):
        errors = []
        for path in reversed(tuple(self.attempts)):
            try:
                self.stop(path)
            except Exception as error:
                errors.append(error)
        if errors:
            raise ExceptionGroup(f"private fixture retained: {self.root}", errors)
        shutil.rmtree(self.root)
        print("private fixture removed", not self.root.exists(), flush=True)
