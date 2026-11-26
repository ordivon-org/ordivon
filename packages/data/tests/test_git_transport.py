"""Real subprocess and Git controls for bounded local observation."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data import git_sources, git_transport


class GitTransportTests(unittest.TestCase):
    def run_child(self, code, *, limit=128, timeout=5, data=None):
        children = []
        native = subprocess.Popen

        def spawn(*args, **kwargs):
            child = native(*args, **kwargs)
            children.append(child)
            return child

        try:
            with patch.object(git_transport.subprocess, "Popen", side_effect=spawn):
                return git_transport.capture_git_output(
                    [sys.executable, "-c", code],
                    env=os.environ.copy(),
                    input_bytes=data,
                    max_output=limit,
                    timeout=timeout,
                )
        finally:
            self.assertEqual(len(children), 1)
            child = children[0]
            self.assertIsNotNone(child.returncode)
            self.assertTrue(child.stdout.closed)
            self.assertTrue(child.stderr.closed)
            if child.stdin is not None:
                self.assertTrue(child.stdin.closed)

    def test_exact_empty_and_binary_output(self):
        for size in (0, 1, 128, 65536, 65537):
            with self.subTest(size=size):
                self.assertEqual(
                    self.run_child(
                        f"import sys; sys.stdout.buffer.write(b'x' * {size})",
                        limit=size,
                    ),
                    b"x" * size,
                )

    def test_overflow_rejects_and_reaps_without_waiting_for_natural_exit(self):
        with self.assertRaisesRegex(ValueError, "bounded transport bytes"):
            self.run_child(
                "import os,time; os.write(1,b'x'*4096); time.sleep(30)",
                limit=128,
            )

    def test_diagnostic_rejects_before_unbounded_stderr(self):
        with self.assertRaisesRegex(ValueError, "native diagnostic"):
            self.run_child("import os,time; os.write(2,b'x'*4096); time.sleep(30)")

    def test_deadline_and_nonzero_terminal_status(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_child("import time; time.sleep(30)", timeout=0.2)
        # Both output descriptors can reach EOF before the child exits.
        with self.assertRaises(subprocess.TimeoutExpired):
            self.run_child(
                "import os,time; os.close(1); os.close(2); time.sleep(30)",
                timeout=0.2,
            )
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_child("import sys; sys.stdout.write('partial'); sys.exit(7)")

    def test_full_duplex_pipe_progress(self):
        payload = bytes(range(256)) * 1024
        self.assertEqual(
            self.run_child(
                "import sys; sys.stdout.buffer.write(b'p'*131072); "
                "sys.stdout.buffer.flush(); "
                "sys.stdout.buffer.write(sys.stdin.buffer.read())",
                data=payload,
                limit=131072 + len(payload),
            ),
            b"p" * 131072 + payload,
        )

    def test_native_listing_is_bounded_before_metadata_parsing(self):
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["/usr/bin/git", "-C", tmp, "init", "-q"], check=True)
            path = repo / "owner" / "odps.json"
            path.parent.mkdir()
            path.write_bytes(b"{}")
            subprocess.run(["/usr/bin/git", "-C", tmp, "add", "."], check=True)
            self.assertEqual(git_sources.tracked_owner_products(repo), [path])
            with (
                patch.object(git_sources, "_MAX_LISTING_BYTES", 1),
                self.assertRaisesRegex(ValueError, "bounded transport bytes"),
            ):
                git_sources.tracked_owner_products(repo)

    def test_real_cut_budget_binding_and_pre_dispatch_count(self):
        for algorithm in ("sha1", "sha256"):
            with self.subTest(algorithm=algorithm), TemporaryDirectory() as tmp:
                repo = Path(tmp)

                def git(*args):
                    return subprocess.check_output(
                        ["/usr/bin/git", "-C", tmp, *args]
                    ).strip()

                git("init", "-q", "--object-format=" + algorithm)
                path = repo / "owner" / "odps.json"
                path.parent.mkdir()
                payload = b"metadata\n\0"
                path.write_bytes(payload)
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
                commit = git("rev-parse", "HEAD").decode("ascii")
                observations = []
                actual_capture = git_transport.capture_git_output

                def observe(
                    argv,
                    actual_capture=actual_capture,
                    observations=observations,
                    **kwargs,
                ):
                    raw = actual_capture(argv, **kwargs)
                    observations.append((argv, kwargs, raw))
                    return raw

                with patch.object(
                    git_sources, "capture_git_output", side_effect=observe
                ):
                    self.assertEqual(
                        git_sources.committed_owner_products(repo, commit),
                        (commit, [payload]),
                    )
                checked = [
                    (kw, raw)
                    for argv, kw, raw in observations
                    if argv[-2:] == ["cat-file", "--batch-check"]
                ]
                self.assertEqual(len(checked), 1)
                headers, raw = checked[0]
                count = len(headers["input_bytes"].splitlines())
                self.assertEqual(headers["max_output"], count * (len(commit) + 17))
                # Independent wire geometry from the actual native header text,
                # not the implementation's partition or admission function.
                frame_sizes = {
                    line.split(b" ", 1)[0]: len(line) + int(line.rsplit(b" ", 1)[1]) + 2
                    for line in raw.splitlines()
                }
                batches = [
                    (kw, raw)
                    for argv, kw, raw in observations
                    if argv[-2:] == ["cat-file", "--batch"]
                ]
                self.assertTrue(batches)
                for kw, raw in batches:
                    budget = sum(
                        frame_sizes[oid] for oid in kw["input_bytes"].splitlines()
                    )
                    self.assertEqual(kw["max_output"], budget)
                    self.assertEqual(len(raw), budget)

                with (
                    patch.object(git_sources, "_MAX_OBJECTS", 1),
                    patch.object(git_sources, "_git", wraps=git_sources._git) as native,
                    self.assertRaisesRegex(ValueError, "bounded object count"),
                ):
                    git_sources.committed_owner_products(repo, commit)
                self.assertFalse(
                    any(call.args[1] == "cat-file" for call in native.call_args_list)
                )
