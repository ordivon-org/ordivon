"""Bounded exact-Git input contract shared by repository selector consumers.

Only known source bytes, modes and membership/presence are qualified.
No dynamic tool closure, installed state, external assumptions or proof
reuse is established. The CI consumer executes the committed script.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import tomllib
from pathlib import Path

SELECTOR_INPUTS = (
    "tools/repo/selector_source_contract.py",
    "tools/repo/convergence_plan.py",
    "tools/repo/affected_owners.py",
    "tools/repo/pg_issuer_consumer.py",
    "tools/repo/owners.toml",
    "tools/repo/dependency_contracts.toml",
    "tools/formal/verify.py",
    "docs/architecture/structure-r2-transition-r1.json",
    "mise.toml",
)

SCOPE_INPUTS = {
    "ci": (".github/workflows/ci.yml", "tools/repo/ci_owner_shards.py"),
    "projection": ("tools/repo/exhaustive_coverage.py", "tools/repo/source_history_legos.py"),
    "evidence": (
        "tools/repo/evidence_validity.py", "tools/repo/evidence_source_policy.py",
        "tools/repo/evidence_github_checks.py", "tools/repo/evidence_check_decision.py",
        "tools/repo/source_history_legos.py", "tools/repo/ci_telemetry.py",
    ),
}


def control_inputs(scope: str) -> tuple[str, ...]:
    if scope not in SCOPE_INPUTS:
        raise ValueError("unknown selector source qualification scope")
    return SELECTOR_INPUTS + SCOPE_INPUTS[scope]


def _native(repo: Path, *args: str) -> bytes:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["GIT_GRAFT_FILE"] = os.devnull
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), *args],
        env=env, stderr=subprocess.PIPE,
    )


def _canonical(relative: object) -> str:
    if not isinstance(relative, str) or not relative:
        raise ValueError("invalid selector source path")
    value = relative.removesuffix("/")
    if (not value or value.startswith("/") or chr(92) in value
            or any(part in ("", ".", "..") for part in value.split("/"))
            or any(char in value for char in "*?[]")):
        raise ValueError("noncanonical selector source path: " + relative)
    return value


def qualify_selector_source(repo: Path, source_cut: str, *, scope: str) -> None:
    """Reject a mixed checkout before/after a known selector operation."""
    repo = repo.resolve()
    head = _native(repo, "rev-parse", "HEAD").decode().strip()
    root = Path(os.fsdecode(_native(repo, "rev-parse", "--show-toplevel").rstrip(b"\n")))
    if root.resolve() != repo or head != source_cut:
        raise ValueError("SourceCut mismatch with active native verification contract")
    raw = _native(repo, "ls-tree", "-rz", "--full-tree", source_cut)
    tree: dict[str, tuple[str, str, str]] = {}
    for entry in raw.split(b"\x00"):
        if entry:
            metadata, name = entry.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split()
            tree[os.fsdecode(name)] = (mode, kind, oid)

    verified: set[str] = set()

    def verify_file(relative: object) -> None:
        rel = _canonical(relative)
        if rel in verified:
            return
        path = repo / rel
        identity = tree.get(rel)
        category = "executed producer source" if rel.endswith(".py") else "verification contract"
        if (identity is None or identity[0] not in ("100644", "100755")
                or identity[1] != "blob" or not path.is_file()
                or path.is_symlink() or path.resolve() != path):
            raise ValueError(f"{category} is not a regular Git file: {rel}")
        mode = "100755" if path.stat().st_mode & stat.S_IXUSR else "100644"
        actual = _native(repo, "hash-object", "--no-filters", "--", rel).decode().strip()
        if mode != identity[0] or actual != identity[2]:
            raise ValueError(f"{category} differs from exact Git SourceCut: {rel}")
        verified.add(rel)

    def presence(relative: object) -> None:
        rel = _canonical(relative)
        path = repo / rel
        if rel in tree:
            verify_file(rel)
        elif any(key.startswith(rel + "/") for key in tree):
            if not path.is_dir() or path.is_symlink() or path.resolve() != path:
                raise ValueError(f"selector source directory differs from exact Git SourceCut: {rel}")
        elif path.exists() or path.is_symlink():
            raise ValueError(f"selector source presence differs from exact Git SourceCut: {rel}")

    for rel in control_inputs(scope):
        verify_file(rel)

    # Derive witnesses from the existing dependency contract, not a new
    # registry. Parse the committed bytes after their live qualification.
    contracts = tomllib.loads(_native(
        repo, "show", f"{source_cut}:tools/repo/dependency_contracts.toml"
    ).decode("utf-8"))
    scanned: set[str] = set()
    for seam in contracts.get("seams", []):
        kind = seam.get("kind")
        if kind not in ("TEST_ONLY_SOURCE_CONTRACT", "TEST_ONLY_NATIVE_RUNTIME_CONSUMER"):
            continue
        source = seam.get("source_glob")
        rel = _canonical(source)
        verify_file(seam.get("contract_ref"))
        if source.endswith("/"):
            if (kind, seam.get("from_owner"), seam.get("to_owner")) != (
                "TEST_ONLY_NATIVE_RUNTIME_CONSUMER", "runtime", "harness"
            ):
                raise ValueError("unqualified selector directory readset")
            if rel in scanned:
                continue
            presence(rel)
            prefix = rel + "/"
            # The existing locator scans all Rust members, including absence
            # of another matching consumer. Qualify membership as well as bytes.
            expected = {
                key for key in tree if key.startswith(prefix) and key.endswith(".rs")
            }
            actual = {
                path.relative_to(repo).as_posix()
                for path in (repo / rel).rglob("*.rs")
            }
            if not expected or actual != expected:
                raise ValueError(f"selector Rust membership differs from exact Git SourceCut: {rel}")
            for member in sorted(expected):
                verify_file(member)
            scanned.add(rel)
        else:
            verify_file(rel)
        if kind == "TEST_ONLY_SOURCE_CONTRACT":
            presence(seam.get("allowed_fragment"))

    # The relocation mapper consumes live existence and directory checks.
    # Untracked resurrection of an old source root changes that result.
    relocation = json.loads(_native(
        repo, "show", f"{source_cut}:docs/architecture/structure-r2-transition-r1.json"
    ))
    for row in relocation.get("mappings", []):
        old, new = row.get("sourcePaths"), row.get("targetPaths")
        if (row.get("mode") == "move" and row.get("standing") == "DEPLOYED"
                and isinstance(old, list) and isinstance(new, list)
                and len(old) == len(new) == 1
                and isinstance(old[0], str) and isinstance(new[0], str)):
            presence(old[0])
            presence(new[0])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-cut", required=True)
    parser.add_argument("--scope", required=True, choices=tuple(SCOPE_INPUTS))
    args = parser.parse_args()
    try:
        qualify_selector_source(Path.cwd(), args.source_cut, scope=args.scope)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
