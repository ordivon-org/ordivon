import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "observe_subject_revision.sh"


class SubjectRevisionObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git = shutil.which("git")
        self.assertIsNotNone(self.git)
        self.git_run("init", "-q")
        (self.repo / "tracked.txt").write_text("initial", encoding="utf-8")
        self.git_run("add", "tracked.txt")
        self.git_run("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                     "commit", "-qm", "initial")
        self.revision = self.git_run("rev-parse", "HEAD")

    def git_run(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True
        ).strip()

    def observe(self, env: dict[str, str] | None = None) -> str:
        return subprocess.check_output(
            ["bash", str(SCRIPT), str(self.repo)], text=True, env=env
        ).strip()

    def fault(self, body: str) -> dict[str, str]:
        bin_dir = self.root / "bin"
        bin_dir.mkdir(exist_ok=True)
        wrapper = bin_dir / "git"
        wrapper.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
        wrapper.chmod(0o755)
        return dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"],
                    REAL_GIT=str(self.git), FAULT_STATE=str(self.root / "state"))

    def test_clean_native_git(self) -> None:
        self.assertEqual(self.observe(), self.revision)

    def test_dirty_native_git(self) -> None:
        (self.repo / "tracked.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(self.observe(), "UNKNOWN")

    def test_untracked_native_git(self) -> None:
        (self.repo / "new.txt").write_text("new", encoding="utf-8")
        self.assertEqual(self.observe(), "UNKNOWN")

    def test_status_failure_with_empty_stdout(self) -> None:
        env = self.fault('if [ "$3" = status ]; then exit 128; fi\nexec "$REAL_GIT" "$@"')
        self.assertEqual(self.observe(env), "UNKNOWN")

    def test_rev_parse_failure_with_partial_stdout(self) -> None:
        env = self.fault(f'printf "%s\\n" {self.revision}; exit 128')
        self.assertEqual(self.observe(env), "UNKNOWN")

    def test_head_changes_during_observation(self) -> None:
        env = self.fault(
            'if [ "$3" = rev-parse ]; then\n'
            '  if [ -e "$FAULT_STATE" ]; then printf "%040d\\n" 0; exit 0; fi\n'
            '  touch "$FAULT_STATE"\n'
            'fi\nexec "$REAL_GIT" "$@"'
        )
        self.assertEqual(self.observe(env), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
