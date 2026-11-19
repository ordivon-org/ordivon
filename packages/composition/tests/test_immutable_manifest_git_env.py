"""Foreign Git environment must not redirect SourceCut-bound Composition reads."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from ordivon_composition.verification_obligation_r1 import _immutable_git_manifest


def _git(repo: Path, *args: str) -> str:
    clean = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    return subprocess.check_output(["git", "-C", str(repo), *args], env=clean, text=True).strip()


@pytest.mark.parametrize("poison", ["GIT_DIR", "GIT_OBJECT_DIRECTORY"])
def test_exact_sourcecut_manifest_ignores_foreign_git_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, poison: str
) -> None:
    owner = tmp_path / "owner"
    foreign = tmp_path / "foreign"
    for repo in (owner, foreign):
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.name", "SourceCut Test")
        _git(repo, "config", "user.email", "sourcecut@example.invalid")

    expected = {"owner": "real", "task": "candidate-evaluation"}
    (owner / "manifest.json").write_text(json.dumps(expected), encoding="utf-8")
    _git(owner, "add", "manifest.json")
    _git(owner, "commit", "-qm", "exact owner input")
    sourcecut = _git(owner, "rev-parse", "HEAD")

    (foreign / "manifest.json").write_text('{"owner":"foreign"}', encoding="utf-8")
    _git(foreign, "add", "manifest.json")
    _git(foreign, "commit", "-qm", "foreign input")
    assert _git(foreign, "rev-parse", "HEAD") != sourcecut

    contaminated = str(foreign / ".git")
    if poison == "GIT_OBJECT_DIRECTORY":
        contaminated = str(foreign / ".git" / "objects")
    monkeypatch.setenv(poison, contaminated)

    # A raw Git call is visibly redirected or loses the owner object.
    raw = subprocess.run(
        ["git", "-C", str(owner), "cat-file", "-t", sourcecut],
        text=True,
        capture_output=True,
        check=False,
    )
    assert raw.returncode != 0

    manifest, identity = _immutable_git_manifest(owner, sourcecut, Path("manifest.json"))
    assert manifest == expected
    assert identity["commit"] == sourcecut
