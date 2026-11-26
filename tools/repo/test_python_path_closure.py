"""Independent finite reference and native Git source-cut controls."""

from __future__ import annotations

import itertools
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from python_path_closure import (
    affected_projects,
    git_manifests,
    project_edges,
    reverse_closure,
)


def manifest(name, sources=""):
    return (f'[project]\nname = "{name}"\n' + sources).encode()


def graph_input(target="../a"):
    return {
        "p/a/pyproject.toml": manifest("a"),
        "p/b/pyproject.toml": manifest(
            "b", f'[tool.uv.sources]\na = {{path="{target}"}}\n'
        ),
        "p/c/pyproject.toml": manifest("c", '[tool.uv.sources]\nb = {path="../b"}\n'),
        "p/d/pyproject.toml": manifest("d"),
    }


def oracle(seeds, edges):
    # Independent synchronous fixed point; not reverse adjacency or BFS.
    selected = set(seeds)
    while True:
        next_set = selected | {
            consumer for consumer, provider in edges if provider in selected
        }
        if next_set == selected:
            return frozenset(selected)
        selected = next_set


class PythonPathClosureTests(unittest.TestCase):
    def test_all_four_vertex_graphs_and_seed_subsets(self):
        vertices = tuple("abcd")
        possible = [(a, b) for a in vertices for b in vertices if a != b]
        cases = 0
        for mask in range(1 << len(possible)):
            graph = {edge for i, edge in enumerate(possible) if mask & (1 << i)}
            for n in range(5):
                for seeds in itertools.combinations(vertices, n):
                    self.assertEqual(
                        reverse_closure(seeds, graph), oracle(seeds, graph)
                    )
                    cases += 1
        self.assertEqual(cases, 65536)

    def test_old_new_edges_and_removed_membership(self):
        before = graph_input()
        after = dict(before)
        after["p/b/pyproject.toml"] = manifest(
            "b", '[tool.uv.sources]\nd = {path="../d"}\n'
        )
        del after["p/a/pyproject.toml"]
        self.assertEqual(
            affected_projects(["p/a/src/old.py"], before, after), {"p/a", "p/b", "p/c"}
        )
        self.assertEqual(
            affected_projects(["p/d/src/new.py"], before, after), {"p/d", "p/b", "p/c"}
        )
        self.assertEqual(affected_projects(["docs/guide.md"], before, after), set())

    def test_multiple_source_alternatives_and_normalized_names(self):
        m = {
            "p/a/pyproject.toml": manifest("a_b"),
            "p/c/pyproject.toml": manifest("A-B"),
            "p/b/pyproject.toml": manifest(
                "b",
                '[tool.uv.sources]\n"a.b" = [{path="../a", marker="sys_platform == \'linux\'"}, {path="../c", marker="sys_platform == \'win32\'"}]\n',
            ),
        }
        self.assertEqual(project_edges(m), {("p/b", "p/a"), ("p/b", "p/c")})

    def test_bad_sources_fail_closed(self):
        for target in (
            "../../outside",
            "../../../escape",
            "/absolute",
            "../missing",
            "../d",
            "../a.whl",
            "../a/../a",
        ):
            with self.subTest(target=target), self.assertRaises(ValueError):
                project_edges(graph_input(target))
        for source in (
            "[tool.uv.sources]\na = {workspace=true}\n",
            '[tool.uv.workspace]\nmembers=["*"]\n',
        ):
            with self.subTest(source=source), self.assertRaises(ValueError):
                project_edges({"p/b/pyproject.toml": manifest("b", source)})

    def test_git_reads_exact_blobs_not_worktree_or_ambient_git(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL
                )

            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "fixture")
            before = graph_input()
            for name, data in before.items():
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            git("add", ".")
            git("commit", "-qm", "before")
            old = git("rev-parse", "HEAD").decode().strip()
            new_b = manifest("b", '[tool.uv.sources]\nd = {path="../d"}\n')
            (repo / "p/b/pyproject.toml").write_bytes(new_b)
            git("add", ".")
            git("commit", "-qm", "after")
            new = git("rev-parse", "HEAD").decode().strip()
            (repo / "p/b/pyproject.toml").write_bytes(b"not TOML")
            with patch.dict(
                os.environ, {"GIT_DIR": "/nonexistent", "GIT_WORK_TREE": "/nonexistent"}
            ):
                self.assertEqual(git_manifests(repo, old), before)
                after = git_manifests(repo, new)
                self.assertEqual(after["p/b/pyproject.toml"], new_b)
                self.assertEqual(
                    affected_projects(["p/a/src/x"], before, after),
                    {"p/a", "p/b", "p/c"},
                )
            with self.assertRaises(ValueError):
                git_manifests(repo, "HEAD")
            (repo / "p/b/pyproject.toml").unlink()
            (repo / "p/b/pyproject.toml").symlink_to("../a/pyproject.toml")
            git("add", ".")
            git("commit", "-qm", "symlink")
            with self.assertRaisesRegex(ValueError, "non-regular"):
                git_manifests(repo, git("rev-parse", "HEAD").decode().strip())

    def test_missing_promisor_blob_does_not_attempt_remote_fetch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "project"
            remote = root / "remote"

            def git(*args, env=None):
                return subprocess.check_output(
                    ["git", "-C", str(repo), *args],
                    env=env,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )

            repo.mkdir()
            git("init", "-q")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "user.name", "fixture")
            (repo / "pyproject.toml").write_bytes(manifest("fixture"))
            git("add", ".")
            git("commit", "-qm", "initial")
            commit = git("rev-parse", "HEAD").decode().strip()
            blob = git("rev-parse", "HEAD:pyproject.toml").decode().strip()
            git("init", "-q", "--bare", str(remote))
            git("remote", "add", "origin", str(remote))
            git("config", "remote.origin.promisor", "true")
            git("config", "remote.origin.partialclonefilter", "blob:none")
            git("config", "extensions.partialClone", "origin")
            git("config", "core.repositoryformatversion", "1")
            probe = root / "upload-pack"
            marker = root / "attempt"
            probe.write_text(
                '#!/bin/sh\nprintf attempt > "' + str(marker) + '"\nexit 1\n'
            )
            probe.chmod(0o700)
            git("config", "remote.origin.uploadpack", str(probe))
            (repo / ".git/objects" / blob[:2] / blob[2:]).unlink()
            # Positive control: actual Git tries the local promisor transport.
            with self.assertRaises(subprocess.CalledProcessError):
                git(
                    "cat-file",
                    "blob",
                    blob,
                    env={**os.environ, "GIT_NO_LAZY_FETCH": "0"},
                )
            self.assertTrue(marker.is_file())
            marker.unlink()
            with (
                patch.dict(os.environ, {"GIT_NO_LAZY_FETCH": "0"}),
                self.assertRaises(subprocess.CalledProcessError),
            ):
                git_manifests(repo, commit)
            self.assertFalse(
                marker.exists(), "qualification invoked a remote transport"
            )

    def test_actual_tracked_source_projects(self):
        repo = Path(__file__).resolve().parents[2]
        commit = (
            subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"])
            .decode()
            .strip()
        )
        manifests = git_manifests(repo, commit)
        expected = {
            ("catalogs/authorities", "packages/composition"),
            ("studies/experimental-episodes/episode-store", "packages/composition"),
        }
        self.assertTrue(expected <= project_edges(manifests))
        self.assertTrue(
            {consumer for consumer, _ in expected}
            <= affected_projects(
                ["packages/composition/pyproject.toml"], manifests, manifests
            )
        )


if __name__ == "__main__":
    unittest.main()
