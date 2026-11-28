"""Known control-input qualification for read-only Owner impact projection.

This does not attest dynamic inputs, a full dependency graph or proof reuse.
It rejects mixing a historical Git diff with a different local policy cut.
"""
from __future__ import annotations

import stat
import tomllib
from pathlib import Path

from pg_issuer_consumer import RUNTIME_PG_CORE_ROOT
from source_history_legos import current_tree, git

# Bounded direct producer inputs of the current selector. The later
# pg_issuer_consumer adapter is checked if present in the target tree.
CONTROL_INPUTS = (
    "tools/repo/evidence_validity.py",
    "tools/repo/evidence_github_checks.py",
    "tools/repo/evidence_formal_archive.py",
    "tools/repo/evidence_check_decision.py",
    "tools/repo/evidence_source_policy.py",
    "tools/repo/source_history_legos.py",
    "tools/repo/convergence_plan.py",
    "tools/repo/affected_owners.py",
    "tools/repo/owners.toml",
    "tools/repo/dependency_contracts.toml",
    "tools/formal/verify.py",
    "docs/architecture/structure-r2-transition-r1.json",
    "mise.toml",
)


def _regular_input(repo: Path, relative: str, tree: dict[str, str]) -> None:
    file = repo / relative
    identity = tree.get(relative, "")
    if (
        not identity.startswith(("100644:blob:", "100755:blob:"))
        or not file.is_file()
        or file.is_symlink()
        or file.resolve() != file
    ):
        raise ValueError("selector control input is not a regular Git file")
    expected_mode, _, expected_blob = identity.split(":")
    actual_mode = "100755" if file.stat().st_mode & stat.S_IXUSR else "100644"
    actual = git(repo, "hash-object", "--no-filters", "--", relative).strip()
    if actual_mode != expected_mode or actual != expected_blob:
        raise ValueError(f"selector control input differs from SourceCut: {relative}")


def _literal_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("selector seam path is not a literal Git path")
    path = value.rstrip("/")
    if (not path or path.startswith("/") or Path(path).as_posix() != path
            or any(part in {".", ".."} for part in path.split("/"))
            or any(char in value for char in "\\*?[]")):
        raise ValueError("selector seam path is not a literal Git path")
    return path


def _seam_inputs(repo: Path, tree: dict[str, str]) -> set[str]:
    """Derive the bounded source reads of the existing test-only seam selector.

    The native graph checks these exact files and, for the issuer locator,
    scans a Rust subtree. Do not introduce a second seam manifest or claim
    that this list closes all dynamic proof/consumer inputs.
    """
    data = tomllib.loads((repo / "tools/repo/dependency_contracts.toml").read_text(encoding="utf-8"))
    seams = data.get("seams", [])
    if not isinstance(seams, list):
        raise ValueError("selector dependency seams are not a list")
    inputs: set[str] = set()
    for seam in seams:
        if not isinstance(seam, dict):
            raise ValueError("selector dependency seam is not a table")
        kind = seam.get("kind")
        if kind not in {"TEST_ONLY_SOURCE_CONTRACT", "TEST_ONLY_NATIVE_RUNTIME_CONSUMER"}:
            continue
        source = _literal_path(seam.get("source_glob"))
        inputs.add(_literal_path(seam.get("contract_ref")))
        if kind == "TEST_ONLY_NATIVE_RUNTIME_CONSUMER" and source == RUNTIME_PG_CORE_ROOT.rstrip("/"):
            root = repo / source
            if not root.is_dir() or root.resolve() != root:
                raise ValueError("selector issuer scanner membership is unqualified")
            expected = {path for path in tree if path.startswith(source + "/") and path.endswith(".rs")}
            observed = {path.relative_to(repo).as_posix() for path in root.rglob("*.rs")
                        if path.is_file() and not path.is_symlink()}
            if expected != observed:
                raise ValueError("selector issuer scanner membership differs from SourceCut")
            inputs.update(expected)
        else:
            inputs.add(source)
        if kind == "TEST_ONLY_SOURCE_CONTRACT":
            # The selector checks the provider's path existence, not the
            # contents of an entire provider directory.
            provider = _literal_path(seam.get("allowed_fragment"))
            target = repo / provider
            if target.resolve() != target or not target.exists():
                raise ValueError("selector provider path differs from SourceCut")
            if provider in tree:
                inputs.add(provider)
            elif not target.is_dir() or not any(path.startswith(provider + "/") for path in tree):
                raise ValueError("selector provider path differs from SourceCut")
    return inputs


def qualify_current_selector(repo: Path, source_cut: str) -> None:
    repo = repo.resolve()
    producer_root = Path(__file__).resolve().parents[2]
    if (
        repo != producer_root
        or git(repo, "rev-parse", "HEAD").strip() != source_cut
    ):
        raise ValueError("selector policy checkout differs from requested SourceCut")
    tree = current_tree(repo, source_cut)
    paths = (*CONTROL_INPUTS, "tools/repo/pg_issuer_consumer.py") if (
        "tools/repo/pg_issuer_consumer.py" in tree
    ) else CONTROL_INPUTS
    for relative in paths:
        _regular_input(repo, relative, tree)
    for relative in sorted(_seam_inputs(repo, tree) - set(paths)):
        _regular_input(repo, relative, tree)
