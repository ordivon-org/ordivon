from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import agent_automation_release as release  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def init(repo: Path) -> None:
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "x@example.invalid")
    git(repo, "config", "user.name", "x")


def test_default_release_source_is_current_modular_monorepo() -> None:
    assert release.SOURCE_REPO == Path("/root/projects/ordivon")
    assert release.SOURCE_SUBTREE == Path("services/harness")


def test_monorepo_materialization_strips_harness_subtree_without_changing_release_abi(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    releases = tmp_path / "releases"
    init(repo)
    harness = repo / "services/harness"
    (harness / "scripts").mkdir(parents=True)
    (harness / "config").mkdir()
    (harness / "scripts/a.py").write_text("print('a')\n")
    (harness / "config/a.toml").write_text("x=1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "monorepo")
    commit = release.exact_commit(repo, "HEAD")
    old_paths = release.RELEASE_PATHS
    try:
        release.RELEASE_PATHS = ("scripts/a.py", "config/a.toml")
        value = release.materialize(repo, commit, releases)
    finally:
        release.RELEASE_PATHS = old_paths
    root = Path(value["path"])
    assert (root / "scripts/a.py").read_text() == "print('a')\n"
    assert (root / "config/a.toml").read_text() == "x=1\n"
    assert not (root / "services").exists()
    marker = json.loads((root / release.MARKER).read_text())
    assert marker["sourceRepo"] == str(repo.resolve())
    assert marker["sourceSubtree"] == "services/harness"


def test_exact_commit_is_owner_scoped_from_git_root_or_owner_subtree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init(repo)
    harness = repo / "services/harness"
    harness.mkdir(parents=True)
    (harness / "owner.txt").write_text("one\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "owner")
    owner_commit = git(repo, "rev-parse", "HEAD")
    (repo / "unrelated.txt").write_text("outside\n")
    git(repo, "add", "unrelated.txt")
    git(repo, "commit", "-qm", "unrelated")
    repo_head = git(repo, "rev-parse", "HEAD")
    assert repo_head != owner_commit
    assert release.exact_commit(repo, "HEAD") == owner_commit
    assert release.exact_commit(harness, "HEAD") == owner_commit
    assert release.source_repo_identity(harness) == str(repo.resolve())


def test_standalone_fixture_materialization_remains_supported(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    releases = tmp_path / "releases"
    init(repo)
    (repo / "a").write_text("one\n")
    git(repo, "add", "a")
    git(repo, "commit", "-qm", "standalone")
    commit = release.exact_commit(repo, "HEAD")
    old_paths = release.RELEASE_PATHS
    try:
        release.RELEASE_PATHS = ("a",)
        value = release.materialize(repo, commit, releases)
    finally:
        release.RELEASE_PATHS = old_paths
    root = Path(value["path"])
    assert (root / "a").read_text() == "one\n"
    marker = json.loads((root / release.MARKER).read_text())
    assert marker["sourceSubtree"] is None


def test_release_fence_binds_explicit_repo_not_global_default(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    init(repo)
    (repo / "x").write_text("x\n")
    git(repo, "add", "x")
    git(repo, "commit", "-qm", "x")
    commit = git(repo, "rev-parse", "HEAD")
    admission = tmp_path / "admission"
    old_root, old_lock, old_closed = (
        release.ADMISSION_ROOT,
        release.ADMISSION_LOCK,
        release.ADMISSION_CLOSED,
    )
    try:
        release.ADMISSION_ROOT = admission
        release.ADMISSION_LOCK = admission / "release-admission.lock"
        release.ADMISSION_CLOSED = admission / "release-admission.closed.json"
        with release.release_admission_fence(commit, repo):
            gate = json.loads(release.ADMISSION_CLOSED.read_text())
            assert gate["sourceRepo"] == str(repo.resolve())
    finally:
        release.ADMISSION_ROOT, release.ADMISSION_LOCK, release.ADMISSION_CLOSED = (
            old_root,
            old_lock,
            old_closed,
        )


def test_release_paths_close_recursive_local_python_import_graph() -> None:
    scripts = ROOT / "scripts"
    local = {path.stem: path for path in scripts.glob("*.py") if path.is_file()}
    release_paths = set(release.RELEASE_PATHS)
    pending = [
        Path(path).stem
        for path in release.RELEASE_PATHS
        if path.startswith("scripts/") and path.endswith(".py")
    ]
    seen: set[str] = set()
    while pending:
        module = pending.pop()
        if module in seen or module not in local:
            continue
        seen.add(module)
        tree = ast.parse(local[module].read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            dependency = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in local and top not in seen:
                        pending.append(top)
                continue
            if isinstance(node, ast.ImportFrom) and node.module:
                parts = node.module.split(".")
                if parts[0] == "scripts" and len(parts) > 1:
                    dependency = parts[1]
                elif parts[0] in local:
                    dependency = parts[0]
            if dependency in local and dependency not in seen:
                pending.append(dependency)
    missing = sorted(
        f"scripts/{local[module].name}"
        for module in seen
        if f"scripts/{local[module].name}" not in release_paths
    )
    assert missing == []


def test_modern_conversation_modules_are_carried_by_immutable_release() -> None:
    required = {
        "scripts/chatgpt_conversation_discovery.py",
        "scripts/sqlite_conversation_binding.py",
        "scripts/sqlite_wake_turn_map.py",
    }
    assert required <= set(release.RELEASE_PATHS)
