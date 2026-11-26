"""Cut-level deadline controls independent of native per-command timeout."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data import git_sources


class GitCutDeadlineTests(unittest.TestCase):
    def make_repo(self, repo: Path, fmt: str) -> str:
        def git(*args):
            return subprocess.check_output(
                ["/usr/bin/git", "-C", str(repo), *args]
            ).strip()

        git("init", "-q", "--object-format=" + fmt)
        for name in ("a", "b"):
            path = repo / name / "odps.json"
            path.parent.mkdir()
            path.write_bytes(name.encode())
        git("add", ".")
        git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )
        return git("rev-parse", "HEAD").decode("ascii")

    def test_native_commands_share_one_cut_budget(self):
        for fmt in ("sha1", "sha256"):
            with self.subTest(fmt=fmt), TemporaryDirectory() as tmp:
                repo = Path(tmp)
                commit = self.make_repo(repo, fmt)
                now = 100.0
                timeouts = []
                commands = []
                native = git_sources.capture_git_output

                def clock(_get=lambda: now):
                    return _get()

                def observe(
                    argv,
                    _native=native,
                    _commands=commands,
                    _timeouts=timeouts,
                    **kwargs,
                ):
                    nonlocal now
                    _commands.append(tuple(argv[4:]))
                    _timeouts.append(kwargs["timeout"])
                    result = _native(argv, **kwargs)
                    now += 11.0
                    return result

                with (
                    patch.object(git_sources, "monotonic", clock, create=True),
                    patch.object(
                        git_sources, "capture_git_output", side_effect=observe
                    ),
                    self.assertRaisesRegex(ValueError, "total observation deadline"),
                ):
                    git_sources.committed_owner_products(repo, commit)
                self.assertEqual(timeouts, [20.0, 20.0, 20.0, 20.0, 16.0, 5.0])
                self.assertFalse(
                    any(cmd[:2] == ("cat-file", "--batch") for cmd in commands)
                )
                self.assertFalse(any(cmd[:1] == ("hash-object",) for cmd in commands))
                self.assertEqual(
                    git_sources.committed_owner_products(repo, commit),
                    (commit, [b"a", b"b"]),
                )

    def test_cpu_phase_expiry_blocks_next_native_dispatch(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            commit = self.make_repo(repo, "sha1")
            now = 100.0
            native = git_sources.qualify_tree_listing

            def delayed(*args, **kwargs):
                nonlocal now
                result = native(*args, **kwargs)
                now += 61.0
                return result

            with (
                patch.object(git_sources, "monotonic", lambda: now, create=True),
                patch.object(git_sources, "qualify_tree_listing", side_effect=delayed),
                patch.object(
                    git_sources,
                    "capture_git_output",
                    wraps=git_sources.capture_git_output,
                ) as calls,
                self.assertRaisesRegex(ValueError, "total observation deadline"),
            ):
                git_sources.committed_owner_products(repo, commit)
            self.assertFalse(
                any(
                    c.args[0][4] in ("cat-file", "hash-object")
                    for c in calls.call_args_list
                )
            )

    def test_tracked_listing_cannot_return_after_cut_deadline(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.make_repo(repo, "sha1")
            now = 100.0
            native = git_sources.capture_git_output
            timeouts = []

            def delayed(argv, **kwargs):
                nonlocal now
                timeouts.append(kwargs["timeout"])
                result = native(argv, **kwargs)
                now += 31.0
                return result

            with (
                patch.object(git_sources, "monotonic", lambda: now, create=True),
                patch.object(git_sources, "capture_git_output", side_effect=delayed),
                self.assertRaisesRegex(ValueError, "total observation deadline"),
            ):
                git_sources.tracked_owner_products(repo)
            self.assertEqual(timeouts, [20.0, 20.0])
            self.assertEqual(
                git_sources.tracked_owner_products(repo),
                [repo / "a" / "odps.json", repo / "b" / "odps.json"],
            )

    def test_remaining_budget_is_enforced_by_native_child(self):
        native = git_sources.capture_git_output
        children = []
        popen = subprocess.Popen
        observed_timeouts = []

        def spawn(*args, **kwargs):
            child = popen(*args, **kwargs)
            children.append(child)
            return child

        def blocked_child(_argv, **kwargs):
            observed_timeouts.append(kwargs["timeout"])
            return native(
                [sys.executable, "-c", "import time; time.sleep(30)"],
                **kwargs,
            )

        with (
            patch.object(git_sources, "capture_git_output", side_effect=blocked_child),
            patch.object(subprocess, "Popen", side_effect=spawn),
            self.assertRaises(ValueError) as failure,
        ):
            git_sources._git(
                ROOT,
                "rev-parse",
                "HEAD",
                deadline=git_sources.monotonic() + 0.25,
            )
        self.assertIsInstance(failure.exception.__cause__, subprocess.TimeoutExpired)
        self.assertEqual(len(observed_timeouts), 1)
        self.assertGreater(observed_timeouts[0], 0)
        self.assertLessEqual(observed_timeouts[0], 0.25)
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].returncode)
        self.assertTrue(children[0].stdout.closed)
        self.assertTrue(children[0].stderr.closed)
